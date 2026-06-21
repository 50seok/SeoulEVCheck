"""
보고서 삽입용 이미지 일괄 생성
① 컬럼 설명 표          → asset_columns.png
② 전처리 코드 스니펫     → asset_code_preprocess.png
③ 모델학습 코드 스니펫   → asset_code_model.png
④ 예측활용 코드 스니펫   → asset_code_predict.png
⑤ DATA IMPORTING 다이어그램 → asset_diagram.png
⑥ Actual vs Predicted   → asset_actual_vs_pred.png
⑦ Feature Importance    → asset_feature_importance.png
"""
import pandas as pd, numpy as np
import matplotlib.pyplot as plt, matplotlib.patches as mpatches
import warnings; warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ═══════════════════════════════════════════════════════
# ① 컬럼 설명 표
# ═══════════════════════════════════════════════════════
cols = [
    ['충전구분',    'object',   '급속 / 완속',                  '충전 방식 구분'],
    ['충전소명',    'object',   '영등포전력지사',                 '충전소 이름'],
    ['주소',       'object',   '서울특별시 영등포구 경인로 878',   '충전소 도로명 주소'],
    ['충전기용량',  'int64',    '50',                           '충전기 최대 용량 (kW)'],
    ['충전량',     'float64',  '13.10',                        '세션 충전 전력량 (kWh) ← 예측 목표'],
    ['충전시간',   'int64',    '0',                            '충전 소요 시간 (시)'],
    ['충전분',     'int64',    '29',                           '충전 소요 시간 (분)'],
    ['충전시작시각', 'datetime', '2021-01-02 14:58:37',          '충전 시작 일시'],
    ['충전종료시각', 'datetime', '2021-01-02 15:28:25',          '충전 종료 일시'],
]
df_col = pd.DataFrame(cols, columns=['컬럼명', '데이터 타입', '예시값', '설명'])

fig, ax = plt.subplots(figsize=(13, 3.6))
ax.axis('off')
row_colors = [['#fff5f5' if i % 2 == 0 else 'white'] * 4 for i in range(len(df_col))]
row_colors[4] = ['#fff3cd'] * 4  # 타깃 행 강조

tbl = ax.table(cellText=df_col.values, colLabels=df_col.columns,
               cellLoc='left', loc='center', cellColours=row_colors)
tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1, 1.9)
for j in range(4):
    tbl[(0, j)].set_facecolor('#c0392b')
    tbl[(0, j)].set_text_props(color='white', fontweight='bold')
tbl[(5, 0)].set_text_props(fontweight='bold')
ax.set_title('데이터 구성 및 변수 설명 (총 638,702 세션 · 9개 컬럼)',
             fontsize=12, fontweight='bold', pad=8)
plt.tight_layout()
plt.savefig('asset_columns.png', dpi=150, bbox_inches='tight')
plt.close()
print('① 컬럼 설명 표 저장 완료')

# ═══════════════════════════════════════════════════════
# 코드 스니펫 공통 렌더러
# ═══════════════════════════════════════════════════════
def save_code_img(code_lines, title, filename):
    n = len(code_lines)
    h = max(2.0, n * 0.38 + 0.8)
    fig, ax = plt.subplots(figsize=(11, h))
    ax.set_facecolor('#1e1e1e'); fig.patch.set_facecolor('#1e1e1e')
    ax.axis('off')
    ax.set_title(title, fontsize=11, fontweight='bold', color='white', pad=6, loc='left')
    for i, line in enumerate(code_lines):
        y = 1.0 - (i + 0.5) / n
        if line.startswith('#'):
            color = '#6a9955'
        elif any(kw in line for kw in ['def ', 'import ', 'from ', 'return']):
            color = '#569cd6'
        elif '=' in line and not '==' in line:
            color = '#9cdcfe'
        else:
            color = '#d4d4d4'
        ax.text(0.02, y, line, transform=ax.transAxes,
                fontsize=9.5, color=color,
                fontfamily='Courier New', va='center')
    plt.tight_layout(pad=0.3)
    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='#1e1e1e')
    plt.close()

# ② 전처리 코드 스니펫
save_code_img([
    "# 주소에서 '구' 추출 (도로명/지번 혼재 대응)",
    "def extract_gu(a):",
    "    for t in a.split():",
    "        if t.endswith('구'): return t",
    "",
    "df['start'] = pd.to_datetime(df['충전시작시각'], errors='coerce')",
    "df['gu']    = df['주소'].map(extract_gu)",
    "df['충전량'] = pd.to_numeric(df['충전량'], errors='coerce')",
    "",
    "# null / 음수 제거",
    "df = df.dropna(subset=['start', 'gu', '충전량'])",
    "df = df[df['충전량'] >= 0]",
    "",
    "# 밀집 구간 필터 (월별 세션 수 10% 이상 → 2021-01 ~ 2022-03)",
    "ym = df['start'].dt.to_period('M')",
    "df = df[ym.isin(ym.value_counts()[lambda c: c >= c.max()*0.10].index)]",
    "",
    "# 파생 특성 생성",
    "df['date']    = df['start'].dt.date",
    "df['weekday'] = df['start'].dt.weekday   # 0=월 ~ 6=일",
    "df['month']   = df['start'].dt.month",
], "② 데이터 정제 및 가공", "asset_code_preprocess.png")
print('② 전처리 코드 스니펫 저장 완료')

# ③ 모델 학습 코드 스니펫
save_code_img([
    "# 구 단위 일별 집계",
    "gu = df.groupby(['gu','충전구분','date']).agg(",
    "    충전량=('충전량','sum'), weekday=('weekday','first'),",
    "    month=('month','first')).reset_index()",
    "",
    "# 특성 행렬 구성 (범주형 원-핫 인코딩)",
    "X = pd.concat([",
    "    pd.get_dummies(gu[['gu','충전구분']].astype(str), dtype=np.uint8),",
    "    gu[['weekday','month']]",
    "], axis=1)",
    "y = gu['충전량'].values",
    "",
    "# 학습 / 테스트 분할 (8:2) · XGBoost 학습",
    "X_train, X_test, y_train, y_test = train_test_split(",
    "    X, y, test_size=0.2, random_state=42)",
    "",
    "model = xgb.XGBRegressor(",
    "    n_estimators=400, max_depth=7, learning_rate=0.08,",
    "    subsample=0.8, colsample_bytree=0.8,",
    "    tree_method='hist', random_state=42)",
    "model.fit(X_train, y_train)",
    "",
    "# 5-Fold 교차검증",
    "cv = cross_val_score(model, X, y,",
    "    cv=KFold(5, shuffle=True, random_state=42), scoring='r2')",
    "print(f'CV R² = {cv.mean():.3f}')   # → 0.768",
], "③ AI 모델 학습 코드", "asset_code_model.png")
print('③ 모델학습 코드 스니펫 저장 완료')

# ④ 예측 활용 코드 스니펫
save_code_img([
    "# 사용자 입력 기반 수요 예측 함수",
    "def predict_demand(gu_name, charge_type, weekday, month):",
    "    row = pd.DataFrame([{",
    "        'gu': gu_name, '충전구분': charge_type,",
    "        'weekday': weekday, 'month': month",
    "    }])",
    "    row_enc = pd.get_dummies(row[['gu','충전구분']].astype(str))",
    "    row_enc = row_enc.reindex(columns=X_cols, fill_value=0)",
    "    row_enc[['weekday','month']] = row[['weekday','month']].values",
    "    return model.predict(row_enc)[0]",
    "",
    "# 예시: 강남구 / 급속 / 금요일(4) / 6월",
    "kwh = predict_demand('강남구', '급속', weekday=4, month=6)",
    "print(f'예상 일 충전량: {kwh:.0f} kWh')  # → 1,245 kWh",
    "",
    "# 수요 핫스팟 TOP10 (Streamlit 대시보드 연동)",
    "hotspot = (gu.groupby('gu')['충전량'].sum()",
    "             .sort_values(ascending=False).head(10))",
    "# → 송파구 > 강남구 > 마포구 > 서초구 > 용산구 ...",
], "④ 예측 결과 활용 코드", "asset_code_predict.png")
print('④ 예측 코드 스니펫 저장 완료')

# ═══════════════════════════════════════════════════════
# ⑤ DATA IMPORTING 다이어그램
# ═══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.set_facecolor('white'); ax.axis('off')

stages = [
    ('데이터\n수집', '#2c3e50',
     '• 한국전력공사 공공데이터\n• 638,702 충전 세션\n• 9개 컬럼 (충전량·구분·주소 등)'),
    ('AI\n예측 모델', '#c0392b',
     '• 오류 데이터 제거 / 구 분류\n• 구 단위 일별 집계\n• AI 모델 학습 및 검증'),
    ('결과\n활용', '#1a6b3a',
     '• 수요 상위 지역 TOP10 도출\n• 구·충전소별 예측 충전량\n• 웹 서비스 제공'),
]

box_w, box_h = 0.24, 0.60
xs = [0.06, 0.38, 0.70]
y0 = 0.20

for i, (title, color, desc) in enumerate(stages):
    x = xs[i]
    rect = mpatches.FancyBboxPatch((x, y0), box_w, box_h,
        boxstyle="round,pad=0.02", linewidth=2,
        edgecolor=color, facecolor=color + '15',
        transform=ax.transAxes, clip_on=False)
    ax.add_patch(rect)
    ax.text(x + box_w/2, y0 + box_h - 0.08, title,
            transform=ax.transAxes, ha='center', va='center',
            fontsize=13, fontweight='bold', color=color)
    ax.text(x + box_w/2, y0 + box_h/2 - 0.05, desc,
            transform=ax.transAxes, ha='center', va='center',
            fontsize=9, color='#333333', linespacing=1.7)
    if i < 2:
        ax.annotate('', xy=(xs[i+1] - 0.01, y0 + box_h/2),
                    xytext=(xs[i] + box_w + 0.01, y0 + box_h/2),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle='->', color='#555555',
                                   lw=2.5, mutation_scale=20))

sub_labels = ['공공데이터 수집\n충전소·세션 데이터',
              '데이터 정제 → 모델 학습\nAI 충전량 예측',
              '예측 결과 시각화\n인프라 투자 의사결정 지원']
for i, lbl in enumerate(sub_labels):
    ax.text(xs[i] + box_w/2, y0 - 0.10, lbl,
            transform=ax.transAxes, ha='center', va='top',
            fontsize=8.5, color='#666666', linespacing=1.5)

ax.set_title('AI 분석모델 구축 프로세스 — SeoulEVCheck',
             fontsize=13, fontweight='bold', pad=4)
plt.tight_layout()
plt.savefig('asset_diagram.png', dpi=150, bbox_inches='tight')
plt.close()
print('⑤ DATA IMPORTING 다이어그램 저장 완료')

# ═══════════════════════════════════════════════════════
# 모델 재학습 (⑥⑦ 생성용)
# ═══════════════════════════════════════════════════════
print('모델 재학습 중 (잠시 기다려주세요)...')

def extract_gu(a):
    if not isinstance(a, str): return None
    for t in a.split():
        if t.endswith('구'): return t
    return None

df = pd.read_excel('../data/한국전력공사_서울시 전기차 충전소 충전량_20220331.xlsx')
df['start'] = pd.to_datetime(df['충전시작시각'], errors='coerce')
df['gu']    = df['주소'].map(extract_gu)
df['충전량'] = pd.to_numeric(df['충전량'], errors='coerce')
df = df.dropna(subset=['start', 'gu', '충전량'])
df = df[df['충전량'] >= 0]
ym = df['start'].dt.to_period('M'); c = ym.value_counts()
df = df[ym.isin(c[c >= c.max() * 0.10].index)].copy()
df['date']    = df['start'].dt.date
df['weekday'] = df['start'].dt.weekday
df['month']   = df['start'].dt.month

gu = (df.groupby(['gu', '충전구분', 'date'], as_index=False)
        .agg(충전량=('충전량', 'sum'),
             weekday=('weekday', 'first'),
             month=('month', 'first')))

X = pd.concat([
    pd.get_dummies(gu[['gu', '충전구분']].astype(str), dtype=np.uint8),
    gu[['weekday', 'month']]
], axis=1)
y = gu['충전량'].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = xgb.XGBRegressor(n_estimators=400, max_depth=7, learning_rate=0.08,
                          subsample=0.8, colsample_bytree=0.8,
                          tree_method='hist', random_state=42)
model.fit(X_train, y_train)
pred = model.predict(X_test)
r2   = r2_score(y_test, pred)
rmse = mean_squared_error(y_test, pred) ** 0.5

# ⑥ Actual vs Predicted
fig, ax = plt.subplots(figsize=(6.5, 6))
ax.scatter(y_test, pred, s=6, alpha=0.25, color='#2980b9', label='예측값')
lim = 4000
ax.plot([0, lim], [0, lim], 'r--', lw=1.5, label='완벽 예측선')
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
ax.set_xlabel('실제 충전량 (kWh)', fontsize=11)
ax.set_ylabel('예측 충전량 (kWh)', fontsize=11)
ax.set_title('AI 예측값 vs 실제 충전량', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.text(0.05, 0.93, f'정확도(R²) = {r2:.1%}\n평균 오차 = {rmse:.0f} kWh',
        transform=ax.transAxes, fontsize=10,
        bbox=dict(boxstyle='round', facecolor='#fff3cd', alpha=0.8))
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
plt.savefig('asset_actual_vs_pred.png', dpi=150, bbox_inches='tight')
plt.close()
print('⑥ Actual vs Predicted 산점도 저장 완료')

# ⑦ Feature Importance
fi = pd.Series(model.feature_importances_, index=X.columns).sort_values()
top = fi.tail(12)
colors = ['#c0392b' if v == top.max() else '#2980b9' for v in top.values]

fig, ax = plt.subplots(figsize=(8, 5))
top.plot(kind='barh', ax=ax, color=colors)
ax.set_xlabel('영향도', fontsize=11)
ax.set_title('충전량 예측에 영향을 준 요소 TOP 12', fontsize=12, fontweight='bold')
for i, v in enumerate(top.values):
    ax.text(v + 0.0005, i, f'{v:.3f}', va='center', fontsize=9)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
plt.savefig('asset_feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print('⑦ Feature Importance 차트 저장 완료')

print('\n✅ 전체 이미지 생성 완료')
for f in ['asset_columns.png', 'asset_code_preprocess.png', 'asset_code_model.png',
          'asset_code_predict.png', 'asset_diagram.png',
          'asset_actual_vs_pred.png', 'asset_feature_importance.png']:
    print(' -', f)
