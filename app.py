"""
보너스 과제 1: 부산 기온 탐색 대시보드 (Streamlit)
실행: streamlit run app.py  → 브라우저에서 http://localhost:8501
"""
import pandas as pd
import streamlit as st

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
st.line_chart(view.set_index("date")[["temp_mean", "ma"]]
              .rename(columns={"temp_mean": "일평균기온", "ma": f"{ma_window}일 이동평균"}))

left, right = st.columns(2)
with left:
    st.subheader("연도별 평균기온")
    yearly = view.groupby(view["date"].dt.year)["temp_mean"].mean().round(2)
    yearly.index = yearly.index.astype(str)
    st.bar_chart(yearly)
with right:
    st.subheader("월별 기온 표준편차 (변동성)")
    mstd = view.groupby(view["date"].dt.month)["temp_mean"].std().round(2)
    mstd.index = [f"{m:02d}월" for m in mstd.index]
    st.bar_chart(mstd)

st.subheader("급변일 목록")
out = view[view["is_outlier_dyn"]][["date", "temp_mean", "temp_change", "precipitation"]].copy()
out["방향"] = out["temp_change"].apply(lambda x: "급상승" if x > 0 else "급하강")
out["date"] = out["date"].dt.date
st.dataframe(out.rename(columns={"date": "날짜", "temp_mean": "평균기온(℃)",
                                 "temp_change": "전일 대비(℃)", "precipitation": "강수(mm)"}),
             hide_index=True)
