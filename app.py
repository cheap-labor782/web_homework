import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from dash import Dash, dcc, html

# ==========================================
# 1. 資料處理與圖表生成函數
# ==========================================
def create_stock_chart(ticker="2330.TW"):
    # 獲取數據
    data = yf.download(ticker, start="2022-01-01", end="2026-05-20")
    if data.empty:
        return go.Figure()
    
    # 修正 MultiIndex 問題
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 特徵工程：計算指標
    data["MA5"] = data["Close"].rolling(window=5).mean()
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["20_STD"] = data["Close"].rolling(window=20).std()
    data["Upper"] = data["MA20"] + (data["20_STD"] * 2)
    data["Lower"] = data["MA20"] - (data["20_STD"] * 2)

    # 計算 OBV (成交量指標)
    direction = np.select(
        [data["Close"] > data["Close"].shift(1), data["Close"] < data["Close"].shift(1)],
        [1, -1], default=0
    )
    data["OBV"] = (direction * data["Volume"]).cumsum()

    # 圖表邏輯
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, 
        vertical_spacing=0.05, row_width=[1, 4],
        specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
    )

    # 主圖：K線與布林通道
    fig.add_trace(go.Candlestick(x=data.index, open=data["Open"], high=data["High"], 
                                 low=data["Low"], close=data["Close"], name="K線"), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data["Upper"], name="布林上軌", 
                             line=dict(color="rgba(173,216,230,0.5)", dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data["Lower"], name="布林下軌", 
                             line=dict(color="rgba(173,216,230,0.5)", dash="dash")), row=1, col=1)

    # 副圖：成交量
    fig.add_trace(go.Bar(x=data.index, y=data["Volume"], name="成交量", opacity=0.5), row=2, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=data.index, y=data["OBV"], name="OBV", line=dict(color="blue")), row=2, col=1, secondary_y=True)

    fig.update_layout(height=700, template="plotly_white", xaxis_rangeslider_visible=False)
    return fig

# ==========================================
# 2. 建立 Dash App 與 部署準備
# ==========================================
app = Dash(__name__)
server = app.server  # 這是給 Render/Heroku 呼叫的關鍵

app.layout = html.Div(style={'padding': '20px'}, children=[
    html.H1("台股技術分析儀表板 (AI 部署演示)", style={'textAlign': 'center'}),
    dcc.Graph(id='stock-candle-chart', figure=create_stock_chart("2330.TW"))
])

if __name__ == '__main__':
    app.run_server(debug=False)
    
    html.Footer("使用 Dash + Plotly 建立", style={'textAlign': 'right', 'fontSize': '12px', 'marginTop': '20px'})
])

if __name__ == '__main__':
    # 執行後開啟瀏覽器訪問 http://127.0.0.1:8050
    app.run_server(debug=True)
