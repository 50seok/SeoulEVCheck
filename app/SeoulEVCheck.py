import streamlit as st, pandas as pd, numpy as np, joblib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; APP=Path(__file__).resolve().parent

@st.cache_resource
def load():
    gm=joblib.load(ROOT/"models"/"xgb_gu.pkl")
    gs=pd.read_csv(APP/"gu_summary.csv",encoding="utf-8-sig")
    hs=pd.read_csv(APP/"station_hotspot.csv",encoding="utf-8-sig")
    return gm,gs,hs
def fnames(m): return list(m.feature_names_in_) if hasattr(m,"feature_names_in_") else m.get_booster().feature_names

gm,gs,hs=load()
GU=sorted(c[3:] for c in fnames(gm) if c.startswith("gu_"))
WD={"월":0,"화":1,"수":2,"목":3,"금":4,"토":5,"일":6}

st.set_page_config(page_title="SeoulEVCheck", page_icon="⚡")
st.title("⚡ SeoulEVCheck")
st.caption("서울 전기차 충전 수요 예측 — 구·충전기·요일·월로 예상 일 충전량과 배달충전 우선지역을 보여줍니다.")

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

st.divider()
st.subheader("📊 구별 평균 일 충전량")
st.bar_chart(gs.set_index("gu")["충전량"])
st.subheader("🔥 충전 수요 핫스팟 TOP10 (배달충전 우선지역)")
st.dataframe(hs.head(10), use_container_width=True)
st.caption("3주 로드맵: 1주 ML(현재) → 2주 DL(LSTM 시계열) → 3주 LLM(충전 어드바이저·RAG)")
