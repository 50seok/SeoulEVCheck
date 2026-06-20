import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd, numpy as np, joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb
plt.rcParams["font.family"]="Malgun Gothic"; plt.rcParams["axes.unicode_minus"]=False
ROOT=Path("C:/teamwork/SeoulEVCheck"); DATA=ROOT/"data"; MODELS=ROOT/"models"; FIG=ROOT/"reports"/"figures"
MODELS.mkdir(exist_ok=True)
def rmse(a,b): return float(np.sqrt(mean_squared_error(a,b)))
def baseline(tr,te,keys):
    gm=tr.groupby(keys,as_index=False)["충전량"].mean().rename(columns={"충전량":"p"})
    m=te.merge(gm,on=keys,how="left"); m["p"]=m["p"].fillna(tr["충전량"].mean())
    return r2_score(te["충전량"],m["p"]), rmse(te["충전량"],m["p"])
def run(df,cats,nums,keys,tag,title):
    Xc=pd.get_dummies(df[cats].astype(str),dtype=np.uint8).reset_index(drop=True)
    Xn=df[nums].reset_index(drop=True)
    X=pd.concat([Xc,Xn],axis=1); y=df["충전량"].values
    Xtr,Xte,ytr,yte,dtr,dte=train_test_split(X,y,df,test_size=0.2,random_state=42)
    br2,brm=baseline(dtr,dte,keys)
    m=xgb.XGBRegressor(n_estimators=400,max_depth=7,learning_rate=0.08,subsample=0.8,
        colsample_bytree=0.8,tree_method="hist",random_state=42)
    m.fit(Xtr,ytr); pred=m.predict(Xte)
    xr2=r2_score(yte,pred); xrm=rmse(yte,pred)
    kf=KFold(5,shuffle=True,random_state=42); cv=cross_val_score(m,X,y,cv=kf,scoring="r2")
    print(f"[{tag}] baseline R2={br2:.3f} RMSE={brm:.0f} | XGB R2={xr2:.3f} RMSE={xrm:.0f} | CV R2={cv.mean():.3f}+/-{cv.std():.3f}")
    joblib.dump(m,MODELS/f"xgb_{tag}.pkl")
    rs=np.random.RandomState(0); idx=rs.choice(len(yte),min(3000,len(yte)),replace=False)
    plt.figure(figsize=(5,5)); plt.scatter(yte[idx],pred[idx],s=5,alpha=0.3)
    lim=float(max(yte.max(),pred.max())); plt.plot([0,lim],[0,lim],'r--')
    plt.xlabel("실제 충전량(kWh)"); plt.ylabel("예측 충전량(kWh)"); plt.title(f"{title} 예측vs실제 (R2={xr2:.2f})")
    plt.tight_layout(); plt.savefig(FIG/f"07_pred_{tag}.png",dpi=110); plt.close()
    imp=pd.Series(m.feature_importances_,index=X.columns).sort_values().tail(15)
    plt.figure(figsize=(6,5)); imp.plot(kind="barh"); plt.title(f"{title} 특성 중요도 TOP15")
    plt.tight_layout(); plt.savefig(FIG/f"08_imp_{tag}.png",dpi=110); plt.close()
gu=pd.read_csv(DATA/"gu_day.csv",encoding="utf-8-sig")
st=pd.read_csv(DATA/"station_day.csv",encoding="utf-8-sig")
print("=== 모델 B: 구 단위 ===")
run(gu,["gu","충전구분"],["weekday","month"],["gu","충전구분","weekday"],"gu","구 모델")
print("=== 모델 A: 충전소 단위 ===")
run(st,["충전소명","gu","충전구분"],["충전기용량","weekday","month"],["충전소명","weekday"],"station","충전소 모델")
print("saved:",[p.name for p in MODELS.glob('*.pkl')])
