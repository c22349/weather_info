import argparse
import csv
import datetime
import sys
from typing import List, Dict, Any
import os
from pathlib import Path
import requests

# 東京駅の緯度経度
latitude = 35.681236
longitude = 139.767125

# Open-Meteo APIから天気データを取得
def get_weather_data(latitude: float, longitude: float, start_date: str, end_date: str) -> Dict[str, Any]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation,windspeed_10m,weathercode",
        "timezone": "Asia/Tokyo"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"APIリクエストエラー: {e}")
        sys.exit(1)


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
        if date not in daily_data:
            daily_data[date] = {
                "weather_code": item["weather_code"],
                "max_temp": item["temperature_2m"],
                "min_temp": item["temperature_2m"],
                "total_precipitation": item["precipitation"],
                "max_wind_speed": item["windspeed_10m"]
            }
        else:
            daily_data[date]["max_temp"] = max(daily_data[date]["max_temp"], item["temperature_2m"])
            daily_data[date]["min_temp"] = min(daily_data[date]["min_temp"], item["temperature_2m"])
            daily_data[date]["total_precipitation"] += item["precipitation"]
            daily_data[date]["max_wind_speed"] = max(daily_data[date]["max_wind_speed"], item["windspeed_10m"])

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
        
    # 日本語のヘッダーを定義
    header_translation = {
        "date": "日付",
        "time": "時間",
        "weather_code": "天気コード",
        "temperature_2m": "気温(°C)",
        "precipitation": "降水量(mm)",
        "windspeed_10m": "最大風速(m/s)"
    }

    translated_columns = [header_translation.get(col, col) for col in columns]

    try:
        writer = csv.DictWriter(csvfile, fieldnames=translated_columns, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for item in weather_data:
            translated_item = {header_translation.get(k, k): v for k, v in item.items() if k in columns}
            writer.writerow(translated_item)
    except csv.Error as e:
        print(f"CSV出力エラー: {e}")
        sys.exit(1)


# メイン関数
def main():
    args = parse_args()
    
    # 無効なオプションのチェック
    invalid_options = ["csv", "c", "s", "v"]
    if args.date in invalid_options:
        print("無効なオプションです。'--csv'と入力してください。")
        sys.exit(1)

    today = datetime.date.today()
    two_weeks_ago = today - datetime.timedelta(days=13)
    four_months_ago = today - datetime.timedelta(days=124)

    if args.date:
        try:
            start_date = end_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
            if start_date > today:
                print("無効な日付です。本日以降を入力してください。")
                sys.exit(1)
            if start_date < four_months_ago:
                print("無効な日付です。過去4ヶ月以内の日付を入力してください。")
                sys.exit(1)
        except ValueError:
            print("無効な日付形式です。YYYY-MM-DD形式で入力してください。")
            sys.exit(1)
    else:
        start_date = two_weeks_ago
        end_date = today

    weather_data = get_weather_data(latitude, longitude, start_date.isoformat(), end_date.isoformat())
    processed_data = process_weather_data(weather_data, end_date)

    if args.csv:
        download_path = Path.home() / "Downloads"
        if args.date:
            base_filename = f"weather_data_{args.date}.csv"
        else:
            base_filename = f"weather_data_{start_date.isoformat()}_{end_date.isoformat()}.csv"
        
        csv_filename = download_path / base_filename
        counter = 1
        while csv_filename.exists():
            if args.date:
                csv_filename = download_path / f"weather_data_{args.date}_{counter}.csv"
            else:
                csv_filename = download_path / f"weather_data_{start_date.isoformat()}_{end_date.isoformat()}_{counter}.csv"
            counter += 1

        with open(csv_filename, 'w', newline='') as csvfile:
            write_csv_output(processed_data, args.columns, csvfile)
        print(f"CSVファイルが作成されました: {os.path.abspath(csv_filename)}")
    else:
        print_console_output(processed_data, daily=True)


if __name__ == "__main__":
    main()
