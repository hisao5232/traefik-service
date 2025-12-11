from flask import Flask, request
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

@app.route("/inbound", methods=["POST"])
def inbound_email():
    data = request.json

    try:
        email_data = data.get("data", {})
        
        # ヘッダー情報の取得
        sender = email_data.get("from")
        if isinstance(sender, list) and sender:
            sender = sender[0]
        to = email_data.get("to")
        if isinstance(to, list) and to:
            to = to[0]
        subject = email_data.get("subject", "件名なし")
        email_id = email_data.get("email_id") # Webhooksから取得するID

        if not email_id:
            return {"status": "error", "message": "email_idが見つかりません"}, 400

    except Exception as e:
        print(f"JSONデータの解析エラー: {e}")
        return {"status": "error", "message": "JSONデータの解析に失敗しました"}, 400

    # 🔑 本文の取得：確定した /emails/receiving/ エンドポイントを使用
    text = "本文の取得を試行中..."
    try:
        # 正しいエンドポイントを使用
        RESEND_RECEIVING_URL = f"https://api.resend.com/emails/receiving/{email_id}"
        
        r = requests.get(
            RESEND_RECEIVING_URL,
            # 認証ヘッダーを使用
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"}
        )
        r.raise_for_status() # 成功しなかった場合はここで例外を発生させる
        
        email = r.json()
        
        # レスポンスから 'text' を取得
        text = email.get("text", "本文（text）がAPIレスポンスから見つかりませんでした。")

    except requests.exceptions.HTTPError as e:
        # APIキーが無効など、エラーが発生した場合
        text = f"Resend APIエラー: {r.status_code} {r.reason}（API Keyまたは権限を確認）"
        print(f"Resend APIエラー: {e}")
    except requests.exceptions.RequestException as e:
        # ネットワークエラー
        text = f"API接続エラー: {e}"
        print(f"API接続エラー: {e}")
        
    # Discord 通知
    message = (
        f"📩 **メール受信！**\n\n"
        f"**From:** {sender}\n"
        f"**To:** {to}\n"
        f"**Subject:** {subject}\n\n"
        f"**Email ID:** {email_id}\n\n"
        f"**本文プレビュー:**\n"
        f">>> {text[:1500]}" 
    )
    
    requests.post(DISCORD_WEBHOOK, json={"content": message})
    
    return {"status": "ok"}
# ... (inbound_email関数の定義ここまで) ...

if __name__ == "__main__":
    # RESEND_API_KEYが正しく読み込まれているか確認するためのデバッグコードを追加
    if RESEND_API_KEY:
        # キーの先頭8文字だけを表示
        print(f"DEBUG: RESEND_API_KEY loaded: {RESEND_API_KEY[:8]}...") 
    else:
        print("ERROR: RESEND_API_KEY is NOT set!")
        
    print("FLASK START")
    app.run(host="0.0.0.0", port=3000, debug=True)

