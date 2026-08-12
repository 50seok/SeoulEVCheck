import os
import pandas as pd
from pathlib import Path

# 원본 데이터는 레포 밖(용량) — 다른 PC에서는 EV_RAW 환경변수로 지정
RAW = Path(os.environ.get("EV_RAW", r"C:\teamwork\충전소충전량"))

# ── 25년 12월말까지 충전소 목록 ──
df25 = pd.read_excel(
    RAW/"서울시 소유 전기차 충전소의 충전량(12월말까지).xlsx",
    header=3
)
df25.columns = ["날짜", "충전소명", "충전구분", "충전량"]
df25 = df25.dropna(subset=["충전소명"])
stations_25 = set(df25["충전소명"].str.strip().unique())

print(f"25년 데이터: {len(df25):,}행")
print(f"25년 날짜 범위: {df25['날짜'].min()} ~ {df25['날짜'].max()}")
print(f"25년 충전소 수: {len(stations_25)}")
print(f"25년 충전구분: {df25['충전구분'].unique()}")

# ── 서울시 충전소 정보 CSV (21~22 기준) ──
info = None
for enc in ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']:
    try:
        info = pd.read_csv(RAW/"서울시 소유 전기차 충전소 정보.csv", encoding=enc)
        print(f"\n충전소 정보 CSV (encoding={enc})")
        print("columns:", list(info.columns))
        print(f"충전소 수: {len(info)}")
        break
    except Exception as e:
        print(f"{enc} 실패: {e}")

if info is not None:
    name_col = [c for c in info.columns if "충전소" in c or "명" in c][0]
    stations_info = set(info[name_col].str.strip().unique())

    only_in_info = stations_info - stations_25
    only_in_25   = stations_25 - stations_info
    common       = stations_info & stations_25

    print(f"\n=== 비교 결과 ===")
    print(f"충전소 정보(기준): {len(stations_info)}개")
    print(f"25년 데이터:       {len(stations_25)}개")
    print(f"공통:              {len(common)}개")
    print(f"사라진 곳(정보에만): {len(only_in_info)}개")
    for s in sorted(only_in_info): print(f"  - {s}")
    print(f"\n신규(25년에만):    {len(only_in_25)}개")
    for s in sorted(only_in_25): print(f"  + {s}")
