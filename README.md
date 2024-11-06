
# Funny Event Scraper

このリポジトリは、お笑い公演や劇場イベント情報の取得を目的としたPythonベースのスクレイピングプロジェクトです。対象ページからチケット情報やスケジュールを収集し、CSV形式で保存します。

## 必要環境

- Python 3.8以上
- ChromeDriver

---

## インストール

0. **事前準備**
   ```bash
   sudo apt update -y

   sudo apt install -y python3-pip
   ```

   ### Google Chrome Install
   ```bash
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

   sudo apt install -y ./google-chrome-stable_current_amd64.deb
   ```

   ### ChromeDriver install
   ```bash
   cd /tmp/
   ```

   最新版は https://sites.google.com/chromium.org/driver/downloads から入手する
   ```bash
   curl -O https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.69/linux64/chromedriver-linux64.zip
   ```

   ### ChromeDriverに実行権限を付与
   ```bash
   unzip chromedriver-linux64.zip && \
   cd chromedriver-linux64/ && \
   sudo mv chromedriver /usr/local/bin/ && \
   sudo chmod +x /usr/local/bin/chromedriver
   ```

   不要になったファイル等は削除
   ```bash
   cd .. && \
   rm chromedriver-linux64.zip && \
   rm -rf chromedriver-linux64/
   ```

   依存ライブラリをインストール
   ```bash
   sudo apt install -y libnss3 libatk-bridge2.0-0 libx11-xcb1
   ```


1. **リポジトリのクローン**
   ```bash
   git clone git@github.com:ykyk-314/funny-event-scraper.git
   cd funny-event-scraper
   ```

2. **利用ライブラリのインストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **.envファイルの作成**  
   プロジェクトルートに`.env`ファイルを作成し、必要情報を記述してください。

   ```bash
   cp .env.dist .env
   ```
