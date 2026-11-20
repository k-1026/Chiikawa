from pathlib import Path
import json, shutil, unicodedata, html, hashlib

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent.parent
N=lambda s:unicodedata.normalize('NFC',str(s))
def find(suffix):
    return next(p for p in ROOT.rglob('*') if p.is_file() and N(p).endswith(suffix) and '_정리관리' not in str(p))

asset_specs=[
('D','성체 대키미 · CG와 티셔츠 얼굴 기준','대키미_꼬리리본_턴어라운드_v01/파란 마스코트의 꼬리 리본.png','승인 외형 참고'),
('O','성체 외지몽 정면','외지몽_승인정면_v04.png','승인 외형 참고'),
('OS','성체 외지몽 측면 폭','외지몽_승인측면_머리폭_v04.png','승인 측면 참고'),
('OP','성체 외지몽 패드·착좌','외지몽_승인젤리패드_동작_v04.png','승인 동작 참고'),
('SC','우주선 닫힘','외지몽_우주선_6방향_v00/03_45_RIGHT.png','비행/착륙 외형'),
('SO','우주선 열림 6방향','외지몽_우주선_열림닫힘_v01/외지몽_우주선_열림_6방향.png','캐노피·전면 계단 구조'),
('P','얼라별','얼라별_디자인자료_v00/reference/01_front_master_v15.png','우주 배경'),
('L','브랜드 로고','01_확정_로고/대구_얼라들_로고_승인원본.png','정확한 로고 후합성'),
('KD','대키미 키링인형','대키미/레퍼런스/대키미_키링인형_승인정면_원본보존_v01.png','상품 원본'),
('KO','외지몽 키링인형','외지몽/레퍼런스/외지몽_키링인형_승인정면_원본보존_v01.png','상품 원본'),
('SD','대키미 시팅인형','시팅인형_디자인자세_v01/reference/01_FRONT.png','기존 승인 앉은 외형'),
('OB','외지몽 아기 정면','외지몽 아가버전 최종_v13/레퍼런스_이미지/01_정면.png','시팅인형 콘셉트의 외형 기준'),
('OBS','외지몽 아기 앉은 보조','외지몽 아가버전 최종_v13/앉은자세_보조이미지/07_앉은자세_정면.png','착좌 참고 · 상품 확정본 아님'),
]
assets={}
refdir=OUT/'references';refdir.mkdir(parents=True,exist_ok=True)
for code,label,suffix,status in asset_specs:
    p=find(suffix); name=code+'_'+p.name
    shutil.copy2(p,refdir/name)
    assets[code]={'label':label,'source':str(p),'file':'references/'+name,'status':status,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

# id, seconds, carousel, name, camera, framing, expression, opening, timed action, ending,
# transition, sound, overlays, refs, English start-frame brief, English motion instruction, QA
rows=[
(1,4,1,'얼라별에서 지구로','초광각 EWS / 24mm / 아주 느린 전진',
'우주선은 오른쪽 아래 1/3, 얼라별은 왼쪽 뒤, 지구는 진행 방향 앞. 빈 우주 여백 확보.',
'조종석 속 외지몽은 원본의 작은 미소. 멀리 있어 얼굴 디테일을 과장하지 않는다.',
'닫힌 우주선이 얼라별과 지구 사이에 떠 있다.',
'0–1초 우주 배경 제시 → 1–3초 우주선이 화면 오른쪽으로 천천히 이동 → 3–4초 지구 쪽으로 향함.',
'닫힌 우주선이 화면 오른쪽 1/3에 남는다.',
'조종석 안 외지몽으로 하드컷. 진행 방향을 뒤집지 않음.',
'낮은 우주선 엔진음, 가벼운 탐험 음악 시작.',
'캐러셀만 상단: 우주에서 받은 신호, 대구에서 만난 친구 / 영상은 타이틀 없이 시작.',
['SC','P','O'],
'A very wide cute stylized 3D outer-space shot. The approved green-and-cream closed spaceship floats between a distant coral pink planet with mint ring and a blue Earth ahead. The approved adult green alien dog is a small pilot visible through the closed canopy. Ship lower right, planet upper left. Clean negative space, no typography.',
'The closed spaceship glides slowly toward the Earth and screen right. Keep its silhouette rigid and antenna count unchanged. Very slow camera push-in. No dramatic banking or canopy movement.',
'우주선 귀형 포드·더듬이·크림 하부 유지. 지구와 얼라별은 서로 다른 행성.'),
(2,3,1,'조종석의 호기심','얼굴 CU / 70mm / 고정',
'외지몽 얼굴은 왼쪽 2/3, 오른쪽에 원본 형태 조종간 일부. 얼굴과 안테나가 프레임에 잘리지 않음.',
'눈을 억지로 키우지 않고 원본 눈에 시선만 이동. 입은 작은 미소.',
'외지몽이 정면 창밖을 보고 있다.',
'0–1초 정면 응시 → 1–2초 계기판 방향으로 눈동자/고개를 조금 돌림 → 2–3초 잠깐 멈춤.',
'외지몽 시선이 오른쪽 아래 계기판에 머문다.',
'짧은 수신음을 다음 쇼트 시작까지 이어 신호 수신으로 연결.',
'엔진음 아래 작은 삑 소리. 음성 없음.',
'영상에서 작은 ? 하나를 외지몽 오른쪽 위 빈 공간에 후합성. 캐러셀은 선택 사항.',
['O','OS','SC'],
'Close-up inside the original one-seat green-and-cream spaceship cockpit. Cute adult Oejimong with exact approved front/three-quarter face, drooping ears, two antennae, original eye motifs. Looking forward, control panel lower right. Stylized 3D matching shot 01. No text, no added human anatomy.',
'Oejimong subtly turns its gaze and head toward the lower-right instrument panel, then pauses with mild curiosity. Keep mouth a small original smile. Do not enlarge the eyes or deform the muzzle. Static camera.',
'외지몽 측면 머리 폭, 눈 하이라이트 3종, 주둥이 경계 확인. 비행복 추가 금지.'),
(3,4,2,'대구 상공 안테나 수신','외부 와이드 WS / 35mm / 고정',
'대한민국 지형 위, 대구 상공의 우주선을 전경 오른쪽 위에 배치. 아래 도시에서 우주선 안테나까지 이어지는 신호가 핵심.',
'우주선 안 외지몽은 작게만 보임. 별도 얼굴 클로즈업 없음.',
'닫힌 우주선이 대구 바로 위 높은 상공에 정지해 있다.',
'0–1초 아래 대한민국 지형 제시 → 1–3초 대구 쪽 지표에서 신호가 올라옴 → 3–4초 우주선 안테나 끝이 한 번 반짝임.',
'안테나 발광이 사라지고 우주선이 아래 방향으로 아주 조금 기울기 시작.',
'구름이 화면을 지나가는 순간 4번 실사 배경으로 매치컷.',
'신호음 2회, 마지막에 맑은 수신 완료음.',
'지명·대구 글자·위치핀·지도 인셋·홀로그램 없음. 신호 파형은 지표→우주선으로만.',
['SC','O'],
'Single full-frame cute cinematic 3D view of South Korea from high above, with the approved closed spaceship directly over the Daegu area in southeastern inland Korea. The terrestrial source is beneath the ship, no map insert, no inset screen, no labels or location pins. Frame the external ball-tipped ship antennas clearly. No second globe.',
'Two soft radio-wave pulses rise from the city below toward the spaceship. On reception, the external antenna tips blink once. The ship remains nearly still, then tips very slightly toward descent. Keep the view one continuous frame, no diagram overlays.',
'신호 방향은 아래→위. 대한민국 지형이 일본/한반도 뒤집힘으로 바뀌지 않음.'),
(4,4,3,'착륙','로우 와이드 / 28mm / 고정',
'실제 두류공원 잔디와 나무, 우주선 전신. 사람 없는 빈 공간, 야외음악당은 멀리 일부만.',
'조종석 안 외지몽은 작은 실루엣.',
'닫힌 우주선이 지면 약간 위에 떠 있고 접지 그림자가 보인다.',
'0–2초 천천히 내려옴 → 2–3초 착륙 다리가 지면에 닿음 → 3–4초 엔진빛이 약해짐.',
'닫힌 상태로 안정적으로 착륙 완료.',
'같은 공간의 전면 3/4 구도로 하드컷.',
'엔진 감속음, 부드러운 착지음, 축제 먼 앰비언스가 들어옴.',
'글씨 없음. 실사 전환은 구름/밝은 하늘로 연결, 사람과 공원만 실사.',
['SC'],
'Photoreal empty grass clearing at Duryu Park, natural trees and distant low outdoor music hall canopy. The approved cute smooth CG green-and-cream CLOSED spaceship hovers just above the grass with a soft physically matched contact shadow. No people in landing zone. Low wide camera, natural afternoon light.',
'The closed CG spacecraft lowers gently onto its existing landing feet. The feet contact the grass, the body settles a tiny amount and engine light dims. No dust explosion, no extra landing legs, no door opening yet. Locked camera.',
'4번부터 사람·지면·물건은 실사, 우주선만 CG. 관객 가까이 착륙 금지.'),
(5,4,3,'캐노피와 전면 계단','전면 3/4 MS / 40mm / 고정',
'열리는 캐노피, 한 개의 크림색 좌석, 중앙 전면 계단이 모두 보이는 각도. 우주선 잘림 없음.',
'외지몽은 좌석에 앉아 대기. 하차 동작을 섞지 않음.',
'우주선은 닫힌 상태. 원본 전면 중앙 구조가 보인다.',
'0–2초 투명 캐노피가 위쪽으로 열림 → 2–4초 전면 계단이 내려와 지면에 닿음. 생성 불안정 시 두 동작을 별도 클립으로 분리 편집.',
'첨부한 열린 6방향과 같은 완전 개방 상태.',
'계단의 마지막 발판을 다음 하차 컷의 기준으로 맞춤.',
'작은 캐노피 모터음, 계단 잠금 소리.',
'글씨 없음. 열림 구조를 설명하는 화살표를 영상에 넣지 않음.',
['SO','SC','O'],
'Front three-quarter medium-wide view of the approved spaceship CLOSED, parked on the same real grass clearing. Exact original green/cream body and single cream cockpit seat. Frame the canopy hinges and central front opening. A cute CG Oejimong remains seated inside. No side doors, no invented hatch.',
'Open the transparent canopy upward using the mechanism in the supplied OPEN six-view reference, then lower the narrow central front stair-ladder with green rails and cream steps onto the grass. Preserve the body shell. If one model cannot preserve both mechanisms, generate canopy opening and stairs lowering as separate clips and join in editing.',
'프런트 계단을 옆문으로 대체 금지. 캐노피가 잘리거나 사람 차 문처럼 열리면 재생성.'),
(6,3,3,'외지몽 하차','발판 높이 로우 풀샷 / 50mm / 고정',
'전면 계단과 외지몽 전신. 카메라가 낮아 작고 귀여운 체형이 보이되 원본 비율 유지.',
'안심한 작은 미소. 첫걸음을 신중하게.',
'우주선 캐노피는 완전히 열렸고 계단은 지면에 닿아 있다. 외지몽은 마지막 발판에 서 있다.',
'0–1.5초 한 발을 잔디에 내려놓음 → 1.5–3초 나머지 발도 내려 한 번 주변을 봄.',
'외지몽이 지면에 두 발로 서고 몸은 축제 쪽으로 향함.',
'시선 연결로 외지몽 뒤쪽 원거리 무대 컷.',
'발판 발소리 한 번, 잔디 밟는 소리, 멀리 음악.',
'글씨 없음.',
['O','OS','SO'],
'Low full-body shot of approved adult CG Oejimong on the LAST STEP of the open spaceship front stair-ladder. Canopy fully raised above cockpit, stairs touch real grass. Exact short rounded limbs and cream belly/tail-tip gradient. Natural contact shadows. No side exit.',
'Oejimong steps carefully from the last front stair onto the grass, places both feet down and briefly looks toward the festival. Keep arms relaxed and body proportions unchanged. One small step only. Canopy and stairs stay fixed.',
'발/계단 관통, 다리 추가, 큰 인체 손가락 금지.'),
(7,5,4,'멀리서 보는 사투리 토론','뒷모습 롱샷 LS / 35mm / 느린 전진',
'외지몽 뒷모습은 화면 아래 15–20%. 넓은 잔디가 가운데, 12번 엔딩과 같은 두류 야외음악당 본무대가 멀리 상단.',
'얼굴은 안 보임. 귀·고개가 무대로 향함.',
'외지몽이 관객 뒤 잔디광장 가장자리에서 본무대를 바라본다.',
'0–2초 공간과 본무대 제시 → 2–4초 무대의 사람 참가자가 발언 제스처 → 4–5초 외지몽이 고개를 살짝 기울임.',
'먼 무대의 토론은 계속, 외지몽은 관람 중.',
'옆쪽 놀이 부스의 고리 소리를 먼저 들려주고 발견 컷으로 이동.',
'먼 관객 박수·무대 앰비언스. 알아들을 수 있는 발언·음성 대사 없음.',
'본무대 현수막 대사투 페스티벌 후합성. 작은 별도 근접 토론무대 생성 금지.',
['O','OS'],
'Photoreal long shot across the broad lawn of Daegu Duryu Kolon Outdoor Music Hall. The SAME actual main stage with its broad shallow slanted canopy is far away, not a separate small debate stage. Tiny real human contestants at two lecterns and a moderator, audience seen mostly from behind. Cute CG Oejimong back occupies only lower 15–20 percent foreground. Afternoon.',
'Very slow camera push toward the distant main stage while the tiny human speakers make restrained debate gestures and the audience gives a little applause. Oejimong tilts its head slightly. Keep stage distant and human faces unfeatured. No readable speech or narration.',
'무대가 대화 근접샷으로 바뀌지 않음. 군중 얼굴 뭉개짐은 원거리/후면으로 회피.'),
(8,4,5,'놀이 중인 대키미 발견','외지몽 어깨 너머 OTS / 50mm / 짧은 팬',
'외지몽 귀와 어깨 일부만 왼쪽 전경, 3–4m 앞 대키미와 고리 던지기 부스가 중심.',
'대키미는 작은 즐거운 미소. 눈·코 위치를 바꾸지 않음.',
'대키미가 고리를 들고 부스 앞에 서 있다. 외지몽이 그쪽을 바라보기 시작.',
'0–1초 고리 소리에 짧게 팬 → 1–3초 대키미가 고리를 한 번 던짐 → 3–4초 외지몽과 시선이 마주침.',
'대키미가 외지몽을 보고 몸을 조금 돌린다.',
'대키미 인사 미디엄으로 시선 매치.',
'고리 부딪히는 소리, 가벼운 놀이터 음악.',
'말풍선 아직 없음.',
['D','O','OS'],
'Over-the-shoulder view past the edge of CG Oejimong toward approved adult CG Daekimi at a real festival ring-toss stand several metres away. Daekimi holds one ring, pink ribbon tied only to curled tail. Real vendor mostly back/side view, softly defocused natural visitors. Keep original adult CG faces cute, not biological.',
'The camera makes one short gentle pan toward Daekimi. Daekimi tosses one ring, then notices Oejimong and turns its gaze toward it. One ring only, no morphing props. Keep cat facial geometry stable.',
'대키미 꼬리 리본 위치, 링/손 분리 확인.'),
(9,3,6,'대키미의 인사','대키미 MS / 65mm / 고정',
'대키미 가슴 위와 두 더듬이 전체. 화면 오른쪽에 외지몽을 향한 시선 여백.',
'원본 미소 유지, 눈은 열려 있음. 손은 한 번만 작게 흔듦.',
'대키미가 외지몽 쪽을 보고 서 있다.',
'0–1초 시선 고정 → 1–2초 한 번 손 흔들기 → 2–3초 대답을 기다림.',
'손을 내리기 시작하고 외지몽을 계속 바라봄.',
'같은 시선 축의 외지몽 리액션 컷.',
'작은 반짝 효과음. 목소리 없음.',
'대키미 말풍선 …! 상단 오른쪽, 귀와 더듬이·얼굴을 가리지 않음.',
['D'],
'Medium shot of approved adult blue alien cat Daekimi facing screen right at a real festival. Both antenna balls visible, exact black eyes and original star glints, tiny original smile, no additional blush. One rounded paw ready at chest height. Space above right for an overlay. No baked text or bubbles.',
'Daekimi gives one small welcoming wave and then waits for a response. Keep mouth in a gentle small smile with no speaking motion. No face stretching, no exaggerated eyebrow changes. Static camera.',
'과한 입 벌림·치아 추가·별이 눈 밖으로 이동하는 오류 금지.'),
(10,3,6,'외지몽의 물음표','외지몽 CU / 75mm / 고정',
'외지몽 얼굴과 더듬이, 짧은 앞팔 일부. 대키미 반대 방향을 봐서 시선 축 유지.',
'입은 닫히거나 원본 작은 미소. 갸웃 5–10도.',
'외지몽이 대키미 쪽을 보고 있다.',
'0–1초 상대를 바라봄 → 1–2초 작게 갸웃 → 2–3초 잠깐 정지.',
'작은 ?를 머리 옆에 띄운 상태로 시선 유지.',
'번역기를 꺼내는 손 인서트로 하드컷.',
'짧은 호기심 음 하나, 축제 소리는 낮게 유지.',
'외지몽 말풍선 ? 상단 왼쪽. 피부 위나 더듬이 위에 겹치지 않음.',
['O','OS'],
'Close-up approved adult green alien dog Oejimong looking screen left toward Daekimi. Exact approved head depth, cream muzzle, star glints, drooping ears and two antennae. Cute smooth CG composited against defocused photoreal festival. Clear negative space upper left. No generated text.',
'Oejimong gently tilts its head five to ten degrees, pauses and blinks once naturally. Keep eye motif anchored to eye surface and muzzle shape unchanged. No huge mouth opening or inflated cheeks. Static camera.',
'무표정이 아닌 작은 호기심. 별 무늬 재배열·두 얼굴 혼합 금지.'),
(11,3,7,'번역기를 들다','소품 인서트 ECU / 85mm / 고정',
'크림/민트 번역기와 외지몽 손, 대키미 파란 몸 일부가 뒤에 흐리게. 화면의 여백 확보.',
'얼굴은 크게 나오지 않음.',
'외지몽이 번역기를 가슴 높이로 들기 시작한다.',
'0–1초 손이 번역기를 들어 올림 → 1–2초 파형 점등 → 2–3초 엉킨 파형이 정돈됨.',
'켜진 번역기가 두 친구 사이 가슴 높이에 안정적으로 위치.',
'정돈된 파형의 빛을 다음 얼굴 반응 컷으로 연결.',
'작은 기동음, 삑-딩 신호음.',
'화면 파형은 편집으로 합성. 실제 문장·언어명·번역문은 없음.',
['O','OP'],
'Extreme close-up of a small provisional cream-and-mint handheld translator held gently by Oejimong rounded paw at chest height. Photoreal lens and background, cute smooth CG hand, hint of blue Daekimi behind. Blank dark device screen reserved for later wave overlay. No human fingers, no text.',
'The paw lifts the translator slightly and holds it steady. A soft device light turns on. Keep screen blank for a waveform to be added in editing. Avoid complex finger presses. Static camera.',
'번역기는 임시 콘셉트이며 컷마다 같은 모양·손잡이·화면 비율 유지.'),
(12,3,8,'통했다는 표정','동등 높이 투샷 / 60mm / 고정',
'대키미 왼쪽, 외지몽 오른쪽. 같은 바닥·카메라 거리. 외지몽이 전체 키 약간 큼.',
'서로 작은 미소, 눈은 열린 상태. 입 모양보다 눈빛과 고개 끄덕임으로 이해 표현.',
'번역기가 두 친구 사이에 있고 둘은 상대를 바라본다.',
'0–1초 상대를 봄 → 1–2초 외지몽이 작게 끄덕임 → 2–3초 대키미도 끄덕임.',
'같은 ! 말풍선이 두 캐릭터 위에 나타남.',
'손을 올리는 움직임을 다음 하이파이브에 연결.',
'이해를 알리는 밝은 두 음, 음악이 따뜻해짐.',
'같은 모양의 ! 말풍선 두 개. 입에서 글씨가 쏟아지는 연출 없음.',
['D','O','OS'],
'Balanced two-shot of adult CG Daekimi on left and adult CG Oejimong on right at same distance on real grass. Oejimong 105cm and Daekimi 103cm to antenna top, virtually same height. Both have exact original faces and small relaxed smiles. Translator between them at chest height. No baked overlays.',
'Oejimong nods once with a relieved tiny smile, then Daekimi nods back. Preserve body and eye geometry. No spoken mouth motion. Both begin to raise one paw toward each other at the end.',
'키 차이, 눈·주둥이·안테나 개수 확인. 얼굴을 더 귀엽게 하려고 비율 재설계 금지.'),
(13,3,8,'친구의 하이파이브','손 중심 타이트 투샷 / 70mm / 고정',
'두 친구 얼굴은 프레임 양쪽, 중앙에 둥근 손. 외지몽 다른 손에 번역기를 안정적으로.',
'원본 눈 윤곽을 유지한 작은 웃음. 눈을 닫는다면 눈꺼풀로만.',
'두 손이 떨어진 채 서로를 향해 올라가 있다.',
'0–1초 손 접근 → 1–1.5초 가볍게 한 번 접촉 → 1.5–3초 손을 조금 내리며 웃음.',
'접촉이 끝난 상태. 서로 한 발짝 가까워짐.',
'발소리 선행 후 걷기 와이드.',
'팍 한 번, 작은 웃음 대신 음악과 귀여운 효과음.',
'! 말풍선은 초반에만 잠깐 남겼다가 사라짐.',
['D','O','OP'],
'Tight two-shot of Daekimi and Oejimong with their raised rounded paws separated just before a high-five at centre. Original cute CG faces at left/right, photoreal festival soft behind. Translator held in green dog other paw. Keep correct number of limbs and authentic pads only on visible palm.',
'Their raised paws meet once softly, pause briefly and lower a little. Preserve original rounded paw anatomy and no added fingers. Gentle smiles, no rubbery face deformation. Static camera.',
'팔 합체·손가락 추가·패드가 손등으로 이동 금지.'),
(14,4,9,'먹거리 길로','옆쪽 풀샷 / 35mm / 짧은 트래킹',
'두 친구 전신, 길 양쪽 부스. 사람은 뒷모습·옆모습 위주. 실제 성인 대비 약1m 크기.',
'편안한 작은 미소. 대키미가 앞장서되 두 친구 동등한 관계.',
'대키미가 왼쪽, 외지몽 오른쪽에서 같은 방향으로 걷기 시작.',
'0–3초 카메라와 나란히 2–3걸음 이동 → 3–4초 판매자 부스 앞에서 멈춤.',
'두 친구가 같은 부스를 바라보며 정지.',
'이동 방향 유지한 채 주문 OTS로 전환.',
'실제 발소리, 조리 소리, 그릇 부딪힘.',
'부스 메뉴명 납작만두·야끼우동·7구 먹거리는 후편집. 지자체/업소 참여 확정 표시 없음.',
['D','O','OS'],
'Photoreal food-stall lane within the same Duryu festival. Real Korean visitors mainly seen from rear/side, realistic counters and cookware. Cute original CG blue cat and green dog walk side by side full-body, about one metre tall relative to adults. Vendor counter ahead. Blank sign areas for menu overlays.',
'Short gentle lateral tracking shot matching the two friends as they take two to three small steps and stop at one food counter. Natural short-limbed walking, no running or dancing. Keep real people softly backgrounded.',
'도시 맛집 외부로 장소 전환 금지. 먹거리 부스와 같은 축제 공간 유지.'),
(15,4,10,'아주머니에게 주문','판매자 옆 OTS / 50mm / 고정',
'중년 여성 판매자는 오른쪽 3/4 옆모습, 왼쪽 아래 두 친구. 얼굴은 자연스러운 중거리, 혼잡한 다수 얼굴 없음.',
'외지몽은 손가락 대신 둥근 손으로 메뉴를 가리킴. 판매자는 작은 자연스러운 미소.',
'판매자는 카운터 뒤, 친구들은 앞. 메뉴판은 판매자 옆.',
'0–1초 외지몽이 메뉴 쪽 손짓 → 1–2.5초 대키미가 접시/수량을 몸짓으로 보탬 → 2.5–4초 판매자가 고개를 끄덕임.',
'판매자가 준비된 음식을 집으려 손을 내림.',
'카운터 높이의 음식 전달 인서트.',
'조리 지글거림, 종이용기 소리. 주문 음성 없음.',
'외지몽 작은 … 말풍선 → 판매자 작은 ! 또는 끄덕임. 실제 주문 문장 없음.',
['D','O'],
'Over-the-shoulder medium shot beside ONE realistic middle-aged Korean woman food vendor at a real festival counter. Natural single face in three-quarter profile, no exaggerated smile. Original CG mascots below normal adult eye level, Oejimong ready to gesture toward blank menu board. Authentic flat fried dumplings on counter.',
'Oejimong gestures toward the menu with one rounded paw. Daekimi makes a small accompanying gesture. The vendor nods once and reaches toward a prepared tray. No dialogue, no lip-sync. Keep human face stable and anatomically natural.',
'판매자 얼굴/손 변형 검사. 중년 여성으로 명확하되 희화화 금지.'),
(16,3,10,'따뜻한 납작만두 받기','음식·손 인서트 / 85mm / 고정',
'갈색 종이트레이와 실제 납작만두를 중앙, 판매자 손과 캐릭터 손만. 얼굴 없음.',
'얼굴 없음.',
'판매자가 종이트레이를 카운터에 내려놓기 직전.',
'0–1.5초 트레이를 내려놓음 → 1.5–3초 외지몽이 양손으로 트레이 가장자리를 받음. 동시에 손이 엉키지 않도록 순차.',
'외지몽이 안정적으로 트레이를 들고 있다.',
'트레이 위치를 다음 시식샷 아래 중앙에 맞춤.',
'종이용기 사각거림, 접시에 닿는 작은 소리.',
'글씨 없음. 영수증·가격·업소 상호를 지어내지 않음.',
['O','OP'],
'Photoreal insert of a shallow kraft paper tray holding authentic Korean napjak-mandu: very thin flat crescent pan-fried dumplings with lightly browned surfaces, not puffy gyoza. One realistic woman hand places tray on counter; CG green rounded paws wait below. No faces or text.',
'The vendor sets the prepared tray on the counter and releases it. Only then Oejimong lifts the tray carefully with both paws. Keep hands separated in time; no direct complex hand-to-hand exchange. Food remains stable.',
'납작만두 형태/실제 질감, 손 관통·트레이 부유 확인.'),
(17,4,11,'한 입 먹고 눈빛 교환','얼굴과 트레이 투샷 / 65mm / 고정',
'두 친구 가슴 위와 음식. 원본 얼굴이 중심, 과한 입 벌림을 피하고 먹기 전/후 중심.',
'작은 기대→작은 미소. 볼을 부풀리거나 주둥이를 늘리지 않음.',
'두 친구가 부스 옆에 멈춰 서서 작은 만두 조각을 입 근처에 들고 있다.',
'0–1초 음식 접근 → 1–2초 짧은 한 입 동작 → 2–4초 서로 보고 작게 끄덕임. 필요하면 접촉 순간 인서트로 가려 편집.',
'음식은 얼굴에서 떨어지고 둘은 만족한 미소.',
'다음 부스로 이동하는 짧은 와이드.',
'바삭 소리 한 번과 밝은 음악. 과장된 씹는 소리 없음.',
'같은 작은 별 그림 말풍선 선택. 맛있다 등 음성 없음.',
['D','O','OS'],
'Cute CG original mascots at a real food-stall side counter, medium close two-shot. Each holds a small bite-sized flat dumpling piece just below its mouth, tray visible lower frame. Exact muzzle and tiny mouth shapes, natural warm light, real food texture. No swollen cheeks, no added teeth.',
'Each makes one very small tasting motion and lowers the food. Then they exchange a happy glance and one tiny nod. Keep mouths close to original small smile; avoid showing deep chewing. If contact deforms face, cut on the food insert and use the satisfied reaction instead.',
'음식/입 관통·치아 추가·혀와 음식 융합 금지. 얼굴 보존이 시식 액션보다 우선.'),
(18,3,11,'다음 부스로','뒤쪽 짧은 와이드 / 35mm / 고정',
'두 친구 뒷모습, 옆에 야끼우동 철판과 7구 먹거리 부스. 이동 동선이 굿즈샵으로 이어짐.',
'얼굴은 옆으로 조금만 보임.',
'두 친구가 트레이를 들고 다음 부스 쪽으로 향한다.',
'0–2초 두 걸음 이동 → 2–3초 대키미가 다음 부스를 가볍게 손짓. 철판 조리는 배경에서만.',
'프레임 진행 방향 앞에 대구 얼라들 굿즈샵이 보이기 시작.',
'굿즈샵 와이드로 하드컷. 음식에서 상품으로 장소 연속 유지.',
'철판 지글거림, 발소리, 음악 이어짐.',
'야끼우동/7구 먹거리 부스 표시는 후합성. 모든 후보를 실명 출점으로 단정하지 않음.',
['D','O','OS'],
'Rear wide shot of both cute CG mascots moving along the SAME real festival food lane with a paper tray. Authentic stir-fried yaki-udon being cooked at a stall to one side, another district-food stall beyond. The merchandise booth can be glimpsed further along the path. Realistic people mostly rear view, no prominent extra faces.',
'The friends take two short steps toward the next stall. Daekimi makes one small open-paw gesture toward it. Background vendor gently stirs noodles. Fixed camera, no dramatic orbit or location change.',
'보유 트레이 갑자기 사라지지 않게. 다음 굿즈 장면 전 쓰레기/음식은 화면밖 정리된 시간 생략.'),
(19,4,12,'세 상품이 보이는 굿즈샵','정면 전체 와이드 / 35mm / 느린 전진',
'중앙 뒤 티셔츠 2종, 왼쪽 앞 키링 랙, 오른쪽 앞 시팅인형 2종. 모두 가림 없이 읽힘. 에코백·머그·스티커는 가장자리 보조.',
'두 친구는 전경 아래에 작게, 상품을 가리지 않는 뒷모습.',
'빈손의 두 친구가 굿즈 부스 바깥에서 상품을 바라본다.',
'0–3초 짧게 부스 쪽 전진 → 3–4초 정지하여 주요 상품 세 종류를 함께 보여줌.',
'키링·티셔츠·시팅인형이 같은 화면에 남음.',
'키링 디테일로 하드컷.',
'진열대 작은 금속 소리, 축제 앰비언스, 음악.',
'상단 간판 대구 얼라들 원본 로고 후합성. 상품별 글씨는 개별 디테일 컷에서 확인.',
['D','O','KD','KO','SD','OB','OBS','L'],
'Photoreal real-fabric festival merchandise booth with three equally visible HERO categories: paired blue/green character plush keyrings on a front-left rack; two white cotton T-shirts hung at centre rear; paired seated blue/green plush dolls at front right. Tote bags, mugs and stickers along edges, not obstructing hero goods. Cute adult CG mascots seen small from rear at bottom, not blocking products. Real human seller side/back view. Reserve blank logo/sign and T-shirt print areas for exact source artwork compositing.',
'Very slow push-in toward the booth, then hold. The two CG friends stop outside and look at the display, without crossing in front of the hero products. Do not animate products or text. Keep arrangement fixed.',
'주요 3종 중 누락 금지. 상품 캐릭터를 성체CG 그대로 축소하거나 다른 IP로 대체 금지.'),
(20,3,13,'키링인형 두 친구','상품 CU / 85mm / 고정',
'대키미·외지몽 키링 둘을 같은 초점면에. 고리·얼굴·더듬이·꼬리까지 보이며 앞뒤 상품 겹침 최소.',
'상품 표정은 각 원본 그대로. 생물처럼 움직이지 않음.',
'두 키링이 랙에 정지한 상태.',
'0–3초 고정 홀드 또는 극히 약한 천의 흔들림. 캐릭터 얼굴 변형 없음.',
'두 상품 정면이 온전히 보임.',
'시팅인형 디테일로 매치컷.',
'고리 금속 소리 아주 작게. 상품이 말하거나 움직이는 소리 없음.',
'캐러셀 상품 설명만 대키미 & 외지몽 키링인형. 가격·출시 일정 없음.',
['KD','KO'],
'Photoreal product close-up of the TWO approved baby-version plush keyrings from supplied product references. Preserve exact individual faces, asymmetric ear/antenna details, ribbon attachment and original fabrics. Silver ball chains visible. Both faces on same focal plane, soft real booth light. These are inanimate merchandise, not the adult CG protagonists. No redesigned prints or text.',
'Hold a nearly static close-up of both plush keyrings. At most a tiny natural rack movement. Do not animate their eyes, mouths, bodies or chains independently. No camera orbit that reveals invented back details.',
'키링 원본과 얼굴/비율 대조. 포커스 흐림으로 주요 상품 얼굴을 숨기지 않음.'),
(21,4,14,'시팅인형 두 친구','상품 아이레벨 CU / 70mm / 고정',
'대키미 시팅인형 왼쪽·외지몽 시팅인형 오른쪽. 두 상품 얼굴과 앉은 발이 모두 보임. 상품 사이 여백.',
'대키미는 승인된 무표정 원본. 외지몽은 승인 아기 얼굴 기준, 임의 과장 미소 금지.',
'두 봉제인형이 선반에 안정적으로 앉아 있다.',
'0–4초 고정 홀드, 따뜻한 광원만 일정. 상품을 일으키거나 주인공으로 변신시키지 않음.',
'두 상품의 앉은 실루엣이 완전히 보임.',
'티셔츠 흰 원단 디테일로 하드컷.',
'부드러운 음악, 배경 앰비언스.',
'외지몽 시팅인형은 사용자 승인된 아기 디자인 기반 상품 콘셉트. 보드 제작 메모에만 표시, 영상 광고 문구로 넣지 않음.',
['SD','OB','OBS'],
'Photoreal close-up of two seated plush dolls on a real shelf. LEFT Daekimi uses the supplied approved seated plush reference exactly, including neutral embroidered mouth, folded ear, bent antenna and pink TAIL ribbon. RIGHT Oejimong is a seated plush CONCEPT based on its approved baby front and seated auxiliary reference, retaining its original face, floppy ears and baby proportions with soft short pile textile. Both sit naturally with legs forward. No adult CG anatomy copied into plush. No text.',
'Hold the paired seated plush dolls completely still, framed at product eye level. No face animation, no posture changes and no camera orbit. Show both faces and seated silhouettes clearly.',
'외지몽 시팅은 콘셉트 승인 범위. 상품3D 확정·양산 승인으로 표기하지 않음.'),
(22,4,15,'뭘보노? 티셔츠','정면 상품 MS / 65mm / 고정',
'실제 흰 면티 앞면이 카메라와 평행. 주름은 적게. 가슴 중앙 대키미 얼굴 크게, 바로 아래 뭘보노?.',
'프린트 얼굴은 성체 대키미 원본의 표정·귀·눈·더듬이 유지.',
'흰 면티가 옷걸이에 정면으로 걸려 있다. 인쇄 영역은 빈 상태로 먼저 생성.',
'0–4초 정면 홀드. 인쇄 아트는 후합성으로 원단 평면에 고정.',
'얼굴과 문구가 가림 없이 읽힘.',
'같은 높이의 외지몽 티셔츠로 하드컷.',
'천 스치는 소리 아주 작게, 음악.',
'정확 문구 뭘보노? / 대키미 얼굴 크게 중앙. 별도 문자·오탈자·자동 생성 캐릭터 금지.',
['D'],
'Photoreal front view of a plain white cotton T-shirt on a hanger inside the same booth. Entire front print area visible, camera square to fabric, gentle natural folds outside print zone. Leave the front chest print area BLANK for compositing the exact approved Daekimi face and Korean text later. No generated illustration or letters.',
'Hold the T-shirt nearly still, minimal fabric sway. No hand covers the chest. Camera fixed. The approved face artwork and the exact text will be composited afterwards, so do not generate changing prints.',
'글씨는 뭘보노? 정확히. 얼굴 프린트를 이미지 모델이 다시 그리게 하지 않음.'),
(23,4,15,'외지인입니다. 티셔츠','정면 상품 MS / 65mm / 고정',
'흰 면티 앞면 정면. 착용자 왼쪽 가슴=화면 오른쪽에 작은 외지몽 얼굴. 문장은 앞면 정중앙 크게.',
'작은 프린트도 외지몽 성체 정면 원본 사용. 눈·주둥이 색영역 생략으로 다른 얼굴 되지 않음.',
'옷걸이의 흰 면티, 작은 얼굴 자리와 중앙 문구 자리는 비어 있다.',
'0–4초 정면 홀드. 얼굴과 문구는 원본 아트/활자로 후합성.',
'작은 얼굴과 큰 중앙 문구가 동시에 보임.',
'굿즈샵에서 본무대로 시선/음악 이어 엔딩.',
'천 소리와 음악 여운.',
'외지인입니다. 마침표 포함. 작은 얼굴만 착용자 왼쪽 가슴, 문구를 그 옆 작게 붙이지 않음.',
['O'],
'Photoreal front view of a second plain white cotton T-shirt on a hanger. Camera square to the shirt, front unobstructed. Reserve a SMALL face-print zone on WEARER LEFT CHEST, which is VIEWER RIGHT, and a LARGE centred text zone across the front. Leave both zones blank for exact approved Oejimong face artwork and Korean text compositing. No generated face or letters.',
'Hold the second shirt nearly still with minimal fabric movement. Keep both print zones flat and unoccluded. Static camera. Exact face and text are post-production layers, never morphing generated imagery.',
'작은 얼굴 좌우 반전 주의. 중앙 문구 외지인입니다. 글자·마침표 확인.'),
(24,6,16,'다시 축제 속으로','후면 와이드 WS / 28mm / 느린 후퇴',
'두 친구 뒷모습 아래 중앙, 넓은 잔디와 7번과 같은 본무대가 멀리. 하늘/잔디에 엔딩 여백.',
'얼굴은 뒤돌아보지 않음. 몸짓과 같은 걸음 속도로 우정 표현.',
'두 친구가 나란히 잔디광장 앞에 서 있다.',
'0–3초 나란히 2–3걸음 → 3–4초 카메라가 조금 뒤로 빠짐 → 4–6초 화면 홀드와 엔딩 문구/로고.',
'두 친구·본무대·로고가 안정적으로 남음.',
'음악 잔향으로 끝. 검정화면 강제 전환 없음.',
'잔디 발소리, 먼 박수, 음악 여운. 대사 없음.',
'마지막 2초 표현이 달라도, 친구가 된다. / 그 아래 승인 로고. 현수막 대사투 페스티벌.',
['D','O','OS','L'],
'Photoreal rear wide view of the SAME Duryu lawn and distant main outdoor music hall stage as shot 07. Cute adult CG Daekimi on left and Oejimong on right walk together, almost same height with dog slightly taller. Cat pink bow only on curled tail; dog thick rounded tail with a small cream-gradient tip. Natural visitors mostly rear/side, open sky/grass negative space for final overlay. No baked text.',
'Both friends take two to three slow steps toward the distant stage as the camera eases back slightly, then hold the composition for the final two seconds. Do not turn faces toward camera or transform tails. Add ending sentence and approved logo in editing only.',
'본무대 동일성, 캐릭터 전체 크기, 꼬리·리본·실사 접지 확인.')
]

shots=[]; t=0
keys=['id','duration','carousel','title','camera','composition','expression','start','action','end','transition','sound','overlay','refs','start_brief_en','motion_en','qa']
for row in rows:
    d=dict(zip(keys,row));d['in']=t;t+=d['duration'];d['out']=t;d['code']='S'+str(d['id']).zfill(2)
    d['style']='귀여운 3D 우주' if d['id']<=3 else '실사 배경 + 귀여운 캐릭터 CG'
    shots.append(d)

slides=[
(1,[1,2],1,'우주에서 받은 신호,\n대구에서 만난 친구','표지. S01 우주 전경을 주 이미지로, 작은 조종석 디테일은 우측 아래 보조 1개. 제목 상단, 캐릭터와 우주선을 가리지 않는다.'),
(2,[3],3,'낯선 신호가\n우주선 안테나에 닿았다.','S03 외부 와이드. 지도/지명 없이 도시→안테나 신호를 중심으로.'),
(3,[4,5,6],6,'신호를 따라,\n처음 내려선 대구.','S06 하차를 주 이미지로. 아래 얇은 2개 보조 프레임에 착륙/완전 개방 모습. 기계 구조를 한 컷에서 동시에 변화시키지 않는다.'),
(4,[7],7,'이 말들은…\n어떤 뜻일까?','S07 먼 본무대와 잔디를 넓게. 관객 뒤 외지몽 작게. 물음표는 외지몽 근처.'),
(5,[8],8,'그러다,\n너를 발견했다.','S08 발견 구도. 대키미 놀이 동작과 외지몽 시선이 연결되도록.'),
(6,[9,10],9,'인사는 반가운데,\n말은 아직 물음표.','대키미 인사와 외지몽 갸웃 2분할. 대키미 …!, 외지몽 ? 기호 말풍선.'),
(7,[11],11,'잠깐!\n이거라면 통할지도.','S11 번역기 인서트 크게, 캐릭터 색이 주변에 조금 보여 누구 손인지 식별.'),
(8,[12,13],13,'말이 통하니,\n마음도 가까워졌다.','S13 하이파이브 메인. S12 이해한 표정은 작은 보조 가능. 같은 ! 기호.'),
(9,[14],14,'대구 구경,\n이번엔 둘이서.','S14 전신 이동샷. 실제 사람·부스가 보여 축제 안 동선임을 전달.'),
(10,[15,16],15,'메뉴를 고르고,\n따뜻한 한 접시를 받고.','상단 주문, 하단 음식 받기 2분할. 판매자 얼굴은 한 명만 자연스럽게.'),
(11,[17,18],17,'처음 먹는 대구의 맛도,\n같이라서 더 즐겁다.','S17 시식이 메인, S18 다음 부스로 이동 보조. 납작만두·야끼우동이 같은 음식으로 바뀌지 않게.'),
(12,[19],19,'이번엔,\n대구 얼라들 굿즈샵!','세 주요 상품군을 한눈에. 키링/티셔츠/시팅인형 동등한 가시성.'),
(13,[20],20,'가방에 달고,\n같이 다니는 두 친구.','키링 두 상품 정면 같은 초점면. 가격/예약/출시 일정 없음.'),
(14,[21],21,'나란히 앉은,\n작은 두 친구.','대키미·외지몽 시팅인형 둘 다 크게. 캐릭터 CG 주인공이 아닌 실제 봉제상품 질감.'),
(15,[22,23],22,'뭘보노?\n외지인입니다.','티셔츠 2종 앞면을 좌우 동일 크기로. 대키미 중앙 큰 얼굴+뭘보노? / 외지몽 착용자 왼쪽 작은 얼굴+앞면 중앙 큰 외지인입니다.'),
(16,[24],24,'표현이 달라도,\n친구가 된다.','S24 두 친구 뒷모습과 본무대. 승인 로고 하단 여백. 새 사건이나 별도 광고 CTA를 추가하지 않는다.')
]
carousel=[dict(zip(['page','shots','hero','copy','layout'],r)) for r in slides]

GLOBAL="""GLOBAL PRODUCTION LOCK
The two protagonists are cute stylized CG mascots, not realistic animals or biological creatures. Preserve the supplied adult character identity and original proportions in every shot. Oejimong height 105cm, Daekimi 103cm to antenna top at equal distance. Do not resculpt heads to increase cuteness. Use small eye-line changes, a tiny smile, natural eyelid blinks and restrained head tilts.
Oejimong: green drooping ears, two ball-tipped antennas, exact rounded triangular black eye shapes with one large white four-point star, one small grey star and one tiny diamond per open eye; cream muzzle, almost round cream belly patch, thick rounded green tail with small cream tip via long soft gradient. No blush, fur, extra fingers or elongated limbs. Visible paw/sole pads: one main plus three small. Never put pads on hand backs.
Daekimi: blue cat, original pink ear interiors, exact eye motifs, two antennas, pink ribbon on its curled TAIL ONLY. Adult character body and original face unchanged.
Shots 01–03 are cute clean stylized 3D space animation. Shots 04–24 use PHOTOREAL humans, park, stage, stalls, food, utensils, cotton and products, with cute CG mascots/spacecraft integrated by physically matched light, contact shadows, reflections and depth. Do not stylize humans into toys. Human faces stay natural, restrained and mostly side/back/background; isolate the single food vendor rather than crowded prominent faces.
Main stage is the same Duryu Kolon Outdoor Music Hall wide low slanted canopy throughout shots 07 and 24. Debate stays distant across the lawn, never a second close stage.
No spoken dialogue or narration, no lip-sync. Symbol-only speech bubbles are added in editing. Do not generate text, logos, shirt prints or bubbles into source images. Festival signs and exact typography are post-production layers.
Main characters never adopt merchandise baby proportions. Product keyrings/seated dolls follow their own source images and textile materials. Oejimong seated plush is an explicitly approved CONCEPT based on approved baby reference; not a finalized manufactured product.
Keep travel direction and 180-degree screen axis consistent within each encounter. Avoid complex object transfers, face-touching, food-mouth collisions and large facial distortions. One principal action per generated clip.
"""
NEGATIVE="""No extra or missing limbs, fingers, antennae or ears; no merged hands; no moving eye-star patterns; no protruding belly plate; no white tail root; no neck bow; no horror or uncanny human faces; no duplicated background people; no human lips/teeth added to mascots; no giant chewing mouth; no realistic fur on CG protagonists; no toys replacing humans; no map insets, location pins or Daegu text in shot03; no spaceship side door; no close-up replacement debate stage; no unapproved branded products or invented merchant participation; no generated Korean gibberish."""

for d in shots:
    selected=d['refs'][:5]
    ref_lines='\n'.join(f'{i+1}. {a}: {assets[a]["label"]} — {assets[a]["file"]}' for i,a in enumerate(selected))
    d['generation_refs']=selected
    d['start_prompt']=GLOBAL+'\nSHOT '+d['code']+' — START FRAME, vertical 9:16, no baked text.\nREFERENCE ROLES:\n'+ref_lines+'\n'+d['start_brief_en']+'\nNEGATIVE:\n'+NEGATIVE
    d['motion_prompt']='SHOT '+d['code']+f' | FINAL EDIT USE {d["duration"]} seconds; generate an available model-supported length and trim.\n'+d['motion_en']+'\nPreserve the supplied start-frame identities, lighting and layout. No dialogue, narration, lip-sync or generated typography. '+NEGATIVE

for c in carousel:
    shot=shots[c['hero']-1]
    c['prompt']='Create a portrait 4:5 text-free carousel base image, same story, characters, venue and event order as video '+','.join('S'+str(i).zfill(2) for i in c['shots'])+'.\n'+GLOBAL+'\nVISUAL PLAN:\n'+c['layout']+'\nHERO START-FRAME BRIEF:\n'+shot['start_brief_en']+'\nDo not render any caption, speech bubble, logo or clothing print. Those exact elements are separate post-production layers. Do not use the storyboard contact sheet as a final frame. For multi-panel layout generate each source image separately, then arrange in editing.\n'+NEGATIVE

plan={'version':'v04','video_seconds':t,'video_shots':shots,'carousel_pages':carousel,'assets':assets,'global_prompt':GLOBAL,'negative_prompt':NEGATIVE,
'seated_oejimong_status':'사용자 승인: 승인된 외지몽 아기 디자인을 기준으로 앉은 봉제인형 콘셉트 구성',
'source_note':'k-1026/Chiikawa 로컬 origin/main, 세부지침안/B파트v1/참고자료/맛집리스트_V1.md. 납작만두/야끼우동 및 7구 후보 기반, 실제 출점 확인 아님.',
'venue_source':'https://tour.daegu.go.kr/index.do?menu_id=00002942&menu_link=%2Ffront%2Ftour%2FtourMapsView.do%3FtourId%3DKOATTR_97'}
(OUT/'storyboard_v04.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))

common="""대구 얼라들 · 상세 제작 스토리보드 v04
우주에서 받은 신호, 대구에서 만난 친구

구성: 캐러셀 16장 / 영상 24쇼트 / 최종 편집 89초 / 음성 대사·내레이션 없음
사용자 승인 내용: 1–3번 만화 같은 귀여운 3D, 이후 실사 환경+귀여운 캐릭터 CG. 같은 이야기와 사건 순서.
파일의 '바로 제작' 범위: 컷별 입력/프롬프트/편집 지시 제공. 실제 최종 장면 이미지·동영상·티셔츠 프린트 완성 파일을 이미 생성한 것은 아님.

제작 순서
1. references 원본 확인. 성체CG와 아기버전 상품 원본을 용도별로 분리.
2. 아래 선행 마스터 6개를 먼저 고정. 전 장면을 한 번에 생성하지 않음.
3. 각 쇼트의 9:16 문구 없는 시작 이미지를 생성하고 얼굴/소품 검수.
4. 그 시작 이미지를 Higgsfield 이미지→영상의 시작 프레임으로 사용. 선택 모델의 입력/길이를 실제 실행 시 확인.
5. 동작 프롬프트는 같은 파일의 컷별 지시만 사용. 긴 공통 이미지 지시를 매번 과도하게 반복하지 않음.
6. 필요한 편집 길이보다 긴 지원 길이로 만들고 동작이 안정적인 구간을 트림. 특정 모델명·지원 길이·자동 연동을 가정하지 않음.
7. 말풍선·신호 파형·번역기 화면·무대 현수막·상품 간판·티셔츠 아트·엔딩 로고는 별도 합성.
8. 캐러셀은 같은 쇼트 원본에서 4:5 별도 리프레이밍. 세로 영상을 캡처·업스케일해 최종 정지 이미지로 쓰지 않음.

선행 마스터
M1 성체 페어: 정면/3/4 동등 거리, O105cm D103cm. 원본 눈/주둥이/리본/꼬리 확인.
M2 공간: 실제 두류 야외음악당 사진을 보고 고정할 배경. 본무대·잔디·관객·부스 동선을 정함. 사진 출처는 JSON에 보존.
M3 우주선: 닫힘, 열림을 별개 마스터로. 열린 캐노피와 중앙 전면 계단은 SO 원본 우선.
M4 번역기: 동일 크림/민트 휴대형 콘셉트 1개. 버튼/화면비/손잡이 고정.
M5 판매자: 자연스러운 중년 한국 여성 1명, 같은 앞치마·머리·부스·조명. 주문/전달 컷에서 동일인.
M6 굿즈샵: 키링 앞왼쪽, 티셔츠 중앙뒤, 시팅인형 앞오른쪽. 나머지는 가장자리. 모든 상품 원본을 한 생성 호출에 억지로 넣지 않고 상품군별 생성·합성.

매체 기준(제작 권장값이며 플랫폼 한도 주장이 아님)
영상 1080×1920, 9:16, 24fps 편집. 동일 타임라인 내 프레임레이트 혼용 금지. 89초.
캐러셀 1080×1350, 4:5, 총16장. 가능하면 더 큰 정지 원본에서 축소.
텍스트는 가장자리 약8–10% 안쪽에 배치하고 앱 UI가 겹칠 상하단은 게시 전 미리보기로 확인.
캐러셀 본문 1–2줄, 말풍선 1개에 기호 1–3개. 원본 얼굴과 더듬이를 가리지 않음.
1–3컷은 우주 판타지, 3→4 구름/밝은 하늘을 이용해 실사로 전환. 색은 캐릭터 원본 유지.

티셔츠 아트 정확 명세
D: 앞면 정중앙에 성체 대키미 원본 얼굴 크게, 그 아래 정확히 '뭘보노?'.
O: 착용자 왼쪽 가슴(정면으로 보는 화면 오른쪽)에 성체 외지몽 원본 얼굴 작게.
O: '외지인입니다.'는 마침표 포함, 앞면 정중앙에 크게. 작은 얼굴 옆에 붙이는 작은 문구가 아님.
모델에게 캐릭터 얼굴·한글을 새로 그리게 하지 않음. 빈 흰 면티 생성→승인 얼굴 아트와 활자 별도 레이어→원단 원근/주름/가림 마스크 적용.
티셔츠 프린트 얼굴은 표정 애니메이션하지 않음. 작은 얼굴도 눈/주둥이 색영역 생략으로 다른 캐릭터가 되지 않도록 확인.

굿즈 우선순위
키링인형·티셔츠·시팅인형 세 종류가 모두 잘 보여야 함. 에코백·머그·스티커는 함께 진열하되 주요3종을 가리지 않음.
대키미 시팅: SD 승인 원본. 외지몽 시팅: OB+OBS 승인 아기 외형을 앉은 봉제인형으로 구성하는 콘셉트 사용을 사용자 승인.
상품 크기·가격·출시일·양산 승인·판매처를 이 스토리에서 새로 확정하지 않음.

일관성
성체 원본과 상품 원본을 혼용하지 않음. 손/발 패드 개수도 각 자료에 따름.
발광·스케일·색감으로 캐릭터를 실사 동물처럼 바꾸지 않음. 귀여움은 작은 몸짓·타이밍으로.
열린 눈의 별 하이라이트는 붙어 있는 고유무늬. 눈을 감을 때에는 눈꺼풀에 가려질 뿐 다른 곳으로 이동하지 않음.
캐릭터 무음: 웃음소리·감탄사·알아들을 수 있는 군중 대사도 생성하지 않음. 필요한 감정은 음악·효과음으로.
사투리 토론은 무대의 사람 배치·제스처·현수막으로 표현, 실제 발언을 녹음/합성하는 구성이 아님.

출처와 권한 범위
가상의 대사투 페스티벌(가칭)을 실제 두류 야외음악당에서 연출하는 기획. 실제 개최·업소 출점을 주장하지 않음.
맛집 자료: 로컬 Git origin/main의 맛집리스트_V1.md(2026-11-03). 납작만두·야끼우동/7구 출점 후보 참고.
이번 작업에서 유료 영상 생성이나 외부 서비스 업로드를 실행하지 않음.
"""

lines=[common,'\n영상 쇼트별 상세\n']
for d in shots:
    lines.append('\n'+'='*65+'\n'+f'{d["code"]} {d["title"]} | {d["in"]:02d}–{d["out"]:02d}초 ({d["duration"]}초) | 캐러셀 C{d["carousel"]:02d}\n')
    for label,key in [('스타일','style'),('카메라','camera'),('구도','composition'),('표정','expression'),('시작 상태','start'),('시간별 동작','action'),('종료 상태','end'),('다음 컷 연결','transition'),('소리','sound'),('후편집','overlay'),('오류 검수','qa')]:
        lines.append(label+': '+d[key])
    lines.append('첨부 레퍼런스: '+', '.join(d['refs']))
    lines.append('\n[시작 이미지 프롬프트 EN]\n'+d['start_prompt'])
    lines.append('\n[Higgsfield 동작 프롬프트 EN]\n'+d['motion_prompt'])
(OUT/'01_영상24쇼트_상세스토리보드와프롬프트.txt').write_text('\n'.join(lines))

clines=['캐러셀 16장 제작 지시 v04\n같은 이야기와 순서. 영상24쇼트의 세부 동작을16장에 묶는다.\n']
for c in carousel:
    clines.append('\n'+'='*55+f'\nC{c["page"]:02d} | 영상 '+','.join('S'+str(i).zfill(2) for i in c['shots'])+'\n')
    clines.append('정확 캡션:\n'+c['copy']+'\n구성: '+c['layout'])
    clines.append('대응 쇼트의 후편집: '+' / '.join(shots[i-1]['overlay'] for i in c['shots']))
    clines.append('\n[텍스트 없는 캐러셀 베이스 이미지 프롬프트]\n'+c['prompt'])
clines.append('\n공통: 모든 문구·말풍선·로고는 편집 레이어. 4:5용 시작 이미지를 별도 생성/확장. 주인공이나 상품 원본을 잘라내지 않는다.')
(OUT/'02_캐러셀16장_페이지별구성과프롬프트.txt').write_text('\n'.join(clines))
(OUT/'00_먼저읽기_제작순서와디자인고정.txt').write_text(common+'\n\n레퍼런스 코드\n'+'\n'.join(k+' — '+v['label']+' — '+v['file']+' — '+v['status'] for k,v in assets.items()))

# Individual files make it practical to attach just the right images and copy one action.
for d in shots:
    folder=OUT/'video_shots'/d['code'];folder.mkdir(parents=True,exist_ok=True)
    (folder/'start_image_prompt_EN.txt').write_text(d['start_prompt'])
    (folder/'motion_prompt_EN.txt').write_text(d['motion_prompt'])
    (folder/'shot_notes_KO.txt').write_text('\n'.join(f'{k}: {d[k]}' for k in ['title','in','out','camera','composition','expression','start','action','end','transition','sound','overlay','qa'])+'\n전체필요자료: '+','.join(d['refs'])+'\n생성호출기본첨부(최대5개): '+','.join(d['generation_refs'])+'\n상품전체샷 S19는 상품군별 원본으로 개별 생성·합성 필요.')
for c in carousel:
    folder=OUT/'carousel_pages'/('C'+str(c['page']).zfill(2));folder.mkdir(parents=True,exist_ok=True)
    (folder/'base_image_prompt.txt').write_text(c['prompt'])
    (folder/'caption_and_layout.txt').write_text(c['copy']+'\n\n'+c['layout']+'\n\n영상대응: '+','.join('S'+str(i).zfill(2) for i in c['shots']))

e=html.escape
def ref_html(codes):
    return ''.join('<figure><img loading="lazy" src="'+e(assets[a]['file'],quote=True)+'" alt="'+e(assets[a]['label'])+'"><figcaption>'+e(a+' · '+assets[a]['label'])+'</figcaption></figure>' for a in codes)
cards=[]
for d in shots:
    details=''.join('<div class="field"><b>'+label+'</b><p>'+e(d[key])+'</p></div>' for label,key in [('구도','composition'),('표정','expression'),('시작','start'),('동작','action'),('종료','end'),('편집 연결','transition'),('소리','sound'),('후편집','overlay'),('검수','qa')])
    cards.append('<details class="shot" id="'+d['code']+'" data-page="'+str(d['carousel'])+'"><summary><span class="no">'+d['code']+'</span><strong>'+e(d['title'])+'</strong><span>'+str(d['in'])+'–'+str(d['out'])+'s · C'+str(d['carousel']).zfill(2)+'</span></summary><div class="inside"><div class="tag">'+e(d['style']+' / '+d['camera'])+'</div>'+details+'<div class="refs">'+ref_html(d['refs'])+'</div><details><summary>시작 이미지 프롬프트 EN</summary><pre>'+e(d['start_prompt'])+'</pre></details><details><summary>영상 동작 프롬프트 EN</summary><pre>'+e(d['motion_prompt'])+'</pre></details></div></details>')
pages=[]
for c in carousel:
    pages.append('<article class="page"><div class="tag">C'+str(c['page']).zfill(2)+' · '+', '.join('S'+str(i).zfill(2) for i in c['shots'])+'</div><h3>'+e(c['copy']).replace('\n','<br>')+'</h3><p>'+e(c['layout'])+'</p><details><summary>베이스 이미지 프롬프트</summary><pre>'+e(c['prompt'])+'</pre></details></article>')
asset_cards=ref_html(list(assets))
timeline=''.join('<a href="#'+d['code']+'" style="flex:'+str(d['duration'])+'" data-target="'+d['code']+'" aria-label="'+e(d['code']+' '+d['title'])+'">'+str(d['id'])+'</a>' for d in shots)
html_doc='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>대구 얼라들 | 상세 제작 스토리보드 v04</title><style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;color:#213832;background:#f6f7f1;line-height:1.65}*{box-sizing:border-box}body{margin:0}header{background:#143b32;color:#fff;padding:48px max(24px,calc((100vw - 1120px)/2))}header .eyebrow{letter-spacing:.13em;color:#b2e4ce;font-size:13px}h1{font-size:clamp(28px,4vw,46px);line-height:1.25;margin:12px 0 18px}header p{max-width:800px;color:#e4f0e8}main{max-width:1168px;margin:auto;padding:24px}.metrics{display:flex;gap:12px;flex-wrap:wrap}.metric{border:1px solid #618777;border-radius:12px;padding:10px 18px}.metric b{font-size:24px;display:block}.nav{position:sticky;top:0;background:#f6f7f1ed;backdrop-filter:blur(10px);padding:14px 0;z-index:3;display:flex;gap:8px;flex-wrap:wrap}button,.nav a{font:inherit;border:1px solid #c1d4c9;background:#fff;color:#174336;border-radius:8px;padding:8px 14px;cursor:pointer;text-decoration:none}button.active{background:#24664e;color:white}.timeline{display:flex;gap:3px;overflow:auto;margin:22px 0}.timeline a{background:#cde5d5;color:#164c38;text-align:center;min-width:28px;text-decoration:none;font-size:12px;padding:9px 0;border-radius:4px}.timeline a:nth-child(-n+3){background:#dcd8f0;color:#45377a}.section{display:none}.section.active{display:block}.shot{background:white;border:1px solid #d5ded5;border-radius:12px;margin-bottom:12px;scroll-margin-top:88px}.shot>summary{display:flex;align-items:center;gap:14px;padding:17px;cursor:pointer}.shot>summary span:last-child{margin-left:auto;font-size:13px;white-space:nowrap}.no{background:#e3f2e9;color:#226648;padding:7px 9px;border-radius:7px;font-weight:700}.inside{padding:0 22px 22px}.tag{font-size:13px;font-weight:650;color:#3a735e;margin:12px 0}.field{display:grid;grid-template-columns:90px 1fr;border-top:1px solid #edf0ea;gap:12px;padding:12px 0}.field b{font-size:13px;color:#496258}.field p{margin:0}.refs{display:flex;gap:12px;overflow:auto;padding:12px 0}.refs figure,figure{margin:0;background:white;border:1px solid #dde4dc;padding:8px;border-radius:8px;min-width:150px;max-width:210px}.refs img,figure img{width:100%;height:140px;object-fit:contain}figcaption{font-size:12px;padding-top:6px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3ee;padding:18px;font:13px/1.65 ui-monospace,monospace;border-radius:8px}details details{margin-top:12px}details details summary{cursor:pointer;color:#215e46}.pages{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.page{background:#fff;border:1px solid #d5ded5;padding:22px;border-radius:12px}.page h3{font-size:25px;line-height:1.4}.assetgrid{display:flex;flex-wrap:wrap;gap:14px}.rules{white-space:pre-wrap;background:#fff;border-radius:12px;padding:24px;border:1px solid #d5ded5}.notice{border-left:4px solid #cf9366;background:#fff3e7;padding:15px;margin:18px 0}.small{font-size:13px;color:#5c6e62}a{color:#256c4e}.copyright{padding:24px 0;font-size:12px;color:#5f7266}@media(max-width:650px){header{padding:28px 22px}.pages{grid-template-columns:1fr}.shot>summary{gap:8px}.shot>summary span:last-child{font-size:11px}.field{grid-template-columns:1fr;gap:3px}.nav{position:static}}@media print{.nav,button{display:none!important}.section{display:block!important}header{background:white;color:#123;padding:12px}header p{color:#234}main{padding:0}.shot,.page{break-inside:avoid}.shot>.inside{display:block}.refs{flex-wrap:wrap}details details{display:none}.timeline{display:none}}
</style></head><body><header><div class="eyebrow">DAEGU EOLLADEUL · PRODUCTION STORYBOARD v04</div><h1>우주에서 받은 신호,<br>대구에서 만난 친구</h1><p>같은 이야기를 캐러셀과 영상으로. 컷마다 시작·동작·종료, 원본 첨부와 후편집 지시를 분리한 제작 보드입니다.</p><div class="metrics"><div class="metric"><b>16장</b>캐러셀</div><div class="metric"><b>24쇼트</b>영상</div><div class="metric"><b>89초</b>편집안</div><div class="metric"><b>무대사</b>기호 말풍선 + 효과음</div></div></header><main><nav class="nav"><button class="active" data-tab="video">영상 쇼트</button><button data-tab="carousel">캐러셀</button><button data-tab="assets">레퍼런스</button><button data-tab="rules">제작 기준</button><button id="expand">영상 모두 펼치기</button><button onclick="window.print()">인쇄 / PDF 저장</button></nav><div class="notice">이 보드는 상세 제작 지시입니다. 장면 이미지·영상·티셔츠 프린트 최종 파일을 이미 생성한 결과물은 아닙니다. 아래 이미지는 모두 출처가 있는 원본 레퍼런스입니다.</div><div class="timeline">'''+timeline+'''</div><section class="section active" id="video">'''+''.join(cards)+'''</section><section class="section" id="carousel"><div class="pages">'''+''.join(pages)+'''</div></section><section class="section" id="assets"><h2>용도별 원본</h2><p>성체 CG와 상품 아기 디자인은 서로 대체하지 않습니다. 외지몽 시팅인형은 승인 아기 디자인 기반 콘셉트입니다.</p><div class="assetgrid">'''+asset_cards+'''</div></section><section class="section" id="rules"><div class="rules">'''+e(common)+'''</div></section><div class="copyright">대사투 페스티벌은 가상의 행사 콘셉트입니다. 상품·참여업소·출시 정보 확정 자료가 아닙니다.</div></main><script>
const tabs=document.querySelectorAll('[data-tab]');
document.querySelectorAll('pre').forEach(pre=>{const b=document.createElement('button');b.type='button';b.textContent='프롬프트 복사';b.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(pre.textContent);b.textContent='복사됨';setTimeout(()=>b.textContent='프롬프트 복사',1500);}catch(err){const range=document.createRange();range.selectNodeContents(pre);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);b.textContent='선택됨 · 복사 키를 누르세요';}});pre.before(b);});
function selectTab(id){document.querySelectorAll('.section').forEach(x=>x.classList.toggle('active',x.id===id));tabs.forEach(x=>x.classList.toggle('active',x.dataset.tab===id));}
tabs.forEach(b=>b.addEventListener('click',()=>selectTab(b.dataset.tab)));
document.getElementById('expand').addEventListener('click',()=>{selectTab('video');const xs=[...document.querySelectorAll('.shot')];const shouldOpen=xs.some(x=>!x.open);xs.forEach(x=>x.open=shouldOpen);document.getElementById('expand').textContent=shouldOpen?'영상 모두 접기':'영상 모두 펼치기';});
document.querySelectorAll('[data-target]').forEach(a=>a.addEventListener('click',()=>{selectTab('video');document.getElementById(a.dataset.target).open=true;}));
</script></body></html>'''
(OUT/'상세제작_스토리보드_v04.html').write_text(html_doc)

assert len(shots)==24 and t==89 and len(carousel)==16
assert sorted(i for c in carousel for i in c['shots'])==list(range(1,25))
assert all(shots[i-1]['carousel']==c['page'] for c in carousel for i in c['shots'])
assert all(len(s['generation_refs'])<=5 for s in shots)
assert all((OUT/v['file']).exists() for v in assets.values())
print(json.dumps({'output':str(OUT),'seconds':t,'shots':len(shots),'carousel_pages':len(carousel),'reference_files':len(assets),'mapping':'complete, unique, sequential','files':len(list(OUT.rglob('*')))},ensure_ascii=False))
