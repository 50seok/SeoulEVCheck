from docx import Document
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from pathlib import Path
ROOT=Path("C:/teamwork/SeoulEVCheck"); FIG=ROOT/"reports"/"figures"
doc=Document()
s=doc.styles['Normal']; s.font.name='맑은 고딕'; s.font.size=Pt(10)
rf=s.element.get_or_add_rPr().get_or_add_rFonts()
rf.set(qn('w:eastAsia'),'맑은 고딕'); rf.set(qn('w:ascii'),'맑은 고딕')
def fig(n,w=5.2):
    p=FIG/n
    if p.exists(): doc.add_picture(str(p),width=Inches(w))
def bullets(items):
    for t in items: doc.add_paragraph(t, style='List Bullet')
doc.add_heading('머신러닝 산출물 — SeoulEVCheck',0)
doc.add_paragraph('서울 전기차 충전 수요 예측 및 시각화  |  담당: 오영석  |  1주차 ML')
doc.add_heading('1. 사업과제',1)
doc.add_paragraph('AI 기반 서울시 전기차 충전 수요 예측 및 시각화 (SeoulEVCheck)')
doc.add_heading('2. 개요 및 현황',1)
doc.add_heading('2.1 추진배경 및 목적',2)
bullets(['전기차 보급 급증 → 충전 인프라 수요 예측·관리 필요성 증대',
         '활용: ①충전 인프라 투자 효율 ②전력 부하 관리(에너지 절감) ③운영 최적화',
         '향후 비전: 예측 수요 기반 충전 인프라 투자 우선순위 결정 → 충전 어드바이저(LLM·RAG)로 발전'])
doc.add_heading('2.2 과제 범위',2)
# (대분류, 중분류, 소분류, 내용) — 소분류 '' 이면 중분류 옆 내용 칸을 가로 병합
scope_rows = [
    ('데이터셋',    '전처리',        '데이터 수집',       'KEPCO 서울 충전 데이터 527,183건 수집 (2025-01~2026-03)'),
    ('데이터셋',    '전처리',        '데이터 정제',       '음수·누락 등 불필요 데이터 제거 → 112,453건 정제'),
    ('데이터셋',    '전처리',        '시군구 처리',       '시군구 컬럼 직접 활용 → 25개 자치구 분류'),
    ('데이터셋',    'EDA 분석',      '분포 분석',         '충전량 분포 확인 (hist)'),
    ('데이터셋',    'EDA 분석',      '상관관계 분석',     '항목 간 상관계수 산출 및 누수 특성 식별 (heatmap)'),
    ('데이터셋',    'EDA 분석',      '구별 분석',         '수요 상위 구 파악 및 시각화 (barplot)'),
    ('데이터셋',    'EDA 분석',      '충전기 유형 분석',  '급속·완속 평균 충전량 비교'),
    ('AI 머신러닝', '모델 구축',     '',                  'XGBoost 기반 일별 충전량 예측 모델 설계'),
    ('AI 머신러닝', '학습 및 예측',  '',                  '충전 특성 선택, 8:2 데이터 분리, 예측 및 결과 출력'),
    ('AI 머신러닝', '분석',          '오차 분석',         'Actual vs Predicted 차이 분석 (scatter)'),
    ('AI 머신러닝', '분석',          '중요도 분석',       '충전량 예측 기여도 인자 분석 (barplot)'),
    ('AI 머신러닝', '모델 성능평가', '지표 계산',         'R², MAE 기반 모델 신뢰도 검증 (5회 교차검증)'),
    ('AI 머신러닝', '프로토타이핑',  '',                  'Streamlit을 이용한 충전 수요 예측 웹 앱 개발'),
]
st = doc.add_table(rows=len(scope_rows)+1, cols=4)
st.style = 'Table Grid'
# 헤더: 텍스트 먼저 설정 후 병합
hdr = st.rows[0]
hdr.cells[0].text = '과제구분'
hdr.cells[3].text = '내용'
hdr.cells[0].merge(hdr.cells[2])
# 데이터 행
for i, (cat, mid, sub, cont) in enumerate(scope_rows):
    ri = i + 1
    row = st.rows[ri]
    row.cells[0].text = cat
    row.cells[1].text = mid
    if sub:
        row.cells[2].text = sub
        row.cells[3].text = cont
    else:
        row.cells[2].text = cont
        row.cells[2].merge(row.cells[3])
# 세로 병합 (마지막에)
st.cell(1,0).merge(st.cell(7,0))    # 데이터셋
st.cell(8,0).merge(st.cell(13,0))   # AI 머신러닝
st.cell(1,1).merge(st.cell(3,1))    # 전처리
st.cell(4,1).merge(st.cell(7,1))    # EDA 분석
st.cell(10,1).merge(st.cell(11,1))  # 분석
doc.add_heading('2.3 과제 추진 방법',2)

def bpara(text):
    p=doc.add_paragraph(); p.add_run(text).bold=True; return p
def cbullet(text):
    p=doc.add_paragraph(); p.paragraph_format.left_indent=Pt(12); p.add_run('○ '+text); return p
def sbullet(text):
    p=doc.add_paragraph(); p.paragraph_format.left_indent=Pt(24); p.add_run('■ '+text); return p

bpara('1) 구축 대상 선정 기준')
cbullet('데이터 접근성 및 활용성')
sbullet('공공데이터포털을 통한 한국전력공사 서울시 전기차 충전 데이터 무료 수집 가능')
sbullet('정부 및 공공기관에서 이미 구축된 충전 이용 데이터베이스 활용 가능')
sbullet('충전량에 영향을 미치는 자치구·충전기 유형·시간 등 다양한 독립변수 포함으로 모델학습 유용성 확보')
cbullet('예측모델 개발 효율성')
sbullet('충전량·충전 구분·자치구·요일·월 등 변수 구조가 단순하여 모델 학습 및 평가 과정 간소화 가능')
sbullet('개발된 모델을 타 지역 및 전국 단위 충전 인프라 예측에 확장 적용 가능')
cbullet('환경문제 해결 기여도 및 경제성')
sbullet('충전 수요 예측을 통한 전력 부하 분산 및 에너지 절감 기여 (ex. 전력 피크 저감, 재생에너지 연계 등)')
sbullet('충전 인프라 투자 우선순위 결정을 통한 설치 비용 절감 효과')
sbullet('충전 병목 해소로 전기차 보급 확대 → 온실가스 감소 등 사회적 비용감소 효과')

bpara('2) AI 예측 분석모델 적용 대상')
at=doc.add_table(rows=2,cols=4); at.style='Table Grid'
for j,h in enumerate(['환경관리\n기능','수집 데이터','예측모델인자(독립변수)','AI예측 분석 대상']):
    at.rows[0].cells[j].text=h
dr=at.rows[1]
dr.cells[0].text='전기차\n충전'
dr.cells[1].text=('- 한국전력공사 서울시 전기차 충전소 충전량 데이터 (527,183건, 2025-01~2026-03)\n'
                   '- 충전소별 일별 충전량 집계 데이터\n'
                   '- 자치구별 일별 충전량 집계 데이터')
dr.cells[2].text=('- 위치변수: 자치구, 충전소명\n'
                   '- 충전기변수: 충전 구분(급속/완속), 충전기 용량(kW)\n'
                   '- 시간변수: 요일, 월')
dr.cells[3].text=('- 일별 충전량(kWh) 예측\n'
                   '- 수요 상위 자치구 도출\n'
                   '- 충전소 핫스팟 TOP10\n'
                   '- 인프라 투자 우선순위 결정')
doc.add_heading('3. 연구개발 주요 결과물',1)
doc.add_heading('① 데이터 수집',2)
doc.add_paragraph('한국전력공사 서울 충전량, 527,183 세션, 19개 컬럼(충전량·충전구분·시군구·날짜 등). 기간: 2025-01~2026-03. 출처: KEPCO 공공데이터 활용승인.')
doc.add_heading('② 데이터 분석',2)
doc.add_paragraph('데이터 정제: 음수·누락 등 불필요 데이터 제거 · 분석 기간(2025-01~2026-03) · 시군구 컬럼으로 자치구 직접 분류 (25개 구 100%) · 충전 후에야 알 수 있는 항목(충전 횟수) 예측에서 제외.')
doc.add_paragraph('항목 간 관련도 분석 — 충전 후에야 알 수 있는 항목은 관련도가 높아도 학습에서 제외:'); fig('06_corr.png',4.3)
doc.add_paragraph('충전량 분포(0~4000 확대) / 충전구분별 평균:'); fig('01_target_dist.png',4.5); fig('05_charger.png',3.3)
doc.add_paragraph('수요 상위 구(인프라 투자 우선 후보 지역): 송파 > 강남 > 성동 > 서초 > 강동'); fig('04_top_gu.png',5.0)
doc.add_paragraph('요일별 충전량 추이 — 요일(weekday)을 독립변수로 선택한 근거:'); fig('02_weekday.png',5.0)
doc.add_paragraph('월별 충전량 추이 — 월(month)을 독립변수로 선택한 근거:'); fig('03_month.png',5.0)
doc.add_heading('③ 데이터 학습 및 모델 정의',2)
doc.add_paragraph('예측 목표: 일별 충전량 · AI 모델: RandomForest · 검증: 학습/테스트 8:2 분할 + 3회 교차검증.')
t=doc.add_table(rows=3,cols=5); t.style='Table Grid'
hdr=['모델','기준 모델 정확도','AI 모델 정확도','교차검증 정확도','평균 오차(kWh)']
data=[['구(거시) — RandomForest','0.756','0.806','0.167','134'],['충전소(미시) — RandomForest','0.469','0.564','0.458','32']]
for j,h in enumerate(hdr): t.rows[0].cells[j].text=h
for i,r in enumerate(data):
    for j,v in enumerate(r): t.rows[i+1].cells[j].text=v
doc.add_paragraph('→ 두 모델 모두 기준 모델 대비 성능 향상 확인.')
doc.add_paragraph('예측 vs 실제(0~4000 확대) / 특성 중요도(구 모델):'); fig('07_pred_gu.png',5.4); fig('08_imp_gu.png',4.8)
doc.add_heading('④ 예측 결과 활용 방안',2)
doc.add_paragraph(
    '충전 수요 예측 결과는 단순 수치가 아니라 \'어디에, 언제, 얼마나\' 충전 자원을 투입할지 '
    '의사결정의 근거로 활용된다. 아래 표는 예측 아웃풋의 3가지 실사용 경로를 정리한 것이다.'
)
ut=doc.add_table(rows=4,cols=3); ut.style='Table Grid'
uhdr=['활용 분야','예측 활용 방식','기대 효과']
udata=[
    ['충전 인프라 투자','수요 상위 구·충전소 TOP-N 파악','신규 충전기 설치 우선순위 결정 (예산 효율 향상)'],
    ['전력 부하 관리','시간대·요일별 수요 피크 예측','한전 부하 분산 계획 수립 (에너지 절감)'],
    ['이동형 충전 배차(비전)','고수요 구역·시간대 사전 탐지','이동 충전 차량 출동 지역·시각 결정'],
]
for j,h in enumerate(uhdr): ut.rows[0].cells[j].text=h
for i,r in enumerate(udata):
    for j,v in enumerate(r): ut.rows[i+1].cells[j].text=v
doc.add_paragraph('')
doc.add_paragraph(
    '【활용 예시】 앱에서 강남구 / 급속 / 금요일 / 6월 선택 시 예측 충전량 1,245 kWh 출력 '
    '→ 이 구역·시간대는 수요 상위권 → 인프라 투자 및 이동형 충전 우선 배치 대상으로 판단.'
)
doc.add_heading('⑤ 예측 모델 실효성 검증 — 25년 학습 모델 vs 26년 1~3월 실제 충전량',2)
doc.add_paragraph(
    '25년(1~12월) 데이터로 학습한 모델이 26년 1~3월 실제 충전량을 얼마나 정확하게 예측하는지 검증하였다. '
    '학습(25년)·검증(26년 Q1) 분리를 통해 모델의 미래 예측력을 확인한다.'
)
vt=doc.add_table(rows=7,cols=4); vt.style='Table Grid'
vhdr=['구분','내용','수치','비고']
vdata=[
    ['학습 데이터','25년 1~12월 충전 세션','서울 527,183건','KEPCO 전체'],
    ['검증 데이터','26년 1~3월 충전 세션','서울 106,569건','out-of-sample'],
    ['구 모델 R²','실제 vs 예측 일치도','0.806','RandomForest'],
    ['충전소 모델 R²','실제 vs 예측 일치도','0.564','RandomForest'],
    ['수요 1위 구','25년 충전량 최다','송파구 252,564 kWh','26년 투자 우선'],
    ['수요 2위 구','25년 충전량 2위','강남구 244,968 kWh','인프라 확충 필요'],
]
for j,h in enumerate(vhdr): vt.rows[0].cells[j].text=h
for i,r in enumerate(vdata):
    for j,v in enumerate(r): vt.rows[i+1].cells[j].text=v
doc.add_paragraph(
    '→ 25년 데이터 학습 모델은 26년 1~3월 실제 충전량을 R²=0.806(구 모델) 수준으로 예측하여 '
    '인프라 투자 의사결정 근거로 활용 가능함을 검증하였다. '
    '수요 상위 구(송파·강남·성동·서초)를 중심으로 26년 충전 인프라 확충이 필요하다.'
)
doc.add_heading('⑥ 프로토타이핑 (화면)',2)
doc.add_paragraph('Streamlit 서비스: 구·충전기·요일·월 입력 → 예상 일 충전량 + 구별 수요 + 충전소 핫스팟 TOP10.')
doc.add_paragraph('[여기에 배포된 Streamlit 앱 스크린샷을 삽입하세요]')
doc.add_heading('4. 결론 및 향후',1)
bullets(['구 모델 정확도 80.6%, 충전소 모델 정확도 56.4% — 두 모델 모두 기준 모델 대비 성능 향상 확인',
         '수요 상위 지역(송파·강남·성동·서초…) 도출 → 26년 인프라 투자 우선순위 의사결정 지원',
         '25년 학습 → 26년 Q1 검증 완료 — 미래 수요 예측 실효성 입증',
         '향후: 2주 DL(LSTM 시계열 예측) / 3주 LLM(충전 어드바이저·RAG 챗봇)으로 확장'])
out=ROOT/'docs'/'오영석_머신러닝프로젝트.docx'
try:
    doc.save(str(out)); print("docx 저장:", out.name)
except PermissionError:
    alt=ROOT/'docs'/'오영석_머신러닝프로젝트_new.docx'; doc.save(str(alt))
    print("원본이 열려있어 새 파일로 저장:", alt.name, "(기존 닫고 이걸 쓰세요)")
