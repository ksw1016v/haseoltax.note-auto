"""DM 키워드가 걸린 편을 3일 안에 올렸으면 1, 아니면 0 (댓글 확인 반복 여부)"""
import json, datetime, pathlib
st = json.loads((pathlib.Path(__file__).resolve().parent / "state.json").read_text(encoding="utf-8"))
now = datetime.datetime.utcnow()
ids = set(st.get("dm_media", {}))
act = [e for e in st.get("log", []) if e.get("media_id") in ids
       and now - datetime.datetime.strptime(e["at"], "%Y-%m-%d %H:%M:%S") < datetime.timedelta(days=3)]
print(1 if act else 0)
