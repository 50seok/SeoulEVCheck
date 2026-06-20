# SeoulEVCheck — 서울 전기차 충전 인텔리전스

서울시 전기차 충전 데이터로 수요를 예측(ML/DL)하고 운영을 권고(LLM)하는 3주 프로젝트.

## 3주 로드맵
| 주차 | 단계 | 내용 | 마감 | 상태 | 태그 | R² |
|---|---|---|---|---|---|---|
| 1주 | ML | 충전 수요 예측 (XGBoost, 충전소·구) | 6/24 | 진행 | - | - |
| 2주 | DL | LSTM 시계열 예측 | 7/1 | 대기 | - | - |
| 3주 | LLM | 충전 어드바이저 (RAG·권고) | 7/8 | 대기 | - | - |

## 구조
- `notebooks/` 주차별 분석 · `src/{common,ml,dl,llm}` · `app/` Streamlit · `models/` · `docs/` PRD

## 실행
```
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```
