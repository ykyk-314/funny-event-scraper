import time as t
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from dotenv import load_dotenv
import os
import re

load_dotenv()

chromedriver_path = os.getenv('CHROMEDRIVER_PATH')

login_url = "https://ty.funity.jp/ticket/mypage_top/view?clientid=yoshimoto"
login_id = os.getenv('FANY_LOGIN_ID')
login_pw = os.getenv('FANY_LOGIN_PW')

def setup_driver_options():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.92 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    return options

def login():
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=setup_driver_options())
    try:
        driver.get(login_url)

        # リダイレクトを待機
        t.sleep(2)

        # ログイン情報を入力
        driver.find_element(By.NAME, "loginId").send_keys(login_id)
        driver.find_element(By.NAME, "loginPw").send_keys(login_pw)

        # ログインボタンをクリック
        driver.find_element(By.ID, "LoginAction_0").click()

        # ページ遷移の待機
        t.sleep(1)

        # ログイン成功の確認
        try:
            member_id = driver.find_element(By.ID, "memberId").text
            if member_id == login_id:
                print("Login successful.")
                return driver
            else:
                print("Login failed: Member ID does not match.")
                driver.quit()
                return None
        except Exception as e:
            print("Login failed: Member ID not found.")
            driver.quit()
            return None
    except Exception as e:
        print(f"An error occurred during login: {e}")
        driver.quit()
        return None

def split_venue_location(venue):
    match = re.match(r"(.+?)[\(（](.+?)[\)）]$", venue)
    if match:
        return match.group(1), match.group(2)
    return venue, ""

def scrape_reservation_details(driver, reservation_id):
    try:
        # 予約番号リンクをクリック
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{reservation_id}')]"))).click()

        # ページ遷移の待機
        t.sleep(1)

        # 詳細情報を取得
        open_time = driver.find_element(By.ID, "lbl_HallOpenTime").text if driver.find_elements(By.ID, "lbl_HallOpenTime") else ""
        start_time = driver.find_element(By.ID, "lbl_ShowStartTime").text if driver.find_elements(By.ID, "lbl_ShowStartTime") else ""
        pickup_method = driver.find_element(By.ID, "lbl_GetMethod").text if driver.find_elements(By.ID, "lbl_GetMethod") else ""
        pickup_method = "劇場" if pickup_method == "自動発券機・劇場窓口" else pickup_method
        ticket_number = driver.find_element(By.ID, "lbl_Caution2").text if driver.find_elements(By.ID, "lbl_Caution2") else ""
        total_price = driver.find_element(By.ID, "lbl_TotalMoney").text.replace(",", "") if driver.find_elements(By.ID, "lbl_TotalMoney") else ""

        # 戻るボタンをクリックして履歴ページに戻る
        driver.back()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-funity tbody tr")))

        return open_time, start_time, pickup_method, ticket_number, total_price

    except Exception as e:
        print(f"An error occurred while fetching details for reservation {reservation_id}: {e}")
        return "", "", "", "", ""

def scrape_purchase_history(driver):
    try:
        # 既存CSVを事前に読み込み予約番号をセットに格納
        csv_file = "purchase_history.csv"
        if os.path.exists(csv_file):
            existing_data = pd.read_csv(csv_file, encoding="utf-8-sig", dtype={"予約番号": str})
            existing_reservation_ids = set(existing_data["予約番号"])
        else:
            existing_reservation_ids = set()

        # "購入履歴" ボタンをクリック
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "InitAction_ticketReserve"))).click()

        # ページ遷移の待機
        t.sleep(1)

        # 履歴ページの確認
        if "履歴" not in driver.find_element(By.TAG_NAME, "h2").text:
            print("Failed to navigate to purchase history.")
            return

        history = []
        current_page = 1
        max_pages = 2  # 最大ページ数を2ページに制限

        while current_page <= max_pages:
            print(f"Scraping page {current_page}...")

            # テーブル行を再取得して処理
            rows = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.table-funity tbody tr"))
            )

            for index in range(len(rows)):
                try:
                    # ページ内のテーブル行を再取得
                    rows = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.table-funity tbody tr"))
                    )
                    row = rows[index]  # 再取得した行を使用

                    columns = row.find_elements(By.TAG_NAME, "td")
                    if len(columns) < 12:
                        continue

                    reservation_id = columns[1].text.strip()

                    # 既存予約番号と重複する場合スキップ
                    if reservation_id in existing_reservation_ids:
                        print(f"Skipping: {reservation_id}")
                        continue

                    event_date = columns[5].text.strip().replace("(", "（").replace(")", "）")
                    event_name = columns[3].text.strip()
                    venue, location = split_venue_location(columns[4].text.strip())
                    price = columns[8].text.strip().replace(",", "").replace("円", "")
                    quantity = columns[9].text.strip().replace("枚", "")
                    seat_type = columns[6].text.strip()
                    purchase_date = columns[2].text.strip().replace("(", "（").replace(")", "）")

                    open_time, start_time, pickup_method, ticket_number, total_price = scrape_reservation_details(driver, reservation_id)

                    # ソートIDの生成 (int型)
                    sort_id = int(
                        event_date[:4] + event_date[5:7] + event_date[8:10] +  # YYMMDD形式
                        open_time.replace(":", "").zfill(4) +  # HHMM形式
                        reservation_id[-3:]  # 予約番号末尾3桁
                    )

                    history.append({
                        "予約番号": reservation_id,
                        "公演日": event_date,
                        "開場": open_time,
                        "開演": start_time,
                        "公演名": event_name,
                        "会場名": venue,
                        "所在地": location,
                        "合計金額": total_price,
                        "枚数": quantity,
                        "分配": "",
                        "席種": seat_type,
                        "引取方法": pickup_method,
                        "引換票番号": ticket_number,
                        "購入日": purchase_date,
                        "ソートID": sort_id
                    })
                except Exception as e:
                    print(f"Error processing row: {e}")

            # 次のページへのリンクをクリック
            next_page = driver.find_elements(By.CSS_SELECTOR, "ul.pagenation a")
            next_links = [link for link in next_page if link.text.strip() == str(current_page + 1)]

            if next_links and current_page < max_pages:
                next_links[0].click()

                # ページ遷移の待機
                t.sleep(2)

                # ページ遷移確認
                if "履歴" not in driver.find_element(By.TAG_NAME, "h2").text:
                    print("Failed to navigate to purchase history.")
                    break

                current_page += 1
            else:
                break

        # 新規データをDataFrameに変換してCSVに追加
        if history:
            new_data = pd.DataFrame(history)
            # 明示的に文字列型に変換
            new_data["予約番号"] = new_data["予約番号"].astype(str)
            new_data["引換票番号"] = new_data["引換票番号"].astype(str)

            if os.path.exists(csv_file):
                existing_data = pd.read_csv(csv_file, encoding="utf-8-sig", dtype={"予約番号": str})
                combined_data = pd.concat([existing_data, new_data]).drop_duplicates(subset=["予約番号"])
            else:
                combined_data = new_data

            # ソートIDで降順ソート
            combined_data.sort_values(by="ソートID", ascending=False, inplace=True)

            # CSVに保存
            combined_data.to_csv(csv_file, index=False, encoding="utf-8-sig")
            print("購入履歴をCSVに更新しました。")
        else:
            print("No new data to add.")

    except Exception as e:
        print(f"An error occurred while scraping purchase history: {e}")

if __name__ == "__main__":
    driver = login()
    if driver:
        scrape_purchase_history(driver)
        driver.quit()
