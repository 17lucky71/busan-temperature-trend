"""
보너스 과제 2: 시계열 심화 (분해 + 베이스라인 예측)
- 입력: data/busan_weather_clean.csv
- 출력: images/04_decomposition.png, images/05_baseline_forecast.png + 콘솔 수치
실행: python bonus.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

IMG = Path("images")
IMG.mkdir(exist_ok=True)

df = pd.read_csv("data/busan_weather_clean.csv", parse_dates=["date"])
s = df.set_index("date")["temp_mean"].asfreq("D")

# ------------------------------------------------------------
# (A) 시계열 분해: 관측값 = 추세 + 계절성 + 잔차 (가법 모델, 주기 365일)
# ------------------------------------------------------------
dec = seasonal_decompose(s, model="additive", period=365)

fig, axes = plt.subplots(4, 1, figsize=(12, 9), sharex=True)
parts = [(dec.observed, "관측값", "gray"), (dec.trend, "추세 (Trend)", "tab:red"),
         (dec.seasonal, "계절성 (Seasonal)", "tab:blue"), (dec.resid, "잔차 (Noise)", "tab:green")]
for ax, (data, name, color) in zip(axes, parts):
    ax.plot(data.index, data, color=color, lw=0.8 if name != "추세 (Trend)" else 2)
    ax.set_ylabel(name)
    ax.grid(alpha=0.3)
axes[0].set_title("부산 일평균기온 시계열 분해 (가법 모델, 주기 365일)")
fig.tight_layout()
fig.savefig(IMG / "04_decomposition.png", dpi=150)
plt.close(fig)

trend = dec.trend.dropna()
seasonal_amp = dec.seasonal.max() - dec.seasonal.min()
print("===== (A) 시계열 분해 =====")
print(f"추세 시작값({trend.index[0].date()}): {trend.iloc[0]:.2f}℃")
print(f"추세 끝값({trend.index[-1].date()}): {trend.iloc[-1]:.2f}℃")
print(f"추세 변화: {trend.iloc[-1] - trend.iloc[0]:+.2f}℃")
print(f"계절성 진폭(최고-최저): {seasonal_amp:.2f}℃")
print(f"잔차 표준편차: {dec.resid.std():.2f}℃")
resid_month = dec.resid.groupby(dec.resid.index.month).std().round(2)
print("월별 잔차 표준편차 (노이즈 크기):")
print(resid_month.to_string())

# ------------------------------------------------------------
# (B) 베이스라인 예측: 2020~2024년으로 2025년 일평균기온 예측
#   1) 작년 같은 날 (Seasonal Naive): 2025-03-01 → 2024-03-01 값
#   2) 평년값 (Climatology): 2020~2024년 같은 월·일의 평균
# ------------------------------------------------------------
train = s[s.index.year <= 2024]
test = s[s.index.year == 2025]

naive = pd.Series([s.get(d - pd.DateOffset(years=1)) for d in test.index], index=test.index)
clim_table = train.groupby([train.index.month, train.index.day]).mean()
clim = pd.Series([clim_table.loc[(d.month, d.day)] for d in test.index], index=test.index)

mae_naive = (test - naive).abs().mean()
mae_clim = (test - clim).abs().mean()

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(test.index, test, color="black", lw=1.2, label="실제 2025년")
ax.plot(test.index, naive, color="tab:orange", lw=0.8, alpha=0.8,
        label=f"작년 같은 날 (MAE {mae_naive:.2f}℃)")
ax.plot(test.index, clim, color="tab:blue", lw=1.8,
        label=f"평년값 2020~2024 평균 (MAE {mae_clim:.2f}℃)")
ax.set_title("2025년 일평균기온: 실제 vs 베이스라인 예측")
ax.set_ylabel("기온 (°C)")
ax.legend(loc="lower center")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(IMG / "05_baseline_forecast.png", dpi=150)
plt.close(fig)

print("\n===== (B) 베이스라인 예측 (2025년, 365일) =====")
print(f"작년 같은 날 MAE: {mae_naive:.2f}℃")
print(f"평년값 MAE: {mae_clim:.2f}℃")
print(f"평년값 대비 실제 2025년 평균 편차: {(test - clim).mean():+.2f}℃ (+면 평년보다 따뜻)")
err_month = (test - clim).abs().groupby(test.index.month).mean().round(2)
print("월별 평년값 MAE:")
print(err_month.to_string())
print(f"\n그래프 저장 완료: {IMG}/04_decomposition.png, 05_baseline_forecast.png")
