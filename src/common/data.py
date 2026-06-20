"""SeoulEVCheck 공통 데이터 파이프라인: 로드·정제·특성·집계 (1~3주 공유)"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "한국전력공사_서울시 전기차 충전소 충전량_20220331.xlsx"
DATA = ROOT / "data"

def extract_gu(addr):
    """주소 문자열에서 '○○구' 추출 (도로명/지번 형식 혼재 대응)"""
    if not isinstance(addr, str):
        return None
    for tok in addr.split():
        if tok.endswith("구"):
            return tok
    return None

def load_clean():
    """엑셀 로드 → null/이상치 제거 → 밀집 구간 필터 → 날짜 특성 파생"""
    df = pd.read_excel(RAW)
    n0 = len(df)
    df["start"] = pd.to_datetime(df["충전시작시각"], errors="coerce")
    df["gu"] = df["주소"].map(extract_gu)
    df["충전량"] = pd.to_numeric(df["충전량"], errors="coerce")
    df = df.dropna(subset=["start", "gu", "충전량"])
    df = df[df["충전량"] >= 0]
    n1 = len(df)
    # 밀집 구간 필터: 월별 건수가 최대월의 10% 미만인 달 제거(희소한 옛 기록 제거)
    df["ym"] = df["start"].dt.to_period("M")
    c = df["ym"].value_counts()
    keep = c[c >= c.max() * 0.10].index
    df = df[df["ym"].isin(keep)].copy()
    n2 = len(df)
    df["date"] = df["start"].dt.date
    df["weekday"] = df["start"].dt.weekday
    df["month"] = df["start"].dt.month
    df["hour"] = df["start"].dt.hour
    return df, (n0, n1, n2)

def agg_gu_day(df):
    """구·충전구분·일별 충전량 집계 (거시 모델 B용)"""
    return (df.groupby(["gu", "충전구분", "date"], as_index=False)
              .agg(충전량=("충전량", "sum"), sessions=("충전량", "size"),
                   weekday=("weekday", "first"), month=("month", "first")))

def agg_station_day(df):
    """충전소·일별 충전량 집계 (미시 모델 A용)"""
    return (df.groupby(["충전소명", "gu", "충전구분", "충전기용량", "date"], as_index=False)
              .agg(충전량=("충전량", "sum"), sessions=("충전량", "size"),
                   weekday=("weekday", "first"), month=("month", "first")))

if __name__ == "__main__":
    df, (n0, n1, n2) = load_clean()
    gu = agg_gu_day(df); st = agg_station_day(df)
    gu.to_csv(DATA / "gu_day.csv", index=False, encoding="utf-8-sig")
    st.to_csv(DATA / "station_day.csv", index=False, encoding="utf-8-sig")
    print("raw rows        :", n0)
    print("after clean     :", n1, "  (dropped null/neg:", n0 - n1, ")")
    print("after period    :", n2, "  (dropped sparse :", n1 - n2, ")")
    print("date range kept :", df["date"].min(), "~", df["date"].max())
    print("days / gu count :", df["date"].nunique(), "/", df["gu"].nunique())
    print("gu_day rows     :", len(gu))
    print("station_day rows:", len(st))
    print("gu_day target mean/min/max:", round(gu["충전량"].mean(),1), "/", round(gu["충전량"].min(),1), "/", round(gu["충전량"].max(),1))
