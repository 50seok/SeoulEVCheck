import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns, pandas as pd
from pathlib import Path
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
ROOT = Path("C:/teamwork/SeoulEVCheck"); DATA = ROOT/"data"
FIG = ROOT/"reports"/"figures"; FIG.mkdir(parents=True, exist_ok=True)
gu = pd.read_csv(DATA/"gu_day.csv", encoding="utf-8-sig")

def save(name, title):
    plt.title(title); plt.tight_layout(); plt.savefig(FIG/name, dpi=110); plt.close()

plt.figure(figsize=(7,4)); sns.histplot(gu["충전량"], bins=60); plt.xlabel("충전량(kWh)")
save("01_target_dist.png","구별 일 충전량 분포")
wd = gu.groupby("weekday")["충전량"].mean()
plt.figure(figsize=(6,4)); wd.plot(kind="bar"); plt.xlabel("요일(0=월)")
save("02_weekday.png","요일별 평균 충전량")
mo = gu.groupby("month")["충전량"].mean()
plt.figure(figsize=(7,4)); mo.plot(kind="bar"); save("03_month.png","월별 평균 충전량")
topgu = gu.groupby("gu")["충전량"].sum().sort_values(ascending=False).head(10)
plt.figure(figsize=(8,4)); topgu.plot(kind="bar"); save("04_top_gu.png","구별 총 충전량 TOP10 (수요 핫스팟)")
ct = gu.groupby("충전구분")["충전량"].mean()
plt.figure(figsize=(5,4)); ct.plot(kind="bar"); save("05_charger.png","충전구분별 평균 충전량")
num = gu[["충전량","sessions","weekday","month"]]
plt.figure(figsize=(5,4)); sns.heatmap(num.corr(), annot=True, cmap="Blues", fmt=".2f")
save("06_corr.png","상관관계 히트맵")

print("figures:", len(list(FIG.glob("*.png"))))
print("\n[충전량 describe]\n", gu["충전량"].describe().round(1).to_string())
print("\n[요일별 평균 0=월]\n", wd.round(1).to_string())
print("\n[충전구분 평균]\n", ct.round(1).to_string())
print("\n[수요 TOP5 구]\n", topgu.head(5).round(0).to_string())
print("\n[타깃 상관]\n", num.corr()["충전량"].round(3).to_string())
try:
    from ydata_profiling import ProfileReport
    ProfileReport(gu, minimal=True, title="SeoulEVCheck gu_day EDA").to_file(ROOT/"reports"/"gu_day_profile.html")
    print("\nydata-profiling: OK -> reports/gu_day_profile.html")
except Exception as e:
    print("\nydata-profiling skip:", str(e)[:70])
