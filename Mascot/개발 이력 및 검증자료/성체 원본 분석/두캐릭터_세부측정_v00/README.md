# 대키미·외지몽 원본 기반 세부 시트

기존 임의 조정 v4의 후속 원본 관측 자료다. 디자인을 변경하지 않았으며 원본 파일은 바이트 그대로 포함했다.

- daekimi/character_sheet.pdf, character_sheet.md: 대키미 시트.
- oejimong/character_sheet.pdf, character_sheet.md: 외지몽 시트.
- 각 폴더 measurement_viewer.html: 원본 확대·표시 켜기/끄기.
- measurements.json: 모든 자동·수동 좌표, 원본 해시, 분석 방법.
- 4시점 outline.csv·scanlines.csv·source_trace.svg: 원본 픽셀별 외곽과 가로 폭.
- eye_left_outline.csv·eye_right_outline.csv: 눈 실제 외곽. 단순 원·타원으로 대체하지 않는다.
- torso_width_stations.csv·head_landmarks.csv: 수동 판독값과 원본 위치.
- reference/original_board.png: 변경하지 않은 원본.

자동 임계값 경계와 수동 이음선 판독값은 구분했다. 엄지 좌표는 실제로 보이는 동작에만 적용한다. 가려진 부분·원본3D 깊이·재질계수는 임의로 만들지 않았다. 사용자 지정 키는 대키미103cm·외지몽105cm를 유지했다. 측면·45도·후면을 공통 축척의 정밀 직교도라고 가정하지 않는다.
