# 해솔노트 자동 게시 (@haesoltax.note)

세무법인 해솔의 사장님 세무·노무 릴스 계정 자동화. 골든덕랩(`ksw1016v/goldenducklab-auto`) 구조를 옮겨 씀.

| 할 일 | 파일 |
|---|---|
| 릴스 대기열 | `reels/NN/` (reel.mp4, cover.jpg, ep.json) → `reels/README.md` |
| 게시 | `publish.py`, 일정 `guard.py` (월·수·금 20:00 KST) |
| 캡션 점검 | `caption_check.py` (결과 보장·과장 표현 경고) |
| 댓글 '장부' → 대댓글 + DM | `dm_bot.py`, `dm_active.py`, `.github/workflows/dm.yml` |
| 성과 수집 | `insights.py` → `insights.json` (매일 00:23) |
| 토큰 확인 | `.github/workflows/token-check.yml` |

- Secrets `IG_TOKEN` : 통합 로그인 시스템 사용자 토큰 (만료 없음)
- `config.json` 의 `ig_user_id` : 인스타 계정 숫자 ID
- 수동 게시: Actions → reel-post → Run workflow
