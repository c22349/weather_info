# 天気情報アプリ
このアプリケーションは、Open-Meteo ( https://open-meteo.com/ )のAPIを使用して "東京駅" の天気情報を取得し、コンソールまたはCSV形式で出力します

![weather_info-2](https://github.com/c22349/weather_info/assets/44188202/ae351404-146a-476a-a3e5-4db149e3bb36)


## 機能
- Open-Meteo APIを使用して東京駅の天気情報を取得
- 取得した情報をコンソールへ出力する場合

  ・天気コード・最高気温・最低気温・降水量・最大風速 を出力
  
- 取得した情報をCSVファイルに出力する場合

  ・天気コード・気温・降水量・風速 を出力

## 環境
| 言語・フレームワーク | バージョン |
| --------------------- | ---------- |
| Python                | 3.12.2|
| requests ライブラリ     | 2.31.0|

## 環境構築
前提：Python 3.12.2をインストール済みのこと
1. このリポジトリをクローンまたはダウンロードします

    `git clone https://github.com/c22349/weather_info.git`

    https://github.com/c22349/weather_info

2. プロジェクトディレクトリに移動します

3. 必要なライブラリをインストールします

    `pip install -r requirements.txt`

## 使用方法
`weather_info.py`と同じ階層でコマンドを実行します
- `python weather_info.py`

  天気情報をコンソールに出力
  
  ・実行日から数えて過去二週間分
  
	・一日ごとに一行ずつ

- `python weather_info.py YYYY-MM-DD`

  天気情報をコンソールに出力
  
  ・入力した日付

- `python weather_info.py --csv`

  天気情報をCSV形式で出力 (ダウンロードフォルダへ)
  
  ・実行日から数えて過去二週間分
  
  ・1時間毎ごとの天気情報

- `python weather_info.py YYYY-MM-DD --csv`

  天気情報をCSV形式で出力 (デスクトップにdataフォルダを作成し出力)
  
  ・入力した日付
  
  ・1時間毎ごとの天気情報

## 天気コード
下記URLをご参照ください

https://www.meteomatics.com/en/api/available-parameters/weather-parameter/general-weather-state/#weather_code

