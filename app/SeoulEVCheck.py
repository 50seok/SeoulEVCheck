import streamlit as st, pandas as pd, numpy as np, joblib, requests
import plotly.express as px
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP  = Path(__file__).resolve().parent
FIG  = ROOT / "reports" / "figures"

@st.cache_resource
def load():
    gm = joblib.load(ROOT/"models"/"model_gu.pkl")
    gs = pd.read_csv(APP/"gu_summary.csv",      encoding="utf-8-sig")
    hs = pd.read_csv(APP/"station_hotspot.csv", encoding="utf-8-sig")
    return gm, gs, hs

def fnames(m):
    return list(m.feature_names_in_) if hasattr(m, "feature_names_in_") else m.get_booster().feature_names

gm, gs, hs = load()
GU = sorted(c[3:] for c in fnames(gm) if c.startswith("gu_"))

st.set_page_config(page_title="SeoulEVCheck", page_icon="⚡")
st.title("⚡ SeoulEVCheck")
st.caption("서울시 자치구역별 전기차 충전 수요 예측 — 급속·완속 병목 지역과 인프라 사각지대를 식별하여 투자 우선순위를 지원합니다.")

tab1, tab2, tab3 = st.tabs(["⚡ 충전 수요 예측", "📊 데이터 분석", "🤖 모델 평가"])

# ── 탭1: 예측 ─────────────────────────────────────────────
with tab1:
    st.subheader("충전 수요 예측")
    c1, c2, c3, c4 = st.columns(4)
    gu = c1.selectbox("자치구역", GU, index=GU.index("강남구") if "강남구" in GU else 0)
    ch = c2.selectbox("충전기", ["급속","완속"])
    yr = c3.selectbox("년도", [2025, 2026, 2027], index=1)
    mo = c4.selectbox("월", list(range(1,13)), index=5)

    if yr == 2027:
        st.caption("⚠️ 2027년 예측은 학습 데이터 범위를 벗어나 정확도가 낮을 수 있습니다.")

    if st.button("🔮 예측하기", type="primary"):
        cols = fnames(gm)

        def predict_gu(g, charge, year, month):
            xi = pd.DataFrame(np.zeros((1, len(cols))), columns=cols)
            if f"gu_{g}" in cols:           xi.loc[0, f"gu_{g}"] = 1.0
            if f"충전구분_{charge}" in cols: xi.loc[0, f"충전구분_{charge}"] = 1.0
            xi.loc[0, "year"]      = year
            xi.loc[0, "month"]     = month
            xi.loc[0, "month_seq"] = (year - 2025) * 12 + month
            return float(np.expm1(gm.predict(xi)[0]))

        pred = predict_gu(gu, ch, yr, mo)
        all_preds = [predict_gu(g, ch, yr, mo) for g in GU]
        rank = sum(1 for p in all_preds if p > pred) + 1

        st.metric(f"{gu} · {ch} · {yr}년 {mo}월 예상 월간 총 충전량", f"{pred:,.0f} kWh")
        st.info(f"이 수요는 서울 25개 자치구역 중 {rank}위 수준입니다. ({ch} 기준, {yr}년 {mo}월)")

    st.divider()
    st.subheader("🗺️ 서울시 자치구역별 충전 수요 지도")
    GEO_URL = "https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/hangjeongdong_%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C.geojson"

    @st.cache_data(ttl=86400)
    def load_geo():
        geo = requests.get(GEO_URL, timeout=15).json()
        for i, f in enumerate(geo["features"]):
            f["id"] = i
            nm = f["properties"].get("adm_nm", "")
            parts = nm.split()
            f["properties"]["gu"] = parts[1] if len(parts) >= 2 else ""
        return geo

    try:
        geo = load_geo()
        gu_map = gs.set_index("gu")["충전량"].to_dict()
        feat_df = pd.DataFrame([{
            "id": f["id"],
            "자치구역": f["properties"]["gu"],
            "일 평균 충전량(kWh)": gu_map.get(f["properties"]["gu"], 0)
        } for f in geo["features"]])
        fig = px.choropleth_mapbox(
            feat_df, geojson=geo, locations="id",
            color="일 평균 충전량(kWh)",
            color_continuous_scale="Blues",
            mapbox_style="carto-positron",
            zoom=10, center={"lat": 37.5665, "lon": 126.9780},
            opacity=0.7,
            hover_data={"자치구역": True, "일 평균 충전량(kWh)": True, "id": False},
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"지도 로드 실패 — 바 차트로 대체합니다. ({e})")
        st.bar_chart(gs.set_index("gu")["충전량"])

    st.subheader("🔥 충전 수요 핫스팟 TOP10")
    top10 = hs.head(10).copy()
    top10.index = range(1, 11)
    st.dataframe(top10, use_container_width=True)

# ── 탭2: 데이터 분석 ──────────────────────────────────────
with tab2:
    st.subheader("데이터 분석 (EDA)")
    col1, col2 = st.columns(2)
    with col1:
        for fname, caption in [
            ("01_target_dist.png", "자치구역별 일 충전량 분포"),
            ("03_month.png",       "월별 평균 충전량"),
            ("04_top_gu.png",      "자치구역별 총 충전량 TOP10"),
        ]:
            if (FIG/fname).exists():
                st.image(str(FIG/fname), caption=caption)
    with col2:
        for fname, caption in [
            ("02_weekday.png", "요일별 평균 충전량"),
            ("05_charger.png", "충전구분별 평균 충전량"),
            ("06_corr.png",    "항목 간 상관관계"),
        ]:
            if (FIG/fname).exists():
                st.image(str(FIG/fname), caption=caption)

# ── 탭3: 모델 평가 ────────────────────────────────────────
with tab3:
    st.subheader("모델 평가")

    if (FIG/"10_model_compare.png").exists():
        st.image(str(FIG/"10_model_compare.png"),
                 caption="5개 모델 비교 결과 (최적: RandomForest R²=0.862)")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if (FIG/"07_pred_gu.png").exists():
            st.image(str(FIG/"07_pred_gu.png"),
                     caption="AI 예측값 vs 실제 충전량 산점도")
    with col2:
        if (FIG/"08_imp_gu.png").exists():
            st.image(str(FIG/"08_imp_gu.png"),
                     caption="충전량 예측 특성 중요도 TOP12")

    st.divider()
    if (FIG/"11_pred_vs_actual_gu.png").exists():
        st.image(str(FIG/"11_pred_vs_actual_gu.png"),
                 caption="자치구역별 실제 vs 예측 충전량 비교")
