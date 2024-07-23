import argparse
import csv
import datetime
import sys
from typing import List, Dict, Any
import os
from pathlib import Path
import requests

# 定数
LATITUDE = 35.681236  # 東京駅の緯度
LONGITUDE = 139.767125  # 東京駅の経度
TODAY = datetime.date.today()
TWO_WEEKS_AGO = TODAY - datetime.timedelta(days=13)  # 2週間
FOUR_MONTHS_AGO = TODAY - datetime.timedelta(days=124)  # 4ヶ月以内

# API関連の定数
API_URL = "https://api.open-meteo.com/v1/forecast"
API_PARAMS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "hourly": "temperature_2m,precipitation,windspeed_10m,weathercode",
    "timezone": "Asia/Tokyo"
}

# CSVヘッダーの日本語訳
HEADER_TRANSLATION = {
    "date": "日付",
    "time": "時間",
    "weather_code": "天気コード",
    "temperature_2m": "気温(°C)",
    "precipitation": "降水量(mm)",
    "windspeed_10m": "最大風速(m/s)"
}

# Open-Meteo APIから天気データを取得
def get_weather_data(latitude: float, longitude: float, start_date: str, end_date: str) -> Dict[str, Any]:
    params = API_PARAMS.copy()
    params.update({
        "start_date": start_date,
        "end_date": end_date
    })
    # APIリクエストでのエラー
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.ConnectionError:
        print("ネットワーク接続エラー: APIサーバーに接続できません。")
        return None
    except requests.Timeout:
        print("タイムアウトエラー: APIリクエストがタイムアウトしました。")
        return None
    except requests.HTTPError as e:
        print(f"HTTPエラー: ステータスコード {e.response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"APIリクエストエラー: {e}")
        return None

# コマンドライン引数を解析
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="天気情報アプリ")
    parser.add_argument("date", nargs="?", help="指定日の天気情報を表示 (YYYY-MM-DD形式)")
    parser.add_argument("--csv", action="store_true", help="CSV形式で出力")
    parser.add_argument("--columns", nargs="+", help="CSV出力時に表示するカラム")
    return parser.parse_args()

# 天気データを処理し、必要な情報を抽出
def process_weather_data(data: Dict[str, Any], end_date: datetime.date) -> List[Dict[str, Any]]:
    processed_data = []
    hourly_data = data["hourly"]
    now = datetime.datetime.now()

    # APIから取得した時間データを処理
    for i, time in enumerate(hourly_data["time"]):
        current_datetime = datetime.datetime.fromisoformat(time)
        current_date = current_datetime.date()
        
        # 現在の時刻を超えるデータを除外
        if current_datetime > now:
            break
        if current_date > end_date:
            break

        weather_info = {
            "date": current_date.isoformat(),
            "time": time.split("T")[1],
            "weather_code": hourly_data["weathercode"][i],
            "temperature_2m": hourly_data["temperature_2m"][i],
            "precipitation": hourly_data["precipitation"][i],
            "windspeed_10m": hourly_data["windspeed_10m"][i]
        }
        processed_data.append(weather_info)

    return processed_data

# コンソールに天気情報を出力
def print_console_output(weather_data: List[Dict[str, Any]], daily: bool = True):
    daily_data = {}
    for item in weather_data:
        date = item["date"]
        # 日ごとの天気データを集計
        if date not in daily_data:
            daily_data[date] = {
                "weather_code": item["weather_code"],
                "max_temp": item["temperature_2m"],
                "min_temp": item["temperature_2m"],
                "total_precipitation": item["precipitation"],
                "max_wind_speed": item["windspeed_10m"]
            }
        # 同じ日付の既存のデータを更新
        else:
            daily_data[date]["max_temp"] = max(daily_data[date]["max_temp"], item["temperature_2m"])
            daily_data[date]["min_temp"] = min(daily_data[date]["min_temp"], item["temperature_2m"])
            daily_data[date]["total_precipitation"] += item["precipitation"]
            daily_data[date]["max_wind_speed"] = max(daily_data[date]["max_wind_speed"], item["windspeed_10m"])

    # コンソールでの表示項目
    for date, info in daily_data.items():
        print(f"{date}: 天気コード {info['weather_code']}, "
            f"最高気温 {info['max_temp']}°C, "
            f"最低気温 {info['min_temp']}°C, "
            f"降水量 {info['total_precipitation']:.1f}mm, "
            f"最大風速 {info['max_wind_speed']}m/s")


# CSV形式で天気情報を出力
def write_csv_output(weather_data: List[Dict[str, Any]], columns: List[str] = None, csvfile=sys.stdout):
    if not columns:
        columns = ["date", "time", "weather_code", "temperature_2m", "precipitation", "windspeed_10m"]

    translated_columns = [HEADER_TRANSLATION.get(col, col) for col in columns]

    # CSVファイルへのデータ書き込み
    try:
        writer = csv.DictWriter(csvfile, fieldnames=translated_columns, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for item in weather_data:
            translated_item = {HEADER_TRANSLATION.get(k, k): v for k, v in item.items() if k in columns}
            writer.writerow(translated_item)
    except csv.Error as e:
        print(f"CSV出力エラー: {e}")
        sys.exit(1)

# 入力した日付文字列を検証し、適切な日付範囲内かのチェック
def validate_date(date_str):
    try:
        start_date = end_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if start_date > TODAY:
            print("無効な日付です。本日以前の日付を入力してください。")
            sys.exit(1)
        if start_date < FOUR_MONTHS_AGO:
            print("無効な日付です。過去4ヶ月以内の日付を入力してください。")
            sys.exit(1)
        return start_date, end_date
    except ValueError:
        print("無効な日付形式です。YYYY-MM-DD形式で入力してください。")
        sys.exit(1)

# CSVファイルの保存先とファイル名を生成
def generate_csv_filename(args, start_date, end_date):
    desktop_path = Path.home() / "Desktop"
    data_folder = desktop_path / "data"
    data_folder.mkdir(exist_ok=True)

    # ファイル名
    if args.date:
        base_filename = f"weather_data_{args.date}.csv"
    else:
        base_filename = f"weather_data_{start_date.isoformat()}_{end_date.isoformat()}.csv"
    
    csv_filename = data_folder / base_filename
    counter = 1
    while csv_filename.exists():
        # 日付を指定している場合
        if args.date:
            csv_filename = data_folder / f"weather_data_{args.date}_{counter}.csv"
        # 日付を指定していない場合
        else:
            csv_filename = data_folder / f"weather_data_{start_date.isoformat()}_{end_date.isoformat()}_{counter}.csv"
        counter += 1
    return csv_filename

# 無効な入力の場合エラー文
def validate_args(args):
    invalid_options = ["csv", "c", "s", "v"]
    if args.date in invalid_options:
        print("無効なオプションです。'--csv'と入力してください。")
        sys.exit(1)

# 日付範囲を決定
def get_date_range(args):
    if args.date:
        return validate_date(args.date)
    return TWO_WEEKS_AGO, TODAY

# 天気データの取得、処理、出力
def process_and_output_data(args, start_date, end_date):
    weather_data = get_weather_data(LATITUDE, LONGITUDE, start_date.isoformat(), end_date.isoformat())
    if weather_data is None:
        return
    processed_data = process_weather_data(weather_data, end_date)

    if args.csv:
        output_csv(args, start_date, end_date, processed_data)
    else:
        print_console_output(processed_data, daily=True)

# 処理された天気データをCSVファイルとして出力するための処理
def output_csv(args, start_date, end_date, processed_data):
    csv_filename = generate_csv_filename(args, start_date, end_date)
    with open(csv_filename, 'w', newline='') as csvfile:
        write_csv_output(processed_data, args.columns, csvfile)
    print(f"CSVファイルが作成されました: {os.path.abspath(csv_filename)}")

# メイン関数
def main():
    args = parse_args()
    validate_args(args)
    start_date, end_date = get_date_range(args)
    process_and_output_data(args, start_date, end_date)

if __name__ == "__main__":
    main()
