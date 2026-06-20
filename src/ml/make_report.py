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
         '향후 비전: 예측 수요 기반 이동형 배달충전 배치 → 자율주행 무인 충전의 두뇌(스토리)'])
doc.add_heading('2.2 과제 범위',2)
doc.add_paragraph('AI(데이터 정제·EDA·모델) / 시각화(Streamlit) / 테스트. 제외: 자율주행 구현, CNN/이미지, 동 단위 예측.')
doc.add_heading('2.3 추진 방법',2)
doc.add_paragraph('DATA IMPORTING → 전처리 → 모델링(XGBoost) → 예측 → 시각화')
doc.add_heading('3. 연구개발 주요 결과물',1)
doc.add_heading('① 데이터 수집',2)
doc.add_paragraph('한국전력공사 서울 충전량, 638,702 세션, 9개 컬럼(충전량·충전구분·주소·시각 등). 출처: 공공데이터포털.')
doc.add_heading('② 데이터 분석',2)
doc.add_paragraph('전처리: null/음수 11,203건 제거 · 밀집구간 필터(2021-01~2022-03, 455일) · 주소→구 추출 98.5% · 누수 특성(세션수·충전시간) 제외.')
doc.add_paragraph('상관관계 히트맵 (세션수 0.89 → 누수로 특성 제외):'); fig('06_corr.png',4.3)
doc.add_paragraph('충전량 분포(0~4000 확대) / 충전구분별 평균:'); fig('01_target_dist.png',4.5); fig('05_charger.png',3.3)
doc.add_paragraph('수요 상위 구(배달충전 우선지역): 송파 > 강남 > 마포 > 서초 > 용산'); fig('04_top_gu.png',5.0)
doc.add_heading('③ 데이터 학습 및 모델 정의',2)
doc.add_paragraph('타깃: 일별 충전량 · 범주형 원-핫 · XGBoost 회귀 · 검증: train/test 8:2 + 5-fold CV(shuffle), random_state=42.')
t=doc.add_table(rows=3,cols=5); t.style='Table Grid'
hdr=['모델','베이스라인 R²','XGBoost R²','CV R²','RMSE(kWh)']
data=[['구(거시)','0.761','0.787','0.768','216'],['충전소(미시)','0.485','0.571','0.570','52']]
for j,h in enumerate(hdr): t.rows[0].cells[j].text=h
for i,r in enumerate(data):
    for j,v in enumerate(r): t.rows[i+1].cells[j].text=v
doc.add_paragraph('→ 두 모델 모두 베이스라인 초과(주 성공기준 달성).')
doc.add_paragraph('예측 vs 실제(0~4000 확대) / 특성 중요도(구 모델):'); fig('07_pred_gu.png',5.4); fig('08_imp_gu.png',4.8)
doc.add_heading('④ 프로토타이핑 (화면)',2)
doc.add_paragraph('Streamlit 서비스: 구·충전기·요일·월 입력 → 예상 일 충전량 + 구별 수요 + 충전소 핫스팟 TOP10.')
doc.add_paragraph('[여기에 배포된 Streamlit 앱 스크린샷을 삽입하세요]')
doc.add_heading('4. 결론 및 향후',1)
bullets(['구 모델 R²≈0.79, 충전소 모델 R²≈0.57 — 두 모델 모두 베이스라인 초과',
         '수요 핫스팟(송파·강남·마포…) 도출 → 배달충전 우선지역 의사결정 지원',
         '향후: year(증가추세) 특성 추가 / 2주 DL(LSTM 시계열) / 3주 LLM(충전 어드바이저·RAG)'])
out=ROOT/'docs'/'오영석_머신러닝프로젝트.docx'
try:
    doc.save(str(out)); print("docx 저장:", out.name)
except PermissionError:
    alt=ROOT/'docs'/'오영석_머신러닝프로젝트_new.docx'; doc.save(str(alt))
    print("원본이 열려있어 새 파일로 저장:", alt.name, "(기존 닫고 이걸 쓰세요)")
