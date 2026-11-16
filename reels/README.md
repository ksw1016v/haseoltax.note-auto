# 릴스 대기열

폴더 이름 순서대로 하나씩 올라갑니다 (01, 02, 03 …). 게시된 폴더는 state.json 의 published 에 기록돼요.

```
reels/01/
  reel.mp4   1080x1920 영상 (Higgsfield로 제작)
  cover.jpg  (선택) 미리보기 표지
  ep.json
```

ep.json 예시
```json
{
 "no": 1,
 "title": "이원장 노동청 편",
 "hold": false,
 "caption": "첫 줄 후킹\n\n본문...\n\n#세무 #사장님 #절세",
 "dm": {
  "keyword": "장부",
  "replies": ["DM 보내드렸어요 🌲 메시지 요청함도 확인해 주세요!"],
  "message": "DM 본문 (가이드 + 상담 신청 링크)"
 }
}
```
- `hold: true` 이면 그 편은 건너뛰고 다음 편을 올립니다.
- `dm` 이 없는 편은 댓글 자동 답장을 하지 않습니다. 신청 페이지가 준비되기 전에는 빼 두세요.
