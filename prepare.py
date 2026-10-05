"""데이터 기본 정보 확인 + 결측치/이상치 점검 및 처리.

입력: data/busan_weather_2020_2025.csv (collect.py 결과)
출력: data/busan_weather_clean.csv  (분석용 데이터, 이상치 표시 컬럼 포함)

처리 기준
1. 숨은 결측치  : 날짜가 연속되지 않고 빠진 날이 있는지 확인 → 있으면 앞뒤 값으로 선형 보간하고 표시
2. 값 결측치    : 기온은 선형 보간, 강수량은 0 으로 채우지 않고 결측 유지 (비가 안 온 것과 모르는 것은 다름)
3. 논리 오류    : 최저기온 <= 평균기온 <= 최고기온 위반 행 확인
4. 물리적 범위  : 부산 기온이 -20℃ ~ 45℃ 를 벗어나면 측정 오류로 보고 결측 처리 후 보간
5. 이상치(급변) : 전날 대비 평균기온 변화가 평소 변화폭의 3 표준편차를 넘는 날
                 → 한파·폭염 같은 실제 기상 사건일 수 있으므로 삭제하지 않고 is_outlier 로 표시만 한다
"""
from pathlib import Path

import pandas as pd

RAW = Path("data/busan_weather_2020_2025.csv")
CLEAN = Path("data/busan_weather_clean.csv")
TEMP_COLS = ["temp_mean", "temp_max", "temp_min"]
VALID_RANGE = (-20, 45)
Z_THRESHOLD = 3


def section(title: str) -> None:
    print(f"\n===== {title} =====")


def main() -> None:
    df = pd.read_csv(RAW, parse_dates=["date"]).sort_values("date")

    section("1. 기본 정보")
    print(f"기간: {df['date'].min():%Y-%m-%d} ~ {df['date'].max():%Y-%m-%d}")
    print(f"행 수: {len(df)}  /  컬럼: {', '.join(df.columns)}")
    print(df.drop(columns='date').describe().round(1).to_string())

    section("2. 결측치")
    full_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    missing_dates = full_range.difference(df["date"])
    duplicated = df["date"].duplicated().sum()
    print(f"빠진 날짜(숨은 결측치): {len(missing_dates)}일")
    print(f"중복 날짜: {duplicated}건")
    df = df.drop_duplicates("date").set_index("date").reindex(full_range)
    df.index.name = "date"
    df["is_filled"] = df[TEMP_COLS].isna().any(axis=1)

    # 물리적으로 불가능한 값은 측정 오류로 보고 결측 처리
    in_range = (df[TEMP_COLS] >= VALID_RANGE[0]) & (df[TEMP_COLS] <= VALID_RANGE[1])
    out_of_range = int((~in_range & df[TEMP_COLS].notna()).sum().sum())
    df[TEMP_COLS] = df[TEMP_COLS].where(in_range)
    print(f"물리적 범위({VALID_RANGE[0]}~{VALID_RANGE[1]}℃) 벗어난 값: {out_of_range}개")
    print("컬럼별 결측치 (보간 전):")
    print(df[TEMP_COLS + ['precipitation']].isna().sum().to_string())

    df["is_filled"] |= df[TEMP_COLS].isna().any(axis=1)
    df[TEMP_COLS] = df[TEMP_COLS].interpolate(method="linear", limit_direction="both")
    print(f"→ 기온 보간 처리: {int(df['is_filled'].sum())}일")

    section("3. 논리 오류 (최저 <= 평균 <= 최고)")
    bad = df[(df["temp_min"] > df["temp_mean"]) | (df["temp_mean"] > df["temp_max"])]
    print(f"위반 행: {len(bad)}건")
    if len(bad):
        print(bad[TEMP_COLS].head().to_string())

    section(f"4. 이상치: 전날 대비 평균기온 급변 (|z| > {Z_THRESHOLD})")
    df["temp_change"] = df["temp_mean"].diff()
    mean, std = df["temp_change"].mean(), df["temp_change"].std()
    df["change_z"] = (df["temp_change"] - mean) / std
    df["is_outlier"] = df["change_z"].abs() > Z_THRESHOLD
    print(f"일교차가 아닌 '전날 대비 변화' 기준. 평균 {mean:.2f}℃, 표준편차 {std:.2f}℃ "
          f"→ ±{Z_THRESHOLD * std:.1f}℃ 넘게 변한 날")
    outliers = df[df["is_outlier"]]
    print(f"해당 일수: {len(outliers)}일 (삭제하지 않고 is_outlier=True 로 표시)")
    if len(outliers):
        print(outliers[["temp_mean", "temp_change", "precipitation"]].round(1).to_string())

    section("5. 저장")
    df = df.drop(columns=["change_z"]).reset_index()
    CLEAN.parent.mkdir(exist_ok=True)
    df.to_csv(CLEAN, index=False, encoding="utf-8")
    print(f"{CLEAN} 저장 ({len(df)}행, 추가 컬럼: is_filled, temp_change, is_outlier)")


if __name__ == "__main__":
    main()
