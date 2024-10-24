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

theaters = json.loads(os.getenv('THEATERS'))

def get_schedule_info(venue_name, url, stages=None):
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=setup_driver_options())
    driver.get(url)

    t.sleep(2)
    # クッキーバナーを非表示
    driver.execute_script("""
        let banner = document.querySelector('.cookie-consent');
        if (banner) {
            banner.style.display = 'none';
        }
    """)

    events = []

    if stages:
        for stage in stages:
            switch_stage(driver, stage)
            events.extend(retrieve_monthly_schedules(driver, venue_name + f"　{stage}"))
    else:
        events.extend(retrieve_monthly_schedules(driver, venue_name))

    driver.quit()
    return events

def switch_stage(driver, stage):
    try:
        stage_button = driver.find_element(By.XPATH, f'//a[text()="{stage}"]')
        stage_button.click()
        t.sleep(2)
    except Exception as e:
        print(f"Failed to switch to Stage {stage}: {e}")

def retrieve_monthly_schedules(driver, venue_name):
    events = []
    # 各月のリンクをクリックしてスケジュールを取得
    month_links = driver.find_elements(By.CSS_SELECTOR, '.calendar-month a')

    for month_link in month_links:
        month_link.click()
        print(f"Retrieving schedule for {month_link.text} at {venue_name}.")
        t.sleep(2)

        # すべての詳細を表示する
        driver.execute_script("""
            document.querySelectorAll('.schedule-detail').forEach(el => {
                el.style.display = 'block';
            });
        """)

        schedule_blocks = driver.find_elements(By.CSS_SELECTOR, '.schedule-block')
        for block in schedule_blocks:
            date = block.get_attribute('id').replace('schedule', '')
            schedule_times = block.find_elements(By.CSS_SELECTOR, '.schedule-time')
            schedule_details = block.find_elements(By.CSS_SELECTOR, '.schedule-detail')

            for time_block, detail_block in zip(schedule_times, schedule_details):
                title = get_element_text(time_block, 'strong')
                # 除外公演
                if any(keyword in title for keyword in ['休館日', '貸切']):
                    continue

                times = get_element_text(time_block, 'span').split('｜')
                open_time, start_time, end_time = parse_times(times)
                members = get_members(detail_block)
                detail = get_element_text(detail_block, 'dl:nth-of-type(3) dd').replace('\n', '|')
                link = get_element_attribute(detail_block, '.btns a:not(.is-pink)', 'href')

                events.append({
                    'Venue': venue_name,
                    'Title': title,
                    'Date': date,
                    'OpenTime': open_time,
                    'StartTime': start_time,
                    'EndTime': end_time,
                    'Members': members,
                    'Detail': detail,
                    'Link': link
                })
    return events

def setup_driver_options():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
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

def get_members(detail_block):
    try:
        members_element = detail_block.find_element(By.CSS_SELECTOR, 'dd.schedule-detail-member')
        all_text = members_element.get_attribute('innerText')
        return all_text.replace('\n', '／') or '-'
    except:
        return '-'

def parse_times(times):
    try:
        open_time = times[0].replace('開場', '').strip()
        start_time = times[1].replace('開演', '').strip()
        end_time = times[2].replace('終演', '').strip()
        return open_time, start_time, end_time
    except:
        return '-', '-', '-'

all_events = []
for venue in theaters:
    stages = venue.get('stages')
    events = get_schedule_info(venue['name'], venue['url'], stages)
    all_events.extend(events)

# データをCSVに保存
df = pd.DataFrame(all_events)
df.to_csv('theater_schedules.csv', index=False, encoding='utf-8-sig')

print("公演スケジュールの取得が完了し、CSVファイルに保存しました。")
