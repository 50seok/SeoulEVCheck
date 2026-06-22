import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd, numpy as np, joblib, holidays
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

ROOT   = Path("C:/teamwork/SeoulEVCheck")
DATA   = ROOT / "data"
MODELS = ROOT / "models"
FIG    = ROOT / "reports" / "figures"
MODELS.mkdir(exist_ok=True)

def rmse(a, b): return float(np.sqrt(mean_squared_error(a, b)))
def mae(a, b):  return float(mean_absolute_error(a, b))

# KNN 제외 — 대용량 데이터에서 CV 시 O(n²) 로 수십 분 소요
CANDIDATES = [
    ("LinearRegression",  LinearRegression()),
    ("Ridge",             Ridge()),
    ("DecisionTree",      DecisionTreeRegressor(max_depth=7, random_state=42)),
    ("RandomForest",      RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)),
    ("GradientBoosting",  GradientBoostingRegressor(n_estimators=50, max_depth=4,
                              learning_rate=0.1, random_state=42)),
]

def baseline(tr, te, keys):
    gm = tr.groupby(keys, as_index=False)["충전량"].mean().rename(columns={"충전량": "p"})
    m  = te.merge(gm, on=keys, how="left")
    m["p"] = m["p"].fillna(tr["충전량"].mean())
    return r2_score(te["충전량"], m["p"]), rmse(te["충전량"], m["p"]), mae(te["충전량"], m["p"])

def run(df, cats, nums, keys, tag, title, cv_sample=5000):
    Xc = pd.get_dummies(df[cats].astype(str), dtype=np.uint8).reset_index(drop=True)
    Xn = df[nums].reset_index(drop=True)
    X  = pd.concat([Xc, Xn], axis=1)
    y  = df["충전량"].values
    Xtr, Xte, ytr, yte, dtr, dte = train_test_split(X, y, df, test_size=0.2, random_state=42)

    br2, brm, bma = baseline(dtr, dte, keys)
    # CV는 최대 cv_sample 행으로 제한 (속도)
    cv_idx = np.random.RandomState(42).choice(len(X), min(cv_sample, len(X)), replace=False)
    Xcv, ycv = X.iloc[cv_idx], y[cv_idx]
    kf = KFold(3, shuffle=True, random_state=42)

    print(f"\n{'='*60}")
    print(f"[{tag}]  데이터 {len(df):,}행  기준모델 R²={br2:.3f}  RMSE={brm:.0f}  MAE={bma:.0f}")
    print(f"{'모델':<22} {'R²':>7} {'RMSE':>8} {'MAE':>8} {'CV R²(3폴드)':>14}")
    print("-" * 62)

    best_r2, best_m, best_name, best_pred = -999, None, "", None
    for name, m in CANDIDATES:
        m.fit(Xtr, ytr)
        pred = m.predict(Xte)
        r2   = r2_score(yte, pred)
        rm   = rmse(yte, pred)
        ma   = mae(yte, pred)
        cv   = cross_val_score(m, Xcv, ycv, cv=kf, scoring="r2")
        print(f"{name:<22} {r2:>7.3f} {rm:>8.0f} {ma:>8.0f}  {cv.mean():>6.3f}±{cv.std():.3f}")
        if r2 > best_r2:
            best_r2, best_m, best_name, best_pred = r2, m, name, pred

    print(f"\n-> 최적 모델: {best_name}  R²={best_r2:.3f}")
    joblib.dump(best_m, MODELS / f"model_{tag}.pkl")

    # 산점도
    rs  = np.random.RandomState(0)
    idx = rs.choice(len(yte), min(2000, len(yte)), replace=False)
    plt.figure(figsize=(5, 5))
    plt.scatter(yte[idx], best_pred[idx], s=5, alpha=0.3)
    lim = float(max(yte.max(), best_pred.max()))
    plt.plot([0, lim], [0, lim], "r--")
    plt.xlabel("실제 충전량(kWh)")
    plt.ylabel("예측 충전량(kWh)")
    plt.title(f"AI 예측값 vs 실제 충전량 (R²={best_r2:.2f})")
    plt.tight_layout()
    plt.savefig(FIG / f"07_pred_{tag}.png", dpi=110)
    plt.close()

    # 특성 중요도
    if hasattr(best_m, "feature_importances_"):
        imp = pd.Series(best_m.feature_importances_, index=X.columns).sort_values().tail(12)
        plt.figure(figsize=(6, 5))
        imp.plot(kind="barh")
        plt.xlabel("영향도")
        plt.title("충전량 예측에 영향을 준 요소 TOP12")
        plt.tight_layout()
        plt.savefig(FIG / f"08_imp_{tag}.png", dpi=110)
        plt.close()

    return best_name, best_r2, rmse(yte, best_pred), mae(yte, best_pred), br2

# ── 학습 실행 ──────────────────────────────────────────────
kr_hol = holidays.KR()

def add_features(df):
    df = df.copy()
    dates = pd.to_datetime(df["date"]).dt.date
    df["is_holiday"] = dates.map(lambda d: 1 if d in kr_hol else 0)
    df["is_weekend"]  = (df["weekday"] >= 5).astype(int)
    return df

gu = pd.read_csv(DATA / "gu_day_2025.csv",      encoding="utf-8-sig")
st = pd.read_csv(DATA / "station_day_2025.csv", encoding="utf-8-sig")

print("=== 구 단위 모델 ===")
gu_best, gu_r2, gu_rmse, gu_mae, gu_br2 = run(
    gu, ["gu", "충전구분"], ["weekday", "month", "is_holiday", "is_weekend"],
    ["gu", "충전구분", "weekday"], "gu", "구 모델"
)

print("\n=== 충전소 단위 모델 ===")
st_best, st_r2, st_rmse, st_mae, st_br2 = run(
    st, ["충전소명", "gu", "충전구분"], ["충전기용량", "weekday", "month", "is_holiday", "is_weekend"],
    ["충전소명", "weekday"], "station", "충전소 모델", cv_sample=3000
)

print("\n=== 최종 결과 요약 ===")
print(f"구 모델      최적={gu_best:<22} R²={gu_r2:.3f}  RMSE={gu_rmse:.0f}  MAE={gu_mae:.0f}")
print(f"충전소 모델  최적={st_best:<22} R²={st_r2:.3f}  RMSE={st_rmse:.0f}  MAE={st_mae:.0f}")
print("saved:", [p.name for p in MODELS.glob("*.pkl")])
