import pandas as pd
import os
import logging
import json
from dotenv import load_dotenv
import csv
import unicodedata
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ログの設定
logging.basicConfig(level=logging.INFO)

# .envの読み込み
load_dotenv()

def load_data():
    """
    CSVファイルと環境変数のロード
    """
    talent_df = pd.read_csv('talent_tickets.csv')
    theater_df = pd.read_csv('theater_schedules.csv')
    talents = json.loads(os.getenv('TALENTS'))
    return talent_df, theater_df, talents

def filter_schedule(theater_df, talent_name):
    """
    指定タレントが出演するスケジュール情報を抽出
    """
    filtered_df = theater_df[theater_df['Members'].str.contains(talent_name, na=False)]
    return filtered_df

def filter_talents(talent_df, talent_name):
    """
    指定タレントのスケジュール情報を抽出
    """
    filtered_df = talent_df[talent_df['TalentName'].str.contains(talent_name, na=False)]
    return filtered_df

def normalize_title(title):
    """
    タイトルの表記揺れを正規化
    """
    # 英数字記号を半角に
    title = unicodedata.normalize('NFKC', title)
    # 特定のキーワード削除
    title = re.sub(r"\s*(\d{1,2}:\d{2}の部|その[壱弐参]|\d{1,2}月公演)", "", title)
    return title.strip()

def merge_data(talent_data, schedule_data):
    """
    タレントデータとスケジュールデータを結合
    """
    talent_data.loc[:, 'Title'] = talent_data['Title'].apply(normalize_title)
    schedule_data.loc[:, 'Title'] = schedule_data['Title'].apply(normalize_title)

    merged_df = pd.concat([talent_data, schedule_data], ignore_index=True)

    # 欠損値を補填
    merged_df.fillna('-', inplace=True)

    # 出力データを整形
    return merged_df[[
        'Date', 'Title', 'Venue', 'OpenTime', 'StartTime',
        'EndTime', 'Members', 'Detail', 'Link', 'Image'
    ]].rename(columns={
        'Date': '公演日',
        'Title': 'タイトル',
        'Venue': '会場',
        'OpenTime': '開場',
        'StartTime': '開演',
        'EndTime': '終演',
        'Members': '出演者',
        'Detail': '詳細',
        'Link': 'チケット',
        'Image': '画像'
    })

def duplicate_merge(merged_data):
    """
    重複データをマージ
    """
    def merge_rows(row):
        non_hyphen_values = row[row != '-']
        return non_hyphen_values.iloc[0] if not non_hyphen_values.empty else '-'

    merged_data = merged_data.groupby(['公演日', 'タイトル', '会場', '開演']).agg({
        '開場': lambda x: merge_rows(x),
        '終演': lambda x: merge_rows(x),
        '出演者': lambda x: merge_rows(x),
        '詳細': lambda x: merge_rows(x),
        'チケット': lambda x: merge_rows(x),
        '画像': lambda x: merge_rows(x)
    }).reset_index()

    # 列の順序を指定
    merged_data = merged_data[[
        '公演日', 'タイトル', '会場', '開場', '開演', '終演',
        '出演者', '詳細', 'チケット', '画像'
    ]]

    # 行をソート
    merged_data = merged_data.sort_values(by=['公演日', '開場', '開演'])

    return merged_data

def detect_changes(new_data, existing_file):
    """
    既存ファイルと新規データを比較し、差分を抽出
    """
    if not os.path.exists(existing_file):
        logging.info(f"既存ファイルが見つかりません: {existing_file}")
        return new_data

    existing_data = pd.read_csv(existing_file, encoding='utf-8-sig')
    diff = pd.concat([new_data, existing_data]).drop_duplicates(keep=False)
    return diff

def load_template(template_path):
    """
    テンプレートファイルを読み込む
    """
    with open(template_path, 'r', encoding='utf-8') as file:
        template = file.read()
    return template

def send_email_notification(subject, body, html_body):
    """
    メール通知を送信
    """
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')
    sender = os.getenv('SENDER')
    to_email = os.getenv('TO_EMAIL')

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)
            logging.info("通知メールが送信されました。")
    except Exception as e:
        logging.error(f"メール送信エラー: {e}")

def send_notification(diff_data, talent_name):
    """
    差分データを基に通知を送信
    """
    if diff_data.empty:
        logging.info(f"{talent_name} に新規イベントはありません")
        return

    subject = f"{talent_name} の新規イベント通知"
    body_template = load_template('email/new_events.txt')
    html_template = load_template('email/new_events.html')
    event_details_template = load_template('email/event_details.txt')
    event_details_html_template = load_template('email/event_details.html')

    body = body_template.replace('{{talent_name}}', talent_name)
    html_body = html_template.replace('{{talent_name}}', talent_name)

    event_details_text = ""
    event_details_html = ""
    for idx, row in diff_data.iterrows():
        event_detail_text = event_details_template
        event_detail_html = event_details_html_template

        event_detail_text = event_detail_text.replace('{{タイトル}}', row['タイトル'])
        event_detail_text = event_detail_text.replace('{{公演日}}', row['公演日'])
        event_detail_text = event_detail_text.replace('{{会場}}', row['会場'])
        event_detail_text = event_detail_text.replace('{{開演}}', row['開演'])
        event_detail_text = event_detail_text.replace('{{詳細}}', row['詳細'])
        event_detail_text = event_detail_text.replace('{{チケット}}', row['チケット'])

        event_detail_html = event_detail_html.replace('{{タイトル}}', row['タイトル'])
        event_detail_html = event_detail_html.replace('{{公演日}}', row['公演日'])
        event_detail_html = event_detail_html.replace('{{会場}}', row['会場'])
        event_detail_html = event_detail_html.replace('{{開演}}', row['開演'])
        event_detail_html = event_detail_html.replace('{{詳細}}', row['詳細'])
        event_detail_html = event_detail_html.replace('{{チケット}}', row['チケット'])
        if row['画像'] != '-':
            event_detail_html = event_detail_html.replace('{{画像}}', f"<img src='{row['画像']}' alt='{row['タイトル']}'>")
        else:
            event_detail_html = event_detail_html.replace('{{画像}}', '')

        event_details_text += event_detail_text + "\n\n"
        event_details_html += event_detail_html

        # debug: コンソールに出力
        print(f"新しいイベントが追加されました: {row['タイトル']}")

    body = body.replace('{{event_details}}', event_details_text)
    html_body = html_body.replace('{{event_details}}', event_details_html)

    send_email_notification(subject, body, html_body)

def save_to_csv(final_df, talent_id, talent_name):
    """
    結合データをCSVに出力
    """
    output_dir = 'schedules'
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"{talent_id}_{talent_name}.csv")
    final_df.to_csv(output_filename, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    logging.info(f"CSVファイルを出力しました: {output_filename}")

def main():
    """
    メイン処理
    """
    talent_df, theater_df, talents = load_data()

    for talent in talents:
        talent_id = talent['id']
        talent_name = talent['name']

        logging.info(f"{talent_name} のデータを処理しています")

        # スケジュールのフィルタリング
        filtered_schedule = filter_schedule(theater_df, talent_name)
        # タレントスケジュールのフィルタリング
        filtered_talent = filter_talents(talent_df, talent_name)

        # データの結合
        merged_data = merge_data(filtered_talent, filtered_schedule)
        # 重複データをマージ
        merged_data = duplicate_merge(merged_data)

        # 既存ファイルとの差分を検出
        existing_file = f'schedules/{talent_id}_{talent_name}.csv'
        diff_data = detect_changes(merged_data, existing_file)

        # CSVへの出力
        save_to_csv(merged_data, talent_id, talent_name)
        send_notification(diff_data, talent_name)

    logging.info("全タレントの処理が完了しました")

if __name__ == "__main__":
    main()
