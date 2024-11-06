import time as t
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
from dotenv import load_dotenv
import os
import json

load_dotenv()

chromedriver_path = os.getenv('CHROMEDRIVER_PATH')

talent_url = os.getenv('TALENT_BASE_URL')
talents = json.loads(os.getenv('TALENTS'))


def get_ticket_info(talent_id, talent_name):
    url = f"{talent_url}{talent_id}"
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=setup_driver_options())
    driver.get(url)

    # 隠れている要素を表示するJavaScriptの実行
    driver.execute_script("""
        document.querySelectorAll('[id^="feedItem2-"]').forEach(el => {
            el.style.display = 'grid';
        });
    """)

    events = []
    for event in driver.find_elements(By.CSS_SELECTOR, '#feed_ticket_info2 .feed-item-container'):
        title = get_element_text(event, '.feed-ticket-title')
        date = format_date(get_element_text(event, '.opt-feed-ft-dateside p:first-child'))
        time = get_element_text(event, '.opt-feed-ft-dateside p:last-child')
        members = get_element_text(event, '.opt-feed-ft-element-member').replace('\n', '|')
        venue = get_element_text(event, '.opt-feed-ft-element-venue')
        image = get_element_attribute(event, '.feed-item-img', 'src')
        link = get_element_attribute(event, '.feed-item-link', 'href')

        events.append({
            'Talent': talent_name,
            'ID': talent_id,
            'Title': title,
            'Date': date,
            'StartTime': time,
            'Members': members,
            'Venue': venue,
            'Image': image,
            'Link': link
        })

    driver.quit()
    return events

def setup_driver_options():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # User-Agentの設定
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.92 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    return options

def get_element_text(element, selector):
    try:
        return element.find_element(By.CSS_SELECTOR, selector).text or '-'
    except:
        return '-'

def get_element_attribute(element, selector, attribute):
    try:
        return element.find_element(By.CSS_SELECTOR, selector).get_attribute(attribute) or '-'
    except:
        return '-'

def format_date(date_text):
    try:
        month, day = date_text.split('/')
        return f"{month.zfill(2)}-{day.zfill(2)}"
    except:
        return '-'

all_events = []
for talent in talents:
    events = get_ticket_info(talent['id'], talent['name'])
    all_events.extend(events)

# データをCSVに保存
df = pd.DataFrame(all_events)
df.to_csv('talent_tickets.csv', index=False, encoding='utf-8-sig')

print("公演情報の取得が完了し、CSVファイルに保存しました。")
