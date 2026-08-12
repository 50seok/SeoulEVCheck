"""
report_v3.docx 내용 수정 → report_v4.docx
변경 사항:
1. 사업과제 → 프로젝트 목표 (목적 문장 + bullet 3개)
2. 추진배경 bullet 교체 (배달충전/자율주행 제거)
3. EDA 결론 문단 추가
4. "배달충전 우선지역" → "인프라 투자 우선 후보 지역"
5. 수요 vs 인프라 불일치 분석 추가
6. 결론 bullet 수정
7. 후기 섹션 추가
"""
import shutil
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

SRC  = Path(r'C:\teamwork\SeoulEVCheck\docs\report_v3.docx')
DEST = Path(r'C:\teamwork\SeoulEVCheck\docs\report_v4.docx')
shutil.copy2(SRC, DEST)
doc = Document(DEST)

def get_text(p):
    return ''.join(r.text or '' for r in p.runs)

def set_text(p, text):
    for run in p.runs:
        run.text = ''
    if p.runs:
        p.runs[0].text = text
    else:
        p.add_run(text)

def find_para(keyword):
    for p in doc.paragraphs:
        if keyword in get_text(p):
            return p
    return None

def insert_after(ref_p, text, style='Normal', bold=False):
    new_p = doc.add_paragraph(text, style=style)
    if bold and new_p.runs:
        new_p.runs[0].bold = True
    ref_p._element.addnext(new_p._element)
    doc.element.body.remove(new_p._element)
    ref_p._element.addnext(new_p._element)
    return new_p

# ══ 1. 사업과제 → 프로젝트 목표 ══════════════════════════════════════════
p = find_para('1. 사업과제')
if p: set_text(p, '1. 프로젝트 목표'); print('✅ H1: 사업과제 → 프로젝트 목표')

p = find_para('AI 기반 서울시 전기차 충전 수요 예측 및 시각화')
if p:
    set_text(p,
        '서울시 전기차 충전 수요를 구·충전기 유형별로 예측하여, '
        '급속 충전 공급 병목과 인프라 사각지대 문제를 해결하기 위한 '
        '데이터 기반 인프라 투자 우선순위 결정을 지원한다.')
    bullets = [
        '데이터 기반 서울시 충전 인프라 투자 우선순위 결정 지원',
        '수요 예측 결과와 실제 충전 데이터 비교를 통한 인프라 병목·사각지대 식별',
        '구별·충전기 유형별 일 충전 수요 예측 모델 구축 (XGBoost)',
    ]
    for b in bullets:
        insert_after(p, b, style='List Bullet')
    print('✅ 목표 문장 + bullet 3개 추가')

# ══ 2. 추진배경 bullet 교체 ═══════════════════════════════════════════════
replacements = {
    '전기차 보급 급증': '서울시 전기차 등록 대수 급증에 비해 급속 충전기 공급 부족, 특정 충전소 쏠림·대기 문제 심화',
    '활용: 충전 인프라 투자 효율': '주거 형태별 충전 인프라 격차 심화 — 아파트 93% 편중, 단독·빌라 거주자 충전 사각지대 발생',
    '향후 비전: 예측 수요 기반 이동형 배달충전': '충전 수요 데이터 기반으로 투자 우선순위를 결정해 인프라 불균형 해소 필요',
}
for keyword, new_text in replacements.items():
    p = find_para(keyword)
    if p: set_text(p, new_text); print(f'✅ 추진배경 교체: {new_text[:30]}...')

# ══ 3. 독립/종속변수 정의 추가 ════════════════════════════════════════════
p = find_para('AI(데이터 정제·EDA·모델)')
if p:
    set_text(p, 'AI(데이터 정제·EDA·모델) / 시각화(Streamlit). 제외: 자율주행 구현, CNN/이미지, 동 단위 예측.')
    insert_after(p,
        '독립변수: gu(자치구), 충전구분(급속/완속), weekday(요일), month(월)  |  종속변수: 일별 충전량(kWh)',
        bold=True)
    print('✅ 독립/종속변수 정의 추가')

# ══ 4. "배달충전 우선지역" → "인프라 투자 우선 후보 지역" ═══════════════
for p in doc.paragraphs:
    txt = get_text(p)
    if '배달충전 우선지역' in txt:
        set_text(p, txt.replace('배달충전 우선지역', '인프라 투자 우선 후보 지역'))
        print(f'✅ 표현 교체 완료')

# ══ 5. EDA 결론 추가 ══════════════════════════════════════════════════════
p = find_para('인프라 투자 우선 후보 지역')
if p:
    eda = [
        ('① 수요 핫스팟: 송파 > 강남 > 마포 > 서초 > 용산 순 확인 → 인프라 투자 우선 후보 지역', 'List Bullet'),
        ('② 특성 선택: gu, 충전구분, weekday, month를 독립변수로 확정', 'List Bullet'),
        ('① 상관관계: 세션수(0.89)·충전시간은 누수 특성 → 학습 제외 결정', 'List Bullet'),
        ('[EDA 결론]', 'Normal'),
    ]
    for text, style in eda:
        np = insert_after(p, text, style=style)
        if '[EDA 결론]' in text and np.runs:
            np.runs[0].bold = True
    print('✅ EDA 결론 추가')

# ══ 6. 수요-인프라 불일치 분석 추가 ══════════════════════════════════════
p = find_para('충전 수요 예측 결과는 단순 수치가 아니라')
if p:
    analysis = [
        ('→ 용산구·금천구 급속 충전기 우선 확충, 광진구·중랑구 신규 투자 보류 권고', 'List Bullet'),
        ('🟢 공급 충분: 광진구(720.7배) · 중랑구(1,173배) — 수요 대비 과잉', 'List Bullet'),
        ('🟡 병목 의심: 강동구(128배) · 영등포구(137배) — 충전기 부족으로 잠재 수요 미충족', 'List Bullet'),
        ('🔴 사각지대: 용산구(55배) · 금천구(108배) — 수요 대비 실제 충전량 현저히 낮음', 'List Bullet'),
        ('[수요-인프라 불일치 분석 — 2023~2025년 실제 충전량 vs 예측 수요 비교]', 'Normal'),
    ]
    for text, style in analysis:
        np = insert_after(p, text, style=style)
        if '[수요-인프라' in text and np.runs:
            np.runs[0].bold = True
    print('✅ 수요-인프라 불일치 분석 추가')

# ══ 7. 결론 bullet 수정 ══════════════════════════════════════════════════
p = find_para('수요 핫스팟(송파·강남·마포')
if p:
    set_text(p, '수요-인프라 불일치 분석: 용산구·금천구 사각지대 식별 → 급속 충전기 우선 확충 권고')
    print('✅ 결론 bullet 수정')

p = find_para('예측 결과 → 인프라 투자')
if p:
    set_text(p, '수요 예측 기반 선택과 집중 — 사각지대 우선 투자·과잉 공급지역 보류로 예산 효율 극대화 가능')
    print('✅ 결론 활용방안 bullet 수정')

# ══ 8. 후기 섹션 추가 ════════════════════════════════════════════════════
p = find_para('향후: 2주 DL')
if p:
    epilogue = [
        ('향후 과제 — 2주차 DL(LSTM)에서 시계열 기반 미래 수요 예측, 3주차 LLM·RAG에서 "어느 구에 충전기를 설치해야 하나요?" 에 데이터로 답하는 인프라 어드바이저로 발전 예정.', 'List Bullet'),
        ('EDA와 전처리의 실질적 효용 — 세션수·충전시간을 누수 특성으로 제외하는 결정이 모델 신뢰도 향상에 결정적이었음. 좋은 데이터가 좋은 모델을 만든다는 원칙을 직접 체감.', 'List Bullet'),
        ('단순 수요 예측에서 실제 인프라 불균형 문제 해결로 — 수요가 높아도 인프라가 부족한 사각지대가 존재함을 실제 데이터로 확인. 데이터를 현실 문제와 연결하는 것이 AI 분석의 핵심임을 배움.', 'List Bullet'),
        ('5. 후기', 'Heading 1'),
    ]
    for text, style in epilogue:
        insert_after(p, text, style=style)
    print('✅ 후기 섹션 추가')

doc.save(DEST)
print(f'\n✅ 저장 완료: {DEST}')
