"""
25년 1~12월 + 26년 1~3월 KEPCO 전기차 충전량 데이터 전처리
→ data/gu_day_2025.csv, data/station_day_2025.csv
"""
import pandas as pd
import numpy as np
import holidays
from pathlib import Path
import glob

ROOT   = Path("C:/teamwork/SeoulEVCheck")
SRC    = Path("C:/teamwork/충전소충전량/충전소최신")
OUT    = ROOT / "data"

COL = {
    "시도": 0, "시군구": 1, "충전소명": 5,
    "충전기용량": 10, "충전구분": 12,
    "충전량": 13, "날짜": 16, "충전시작시각": 17,
}

kr_hol = holidays.KR()

def load_all():
    files = sorted(glob.glob(str(SRC / "*.xlsx")))
    print(f"파일 {len(files)}개 로드 중...")
    chunks = []
    for f in files:
        df = pd.read_excel(f, usecols=list(COL.values()), header=0, dtype=str)
        df.columns = list(COL.keys())
        df = df[df["시도"].str.contains("서울", na=False)]
        chunks.append(df)
        print(f"  {Path(f).stem}: {len(df):,}행")
    return pd.concat(chunks, ignore_index=True)

def clean(df):
    df = df.copy()
    df["충전량"]    = pd.to_numeric(df["충전량"],    errors="coerce")
    df["충전기용량"] = pd.to_numeric(df["충전기용량"], errors="coerce")
    df["date"]     = pd.to_datetime(df["날짜"].str.replace("-",""), format="%Y%m%d", errors="coerce").dt.date
    df = df.dropna(subset=["충전량", "date", "시군구"])
    df = df[df["충전량"] > 0]
    df["gu"]       = df["시군구"].str.strip()
    df["충전구분"]  = df["충전구분"].str.strip().str[:2]
    dt              = pd.to_datetime(df["date"])
    df["year"]      = dt.dt.year
    df["weekday"]   = dt.dt.weekday
    df["month"]     = dt.dt.month
    dates           = dt.dt.date
    df["is_holiday"]= dates.map(lambda d: 1 if d in kr_hol else 0)
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["hour"]      = pd.to_datetime(df["충전시작시각"], errors="coerce").dt.hour
    return df

def make_gu_day(df):
    return (df.groupby(["gu","충전구분","date","year","weekday","month","is_holiday","is_weekend"])
              .agg(충전량=("충전량","sum"), sessions=("충전량","count"), avg_hour=("hour","mean"))
              .reset_index())

def make_station_day(df):
    return (df.groupby(["충전소명","gu","충전구분","충전기용량",
                        "date","year","weekday","month","is_holiday","is_weekend"])
              .agg(충전량=("충전량","sum"), sessions=("충전량","count"), avg_hour=("hour","mean"))
              .reset_index())

if __name__ == "__main__":
    df = load_all()
    print(f"\n전체 서울 행: {len(df):,}")
    print(f"날짜 범위: {df['날짜'].min()} ~ {df['날짜'].max()}")
    print(f"자치구 수: {df['시군구'].nunique()}")

    df = clean(df)
    print(f"정제 후 행: {len(df):,}")
    print(f"충전구분: {df['충전구분'].unique()}")

    gu = make_gu_day(df)
    st = make_station_day(df)

    gu.to_csv(OUT / "gu_day_2025.csv",      index=False, encoding="utf-8-sig")
    st.to_csv(OUT / "station_day_2025.csv", index=False, encoding="utf-8-sig")

    print(f"\ngu_day_2025.csv:      {len(gu):,}행")
    print(f"station_day_2025.csv: {len(st):,}행")
    print("저장 완료 →", OUT)
