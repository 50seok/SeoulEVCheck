import pandas as pd
from ydata_profiling import ProfileReport
from pathlib import Path

ROOT = Path("C:/teamwork/SeoulEVCheck")
OUT  = ROOT / "reports"

gu = pd.read_csv(ROOT / "data" / "gu_day.csv", encoding="utf-8-sig")
ProfileReport(gu, title="SeoulEVCheck — 구 단위 EDA", minimal=False).to_file(str(OUT / "eda_gu.html"))
print("gu 완료:", OUT / "eda_gu.html")

st = pd.read_csv(ROOT / "data" / "station_day.csv", encoding="utf-8-sig")
ProfileReport(st, title="SeoulEVCheck — 충전소 단위 EDA", minimal=True).to_file(str(OUT / "eda_station.html"))
print("station 완료:", OUT / "eda_station.html")
