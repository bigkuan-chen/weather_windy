import requests
import csv
import sqlite3
import json

# ==================== 設定區 ====================
# ⚠️ 請記得在這裡換上你剛剛申請的【Point Forecast】新 Key
API_KEY = "OpvChRGjEOV7VfSMZNJuj7776rTmy947" 
DB_NAME = "weather.db"
CSV_NAME = "weather_data.csv"
# ===============================================

url = "https://api.windy.com/api/point-forecast/v2"

# 查詢台北的經緯度與預報參數
payload = {
    "key": API_KEY,
    "lat": 25.03,
    "lon": 121.56,
    "model": "gfs",
    "parameters": ["temp", "wind", "precip"],
    "levels": ["surface"]
}

try:
    print("1. 開始從 Windy API 擷取氣象資料...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 資料擷取成功！")
        
        # 解析 Windy 吐回來的時間與地表資料
        # 註：Windy 格式通常包含 ts (時間軸) 與各參數陣列
        timestamps = data.get("ts", [])
        temp_list = data.get("temp-surface", [])
        precip_list = data.get("precip-surface", [])
        
        weather_rows = []
        for i in range(len(timestamps)):
            # 轉換為標準清單格式
            row = {
                "timestamp": timestamps[i],
                "temperature": temp_list[i] if i < len(temp_list) else None,
                "precipitation": precip_list[i] if i < len(precip_list) else None
            }
            weather_rows = [row for row in weather_rows]
            
        # 2. 儲存為 CSV
        print(f"2. 正在將資料寫入 {CSV_NAME}...")
        with open(CSV_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Temperature", "Precipitation"])
            for row in weather_rows:
                writer.writerow([row["timestamp"], row["temperature"], row["precipitation"]])
        print("✅ CSV 檔案儲存完成！")
        
        # 3. 轉存至 SQLite3 資料庫
        print(f"3. 正在寫入本地資料庫 {DB_NAME}...")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 建立資料表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_forecast (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                temperature REAL,
                precipitation REAL
            )
        ''')
        
        # 寫入資料
        for row in weather_rows:
            cursor.execute('''
                INSERT INTO weather_forecast (timestamp, temperature, precipitation)
                VALUES (?, ?, ?)
            ''', (str(row["timestamp"]), row["temperature"], row["precipitation"]))
            
        conn.commit()
        conn.close()
        print(f"✅ SQLite 資料庫 {DB_NAME} 寫入成功！作業全部完成。")
        
    else:
        print(f"❌ 擷取失敗，狀態碼: {response.status_code}")
        print(f"錯誤訊息: {response.text}")

except Exception as e:
    print(f" 程式執行發生異常: {e}")