import os, sys, pandas as pd
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
# 원본 데이터는 레포 밖(용량) — 다른 PC에서는 EV_RAW 환경변수로 지정
RAW  = Path(os.environ.get('EV_RAW', r'C:\teamwork\충전소충전량'))
NB   = ROOT / 'notebooks'

GU_LIST = ['강남구','강동구','강북구','강서구','관악구','광진구','구로구','금천구',
           '노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구',
           '성동구','성북구','송파구','양천구','영등포구','용산구','은평구',
           '종로구','중구','중랑구']

# 충전소 정보 → 매핑 테이블
info = pd.read_csv(RAW/'서울시 소유 전기차 충전소 정보.csv', encoding='cp949')
info = info[info['시군구'] != '안양시'].copy()
info['타입'] = info['충전기타입'].apply(lambda x: '완속' if 'AC완속' in str(x) else '급속')
station_map = info.groupby('충전소').agg(
    시군구=('시군구','first'),
    타입=('타입', lambda x: '급속' if '급속' in x.values else '완속')
).reset_index()

# 3개 연도 충전량 로드
frames = []
for year in [2023, 2024, 2025]:
    df = pd.read_excel(
        RAW/f'서울시 소유 전기차충전기 일별 시간별 충전현황({year}년).xlsx',
        header=2)
    df.columns = ['충전소명','충전시작시간','충전종료시간','충전량']
    df['year'] = year
    frames.append(df)

raw = pd.concat(frames, ignore_index=True)
raw = raw[raw['충전소명'] != '충전소명'].copy()
raw['충전량'] = pd.to_numeric(raw['충전량'], errors='coerce')
raw = raw.dropna(subset=['충전소명','충전량'])

# 1차: 정보 파일 exact join
merged = raw.merge(station_map, left_on='충전소명', right_on='충전소', how='left')

# 2차: 미매칭은 충전소명에서 구 직접 추출
def extract_gu(name):
    if not isinstance(name, str): return None
    for gu in GU_LIST:
        if gu in name: return gu
    return None

mask = merged['시군구'].isna()
merged.loc[mask, '시군구'] = merged.loc[mask, '충전소명'].apply(extract_gu)

total = len(merged)
matched = merged['시군구'].notna().sum()
print(f"전체: {total:,}")
print(f"구 매핑 성공: {matched:,} ({matched/total*100:.1f}%)")
print(f"구 매핑 실패: {total-matched:,}")
print()

# 구별 연도별 총 충전량
valid = merged.dropna(subset=['시군구']).copy()
valid['시군구'] = valid['시군구'].str.strip()
valid = valid[valid['시군구'].isin(GU_LIST)]
gu_year = valid.groupby(['시군구','year'])['충전량'].sum().unstack(fill_value=0)
gu_year.columns = [f'{int(c)}년' for c in gu_year.columns]
gu_year['합계'] = gu_year.sum(axis=1)
gu_year = gu_year.sort_values('합계', ascending=False)
print("=== 구별 연도별 실제 충전량 (kWh) ===")
print(gu_year.to_string())
print()

# 수요 예측 vs 실제 비교
gs = pd.read_csv(ROOT/'app'/'gu_summary.csv', encoding='utf-8-sig')
gs['gu'] = gs['gu'].str.strip()
gs = gs.rename(columns={'gu':'시군구','충전량':'예측수요(kWh/일)'})
gu_total = gu_year[['합계']].reset_index().rename(columns={'합계':'실제충전량합계(23-25)'})
compare = gs.merge(gu_total, on='시군구', how='left')
compare['수요대비공급비율'] = (compare['실제충전량합계(23-25)'] / compare['예측수요(kWh/일)']).round(1)
compare = compare.sort_values('예측수요(kWh/일)', ascending=False)
print("=== 수요 예측 vs 실제 충전량 비교 ===")
print(compare.to_string(index=False))

# 결과 저장
gu_year.to_csv(NB/'gu_charging_2023_2025.csv', encoding='utf-8-sig')
compare.to_csv(NB/'demand_vs_supply.csv', encoding='utf-8-sig', index=False)
print("\n저장 완료")
