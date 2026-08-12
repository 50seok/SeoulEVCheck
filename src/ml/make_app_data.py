"""
앱이 읽는 데이터 파일 생성 — app/gu_summary.csv, app/station_hotspot.csv

이 두 파일은 원래 생성 스크립트 없이 레포에 들어와 있었다.
그래서 data/ 가 갱신돼도 앱의 지도·핫스팟은 따라오지 않았다.
model_compare_gu.csv 를 model.py 가 만들도록 바꾼 것과 같은 이유로 스크립트화한다.

정의
----
gu_summary.csv      : 구 전체 하루 충전량 = 급속+완속을 합산한 뒤 날짜 평균
                      (앱 지도 범례 "일 평균 충전량(kWh)" 과 일치)
station_hotspot.csv : 충전소·충전구분별 일 평균 충전량, 내림차순
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
APP  = ROOT / "app"

# model.py·eda.py 와 같은 값이어야 함 (구 단위 일 충전량의 물리적 상한)
OUTLIER_MAX_KWH = 10000


def gu_summary(day):
    """구 전체 하루 충전량의 평균.

    급속·완속이 별도 행이므로 먼저 (구, 날짜) 로 합산해야
    '그 구에서 하루에 충전된 총량' 이 된다. 합산 없이 행 평균을 내면
    충전기 종류별 평균이 되어 값이 약 절반으로 나온다.
    """
    per_day = day.groupby(["gu", "date"], as_index=False)["충전량"].sum()
    out = (per_day.groupby("gu", as_index=False)["충전량"].mean()
                  .sort_values("충전량", ascending=False))
    return out


def station_hotspot(station):
    """충전소·충전구분별 일 평균 충전량 (수요 핫스팟).

    구 단위와 같은 이상치 필터를 충전소 단위에도 건다. 안 걸면 오류값이
    섞인 서울숲M타워(최댓값 44,894 kWh)가 1위로 올라온다 — 정상 중앙값은 69.5.
    참고로 임계값을 1,000 으로 낮춰도 걸러지는 행은 동일해서,
    이상치가 정상 분포와 확연히 분리돼 있고 임계값에 민감하지 않다.
    """
    station = station[station["충전량"] <= OUTLIER_MAX_KWH]
    out = (station.groupby(["충전소명", "gu", "충전구분"], as_index=False)["충전량"].mean()
                  .rename(columns={"gu": "구", "충전량": "일평균충전량(kWh)"})
                  .sort_values("일평균충전량(kWh)", ascending=False)
                  .reset_index(drop=True))
    out["일평균충전량(kWh)"] = out["일평균충전량(kWh)"].round(1)
    return out[["충전소명", "구", "충전구분", "일평균충전량(kWh)"]]


if __name__ == "__main__":
    day = pd.read_csv(DATA / "gu_day_2025.csv", encoding="utf-8-sig")
    day = day[day["충전량"] <= OUTLIER_MAX_KWH]

    station = pd.read_csv(DATA / "station_day_2025.csv", encoding="utf-8-sig")

    gs = gu_summary(day)
    hs = station_hotspot(station)

    gs.to_csv(APP / "gu_summary.csv",      index=False, encoding="utf-8-sig")
    hs.to_csv(APP / "station_hotspot.csv", index=False, encoding="utf-8-sig")

    print(f"gu_summary.csv      : {len(gs):,}행  (구 전체 하루 충전량 평균)")
    print(f"  상위 5: {', '.join(f'{r.gu} {r.충전량:,.0f}' for r in gs.head(5).itertuples())}")
    print(f"station_hotspot.csv : {len(hs):,}행")
    print(f"  1위: {hs.iloc[0]['충전소명']} ({hs.iloc[0]['구']}) {hs.iloc[0]['일평균충전량(kWh)']:,.1f} kWh")
    print("저장 완료 →", APP)
