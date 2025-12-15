import os
import streamlit as st
import requests
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

API_KEY = os.getenv("API_SECRET_KEY")

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

# ページ設定
st.set_page_config(page_title="経済ニュースリーダー", page_icon="📰", layout="wide")

# APIのURL (Dockerネットワーク内ではなく、ブラウザからアクセス可能なURLを指定)
API_URL = "https://stock-news-api.go-pro-world.net/news"

st.title("📰 経済ニュース・ダッシュボード")
st.caption("日経ビジネス・Yahooニュース・東洋経済から最新記事を取得しています")

# データの取得（キャッシュを利用して高速化）
@st.cache_data(ttl=600)  # 10分間キャッシュ
def fetch_news():
    try:
        # ヘッダーにAPIキーをセット
        headers = {"X-API-KEY": API_KEY}
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        df = pd.DataFrame(data)
        # 日時を読みやすい形式に変換
        df['scraped_at'] = pd.to_datetime(df['scraped_at']).dt.strftime('%Y/%m/%d %H:%M')
        return df
    except Exception as e:
        st.error(f"APIからのデータ取得に失敗しました: {e}")
        return pd.DataFrame()

df = fetch_news()

if not df.empty:
    # ニュースソースごとにタブを作成
    sources = ["すべて"] + list(df['source'].unique())
    tabs = st.tabs(sources)

    for i, source in enumerate(sources):
        with tabs[i]:
            # フィルタリング
            filtered_df = df if source == "すべて" else df[df['source'] == source]
            
            # 記事をリスト表示
            for _, row in filtered_df.iterrows():
                with st.container():
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        st.markdown(f"### [{row['title']}]({row['url']})")
                        st.caption(f"ソース: {row['source']} | 取得日時: {row['scraped_at']}")
                    with col2:
                        # リンクボタン
                        st.link_button("記事を開く", row['url'])
                    st.divider()
else:
    st.info("現在表示できるニュースはありません。スクレイパーが動作しているか確認してください。")
