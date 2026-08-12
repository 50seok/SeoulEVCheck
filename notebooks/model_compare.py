"""
모델 비교표 생성 스크립트
LinearRegression / RandomForest / XGBoost 성능 비교 (구 모델 기준)
결과: model_compare_result.png
"""
import pandas as pd, numpy as np, matplotlib.pyplot as plt, matplotlib
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB   = ROOT / 'notebooks'

from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ── 1. 데이터 로드 & 전처리 (week1_ml.ipynb 동일) ──────────────────────────
def extract_gu(a):
    if not isinstance(a, str): return None
    for t in a.split():
        if t.endswith('구'): return t
    return None

df = pd.read_excel(ROOT/'data'/'한국전력공사_서울시 전기차 충전소 충전량_20220331.xlsx')
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

# ── 2. 구 단위 집계 ─────────────────────────────────────────────────────────
gu = (df.groupby(['gu', '충전구분', 'date'], as_index=False)
        .agg(충전량=('충전량', 'sum'),
             weekday=('weekday', 'first'),
             month=('month', 'first')))

X = pd.concat([
    pd.get_dummies(gu[['gu', '충전구분']].astype(str), dtype=np.uint8),
    gu[['weekday', 'month']]
], axis=1)
y = gu['충전량'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

# ── 3. 모델 학습 & 평가 ─────────────────────────────────────────────────────
models = {
    'Linear Regression': LinearRegression(),
    'Random Forest':     RandomForestRegressor(n_estimators=200, max_depth=10,
                                               random_state=42, n_jobs=-1),
    'XGBoost':           xgb.XGBRegressor(n_estimators=400, max_depth=7,
                                          learning_rate=0.08, subsample=0.8,
                                          colsample_bytree=0.8,
                                          tree_method='hist', random_state=42),
}

rows = []
for name, model in models.items():
    print(f'{name} 학습 중...')
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    rows.append({
        '모델':  name,
        'R²':   round(r2_score(y_test, pred), 4),
        'RMSE': round(mean_squared_error(y_test, pred) ** 0.5, 1),
        'MAE':  round(mean_absolute_error(y_test, pred), 1),
    })

result = pd.DataFrame(rows)
print('\n── 모델 성능 비교 (구 모델) ──')
print(result.to_string(index=False))

# ── 4. 표 이미지 저장 ───────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 2.2))
ax.axis('off')

best_idx = result['R²'].idxmax()
cell_colors = []
for i in range(len(result)):
    if i == best_idx:
        cell_colors.append(['#fff3cd'] * len(result.columns))
    else:
        cell_colors.append(['white'] * len(result.columns))

tbl = ax.table(
    cellText=result.values,
    colLabels=result.columns,
    cellLoc='center',
    loc='center',
    cellColours=cell_colors,
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(12)
tbl.scale(1, 2.0)

for j in range(len(result.columns)):
    tbl[(0, j)].set_facecolor('#c0392b')
    tbl[(0, j)].set_text_props(color='white', fontweight='bold')

ax.set_title('모델 성능 비교 — 구(거시) 단위 일별 충전량 예측',
             fontsize=13, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig(NB/'model_compare_result.png', dpi=150, bbox_inches='tight')
print('\n모델 비교 이미지 저장 완료: model_compare_result.png')
