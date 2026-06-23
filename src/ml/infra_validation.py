"""
21~22년 모델 예측 고수요 자치구 vs 25년 신규 충전소 설치 검증
"모델이 인프라 필요하다고 예측한 곳에 실제로 설치되었는가?"
"""
import pandas as pd

# ── 1. 21~22 모델 예측: 구별 수요 순위 ──
gs = pd.read_csv("C:/teamwork/SeoulEVCheck/app/gu_summary.csv", encoding="utf-8-sig")
gs.columns = ["gu", "충전량"]
gs = gs.sort_values("충전량", ascending=False).reset_index(drop=True)
gs["rank"] = gs.index + 1
top_gu = set(gs[gs["rank"] <= 10]["gu"])
print("=== 21~22 예측 수요 상위 10개 자치구 ===")
print(gs.head(10)[["rank","gu","충전량"]].to_string(index=False))

# ── 2. 충전소 정보 CSV (col1=충전소명, col8=주소) ──
info = pd.read_csv("C:/teamwork/충전소충전량/서울시 소유 전기차 충전소 정보.csv",
                   encoding="cp949", header=0)
# 컬럼 인덱스로 직접 접근 (이름 인코딩 무관)
info_nm  = info.iloc[:, 1].astype(str).str.strip()   # 충전소명
info_adr = info.iloc[:, 8].astype(str)               # 주소
info_gu  = info_adr.str.extract(r'서울.{0,3}?\s*([\w]+구)')[0]

stations_info = pd.DataFrame({"충전소명": info_nm, "자치구": info_gu}).dropna()
old_names = set(stations_info["충전소명"])
print(f"\n충전소 정보: {len(stations_info)}행, 고유 충전소: {len(old_names)}개")
print("자치구 샘플:", stations_info["자치구"].dropna().unique()[:5].tolist())

# ── 3. 25년 충전소 목록 ──
df25 = pd.read_excel(
    "C:/teamwork/충전소충전량/서울시 소유 전기차 충전소의 충전량(12월말까지).xlsx",
    header=3
)
df25.columns = ["날짜", "충전소명", "충전구분", "충전량"]
df25 = df25.dropna(subset=["충전소명"])
df25["충전소명"] = df25["충전소명"].str.strip()
new_25 = set(df25["충전소명"].unique())

# ── 4. 신규 충전소 (25년에만 있는 곳) ──
new_only = new_25 - old_names
print(f"\n신규 충전소(25년 신설 추정): {len(new_only)}개")

# ── 5. 자치구 추출: 충전소명에서 직접 + 정보CSV 주소 fallback ──
# 서울 25개 자치구 목록
GU_LIST = [
    "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구",
    "노원구","도봉구","동대문구","동작구","마포구","서대문구","서초구",
    "성동구","성북구","송파구","양천구","영등포구","용산구","은평구",
    "종로구","중구","중랑구"
]

# 정보CSV 주소 기반 매핑 딕셔너리
addr_map = dict(zip(stations_info["충전소명"], stations_info["자치구"]))

def extract_gu(name):
    # 방법1: 충전소명에서 자치구 키워드 직접 탐색
    for g in GU_LIST:
        if g in name or g.replace("구","") in name:
            return g
    # 방법2: 정보CSV 주소 매핑 (임시 제거 후)
    norm = name.replace("(임시)","").replace("(임시 )","").strip()
    return addr_map.get(norm, addr_map.get(name, None))

result = []
for nm in sorted(new_only):
    gu_found = extract_gu(nm)
    result.append({"충전소명": nm, "자치구": gu_found})

new_df  = pd.DataFrame(result)
matched = new_df.dropna(subset=["자치구"])
print(f"자치구 추출 성공: {len(matched)}개 / 실패: {len(new_df)-len(matched)}개")

# ── 6. 핵심 검증 ──
matched_top = matched[matched["자치구"].isin(top_gu)]
print(f"\n=== 핵심 결과: 예측 고수요 자치구에 신규 설치 ===")
print(f"21~22 고수요 상위 10 자치구: {sorted(top_gu)}")
print(f"해당 자치구 신규 설치 충전소: {len(matched_top)}개")
print()
if len(matched_top) > 0:
    print(matched_top[["자치구","충전소명"]].sort_values("자치구").to_string(index=False))

# ── 7. 자치구별 신규 설치 현황 전체 ──
print("\n=== 자치구별 신규 설치 현황 (전체) ===")
gu_count = matched.groupby("자치구").size().reset_index(name="신규설치수")
gu_count = gu_count.merge(gs[["gu","rank","충전량"]], left_on="자치구", right_on="gu", how="left")
gu_count["예측상위10"] = gu_count["자치구"].isin(top_gu).map({True:"★", False:""})
gu_count = gu_count.sort_values("신규설치수", ascending=False)
print(gu_count[["자치구","신규설치수","rank","충전량","예측상위10"]].to_string(index=False))
