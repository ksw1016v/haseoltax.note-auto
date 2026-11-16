"""IG_TOKEN 으로 연결된 인스타 계정을 찾아 아이디·숫자 ID·권한을 출력한다 (토큰 값은 출력하지 않음)."""
import json, os, urllib.request, urllib.parse, urllib.error

tok = os.environ.get("IG_TOKEN", "")
if not tok:
    raise SystemExit("IG_TOKEN 시크릿이 비어 있어요")


def get(base, path, **p):
    p["access_token"] = tok
    try:
        with urllib.request.urlopen(f"{base}/{path}?" + urllib.parse.urlencode(p), timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


print("토큰 종류:", "인스타 로그인(IG…, 60일)" if tok.startswith("IG") else "통합 로그인(EAA…)")
found = []
if tok.startswith("IG"):
    me = get("https://graph.instagram.com/v23.0", "me", fields="user_id,username,account_type,followers_count")
    print("계정:", {k: me.get(k) for k in ("username", "user_id", "account_type", "followers_count")}, me.get("error", {}).get("message", ""))
    if me.get("user_id"):
        found.append((me.get("username"), me["user_id"]))
else:
    G = "https://graph.facebook.com/v23.0"
    me = get(G, "me", fields="id,name")
    print("토큰 주인:", me.get("name"), me.get("error", {}).get("message", ""))
    pages = get(G, "me/accounts", fields="name,instagram_business_account{id,username,followers_count}", limit=50)
    for pg in pages.get("data", []):
        ig = pg.get("instagram_business_account")
        if ig:
            found.append((ig.get("username"), ig["id"]))
    for path in ("me/instagram_accounts", ):
        r = get(G, path, fields="id,username", limit=50)
        for a in r.get("data", []):
            found.append((a.get("username"), a.get("id")))
    d = get(G, "debug_token", input_token=tok).get("data", {})
    print("권한:", sorted(s for s in d.get("scopes", []) if "instagram" in s or "pages" in s or "business" in s))
    for g in d.get("granular_scopes", []):
        if "instagram" in g.get("scope", ""):
            print("  ", g.get("scope"), "대상 ID:", g.get("target_ids"))
            for tid in g.get("target_ids") or []:
                a = get(G, tid, fields="id,username,followers_count")
                if a.get("username"):
                    found.append((a["username"], a["id"]))
seen = set()
for u, i in found:
    if (u, i) not in seen:
        seen.add((u, i))
        print(f"찾은 인스타 계정: @{u}  IG_USER_ID={i}")
if not found:
    raise SystemExit("토큰으로 인스타 계정을 찾지 못했어요")
