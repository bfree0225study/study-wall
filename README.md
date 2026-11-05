# study-wall

공부 기록장과 잠금화면 이미지. Claude 없이 무료로 돌아간다.

## 흐름
1. 기록장: 구글 시트에 붙은 Apps Script 웹앱(`apps-script/Code.gs`). 화면 코드는 이 저장소의 `app/index.html`을 불러온다(고치면 1분 안에 반영, 재배포 필요 없음).
2. 저장하면 1~2분 뒤 Apps Script가 GitHub Actions(`.github/workflows/wall.yml`)를 한 번 실행한다. 매일 한국 00:10, 05:00, 05:40에도 실행된다.
3. Actions: 기록장 내보내기를 받아 `tools/unpack.py` -> `sync.py` -> `make.py` 순서로 `phone*.png`, `tablet*.png`를 만들어 올린다.
4. 폰·태블릿의 Automate가 30분마다 raw 이미지를 받아 배경화면으로 쓴다.

## 고칠 곳
- 잠금화면 디자인: `make.py` 맨 위 설정 블록(색, 위아래 빈 공간).
- 기록장 디자인: `app/index.html`의 `:root` 색 변수, 항목 목록은 `BASE_LABELS`.
- 파일 이름: `wall.yml`의 `WALL_SUFFIX`. 지금은 `""`(전환 완료)라서 `phone.png`, `tablet.png`로 만든다. 따로 시험할 때만 `"_new"`.

## 비밀 값
- Apps Script 스크립트 속성: `TOKEN`(setup이 만듦), `GH_TOKEN`(GitHub 토큰, 이 저장소 Actions 쓰기만), `SHEET_ID`.
- GitHub 저장소 Secrets: `APPS_SCRIPT_URL`(웹앱 /exec 주소), `APPS_SCRIPT_TOKEN`(위 TOKEN).
