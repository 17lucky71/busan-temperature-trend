"""
부산 일별 기온 시계열 분석 (4단계: 시각화)
- 입력: data/busan_weather_clean.csv (prepare.py 결과)
- 출력: images/ 폴더에 그래프 3개 + 콘솔에 관찰용 수치
실행: python analysis.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# 한글 폰트 (Windows 기본 '맑은 고딕') + 마이너스 기호 깨짐 방지
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

DATA = Path("data/busan_weather_clean.csv")
IMG = Path("images")
IMG.mkdir(exist_ok=True)

df = pd.read_csv(DATA, parse_dates=["date"]).sort_values("date").set_index("date")
df["year"] = df.index.year
df["month"] = df.index.month

# ------------------------------------------------------------
# 그래프 1: 일별 평균기온 + 30일 / 365일 이동평균 (질문 1: 장기 추세)
# ------------------------------------------------------------
df["ma30"] = df["temp_mean"].rolling(30, center=True).mean()
df["ma365"] = df["temp_mean"].rolling(365, center=True).mean()

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df.index, df["temp_mean"], color="lightgray", lw=0.8, label="일별 평균기온")
ax.plot(df.index, df["ma30"], color="tab:blue", lw=1.5, label="30일 이동평균 (계절 흐름)")
ax.plot(df.index, df["ma365"], color="tab:red", lw=2.5, label="365일 이동평균 (장기 추세)")
ax.set_title("부산 일별 평균기온과 이동평균 (2020~2025)")
ax.set_ylabel("기온 (°C)")
ax.legend(loc="lower right")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(IMG / "01_temp_trend_moving_average.png", dpi=150)
plt.close(fig)

# ------------------------------------------------------------
# 그래프 2: 월별 평균기온 박스플롯 (질문 2: 계절성과 계절별 변동성)
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))
monthly_groups = [df.loc[df["month"] == m, "temp_mean"] for m in range(1, 13)]
ax.boxplot(monthly_groups, tick_labels=[f"{m}월" for m in range(1, 13)])
ax.set_title("월별 일평균기온 분포 (2020~2025)")
ax.set_ylabel("기온 (°C)")
ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(IMG / "02_monthly_boxplot.png", dpi=150)
plt.close(fig)

# ------------------------------------------------------------
# 그래프 3: 월별 기온 급변일 수 (상승/하강 구분) (질문 3: 급변일의 시기)
# ------------------------------------------------------------
out = df[df["is_outlier"]]
rise = out[out["temp_change"] > 0].groupby("month").size().reindex(range(1, 13), fill_value=0)
fall = out[out["temp_change"] < 0].groupby("month").size().reindex(range(1, 13), fill_value=0)

fig, ax = plt.subplots(figsize=(10, 5))
x = [f"{m}월" for m in range(1, 13)]
ax.bar(x, fall, color="tab:blue", label="급하강")
ax.bar(x, rise, bottom=fall, color="tab:orange", label="급상승")
ax.set_title("월별 기온 급변일 수 (2020~2025 합계)")
ax.set_ylabel("일수")
ax.legend()
ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(IMG / "03_outlier_by_month.png", dpi=150)
plt.close(fig)

# ------------------------------------------------------------
# 관찰용 수치 출력 (리포트 '관찰(근거)'에 쓸 숫자)
# ------------------------------------------------------------
print("===== 1. 연도별 평균기온 =====")
print(df.groupby("year")["temp_mean"].mean().round(2).to_string())

print("\n===== 2. 월별 평균기온 / 표준편차 =====")
print(df.groupby("month")["temp_mean"].agg(["mean", "std"]).round(2).to_string())

print("\n===== 3. 기온 급변일 =====")
print(f"전체 급변일: {len(out)}일 (급상승 {rise.sum()}일, 급하강 {fall.sum()}일)")
print("월별 급변일 수:")
print((rise + fall).to_string())
rainy_rise = (out["temp_change"] > 0) & (out["precipitation"] >= 10)
rainy_fall = (out["temp_change"] < 0) & (out["precipitation"] >= 10)
print(f"급상승일 중 강수 10mm 이상: {rainy_rise.sum()}일 / {rise.sum()}일")
print(f"급하강일 중 강수 10mm 이상: {rainy_fall.sum()}일 / {fall.sum()}일")

print(f"\n그래프 저장 완료: {IMG}/ (3개)")
