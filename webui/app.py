import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import json
import sys
import traceback
import os
import base64
import io
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model import Kronos, KronosTokenizer, KronosPredictor

app = FastAPI()

# 全局模型实例（启动时加载一次）
model = None
predictor = None

def load_model():
    global model, predictor
    print("Loading Kronos model...")
    tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
    predictor = KronosPredictor(model, tokenizer, max_context=512)
    print("Model loaded successfully.")

@app.on_event("startup")
def startup():
    load_model()

class PredictRequest(BaseModel):
    stock_code: str
    history_bars: int = 200
    predict_bars: int = 48

def fetch_stock_data(stock_code: str, bars: int = 200):
    """通过 opencli 获取实时K线数据（5分钟级别）"""
    result = subprocess.run(
        ["opencli", "eastmoney", "kline", stock_code, "--period", "5m", "--limit", str(bars), "-f", "json"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise Exception(f"opencli 调用失败: {result.stderr}")

    data = json.loads(result.stdout)
    rows = []
    for item in data:
        rows.append({
            "timestamps": item.get("date", item.get("timestamp", item.get("time"))),
            "open": float(item["open"]),
            "high": float(item["high"]),
            "low": float(item["low"]),
            "close": float(item["close"]),
            "volume": float(item.get("volume", 0)),
            "amount": float(item.get("turnover", item.get("amount", 0))),
        })
    df = pd.DataFrame(rows)
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    return df

def generate_chart(kline_df, pred_df, lookback, pred_len, stock_code):
    """生成K线预测图"""
    kline_df = kline_df.copy()
    kline_df["time_idx"] = pd.to_datetime(kline_df["timestamps"])
    kline_df.set_index("time_idx", inplace=True)

    # 预测结果的时间索引使用 pred_df 原有的 index（由 predictor 返回）
    pred_df = pred_df.copy()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    ax1.plot(kline_df.index, kline_df["close"], label="Ground Truth", color="blue", linewidth=1.5)
    ax1.plot(pred_df.index, pred_df["close"], label="Prediction", color="red", linewidth=1.5)
    ax1.set_ylabel("Close Price", fontsize=14)
    ax1.legend(loc="lower left", fontsize=12)
    ax1.grid(True)

    ax2.plot(kline_df.index, kline_df["volume"], label="Ground Truth", color="blue", linewidth=1.5)
    ax2.plot(pred_df.index, pred_df["volume"], label="Prediction", color="red", linewidth=1.5)
    ax2.set_ylabel("Volume", fontsize=14)
    ax2.legend(loc="upper left", fontsize=12)
    ax2.grid(True)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

@app.post("/api/predict")
async def predict(req: PredictRequest):
    if predictor is None:
        return {"error": "模型未加载"}
    
    try:
        # 1. 获取数据
        df = fetch_stock_data(req.stock_code, req.history_bars)
        
        lookback = min(req.history_bars, 400)
        pred_len = req.predict_bars
        
        x_df = df.loc[:lookback-1, ["open", "high", "low", "close", "volume", "amount"]]
        x_timestamp = df.loc[:lookback-1, "timestamps"]
        
        # 生成未来时间戳（每5分钟一根）
        last_ts = df["timestamps"].iloc[-1]
        y_timestamp = pd.Series(pd.date_range(start=last_ts + pd.Timedelta(minutes=5), periods=pred_len, freq="5min"))
        
        # 2. 预测
        pred_df = predictor.predict(
            df=x_df,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=pred_len,
            T=1.0,
            top_p=0.9,
            sample_count=3,
            verbose=False,
        )

        # 设置预测结果的时间索引
        pred_df.index = [pd.Timestamp(t) for t in y_timestamp.values]
        
        # 3. 生成图表
        chart_b64 = generate_chart(df, pred_df, lookback, pred_len, req.stock_code)
        
        # 4. 统计信息
        latest_close = df["close"].iloc[-1]
        pred_close = pred_df["close"].iloc[-1]
        change_pct = (pred_close - latest_close) / latest_close * 100
        
        return {
            "chart": chart_b64,
            "stock_code": req.stock_code,
            "latest_close": float(round(latest_close, 2)),
            "pred_close": float(round(pred_close, 2)),
            "change_pct": float(round(change_pct, 2)),
        }
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/")
async def index():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8899)
