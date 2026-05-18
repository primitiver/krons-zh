import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.append("../")
from model import Kronos, KronosTokenizer, KronosPredictor


def plot_prediction(kline_df, pred_df, lookback, pred_len):
    pred_df = pred_df.copy()
    pred_df.index = pd.to_datetime(kline_df.loc[lookback:lookback+pred_len-1, 'timestamps'].values)

    # 为真实值创建时间索引
    kline_df = kline_df.copy()
    kline_df.index = pd.to_datetime(kline_df['timestamps'].values)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    ax1.plot(kline_df.index, kline_df['close'], label='Ground Truth', color='blue', linewidth=1.5)
    ax1.plot(pred_df.index, pred_df['close'], label='Prediction', color='red', linewidth=1.5)
    ax1.set_ylabel('Close Price', fontsize=14)
    ax1.legend(loc='lower left', fontsize=12)
    ax1.grid(True)

    ax2.plot(kline_df.index, kline_df['volume'], label='Ground Truth', color='blue', linewidth=1.5)
    ax2.plot(pred_df.index, pred_df['volume'], label='Prediction', color='red', linewidth=1.5)
    ax2.set_ylabel('Volume', fontsize=14)
    ax2.legend(loc='upper left', fontsize=12)
    ax2.grid(True)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('prediction_result.png', dpi=150)
    print('结果已保存到 prediction_result.png')


# 1. Load Model and Tokenizer
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")

# 2. Instantiate Predictor
predictor = KronosPredictor(model, tokenizer, max_context=512)

# 3. Prepare Data
df = pd.read_csv("./data/XSHG_5min_600977.csv")
df['timestamps'] = pd.to_datetime(df['timestamps'])

lookback = 400
pred_len = 120

x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
x_timestamp = df.loc[:lookback-1, 'timestamps']
y_timestamp = df.loc[lookback:lookback+pred_len-1, 'timestamps']

# 4. Make Prediction
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,
    top_p=0.9,
    sample_count=1,
    verbose=True
)

# 5. Visualize Results
print("Forecasted Data Head:")
print(pred_df.head())

# Combine historical and forecasted data for plotting
kline_df = df.loc[:lookback+pred_len-1]

# visualize
plot_prediction(kline_df, pred_df, lookback, pred_len)

