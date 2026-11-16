"""캡션 점검 (게시는 막지 않고 경고만). 세무사 광고 규정상 결과 보장·과장 표현을 피한다.
사용법: python3 caption_check.py reels/01/ep.json [--strict]
"""
import json, re, sys, pathlib

LIMIT = 2200
BANNED = {
    "100%": "결과 보장 표현", "무조건": "확정 표현", "걱정 끝": "결과 보장 표현", "확실히 줄여": "결과 보장 표현",
    "세금 0원": "결과 보장 표현", "업계 최저": "비교·과장 광고", "최저가": "비교·과장 광고", "1위": "근거 없는 순위 표현",
    "보장": "보장 표현(문맥 확인)",
}
FINGERPRINT = {"—": "긴 줄표(—)", "–": "중간 줄표(–)", "​": "보이지 않는 문자", " ": "줄바꿈 안 되는 공백"}
TAG_RE = re.compile(r"#[0-9A-Za-z_가-힣]+")


def check(path):
    ep = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    cap = ep.get("caption", "")
    out = []
    if not cap.strip():
        out.append(("error", "캡션이 비어 있어요"))
    if len(cap) > LIMIT:
        out.append(("error", f"캡션 {len(cap)}자 (최대 {LIMIT})"))
    for w, why in BANNED.items():
        if w in cap:
            out.append(("warning", f"'{w}': {why}"))
    for ch, why in FINGERPRINT.items():
        if ch in cap:
            out.append(("warning", f"AI 흔적 문자: {why}"))
    n = len(TAG_RE.findall(cap))
    if not 3 <= n <= 10:
        out.append(("warning", f"해시태그 {n}개 (3~10개 권장)"))
    return out


def warn_only(path):
    for lvl, msg in check(path):
        print(f"::warning::캡션 점검 {path}: {msg}")


if __name__ == "__main__":
    res = check(sys.argv[1])
    for lvl, msg in res:
        print(lvl, msg)
    if "--strict" in sys.argv and any(l == "error" for l, _ in res):
        sys.exit(1)
    print("점검 끝" if not res else f"{len(res)}건")
