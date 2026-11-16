"""댓글 키워드('장부' 등) → 자동 대댓글 + 비공개 답장 DM.

- 대상: ep.json 에 "dm" 이 있는 편 (state.json 의 dm_media: {media_id: 폴더})
  "dm": {"keyword": "장부", "replies": ["대댓글 후보", ...], "message": "DM 본문"}
- 인스타 규정: 댓글 1개당 비공개 답장 1통, 댓글 단 지 7일 이내만 가능
- 처리한 댓글 ID는 state.json 의 dm_done 에 남겨 두 번 보내지 않음
- 공개 저장소라 사용자 아이디·댓글 내용은 기록하지 않음 (건수와 성공 여부만)
환경변수 TEST=1 : 최근 게시물 10개 전체에서 TEST_EP 편의 문구로 응답(시험용, 한 번만)
"""
import json, os, re, random, time, datetime, pathlib
from publish import call, IG_USER_ID, CONFIG, ROOT, load_state, save_state


def norm(t):
    return re.sub(r"[\s!~.?·'\"]", "", t or "")


def safe(method, path, **p):
    try:
        return call(method, path, **p), None
    except SystemExit as ex:
        return None, str(ex)[:300]


def send_dm(cid, text):
    payload = dict(recipient=json.dumps({"comment_id": cid}), message=json.dumps({"text": text}, ensure_ascii=False))
    r, err = safe("POST", f"{IG_USER_ID}/messages", **payload)
    if err:
        r2, err2 = safe("POST", "me/messages", **payload)
        if not err2:
            return r2, None
        err = f"{err} | me/messages: {err2}"
    return r, err


def targets(st):
    t = dict(st.get("dm_media", {}))
    if os.environ.get("TEST") == "1":
        ep = os.environ.get("TEST_EP", "")
        media, err = safe("GET", f"{IG_USER_ID}/media", fields="id", limit=10)
        if err:
            print("::error::게시물 목록 실패", err)
        for m in (media or {}).get("data", []):
            t.setdefault(m["id"], ep)
    return t


def main():
    st = load_state()
    done = set(st.get("dm_done", []))
    log = st.setdefault("dm_log", [])
    own = CONFIG.get("username")
    now = datetime.datetime.now(datetime.timezone.utc)
    sent = 0
    for media_id, folder in targets(st).items():
        ep = json.loads((ROOT / folder / "ep.json").read_text(encoding="utf-8"))
        dm = ep.get("dm")
        if not dm:
            continue
        kw = norm(dm.get("keyword") or CONFIG.get("dm_keyword", "장부"))
        res, err = safe("GET", f"{media_id}/comments", fields="id,text,username,timestamp", limit=50)
        if err:
            print("::warning::댓글 읽기 실패", media_id, err)
            continue
        for c in res.get("data", []):
            if c["id"] in done or c.get("username") == own or kw not in norm(c.get("text")):
                continue
            ts = datetime.datetime.strptime(c["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            if now - ts > datetime.timedelta(days=6, hours=20):
                continue
            _, dm_err = send_dm(c["id"], dm["message"])
            reply = random.choice(dm["replies"]) if not dm_err else "댓글 감사합니다 🌲 가이드는 곧 DM으로 보내드릴게요!"
            _, rp_err = safe("POST", f"{c['id']}/replies", message=reply)
            rec = {"media": media_id, "folder": folder, "dm": "fail" if dm_err else "ok", "reply": "fail" if rp_err else "ok",
                   "at": time.strftime("%Y-%m-%d %H:%M:%S")}
            if dm_err:
                rec["dm_error"] = dm_err
                print("::warning::DM 실패", dm_err)
            if rp_err:
                print("::warning::대댓글 실패", rp_err)
            log.append(rec)
            done.add(c["id"])
            sent += 1
            time.sleep(2)
    st["dm_done"] = sorted(done)
    st["dm_log"] = log[-500:]
    save_state(st)
    print(f"새로 처리한 댓글 {sent}개")


if __name__ == "__main__":
    main()
