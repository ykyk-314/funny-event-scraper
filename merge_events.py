import pandas as pd
import os
import logging
import json
from dotenv import load_dotenv
import csv

# ログの設定
logging.basicConfig(level=logging.INFO)

# .envの読み込み
load_dotenv()

# データの読み込み
talent_df = pd.read_csv('talent_tickets.csv')
theater_df = pd.read_csv('theater_schedules.csv')

def process_talent_schedule(talent_id, talent_name):
    """
    タレントスケジュールと劇場スケジュールを処理し、タレントごとのCSVを出力
    """
    logging.info(f"{talent_name} のデータを処理しています")

    # タレントスケジュールをフィルタリング
    talent_schedule = talent_df[talent_df['TalentID'] == talent_id]

    # 劇場スケジュールのフィルタリング
    theater_schedule_filtered = theater_df[theater_df['Members'].str.contains(talent_name, na=False)]

    # マージ処理
    merged_schedule = pd.merge(
        talent_schedule,
        theater_schedule_filtered,
        left_on=['EventTitle', 'EventDate'],
        right_on=['Title', 'Date'],
        how='outer',
        suffixes=('_talent', '_theater')
    )

    # 欠損値を埋める
    merged_schedule.fillna('-', inplace=True)

    # タレントスケジュールにないTitleを追加
    for column in ['TheaterVenue', 'EventStartTime', 'EndTime', 'EventMembers', 'Detail', 'Image', 'TicketLink']:
        if column not in merged_schedule.columns:
            merged_schedule[column] = '-'

    # 出力用データフレームの作成
    final_schedule = merged_schedule[[
        'EventDate', 'EventTitle', 'TheaterVenue', 'OpenTime', 'EventStartTime',
        'EndTime', 'EventMembers', 'Detail', 'Image', 'TicketLink'
    ]].rename(columns={
        'EventDate': 'Date',
        'EventTitle': 'Title',
        'TheaterVenue': 'Venue',
        'EventStartTime': 'StartTime',
        'EventMembers': 'Members',
        'TicketLink': 'Link'
    })

    for column in ['Detail', 'Members']:
        final_schedule[column] = final_schedule[column].apply(clean_text)

    # ソート処理
    final_schedule.sort_values(by=['Date', 'StartTime'], inplace=True)

    # CSV出力
    output_filename = f"schedules/{talent_id}_{talent_name}.csv"
    final_schedule.to_csv(output_filename, index=False, encoding='utf-8-sig')
    logging.info(f"{output_filename} を出力しました。")

def clean_text(text):
    """
    改行やカンマを適切に整形する
    """
    if isinstance(text, str):
        text = text.replace('\n', ' ').replace(',', '、').strip()
    return text

# .envからタレント情報を取得
talents = json.loads(os.getenv('TALENTS'))

# タレントごとに処理を実行
for talent in talents:
    process_talent_schedule(talent['id'], talent['name'])

logging.info("全タレントの処理が完了しました。")
