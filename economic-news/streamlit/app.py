import os
import streamlit as st
import requests
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

st.title("日経平均とドル円レートのチャート")

# --- 日経平均チャート ---
nikkei_ticker = "^N225"
period = st.selectbox("期間を選択", ["5d", "1mo", "3mo", "6mo", "1y", "2y"], index=1)

nikkei_data = yf.download(nikkei_ticker, period=period, interval="1d")
if isinstance(nikkei_data.columns, pd.MultiIndex):
    nikkei_data.columns = nikkei_data.columns.get_level_values(0)

# ここに昨日の日経平均の終値を表示　H2タグくらいの大きさ
if not nikkei_data.empty and "Close" in nikkei_data.columns:
    # 最後のデータポイント（通常は「昨日」の終値）を取得
    last_close_nikkei = nikkei_data["Close"].iloc[-1]
    # H2タグくらいの大きさで表示
    st.markdown(f"## 昨日の日経平均終値: {last_close_nikkei:,.2f}")
else:
    st.info("終値データが利用できません。")

st.subheader(f"{nikkei_ticker} のローソク足チャート")
if not nikkei_data.empty and all(col in nikkei_data.columns for col in ["Open", "High", "Low", "Close"]):
    fig_nikkei = go.Figure(
        data=[
            go.Candlestick(
                x=nikkei_data.index,
                open=nikkei_data["Open"],
                high=nikkei_data["High"],
                low=nikkei_data["Low"],
                close=nikkei_data["Close"],
                name="日経平均"
            )
        ]
    )
    fig_nikkei.update_layout(
        xaxis_title="日付",
        yaxis_title="価格",
        xaxis_rangeslider_visible=False,
        yaxis=dict(tickformat=",.0f")  # 3桁カンマ区切りで整数表示
    )
    st.plotly_chart(fig_nikkei)
else:
    st.warning("日経平均のデータがありません。")

# --- ドル円レートの折れ線グラフ ---
usd_jpy_ticker = "JPY=X"
usd_jpy_data = yf.download(usd_jpy_ticker, period=period, interval="1d")
if isinstance(usd_jpy_data.columns, pd.MultiIndex):
    usd_jpy_data.columns = usd_jpy_data.columns.get_level_values(0)

# ここに昨日のドル円の終値を表示　H2タグくらいの大きさ
if not usd_jpy_data.empty and "Close" in usd_jpy_data.columns:
    # 最後のデータポイント（通常は「昨日」の終値）を取得
    last_close_fx = usd_jpy_data["Close"].iloc[-1]
    # H2タグくらいの大きさで表示
    st.markdown(f"## 昨日のドル円終値: {last_close_fx:,.3f}円")
else:
    st.info("終値データが利用できません。")

st.subheader(f"{usd_jpy_ticker} の終値折れ線グラフ")
if not usd_jpy_data.empty and "Close" in usd_jpy_data.columns:
    fig_fx = go.Figure(
        data=[
            go.Scatter(
                x=usd_jpy_data.index,
                y=usd_jpy_data["Close"],
                mode="lines+markers",
                name="USD/JPY"
            )
        ]
    )
    fig_fx.update_layout(
        xaxis_title="日付",
        yaxis_title="為替レート"
    )
    st.plotly_chart(fig_fx)
else:
    st.warning("ドル円レートのデータがありません。")