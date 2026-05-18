# Kronos 股票预测工具

> 基于 Kronos 基础模型的 A 股走势预测工具，提供 WebUI 界面和一键安装脚本。

## 快速开始

### 一键安装（推荐）

```bash
bash install.sh
```

脚本会自动完成以下操作：
1. 检查 Python 版本（需要 3.10+）
2. 创建虚拟环境
3. 安装所有依赖
4. 从 HuggingFace 下载模型到本地缓存

### 启动 WebUI

```bash
bash webui/start.sh
```

或者手动启动：

```bash
source kronos_env/bin/activate
python webui/app.py
```

然后在浏览器中访问 **http://localhost:8899**

## 功能介绍

### WebUI 预测界面

输入股票代码即可进行实时预测：

- **股票代码**：输入 A 股代码（如 601138）
- **历史K线数**：用于预测的历史数据量（默认 200 根）
- **预测K线数**：未来要预测的数据量（默认 48 根，约 4 小时）

页面会展示：
- 历史收盘价 + 预测收盘价的对比曲线
- 成交量对比图
- 最新价、预测收盘价、涨跌幅统计

### 命令行预测

也可以使用 Python 脚本进行命令行预测：

```python
from model import Kronos, KronosTokenizer, KronosPredictor
import pandas as pd

# 加载模型
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
predictor = KronosPredictor(model, tokenizer, max_context=512)

# 准备数据（需要包含 open, high, low, close, volume, amount 列）
df = pd.read_csv("data/XSHG_5min_600977.csv")
df['timestamps'] = pd.to_datetime(df['timestamps'])

lookback = 400
pred_len = 120

x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
x_timestamp = df.loc[:lookback-1, 'timestamps']
y_timestamp = pd.date_range(start=df['timestamps'].iloc[-1] + pd.Timedelta(minutes=5), periods=pred_len, freq="5min")
y_timestamp = pd.Series(y_timestamp)

# 预测
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,
    top_p=0.9,
    sample_count=3,
)

print("预测结果：")
print(pred_df.head())
```

更多示例请参考 `examples/` 目录下的脚本。

## 数据获取

### 使用 opencli（推荐）

获取实时 5 分钟 K 线数据：

```bash
opencli eastmoney kline 601138 --period 5m --limit 200 -f json
```

安装 opencli：

```bash
npm install -g opencli
```

### 使用 akshare

```python
import akshare as ak
df = ak.stock_zh_a_hist_min_em(symbol="601138", period="5", adjust="qfq")
```

## 常见问题

### Q: 模型下载失败

模型会自动下载到 HuggingFace 缓存目录（`~/.cache/huggingface/hub`）。如果网络不佳，可以设置镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

然后重新运行 `install.sh`。

### Q: 预测结果不准

Kronos 是一个基础模型，预测结果反映的是历史数据中的统计规律，不构成投资建议。可以通过以下方式改善：
- 增加历史数据量（`history_bars`）
- 增加采样次数（`sample_count`）获得更稳定的结果
- 在自己的数据上微调模型（参考 `finetune/` 目录）

### Q: 支持哪些市场

当前版本主要支持中国 A 股市场。模型在 45 个全球交易所的数据上预训练，理论上可以预测其他市场，但需要调整数据格式。

### Q: 如何修改预测端口

编辑 `webui/app.py` 最后一行，修改 `port=8899` 为其他端口。

## 目录结构

```
├── install.sh              # 一键安装脚本
├── README_ZH.md            # 中文说明文档
├── requirements.txt        # Python 依赖
├── model/                  # Kronos 模型代码
│   ├── kronos.py           # 主模型定义
│   └── module.py           # 模型模块
├── webui/                  # WebUI 界面
│   ├── app.py              # FastAPI 后端
│   ├── index.html          # 前端页面
│   ├── requirements.txt    # WebUI 依赖
│   └── start.sh            # 启动脚本
├── examples/               # 示例脚本
│   ├── prediction_example.py
│   └── get_date_new.py     # 数据获取脚本
├── finetune/               # 模型微调脚本
└── data/                   # 示例数据
```

## 依赖

- Python 3.10+
- PyTorch >= 2.0.0
- FastAPI + Uvicorn（WebUI）
- opencli（可选，用于实时数据获取）
- akshare（可选，用于历史数据获取）

## 许可证

本项目遵循 [MIT License](./LICENSE)

## 致谢

- [Kronos](https://github.com/shiyu-coder/Kronos) - 基础模型
- [HuggingFace](https://huggingface.co/NeoQuasar) - 模型托管
