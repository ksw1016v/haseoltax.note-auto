"""오늘 이미 올렸거나 아직 게시 시간이 아니면 건너뛴다. 출력: skip=0 또는 skip=1

예약 실행(cron)은 늦거나 겹칠 수 있어 목표 시각 앞뒤로 여러 번 돌리고, 조건을 처음 만족한 실행만 올린다.
수동 실행(workflow_dispatch)은 요일·시간을 무시하고 '오늘 이미 올렸는지'만 본다.
"""
import json, os, pathlib, datetime

TARGET = (20, 0)                 # 한국 시간 게시 목표
DAYS = {0, 2, 4}                 # 월=0 … 일=6  → 월·수·금
LATE = (23, 30)                  # 이 시각이 지나면 그날은 건너뜀(예약 실행만)
EARLY = datetime.timedelta(minutes=15)

st = pathlib.Path(__file__).parent / "state.json"
log = json.loads(st.read_text(encoding="utf-8")).get("log", []) if st.exists() else []
now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=9)
today = now.date()
skip = 0
for e in log:
    at = datetime.datetime.strptime(e["at"], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=9)
    if at.date() == today and not e.get("repost"):
        skip = 1
if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
    start = datetime.datetime.combine(today, datetime.time(*TARGET)) - EARLY
    if now < start or today.weekday() not in DAYS or now > datetime.datetime.combine(today, datetime.time(*LATE)):
        skip = 1
print(f"skip={skip}")
