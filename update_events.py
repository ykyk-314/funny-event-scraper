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

def merge_data(talent_data, schedule_data):
    """
    タレントデータとスケジュールデータを結合
    """
    merged_df = pd.concat([talent_data, schedule_data], ignore_index=True)

    # 欠損値を補填
    merged_df.fillna('-', inplace=True)

    # 出力データを整形
    final_df = merged_df[[
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

    return final_df

def duplicate_merge(merged_data):
    """
    重複データをマージ
    両データから取得できる情報を結合する
    """
    merged_data = merged_data.groupby(['公演日', 'タイトル', '会場']).agg({
        '開場': 'first',
        '開演': 'first',
        '終演': 'first',
        '出演者': 'first',
        '詳細': 'first',
        'チケット': 'first',
        '画像': 'first'
    }).reset_index()
    return merged_data

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

        # CSVへの出力
        save_to_csv(merged_data, talent_id, talent_name)

    logging.info("全タレントの処理が完了しました")

if __name__ == "__main__":
    main()

