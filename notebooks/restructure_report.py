"""
report_v4.docx 섹션 구조 재편 → report_v5.docx
5단계 구조로 재배치:
[1단계] 데이터 수집 및 통합
[2단계] 탐색적 데이터 분석 (EDA)
[3단계] 데이터 전처리
[4단계] AI 모델 학습
[5단계] 성능평가 및 인프라 불일치 분석
"""
import sys, shutil, copy
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC  = Path(r'C:\teamwork\SeoulEVCheck\docs\report_v4.docx')
DEST = Path(r'C:\teamwork\SeoulEVCheck\docs\report_v5.docx')
shutil.copy2(SRC, DEST)
doc = Document(DEST)
body = doc.element.body

def get_text(elem):
    return ''.join(t.text or '' for t in elem.iter(qn('w:t')))

def set_elem_text(elem, text):
    """XML 요소의 텍스트 전부 교체 (첫 run에 새 텍스트)"""
    # 모든 t 요소 초기화
    for t in elem.iter(qn('w:t')):
        t.text = ''
    # 첫 번째 run의 t에 새 텍스트 삽입
    runs = elem.findall('.//' + qn('w:r'))
    if runs:
        t_elem = runs[0].find(qn('w:t'))
        if t_elem is None:
            t_elem = OxmlElement('w:t')
            runs[0].append(t_elem)
        t_elem.text = text
    else:
        # run이 없으면 새로 생성
        r = OxmlElement('w:r')
        t_elem = OxmlElement('w:t')
        t_elem.text = text
        r.append(t_elem)
        elem.append(r)

def make_para_elem(text, style_id='21', bold=False):
    """새 단락 XML 요소 생성 (body에 추가하지 않음)"""
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    pStyle = OxmlElement('w:pStyle')
    pStyle.set(qn('w:val'), style_id)
    pPr.append(pStyle)
    p.append(pPr)
    r = OxmlElement('w:r')
    if bold:
        rPr = OxmlElement('w:rPr')
        b = OxmlElement('w:b')
        rPr.append(b)
        r.append(rPr)
    t = OxmlElement('w:t')
    t.text = text
    r.append(t)
    p.append(r)
    return p

# ── 현재 body 자식 목록 ───────────────────────────────────────────────────
children = list(body)
sect = body.find(qn('w:sectPr'))
# 인덱스별 딕셔너리
elems = {i: children[i] for i in range(len(children))}

print('=== 현재 구조 확인 (주요 인덱스) ===')
for i in [18, 19, 22, 36, 42, 43, 44, 45, 46, 56]:
    if i < len(children):
        txt = get_text(children[i])
        has_img = children[i].find('.//' + qn('w:drawing')) is not None
        print(f'[{i:03d}] img={int(has_img)} | {txt[:70]}')

print()

# ── 헤더 텍스트 수정 ──────────────────────────────────────────────────────
set_elem_text(elems[18], '3. 분석 내용')
set_elem_text(elems[19], '[1단계] 데이터 수집 및 통합')
set_elem_text(elems[22], '[2단계] 탐색적 데이터 분석 (EDA)')
set_elem_text(elems[36], '[4단계] AI 모델 학습')
set_elem_text(elems[45], '[5단계] 성능평가 및 인프라 불일치 분석')

# ── 새 헤딩 요소 생성 ────────────────────────────────────────────────────
h_preprocess = make_para_elem('[3단계] 데이터 전처리', style_id='21')

# ── 재배치 순서 정의 ─────────────────────────────────────────────────────
# 현재 v4 body 인덱스 기준:
#   000-017: 타이틀~다이어그램 (유지)
#   018: "3. 분석 내용" (헤더 수정)
#   019: "[1단계]..." (헤더 수정)
#   020-021: 1단계 내용 (컬럼 텍스트 + 컬럼 이미지)
#   022: "[2단계]..." (헤더 수정)
#   023-024: 전처리 텍스트 + 전처리 코드 이미지 → [3단계]로 이동
#   025-035: EDA 내용 (히트맵~분포~EDA결론~TOP10)
#   036: "[4단계]..." (헤더 수정)
#   037-041: 4단계 내용 (모델 코드~성능표~비교표)
#   042-044: 예측vs실제 제목 + 산점도 + FI → [5단계] 앞부분
#   045: "[5단계]..." (헤더 수정, 기존 ④)
#   046-055: 5단계 내용 (불일치분석~활용표~코드)
#   056-058: 프로토타이핑
#   059~끝: 결론/후기

end_idx = len(children)
if sect is not None:
    end_idx -= 1  # sectPr 제외

new_order = (
    list(range(0, 22)) +          # [000-021] 타이틀 ~ 1단계 content
    [elems[22]] +                 # [2단계] EDA 헤더 (텍스트 수정됨)
    list(range(25, 36)) +         # [025-035] EDA 내용 (히트맵~TOP10~EDA결론)
    [h_preprocess] +              # [3단계] 헤더 (신규 생성)
    list(range(23, 25)) +         # [023-024] 전처리 텍스트 + 코드 이미지
    list(range(36, 42)) +         # [036-041] [4단계] 헤더 + 모델코드 + 성능표 + 비교표
    [elems[45]] +                 # [5단계] 헤더 (기존 ④에서 변환)
    list(range(42, 45)) +         # [042-044] 예측vs실제 제목 + 산점도 + FI
    list(range(46, 56)) +         # [046-055] 불일치분석 + 활용표 + 코드
    list(range(56, end_idx))      # [056~] 프로토타이핑~결론~후기
)

# ── body 재구성 ──────────────────────────────────────────────────────────
for child in list(body):
    if child.tag != qn('w:sectPr'):
        body.remove(child)

for item in new_order:
    if isinstance(item, int):
        body.append(elems[item])
    else:
        body.append(item)

if sect is not None:
    body.append(sect)

doc.save(DEST)
print(f'✅ 저장 완료: {DEST}')
print()

# ── 검증 ─────────────────────────────────────────────────────────────────
doc2 = Document(DEST)
body2 = doc2.element.body
print('=== 재편 후 구조 ===')
for i, child in enumerate(body2):
    tag = child.tag.split('}')[-1]
    if tag == 'p':
        txt = get_text(child)
        has_img = child.find('.//' + qn('w:drawing')) is not None
        if txt.strip() or has_img:
            print(f'[{i:03d}] img={int(has_img)} | {txt[:70]}')
    elif tag == 'tbl':
        print(f'[{i:03d}] TABLE')
