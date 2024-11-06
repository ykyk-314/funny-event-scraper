import pandas as pd
import os
import logging
import json
from dotenv import load_dotenv

# ログの設定
logging.basicConfig(level=logging.INFO)

# .envの読み込み
load_dotenv()

# データの読み込み
talent_df = pd.read_csv('talent_tickets.csv')
theater_df = pd.read_csv('theater_schedules.csv')

def merge_and_export(talent_id, talent_name):
    """
    指定タレントごとにデータをマージし、CSVとして出力する
    """
    logging.info(f"{talent_name} のデータを処理しています")

    # 1. talent_ticketsのデータを取得
    talent_events = talent_df[talent_df['ID'] == talent_id]

    # 2. theater_schedulesの該当タレントのデータを取得
    theater_events = theater_df[theater_df['Members'].str.contains(talent_name, na=False)]

    # 3. マージ処理
    merged_df = pd.merge(
        talent_events,
        theater_events,
        on=['Title', 'Date'],
        how='outer',
        suffixes=('_theater', '_talent')
    )

    # 中間CSV出力（デバッグ用）
    output_merged_df = f"schedule_{talent_id}_merged_df.csv"
    merged_df.to_csv(output_merged_df, index=False, encoding='utf-8-sig')
    logging.info(f"{output_merged_df} を出力しました。")

    # 4. 欠損値処理と列の整形
    final_df = merged_df[[
        'Date', 'Title', 'Venue_talent', 'OpenTime', 'StartTime_talent',
        'EndTime', 'Members_talent', 'Detail', 'Image_talent', 'Link_talent'
    ]].rename(columns={
        'Venue_talent': 'Venue',
        'StartTime_talent': 'StartTime',
        'Members_talent': 'Members',
        'Image_talent': 'Image',
        'Link_talent': 'Link'
    })

    # 5. CSVに出力
    output_filename = f"schedules/{talent_id}_{talent_name}.csv"
    final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    logging.info(f"{output_filename} を出力しました。")

# .envからタレント情報を取得
talents = json.loads(os.getenv('TALENTS'))

# タレントごとにマージ処理を実行
for talent in talents:
    merge_and_export(talent['id'], talent['name'])

logging.info("全タレントの処理が完了しました。")
