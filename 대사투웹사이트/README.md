# 대사투 웹사이트 — 로컬 시안

main `세부지침안/K파트v1/`(웹) 지침으로 옛 시안(degu-one.vercel.app)의 모바일 탭 구조를 다시 만든 **로컬 전용** 안내 사이트예요. 실제 가입·신청·저장은 없는 데모예요.

## 실행

```bash
python3 -m http.server 5178 --bind 127.0.0.1 --directory 대사투웹사이트
```

브라우저에서 http://localhost:5178 을 열어요. (레포 맨 위에서 실행)

## 파일

| 파일 | 내용 |
|---|---|
| `data.js` | **화면에 나오는 내용 전부.** 묶음마다 `src`에 원본 세부지침 위치가 적혀 있어요 |
| `app.js` | 탭 화면 그리기, 데모 동작(로그인·투표, 숙박 인증). 스탬프 북은 현장 배부라 안내만 함 |
| `style.css` | 디자인 (옛 시안 색·글꼴 기준, 마스코트 색은 D-1 기준) |
| `assets/` | 마스코트(D파트 `04_재현기준`에서 자름), 지도(Y.지도 `Y_축제전체_1안내도.webp`) |

## 다른 파트가 바뀌면

1. K파트 문서(K01~K06)를 먼저 맞춘다.
2. `data.js`에서 해당 `src`가 붙은 묶음만 고친다. (예: 토론 일정 → `schedule`·`debate`, 스탬프 → `stamp`, 숙박 → `stay`, 지도 → `zones`)
3. 지도 그림이 바뀌면 `assets/map_full.webp`를 새 파일로 바꾸고 `zones`의 x·y(%)를 맞춘다.

| 바뀐 파트 | 고칠 곳 |
|---|---|
| P0-1·P0-3·P0-4 | `festival`, `schedule`, `zones` |
| A (토론·골든벨·뮤지컬·NPC) | `debate`, `stageExtras`, `schedule` |
| B (10미·7구) | `programs`, `tenFoods`, `sevenGu`, `foodNotes` |
| C (플리마켓) | `programs`, `fleaNotes` |
| D (마스코트) | `mascots`, `assets/` |
| G-5 (숙박) | `stay` |
| H-10 (스탬프) | `stamp` |
| Y (지도) | `zones`, `assets/map_full.webp` |
