# Traefik + Docker Compose サンプル構成  
Flask と Streamlit をサブドメインで公開するプロジェクト

このプロジェクトは **Traefik（リバースプロキシ）** を使って  
以下の 3 サービスを HTTPS で公開する構成です。

| サービス | URL |
|---------|------|
| Flask | https://todo-flask.YOUR_DOMAIN |
| Streamlit | https://stock-streamlit.YOUR_DOMAIN |
| Traefik Dashboard | https://traefik.YOUR_DOMAIN |

---

## 📁 ディレクトリ構成
```
traefik-service/
├── docker-compose.yml
├── .env
├── .gitignore
├── traefik/
│ ├── traefik.toml
│ ├── dynamic_conf.toml
│ └── acme.json
├── flask/
│ ├── app.py
│ ├── Dockerfile
│ └── requirements.txt
└── streamlit/
├── app.py
├── Dockerfile
└── requirements.txt
```

---

## 🔧 必要環境

- Ubuntu / Debian / WSL2
- Docker
- Docker Compose plugin
- Git

---

## 🧩 1. `.env` の作り方

プロジェクト直下に `.env` を作成します。

```env
DOMAIN=go-pro-world.net
ACME_EMAIL=your-email@example.com

# admin:YOUR_PASSWORD の Basic Auth ハッシュ値
TRAEFIK_BASIC_AUTH=admin:$apr1$dqmYvnm4$/n7dj4SUVSbpa5TpCMAug.
```

## 🔐 Basic Auth のハッシュ生成コマンド

htpasswd が無い場合はインストール
```bash
sudo apt install -y apache2-utils
```

生成：
```bash
htpasswd -nb admin YOUR_PASSWORD
```
## 🚀 2. Docker 起動方法

初回ビルド：
```bash
docker compose up -d --build
```

通常起動：
```bash
docker compose up -d
```

ログ確認：
```bash
docker compose logs -f
```

## 🌐 3. DNS設定（重要）

ドメイン側で次の A レコードを作成：

サブドメイン	IP	用途
todo-flask	VPS の IP	Flask
stock-streamlit	VPS の IP	Streamlit
traefik	VPS の IP	Dashboard

## 📊 4. Traefik ダッシュボードの見方

アクセス：
```
https://traefik.DOMAIN
```

主な項目
項目	意味
Routers	ドメインごとのルーティング設定
Services	バックエンドコンテナの情報
Middlewares	Basic Auth / Redirect / RateLimit
Certificates	Let’s Encrypt の SSL 証明書ステータス
Providers	docker / file の設定状況
