import asyncio
import os
from datetime import datetime, timedelta
import pytz
from playwright.async_api import async_playwright

# PostgreSQL接続用ライブラリ
import asyncpg

# ==========================================================
# データベース設定 (環境変数から読み込む)
# ==========================================================
DB_USER = os.environ.get("POSTGRES_USER", "myuser")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "mypassword")
DB_NAME = os.environ.get("POSTGRES_DB", "scraped_data_db")
# Docker Composeのネットワーク内から接続する場合は 'db' をホスト名に指定
# ホストマシンから接続する場合は 'localhost' または '127.0.0.1' に変更してください
DB_HOST = os.environ.get("DB_HOST", "db") 
DB_PORT = os.environ.get("DB_PORT", "5432")

# === 各ニュースサイトのスクレイピング関数 ===
async def scrape_nikkei(page):
    await page.goto("https://business.nikkei.com/ranking/?i_cid=nbpnb_ranking", timeout=60000, wait_until="domcontentloaded")
    results = []
    article_list = page.locator('section.p-articleList_item')
    count = await article_list.count()
    for i in range(min(count, 10)):
        try:
            article = article_list.nth(i)
            title = await article.locator('h3.p-articleList_item_title').inner_text()
            href = await article.locator('a.p-articleList_item_link').get_attribute('href')
            if href and not href.startswith("http"):
                href = "https://business.nikkei.com" + href
            results.append((title.strip(), href))
        except:
            continue
    return results

async def scrape_yahoo(page):
    await page.goto("https://news.yahoo.co.jp/categories/business", timeout=60000, wait_until="domcontentloaded")
    results = []
    article_list = page.locator('a.sc-1nhdoj2-1')
    count = await article_list.count()
    for i in range(min(count, 10)):
        try:
            article = article_list.nth(i)
            title = await article.inner_text()
            url = await article.get_attribute('href')
            if url and title:
                results.append((title.strip(), url))
        except:
            continue
    return results

async def scrape_toyokeizai(page):
    await page.goto("https://toyokeizai.net/list/genre/market", timeout=60000, wait_until="domcontentloaded")
    results = []
    article_list = page.locator('li.wd217')
    count = await article_list.count()
    for i in range(min(count, 10)):
        try:
            article = article_list.nth(i)
            title = await article.locator('span.title').inner_text()
            href = await article.locator('span.title > a').get_attribute('href')
            if href and not href.startswith("http"):
                href = "https://toyokeizai.net" + href
            results.append((title.strip(), href))
        except:
            continue
    return results

# ==========================================================

async def setup_database():
    """データベースに接続し、テーブルが存在しなければ作成する"""
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )
        # テーブル作成SQL
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id SERIAL PRIMARY KEY,
                source VARCHAR(50) NOT NULL,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                scraped_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """)
        await conn.close()
        print("✅ データベース接続とテーブルのセットアップが完了しました。")
    except Exception as e:
        print(f"❌ データベース接続またはセットアップ中にエラーが発生しました: {e}")
        # スクレピングを実行させないように、致命的なエラーとして再raise
        raise

async def delete_old_data(conn):
    """1週間以上前の古いニュースデータを削除する"""
    try:
        # 現在時刻から7日前の時間を計算（JST）
        jst = pytz.timezone('Asia/Tokyo')
        one_week_ago = datetime.now(jst) - timedelta(days=7)

        # 削除クエリの実行
        delete_query = "DELETE FROM news_articles WHERE scraped_at < $1;"
        result = await conn.execute(delete_query, one_week_ago)
        
        # ログ出力（例：DELETE 5 のような形式から件数を取得）
        count = result.split(" ")[1]
        if int(count) > 0:
            print(f"🧹 古いデータを {count} 件削除しました。")
    except Exception as e:
        print(f"⚠️ 古いデータの削除中にエラーが発生しました: {e}")

async def save_to_database(news_data: list):
    """取得したニュースデータをPostgreSQLに保存する"""
    if not news_data:
        print("保存するデータがありません。")
        return

    # JSTタイムゾーンを設定
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst)

    # データベースに接続
    conn = None
    try:
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )
        
        # --- 追加: 保存の前に古いデータを削除 ---
        await delete_old_data(conn)
        # -----------------------------------

        # INSERTクエリ (ON CONFLICT DO NOTHINGで重複をスキップ)
        insert_query = """
            INSERT INTO news_articles(source, title, url, scraped_at) 
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (url) DO NOTHING;
        """
        
        # データベースに一括でデータを挿入
        # news_dataの要素は (source, title, url, timestamp) の順
        values = [(item[2], item[0], item[1], now_jst) for item in news_data]

        await conn.executemany(insert_query, values)
        print(f"✅ 合計 {len(news_data)} 件のデータをデータベースに保存（または更新）しました。")

    except Exception as e:
        print(f"❌ データベース保存中にエラーが発生しました: {e}")
        
    finally:
        if conn:
            await conn.close()

async def main():
    # データベースの準備（テーブル作成など）
    await setup_database()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        nikkei_page = await browser.new_page()
        yahoo_page = await browser.new_page()
        toyokeizai_page = await browser.new_page()

        # 並列スクレイピングを実行
        print("🚀 スクレイピングを開始します...")
        nikkei_task = scrape_nikkei(nikkei_page)
        yahoo_task = scrape_yahoo(yahoo_page)
        toyokeizai_task = scrape_toyokeizai(toyokeizai_page)

        nikkei_news, yahoo_news, toyokeizai_news = await asyncio.gather(
            nikkei_task, yahoo_task, toyokeizai_task
        )

        await browser.close()
        print("✅ スクレイピングが完了しました。")

        # データを一つのリストに統合 (title, url, source)
        all_news = []
        all_news.extend([(title, url, "日経") for title, url in nikkei_news])
        all_news.extend([(title, url, "Yahoo") for title, url in yahoo_news])
        all_news.extend([(title, url, "東洋経済") for title, url in toyokeizai_news])
        
        # データベースに保存
        await save_to_database(all_news)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"致命的なエラーにより処理を中断しました: {e}")
        