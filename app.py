"""
보너스 과제 1: 부산 기온 탐색 대시보드 (Streamlit)
실행: streamlit run app.py  → 브라우저에서 http://localhost:8501
"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# 그래프는 matplotlib 이미지로 그림 (Windows에서 st.line_chart 등이 빈칸으로 보이는 문제 회피)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="부산 기온 트렌드 대시보드", page_icon="🌡️", layout="wide")


@st.cache_data
def load():
    df = pd.read_csv("data/busan_weather_clean.csv", parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


df = load()

st.title("🌡️ 부산 일별 기온 트렌드 대시보드 (2020~2025)")
st.caption("데이터: Open-Meteo Historical Weather API (CC BY 4.0) · 왼쪽 사이드바에서 기간과 조건을 바꿔 보세요.")

# ---------------- 사이드바: 조건 ----------------
st.sidebar.header("조건 설정")
min_d, max_d = df["date"].min().date(), df["date"].max().date()
start, end = st.sidebar.slider("기간", min_value=min_d, max_value=max_d,
                               value=(min_d, max_d), format="YYYY-MM-DD")
months = st.sidebar.multiselect("월 선택", list(range(1, 13)), default=list(range(1, 13)),
                                format_func=lambda m: f"{m}월")
ma_window = st.sidebar.slider("이동평균 기간(일)", 7, 365, 30, step=1)
z_thr = st.sidebar.slider("급변일 기준 |z| >", 2.0, 4.0, 3.0, step=0.1,
                          help="전날 대비 기온 변화량의 z-score 기준. 리포트는 3.0 사용")

# 급변일은 전체 기간 분포로 z 계산 (prepare.py와 같은 방식)
chg = df["temp_mean"].diff()
df["z"] = (chg - chg.mean()) / chg.std()
df["temp_change"] = chg
df["is_outlier_dyn"] = df["z"].abs() > z_thr
df["ma"] = df["temp_mean"].rolling(ma_window, center=True).mean()

mask = (df["date"].dt.date.between(start, end)) & (df["date"].dt.month.isin(months))
view = df[mask]

if view.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

# ---------------- 요약 지표 ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("평균기온", f"{view['temp_mean'].mean():.2f} ℃")
c2.metric("기온 표준편차", f"{view['temp_mean'].std():.2f} ℃")
c3.metric("급변일 수", f"{int(view['is_outlier_dyn'].sum())} 일",
          help=f"±{z_thr * chg.std():.1f}℃ 넘게 변한 날")
c4.metric("강수일 (≥1mm)", f"{int((view['precipitation'] >= 1).sum())} 일")

# ---------------- 차트 ----------------
st.subheader(f"일평균기온과 {ma_window}일 이동평균")
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(view["date"], view["temp_mean"], color="lightgray", lw=0.8, label="일평균기온")
ax.plot(view["date"], view["ma"], color="tab:blue", lw=1.8, label=f"{ma_window}일 이동평균")
o = view[view["is_outlier_dyn"]]
ax.scatter(o["date"], o["temp_mean"], color="red", s=18, zorder=3, label="급변일")
ax.set_ylabel("기온 (°C)")
ax.legend(loc="lower right")
ax.grid(alpha=0.3)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

left, right = st.columns(2)
with left:
    st.subheader("연도별 평균기온")
    yearly = view.groupby(view["date"].dt.year)["temp_mean"].mean()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(yearly.index.astype(str), yearly, color="tab:red")
    ax.set_ylim(yearly.min() - 1, yearly.max() + 0.5)  # 1℃ 차이가 보이도록 y축 확대
    for x, v in zip(yearly.index.astype(str), yearly):
        ax.text(x, v + 0.05, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_ylabel("기온 (°C)")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
with right:
    st.subheader("월별 기온 표준편차 (변동성)")
    mstd = view.groupby(view["date"].dt.month)["temp_mean"].std()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([f"{m}월" for m in mstd.index], mstd, color="tab:blue")
    ax.set_ylabel("표준편차 (°C)")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

st.subheader("급변일 목록")
out = view[view["is_outlier_dyn"]][["date", "temp_mean", "temp_change", "precipitation"]].copy()
if out.empty:
    st.info("선택한 조건에 급변일이 없습니다.")
else:
    out["방향"] = out["temp_change"].apply(lambda x: "급상승" if x > 0 else "급하강")
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out = out.rename(columns={"date": "날짜", "temp_mean": "평균기온(℃)",
                              "temp_change": "전일 대비(℃)", "precipitation": "강수(mm)"})
    st.table(out.round(1).astype(str).set_index("날짜"))  # 단순 HTML 표 (빈칸 문제 회피)
