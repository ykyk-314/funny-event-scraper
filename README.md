
# Funny Event Scraper

このリポジトリは、お笑い公演や劇場イベント情報の取得を目的としたPythonベースのスクレイピングプロジェクトです。対象ページからチケット情報やスケジュールを収集し、CSV形式で保存します。

## 必要環境

- Python 3.8以上
- ChromeおよびChromeDriver
- `git` (オプション：リポジトリのクローン時)

---

## インストール手順

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/your-username/funny-event-scraper.git
   cd funny-event-scraper
   ```

2. **必要ライブラリのインストール**
   以下のコマンドでライブラリをインストールします。
   ```bash
   pip install -r requirements.txt
   ```

3. **ChromeDriverのインストール**
   - Chromeのバージョンに対応した[ChromeDriver](https://chromedriver.chromium.org/)をダウンロードします。
   - `/usr/local/bin/`に配置するか、PATHを通してください。

---

## 設定

1. **.envファイルの作成**  
   プロジェクトルートに`.env`ファイルを作成し、必要情報を記述してください。

   ```bash
   cp .env.dist .env
   ```

---

## 実行方法

1. **フライヤー画像のダウンロード**
   ```bash
   python3 download_flier_images.py
   ```

2. **タレントチケット情報の取得**
   ```bash
   python3 talent_tickets.py
   ```

3. **劇場スケジュールの取得**
   ```bash
   python3 theater_schedules.py
   ```

---

## 注意事項

- 対象サイトの仕様変更により、取得処理が正常に動作しなくなる場合があります。
- スクレイピングの使用については対象サイトの利用規約を遵守してください。
