import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns, pandas as pd
from pathlib import Path
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
ROOT = Path("C:/teamwork/SeoulEVCheck"); DATA = ROOT/"data"
FIG = ROOT/"reports"/"figures"; FIG.mkdir(parents=True, exist_ok=True)
gu = pd.read_csv(DATA/"gu_day_2025.csv", encoding="utf-8-sig")

def save(name, title):
    plt.title(title); plt.tight_layout(); plt.savefig(FIG/name, dpi=110); plt.close()

clipped = gu[gu["충전량"] <= 3000]
pct = len(clipped) / len(gu) * 100
plt.figure(figsize=(7,4))
ax1 = plt.gca()
sns.histplot(clipped["충전량"], bins=60, ax=ax1)
ax2 = ax1.twinx()
sns.kdeplot(clipped["충전량"], ax=ax2, color="red", linewidth=2)
ax2.set_yticks([]); ax2.set_ylabel("")
plt.xlabel("충전량(kWh)"); plt.xlim(0, 3000)
plt.title(f"자치구별 일 충전량 분포 (0~3,000 kWh, 전체의 {pct:.1f}%)")
plt.tight_layout(); plt.savefig(FIG/"01_target_dist.png", dpi=110); plt.close()
wd = gu.groupby("weekday")["충전량"].mean()
plt.figure(figsize=(6,4))
wd.plot(kind="bar")
plt.xticks(range(7), ["월","화","수","목","금","토","일"], rotation=0)
plt.xlabel("")
save("02_weekday.png","요일별 평균 충전량")
mo = gu.groupby("month")["충전량"].mean()
plt.figure(figsize=(7,4)); mo.plot(kind="bar"); save("03_month.png","월별 평균 충전량")
topgu = gu.groupby("gu")["충전량"].sum().sort_values(ascending=False).head(10)
plt.figure(figsize=(8,4)); topgu.plot(kind="bar"); save("04_top_gu.png","구별 총 충전량 TOP10 (수요 핫스팟)")
ct = gu.groupby("충전구분")["충전량"].mean()
plt.figure(figsize=(5,4)); ct.plot(kind="bar"); save("05_charger.png","충전구분별 평균 충전량")
num = gu[["충전량","sessions","year","month","weekday","is_holiday","is_weekend","avg_hour"]]
num.columns = ["충전량(kWh)","세션수","연도","월","요일","공휴일","주말","평균시작시각"]
plt.figure(figsize=(8,6)); sns.heatmap(num.corr(), annot=True, cmap="Blues", fmt=".2f")
save("06_corr.png","항목 간 관련도 (상관관계)\n예측 불가 항목은 충전량과 관련도가 높아도 학습에서 제외")

print("figures:", len(list(FIG.glob("*.png"))))
print("\n[충전량 describe]\n", gu["충전량"].describe().round(1).to_string())
print("\n[요일별 평균 0=월]\n", wd.round(1).to_string())
print("\n[충전구분 평균]\n", ct.round(1).to_string())
print("\n[수요 TOP5 구]\n", topgu.head(5).round(0).to_string())
print("\n[타깃 상관]\n", num.corr()["충전량(kWh)"].round(3).to_string())
try:
    from ydata_profiling import ProfileReport
    ProfileReport(gu, minimal=True, title="SeoulEVCheck gu_day EDA").to_file(ROOT/"reports"/"gu_day_profile.html")
    print("\nydata-profiling: OK -> reports/gu_day_profile.html")
except Exception as e:
    print("\nydata-profiling skip:", str(e)[:70])
