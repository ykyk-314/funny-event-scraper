import requests
from tqdm import tqdm
import os
import time
import random
from dotenv import load_dotenv
import os

load_dotenv()

# ベースURLの指定
base_url = os.getenv('FLIER_BASE_URL')
# ダウンロードする範囲を指定
start_number = int(os.getenv('START_NUMBER'))
end_number = int(os.getenv('END_NUMBER'))

# 保存先のディレクトリを指定
save_directory = "./flier_images/"

# 保存用ディレクトリを作成
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

def download_image(image_url, save_path, retries=3):
    """画像をダウンロードする関数（エラー時のリトライ付き）"""
    for attempt in range(retries):
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            
            # ステータスコードが403の場合の処理
            if response.status_code == 403:
                print(f"403 Forbidden: Skipping {image_url}")
                return False

            response.raise_for_status()  # HTTPエラーがあれば例外を発生
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            print(f"Downloaded: {save_path}")
            return True  # 成功した場合はTrueを返す
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {image_url} (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(2 ** attempt)  # リトライ前に指数関数的に遅延
    return False  # すべてのリトライが失敗した場合

# 画像を順番にダウンロード（遅延を追加）
for number in tqdm(range(start_number, end_number + 1)):
    image_name = f"R_{number:08d}.jpg"
    image_url = base_url + image_name
    save_path = os.path.join(save_directory, image_name)

    if download_image(image_url, save_path):
        # ランダムな遅延を追加し、サーバ負荷を軽減
        sleep_time = random.uniform(5, 20)  # 1～3秒の遅延
        print(f"Waiting for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)
    else:
        print(f"Skipping {image_name} due to errors.")

