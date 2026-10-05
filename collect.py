"""부산 일별 기상 데이터 수집 스크립트.

출처: Open-Meteo Historical Weather API (https://open-meteo.com/en/docs/historical-weather-api)
- ERA5 재분석 자료 기반, API 키 불필요 (비상업적 이용 무료)
- 라이선스: CC BY 4.0 (출처 표기 필요)

실행: python collect.py
결과: data/busan_weather_2020_2025.csv
"""
import sys
from pathlib import Path

import pandas as pd
import requests

URL = "https://archive-api.open-meteo.com/v1/archive"
PARAMS = {
    "latitude": 35.1796,      # 부산광역시청 부근
    "longitude": 129.0756,
    "start_date": "2020-01-01",
    "end_date": "2025-12-31",
    "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum",
    "timezone": "Asia/Seoul",
}
OUT = Path("data/busan_weather_2020_2025.csv")
COLUMNS = {  # API 이름 → 분석에서 쓸 짧은 이름
    "time": "date",
    "temperature_2m_mean": "temp_mean",
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "precipitation_sum": "precipitation",
}


def main() -> int:
    print(f"데이터 요청: 부산 {PARAMS['start_date']} ~ {PARAMS['end_date']}")
    try:
        resp = requests.get(URL, params=PARAMS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] 데이터 요청 실패: {e}")
        return 1

    daily = resp.json().get("daily")
    if not daily:
        print("[ERROR] 응답에 daily 데이터가 없습니다.")
        return 1

    df = pd.DataFrame(daily).rename(columns=COLUMNS)
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8")

    print(f"저장 완료: {OUT} ({len(df)}행)")
    print("\n[앞 5행]")
    print(df.head().to_string(index=False))
    print("\n[컬럼별 결측치 수]")
    print(df.isna().sum().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
