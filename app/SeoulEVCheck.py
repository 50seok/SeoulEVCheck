import streamlit as st, pandas as pd, numpy as np, joblib, requests
import plotly.express as px
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; APP=Path(__file__).resolve().parent

@st.cache_resource
def load():
    gm=joblib.load(ROOT/"models"/"model_gu.pkl")
    gs=pd.read_csv(APP/"gu_summary.csv",encoding="utf-8-sig")
    hs=pd.read_csv(APP/"station_hotspot.csv",encoding="utf-8-sig")
    return gm,gs,hs
def fnames(m): return list(m.feature_names_in_) if hasattr(m,"feature_names_in_") else m.get_booster().feature_names

gm,gs,hs=load()
GU=sorted(c[3:] for c in fnames(gm) if c.startswith("gu_"))
WD={"월":0,"화":1,"수":2,"목":3,"금":4,"토":5,"일":6}

st.set_page_config(page_title="SeoulEVCheck", page_icon="⚡")
st.title("⚡ SeoulEVCheck")
st.caption("서울시 구별 전기차 충전 수요 예측 — 급속·완속 병목 지역과 인프라 사각지대를 식별하여 투자 우선순위를 지원합니다.")

c1,c2,c3,c4=st.columns(4)
gu=c1.selectbox("구",GU,index=GU.index("강남구") if "강남구" in GU else 0)
ch=c2.selectbox("충전기",["급속","완속"])
wd=c3.selectbox("요일",list(WD))
mo=c4.selectbox("월",list(range(1,13)),index=5)

if st.button("🔮 예측하기", type="primary"):
    cols=fnames(gm); x=pd.DataFrame(np.zeros((1,len(cols))),columns=cols)
    if f"gu_{gu}" in cols: x.loc[0,f"gu_{gu}"]=1.0
    if f"충전구분_{ch}" in cols: x.loc[0,f"충전구분_{ch}"]=1.0
    x.loc[0,"weekday"]=WD[wd]; x.loc[0,"month"]=mo
    pred=float(gm.predict(x)[0])
    st.metric(f"{gu} · {ch} · {wd}요일 예상 일 충전량", f"{pred:,.0f} kWh")
    rank=int((gs["충전량"]>=pred).sum())
    st.info(f"이 수요는 서울 25개 구 평균 중 상위 {rank}번째 수준입니다." if rank<=10 else "평균 이하 수요 구간입니다.")

GEO_URL = "https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/hangjeongdong_%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C.geojson"

@st.cache_data(ttl=86400)
def load_geo():
    geo = requests.get(GEO_URL, timeout=15).json()
    for i, f in enumerate(geo['features']):
        f['id'] = i
        nm = f['properties'].get('adm_nm', '')
        parts = nm.split()
        f['properties']['gu'] = parts[1] if len(parts) >= 2 else ''
    return geo

st.divider()
st.subheader("🗺️ 서울시 구별 충전 수요 지도")
try:
    geo = load_geo()
    gu_map = gs.set_index("gu")["충전량"].to_dict()
    feat_df = pd.DataFrame([{
        "id": f["id"],
        "자치구": f["properties"]["gu"],
        "일 평균 충전량(kWh)": gu_map.get(f["properties"]["gu"], 0)
    } for f in geo["features"]])
    fig = px.choropleth_mapbox(
        feat_df, geojson=geo, locations="id",
        color="일 평균 충전량(kWh)",
        color_continuous_scale="Blues",
        mapbox_style="carto-positron",
        zoom=10, center={"lat": 37.5665, "lon": 126.9780},
        opacity=0.7,
        hover_data={"자치구": True, "일 평균 충전량(kWh)": True, "id": False},
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=500)
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"지도 로드 실패 — 바 차트로 대체합니다. ({e})")
    st.bar_chart(gs.set_index("gu")["충전량"])

st.subheader("🔥 충전 수요 핫스팟 TOP10 (인프라 투자 우선 후보 지역)")
st.dataframe(hs.head(10), use_container_width=True)
st.caption("로드맵: 1주 ML(현재) → 2주 DL(LSTM 시계열) → 3주 LLM(충전 인프라 어드바이저·RAG)")
