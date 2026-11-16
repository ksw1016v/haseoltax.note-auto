"""대기열(reels/NN/)에서 다음 편을 골라 인스타그램 릴스로 게시한다.

편 폴더 reels/NN/
  reel.mp4   1080x1920 릴스 영상
  cover.jpg  (선택) 미리보기 표지
  ep.json    {"no": 1, "title": "...", "caption": "...", "dm": {...}(선택)}

환경변수
  IG_TOKEN     인스타 액세스 토큰 (GitHub Secrets)
  IG_USER_ID   (선택) 계정 숫자 ID. 없으면 config.json 의 ig_user_id
  IMAGE_BASE   파일 공개 주소 접두사 (jsDelivr, 커밋 SHA 고정)
  DRY_RUN=1    실제 게시 없이 확인만

사용법
  python3 publish.py next          -> 다음 게시할 편 폴더 (없으면 빈 줄)
  python3 publish.py reel <폴더>   -> 그 편 게시 후 state.json 기록
"""
import json, os, sys, time, pathlib, urllib.request, urllib.parse, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent
STATE = ROOT / "state.json"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
IG_USER_ID = os.environ.get("IG_USER_ID") or CONFIG.get("ig_user_id", "")


def api_base():
    tok = os.environ.get("IG_TOKEN", "")
    return "https://graph.instagram.com/v23.0" if tok.startswith("IG") else "https://graph.facebook.com/v23.0"


def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"published": [], "log": []}


def save_state(st):
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def next_reel():
    done = set(load_state().get("published", []))
    for d in sorted((ROOT / "reels").iterdir() if (ROOT / "reels").exists() else []):
        if d.is_dir() and d.name not in done and (d / "reel.mp4").exists() and (d / "ep.json").exists():
            if json.loads((d / "ep.json").read_text(encoding="utf-8")).get("hold"):
                continue  # 보류 중인 편은 건너뜀
            return d
    return None


def call(method, path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{api_base()}/{path}"
    req = urllib.request.Request(url + "?" + data.decode()) if method == "GET" else urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API 오류 {e.code} {path}: {e.read().decode()}")


def raw_base(base):
    pre = "https://cdn.jsdelivr.net/gh/"
    if not base.startswith(pre) or "@" not in base:
        return None
    repo, sha = base[len(pre):].split("@", 1)
    return f"https://raw.githubusercontent.com/{repo}/{sha}"


def create_media(base, rel, **params):
    """컨테이너 생성. 인스타가 파일을 못 받아 오면(9004 등) 잠시 뒤 재시도 → GitHub raw 주소로 대체."""
    last = None
    for i, b in enumerate(t for t in (base, base, raw_base(base)) if t):
        if i:
            print(f"::warning::파일 주소를 못 가져와 다시 시도 ({b.split('/')[2]}) {rel}")
            time.sleep(15)
        extra = dict(params)
        if "cover_url" in extra:
            extra["cover_url"] = f"{b}/{extra['cover_url']}"
        try:
            return call("POST", f"{IG_USER_ID}/media", video_url=f"{b}/{rel}", **extra)["id"]
        except SystemExit as e:
            last = e
            if "9004" not in str(e) and "2207052" not in str(e):
                raise
    raise last


def wait_ready(cid, tries=72):
    for _ in range(tries):
        r = call("GET", cid, fields="status_code,status")
        if r["status_code"] == "FINISHED":
            return
        if r["status_code"] in ("ERROR", "EXPIRED"):
            raise SystemExit(f"컨테이너 {cid} 상태 {r['status_code']} {r.get('status', '')}")
        time.sleep(5)
    raise SystemExit(f"컨테이너 {cid} 준비 시간 초과")


def post_reel(folder):
    folder = pathlib.Path(folder)
    rel = folder.resolve().relative_to(ROOT).as_posix()
    ep = json.loads((folder / "ep.json").read_text(encoding="utf-8"))
    import caption_check
    caption_check.warn_only(folder / "ep.json")
    base = os.environ["IMAGE_BASE"].rstrip("/")
    extra = {"cover_url": f"{rel}/cover.jpg"} if (folder / "cover.jpg").exists() else {"thumb_offset": str(ep.get("thumb_ms", 1500))}
    if os.environ.get("DRY_RUN"):
        print("DRY RUN", f"{base}/{rel}/reel.mp4", ep["caption"][:80], sep="\n")
        return
    if not IG_USER_ID:
        raise SystemExit("IG_USER_ID 가 비어 있어요 (config.json 의 ig_user_id)")
    print("계정:", call("GET", IG_USER_ID, fields="username").get("username"))
    for attempt in range(3):  # CDN이 방금 올린 영상을 아직 못 줄 때가 있어 1분 간격 3번
        cid = create_media(base, f"{rel}/reel.mp4", media_type="REELS", caption=ep["caption"], share_to_feed="true", **extra)
        try:
            wait_ready(cid)
            break
        except SystemExit as ex:
            print(f"::warning::릴스 준비 실패({attempt + 1}/3): {ex}")
            if attempt == 2:
                raise
            time.sleep(60)
    res = call("POST", f"{IG_USER_ID}/media_publish", creation_id=cid)
    print("릴스 게시 완료 media id:", res["id"])
    st = load_state()
    st.setdefault("published", []).append(folder.name)
    if ep.get("dm"):
        st.setdefault("dm_media", {})[res["id"]] = rel  # 댓글 DM 봇이 이 게시물의 답장을 찾는 표
    st.setdefault("log", []).append({"no": ep.get("no"), "slug": folder.name, "title": ep.get("title"), "media_id": res["id"],
                                     "at": time.strftime("%Y-%m-%d %H:%M:%S")})
    save_state(st)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"
    if cmd == "next":
        d = next_reel()
        print("" if d is None else d.relative_to(ROOT).as_posix())
    elif cmd == "reel":
        post_reel(ROOT / sys.argv[2])
