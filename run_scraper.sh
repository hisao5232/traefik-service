#!/bin/bash
set -e  # エラーが起きたらその時点で中止する設定

# フルパスで移動
cd /home/hisao/traefik-service

# 実行ログに見出しを付ける（デバッグ用）
echo "--- Scraping started at $(date) ---"

# 実行
/usr/bin/docker compose run --rm scraper

echo "--- Scraping finished at $(date) ---"
