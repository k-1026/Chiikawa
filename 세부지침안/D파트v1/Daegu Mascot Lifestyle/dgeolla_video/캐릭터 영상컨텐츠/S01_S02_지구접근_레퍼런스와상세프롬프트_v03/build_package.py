from pathlib import Path
import json,shutil,hashlib,zipfile,html,struct

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent.parent
BASE=ROOT/'캐릭터 영상컨텐츠/첫게시물_상세제작보드_v04'
d=json.loads((BASE/'storyboard_v04.json').read_text())
refdir=OUT/'01_원본레퍼런스';refdir.mkdir(exist_ok=True,parents=True)
imgdir=OUT/'02_생성이미지';imgdir.mkdir(exist_ok=True)
pdir=OUT/'03_이미지별프롬프트';pdir.mkdir(exist_ok=True)
vdir=OUT/'04_영상과음향프롬프트';vdir.mkdir(exist_ok=True)

sources={
'R01':('외지몽_성체정면.png',Path(d['assets']['O']['source']),'성체 얼굴·귀·눈무늬·몸비율 우선'),
'R02':('외지몽_성체측면.png',Path(d['assets']['OS']['source']),'머리 깊이·측면·45도 원본'),
'R03':('우주선_닫힘6방향.png',next(p for p in (ROOT/'세계관 및 소품').rglob('*.png') if p.name=='외지몽_우주선_닫힘_6방향.png'),'닫힌 단일 캐노피·한 좌석·조종간·외형'),
'R04':('얼라별.png',Path(d['assets']['P']['source']),'코랄 행성·민트 고리·더듬이 원본'),
}
refs={}
for k,(name,src,role) in sources.items():
    dest=refdir/(k+'_'+name);shutil.copy2(src,dest)
    refs[k]={'file':str(dest.relative_to(OUT)),'source':str(src),'role':role,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
board=ROOT/'캐릭터 영상컨텐츠/S01_우주비행_수정스토리보드_v02/S01_지구접근_크기변화_S02연결_원페이지_v02.png'
shutil.copy2(board,refdir/'R05_스토리보드_구도설명전용.png')
refs['R05']={'file':str((refdir/'R05_스토리보드_구도설명전용.png').relative_to(OUT)),'source':str(board),'role':'진행 순서·크기 변화·구도 설명 전용. 글씨/화살표/캐릭터 재현의 우선 원본이 아님.'}
start_source=Path('/Users/seunghui/.codex/generated_images/01a1dd90-e1a8-7600-bfdb-c34e3d473d69/exec-76a0a85d-5ce0-4e08-8bf3-d10e54dc370f.png')
shutil.copy2(start_source,imgdir/'G01_S01_00초_START.png')

LOCK="""Use case: illustration-story / identity-preserving keyframe production.
Output ONE full-frame vertical 9:16 image. No text, logos, symbols, labels, map pins, inset maps, arrows, panels, borders or speech bubbles. This is an animation frame, not a storyboard sheet.
Style: cute smooth cinematic 3D animation. No humans, real animal fur, photoreal dog, new clothes, blush, human lips, large teeth, human fingers, baby redesign or added props.
Original adult Oejimong: exact approved head depth and front/three-quarter proportions, drooping green dog ears, TWO ball-tipped head antennas, original rounded triangular black eyes with a large white four-point star, small grey star and tiny diamond per open eye, cream muzzle around original rounded black nose and small mouth. Calm original little smile. Preserve eye motifs as fixed design, not floating pupils. Small steering motions only; no face deformation.
Spacecraft: original green/cream body and ear-like side pods, TWO external ship antennas separate from pilot's two head antennas, ONE fully CLOSED transparent canopy, original single cream seat, original two slender green joystick stems with cream ball knobs and low central oval cream button. No second glass shell, raised lid, exterior overhead arch, open canopy, deployed ladder, invented radar console or side door.
Earth is ONE globe ahead at RIGHT/lower-right; Eollastar is ONE small coral/mint planet far behind upper-left. Never swap them. Ship nose and pilot gaze toward SCREEN RIGHT/Earth. Earth stays larger than Eollastar.
Lighting: cool blue-white Earth light from right/upper-right and warm soft engine light behind the ship on left. Do not mirror the flight axis.
For S01: ship and pilot grow together; Earth grows; Eollastar shrinks. Planet surface landmarks rotate coherently. This is real travel plus camera approach, not a single uniform digital zoom of a still.
For S02: camera is inside the same closed cockpit. No added external dome/canopy arch on top of the interior frame. Same Asia-facing Earth out the RIGHT window and same blue bounce light.
"""

jobs=[
{'id':'G01','name':'S01_00초_START','time':'0s','status':'generated','attachments':['R01','R02','R03','R04','R05'],'role':'开始帧','ko_role':'S01 시작 프레임. 영상 시작 입력.',
'prompt':"""Make the START of the S01 eight-second approach. Attach R01/R02 as character identity, R03 as closed vehicle, R04 as Eollastar, R05 as composition/story guide ONLY; remove all guide typography/arrows.
Closed ship fully visible at left-midground around 30–40 percent frame width, nose right, original pilot small but recognisable inside glass with paws resting on controls. Eollastar small upper-left around 15–20 percent frame width. Earth is much larger on RIGHT/lower-right, partly cropped by right edge, visible curved blue limb and Asian/Indian Ocean region. Sparse navy stars and soft violet haze.
This is the small-ship/less-close-Earth start, leaving room for the ship and Earth to GROW through later keyframes. Eollastar will recede. No title, engine flame explosion, warp tunnel or movement graphic. Entire ship silhouette and antennas in frame. Keep original adult face and original vehicle proportions."""},
{'id':'G04','name':'S01_08초_END_아시아','time':'8s','status':'pending_usage_limit','attachments':['G01','R01','R02','R03','R04'],'ko_role':'S01 종료 프레임. 우주선·지구 확대, 얼라별 축소, 아시아 방향 연결.',
'prompt':"""Advance the supplied G01 START scene to the END at 8 seconds. G01 is the scene/lighting/flight-axis reference, R01/R02 original face references, R03 original closed spacecraft, R04 planet identity.
Make the spacecraft AND its seated pilot CLEARLY LARGER together, around 1.6–2 times their starting apparent size as composition permits, without cropping or reshaping the vehicle. Ship centre stays left/middle and nose faces SCREEN RIGHT. The cockpit and pilot should now be readable enough to motivate the next cockpit close-up. Driver makes one gentle joystick adjustment; face remains original small smile.
Eollastar far upper-left SHRINKS to about one third of its starting apparent width. Its cream-star/crater orientation advances slightly through coherent self-rotation; mint ring plane is stable.
Earth on RIGHT/lower-right GROWS substantially and extends beyond the right/bottom frame edges; its curved illuminated limb comes farther into frame. Earth remains safely ahead of the ship, not a surface they have landed on. Preserve room to see the globe on right beside the ship.
The final visible globe face MUST show recognizable ASIA: Eurasia/China, India lower-left, east Asian coast, Korean peninsula and Japan to east, Southeast Asia below. No central North America/Africa replacement. Preserve geography; no invented continent shapes or location labels. Cool blue-white Earth light remains from upper/right.
Stars/near particles show modest parallax. Ship and Earth enlarge while Eollastar shrinks, so do NOT uniformly scale up the entire G01 image. No collision, atmospheric entry, canopy opening, extra controls or graphic overlay."""},
{'id':'G02','name':'S01_约03秒_MID_A','file_name':'G02_S01_03초_MID_A.png','time':'~2.7s','status':'pending_usage_limit','attachments':['G01','G04','R01','R03','R04'],'ko_role':'S01 전반 중간 프레임. 양 끝 이미지 사이의 작은 크기 변화.',
'prompt':"""Create the FIRST INTERMEDIATE keyframe, about 2.7 seconds into S01. G01 is time0 and G04 is time8 endpoint; interpolate their same scene, identity, flight direction and lighting. R01 is original face, R03 closed spacecraft structure, R04 Eollastar.
Keep camera angle the same front-side three-quarter. Ship and pilot apparent width about 1.2 times G01, still smaller than G04. Earth visibly larger than G01 but smaller than G04. Eollastar about three quarters of G01 apparent width, still upper-left. All three sizes must follow their own trajectories rather than a uniform poster zoom.
Earth and Eollastar surface markings advance only a small coherent fraction of the endpoint rotation; original continent topology and planet ring preserved. Original pilot subtly nudges one joystick with a rounded paw, not a large new gesture. Maintain ship antenna positions, canopy silhouette, original seat and small engine glow.
Use sparse depth-dependent particle drift, not warp-speed streaks. Keep Earth to right, ship middle-left, planet behind. No new camera angle, text, map inset, speech bubble or fake timeline."""},
{'id':'G03','name':'S01_约05秒_MID_B','file_name':'G03_S01_05초_MID_B.png','time':'~5.3s','status':'pending_usage_limit','attachments':['G01','G04','R01','R03','R04'],'ko_role':'S01 후반 중간 프레임. 아시아를 향하는 지구 방향과 접근 심화.',
'prompt':"""Create the SECOND INTERMEDIATE keyframe at about 5.3 seconds between supplied G01(time0) and G04(time8). Preserve their identical ship/face identity, coherent Earth geography, lighting and front-side camera angle. R01/R03/R04 lock original character, closed spacecraft and planet.
Spacecraft and pilot apparent width about 1.4–1.6 times G01, larger than first intermediate but still smaller than endpoint. Earth expands farther into right/lower-right, approaching G04 size. Eollastar upper-left is about half its starting width. These changes must be visually distinct.
Earth rotates coherently toward the ASIA orientation of G04. Do not morph continents; East Asia/India/SEA should already be readable and move gradually toward final orientation. Eollastar's surface stars/craters rotate gently with a stable mint-ring plane.
Pilot now holds its small steering adjustment, focused on Earth with unchanged original small smile, head/eyes not redesigned. Engine gently brighter, particles have modest parallax. Ship remains outside atmosphere, single closed canopy throughout. No labels/arrows/map/close-up cut or uniform scaling of all layers."""},
{'id':'G05','name':'S02_00초_START_아시아연결','time':'S02 0s / total8s','status':'pending_usage_limit','attachments':['G04','R01','R02','R03'],'ko_role':'S02 실내 시작. S01 종료의 지구 방향/빛/시선 연결.',
'prompt':"""Create the next-shot S02 START, a deliberate cut from G04 exterior to cockpit interior. G04 is the ending Earth orientation, blue lighting and travel-direction reference. R01 original adult dog front, R02 approved side/head depth, R03 original CLOSED single-cockpit spacecraft.
Camera is INSIDE the single closed canopy, looking from front-left toward the seated pilot at screen LEFT 60 percent. Medium close-up; both original head antenna balls visible, original cream seat behind, partial two original joystick stems and low oval central button at lower-right. Face looks forward SCREEN RIGHT toward Earth, calm original smile and unchanged geometry.
Show ONE curved transparent window on right, no new lifted lid or exterior green overhead arch, no duplicate canopy dome, no circular radar screen or extra dashboard.
Earth outside RIGHT glass MUST match the ASIA face in G04: same China/East Asia/India/SEA arrangement, same rotation direction, same upper-right cool blue-white light. Cropping changes naturally from exterior-to-interior camera; no mirroring, jump to America, second Earth or inset.
Body/paws resting in same seat, no added fingers. Cute original CG head not miniature baby. Keep Earth and controls visible enough to motivate noticing a signal. No text or question mark; those are later edit layers."""},
{'id':'G06','name':'S02_03초_END_注意到仪表','file_name':'G06_S02_03초_END_조종간주시.png','time':'S02 3s / total11s','status':'pending_usage_limit','attachments':['G05','G04','R01','R02','R03'],'ko_role':'S02 종료. 얼굴 보존한 작은 고개 이동, 아시아 연속성 유지.',
'prompt':"""Edit the supplied G05 locked S02 interior start to the END pose about3 seconds later. G05 is the edit target. G04 is Earth/flight continuity, R01/R02 original character, R03 closed spacecraft structure.
Change ONLY a restrained reaction: pilot gently turns head down/right about 5–8 degrees toward existing controls, then pauses with curiosity. Keep original little smile and original eye motifs, no huge mouth/cheeks/eyebrows or looking at the camera. Both antennae and floppy ears move naturally with the small head rotation.
Keep camera/crop/seat/body/paws/joysticks/central button and single closed window position as close to G05 as possible. No new radar display or opened canopy.
Asia-facing Earth remains outside RIGHT with same blue illumination; only a very small coherent continuation of slow rotation is permitted. No reset to a different globe orientation or mirror. No Eollastar inserted into the cockpit background unless naturally visible in G05.
Do not bake in any ?, !, speech bubbles, waveform, title, logo or signal graphic. Preserve the scene for later sound/overlay editing."""},
]

for j in jobs:
    if 'file_name' not in j:j['file_name']=j['id']+'_'+j['name']+'.png'
    # Normalise internal editorial names to Korean/ASCII, no foreign placeholder labels.
    if j['id']=='G01':j['file_name']='G01_S01_00초_START.png'
    j['prompt_full']=LOCK+'\n\nREFERENCE ATTACHMENT ORDER: '+', '.join(j['attachments'])+'\n'+j['prompt']
    (pdir/(j['id']+'_이미지생성_EN.txt')).write_text(j['prompt_full'])

video_s01="""S01 · 지구 접근 · 최종8초 / 9:16
첨부 기본: G01은 시작, G04는 종료. G02/G03는 실제 다중키프레임/참조 기능을 지원할 때만 각각 약2.7초/5.3초 역할을 지정.
디자인 검증 보조: R01 외지몽 정면, R02 측면, R03 닫힌 우주선, R04 얼라별. 지원 개수 확인 후 역할별로 사용.
한 페이지 스토리보드 전체를 영상 시작 프레임으로 넣지 않음.

핵심: 얼라별은 작아지고 우주선과 외지몽·지구는 커진다. 전부 같은 비율로 확대하는 단일 줌이 아니다.
0–2초 출발 공간 제시. 두 행성은 처음부터 느리게 자전.
2–4초 외지몽이 조종간을 작게 조작하고 우주선이 실제로 지구 방향으로 전진.
4–6초 얼라별은 더 멀어지고 별/입자 시차가 보임. 우주선과 지구가 각각 커짐.
6–8초 지구의 아시아가 뚜렷하게 보이고 우주선/조종석도 가까워짐. 대기권 진입·착륙 없음. 다음 S02와 시선/빛 방향 연결.
지구와 우주선이 함께 커지는 크기 변화는 카메라 접근과 실제 비행의 합성 연출. 고정 사진 전체 확대를 지시하지 않음.

EN VIDEO PROMPT
An eight-second continuous cute cinematic 3D space approach. Use G01 as the start and G04 as the endpoint, with G02 and G03 as supported intermediate pose/composition references only. The original adult green alien dog actively pilots the original closed green-and-cream spacecraft toward Earth at screen right, making one small joystick adjustment and a restrained forward body response. Keep its face, eye-star motifs, muzzle, drooping ears, head depth and two head antennas unchanged; keep the spacecraft's original two external antennas, single CLOSED canopy, ear-like side pods, original seat and two controls.

Animate THREE independent depth trajectories simultaneously: the distant coral planet with mint ring behind at upper left recedes and SHRINKS; the spacecraft AND its pilot advance and GROW visibly together; Earth in the right foreground grows as distance to it closes. Camera approaches from the same front-side three-quarter angle while the craft travels forward. Do not simply apply one digital zoom to the entire starting still. Do not keep the spacecraft size constant.

Both planets slowly rotate on their own axes with coherent surface features. Eollastar surface stars/craters drift around its sphere, its ring plane stable. Earth continent/cloud orientation changes smoothly with no land morphing, finishing clearly on ASIA: China/East Asia, Korean peninsula/Japan, India and Southeast Asia. Keep the screen-right Earth placement and upper-right blue-white Earth light so the next cockpit shot can match. Sparse nearby particles drift relative to distant stars at different speeds; no warp tunnel.

0–2s establish moving space; 2–4s tiny joystick adjustment and purposeful acceleration; 4–6s stronger depth/parallax and receding planet; 6–8s gentle Earth approach ending on the Asia-facing globe and a larger readable cockpit. Maintain forward motion through the final frame, no freeze/stop, collision, landing, atmospheric entry, abrupt spin, camera-axis flip, opened canopy or scene cut.

No text, map labels, pins, inset maps, overlays, logos, speech bubbles, dialogue, narration, lip-sync or altered face. Mild warm engine light pulses naturally, no violent flame.

음향: 03_BGM_효과음_프롬프트.txt의8초 구간 적용. 영상 모델의 오디오 지원이 확인되지 않으면 영상과 음향을 분리 제작/편집.

입력 기능에 따른 실행
A. 실제 start/end 입력 지원: G01/G04를 역할대로 지정하고8초 연속쇼트 생성. MID는 지원되는 기능으로만.
B. 실제 다중 시간키프레임 지원: G01/G02/G03/G04를0/2.7/5.3/8초로 지정(정확 시간 지정이 가능한 경우에만).
C. start만 지원하거나 A에서 크기 변화를 놓침: G01→G02, G02→G03, G03→G04를 각각 짧은 구간으로 생성해 약2.7/2.6/2.7초로 편집. 끝프레임 미지원이면 목표포즈를 프롬프트로 지정. 구간 사이 카메라/비행방향/속도가 끊기면 사용하지 않고 재조정.
생성 모델·지원 길이·입력 개수는 실행 시 확인. 특정 모델이 이 모든 기능을 지원한다고 가정하지 않음.
"""
video_s02="""S02 · 아시아 방향과 조종석 연결 · 최종3초 / 9:16
첨부: G05 기본 시작. 종료 입력이 실제 지원되면 G06 추가. G04는 S01 종료의 아시아 방향/빛/진행 방향 보조.
원본 검수: R01/R02/R03. 기존 S02 패키지 v02의 지구 방향은 이 버전과 다를 수 있으므로 최신 G05/G06을 먼저 제작한 뒤 사용.

EN VIDEO PROMPT
Cut naturally from the preceding Asia-facing Earth approach into the same closed cockpit. Use G05 as the start and G06 as supported end-pose reference. Fixed interior front-left medium close-up, original cute adult green pilot on left, original controls lower-right and the SAME ASIA-facing Earth through the right window. Preserve screen direction, geographic orientation, upper-right cool Earth light, original cream seat, two green joystick stems with cream ball knobs and the low oval centre button.

For the first0.3 seconds keep the forward gaze. A soft offscreen instrument reception beep occurs, then the pilot gently turns its head five to eight degrees down/right toward the existing controls between0.5 and2.2 seconds, and pauses with small calm curiosity for the remainder. Keep face/muzzle/eye shapes and fixed star motifs unchanged. Body, arms and controls remain stable. Outside Earth may continue a very slight coherent rotation, no jump or mirror of continents.

No zoom, opened canopy, exterior lid/overhead arch, second glass dome, invented radar console, extra fingers, fur, blush, human mouth/teeth, talking, narration, text or speech bubbles. The question mark is a separate later2D overlay, never a required part of video generation.

Camera stays inside the closed window throughout. Do not generate a second globe or Eollastar outside the wrong window. No head morphing or exaggerated mouth change.

音は後制作: use the sound plan below; add the question-mark graphic briefly above-right away from face/antennae if desired.
"""
video_s02=video_s02.replace('音は後制作:','음향은 후편집:')
audio="""BGM / 효과음 제작 지시 · S01 8초 + S02 3초
음성 대사·내레이션·노래·실제 발화 없음.
의도: 호기심 어린 귀여운 우주 모험. 무섭거나 군사적·웅장한 전투 음악이 아님.

BGM EN
Create an original instrumental eleven-second cue for a cute 3D alien pilot approaching Earth. Around100 BPM, light curious adventure mood, soft warm synth pad, delicate bell/celesta notes, gentle airy strings and a very restrained rhythmic pulse. No vocals, spoken words, choir, aggressive drums, brass fanfare, known melody or copyrighted song imitation. Keep it playful, spacious and tender.
0–2s: soft sustained pad opens with one sparse bell motif.
2–6s: a light pulse and a few sparkling bell notes build the feeling of purposeful travel.
6–8s: a gentle melodic lift conveys anticipation on seeing Asia, no giant climax.
8–11s: thin the rhythm smoothly for the cockpit cut and leave room for a soft reception beep, continuing the same musical world without a new song.
No audible hard stop at8 seconds. A short warm tail after11 seconds may be provided for editing.

SFX EN
Provide separate clean sound effects with no voices or music baked in:
1. Soft continuous spacecraft engine hum, warm low synthetic tone with a subtle airy layer, steady enough to loop, no harsh mechanical rattles.
2. Tiny plastic/soft mechanical joystick click, short and gentle, not a gun or alarm.
3. Smooth restrained thruster rise/whoosh for forward acceleration, subtle, no explosive launch.
4. Very soft sparse passing cosmic particle swishes, little stereo movement, no warp-speed tunnel.
5. One quiet friendly two-tone instrument reception beep, clear but not startling, used only AFTER the S02 cut.

초 단위 편집 위치
0.0–8.0초: 낮은 엔진 허밍 지속. 큰 음량 변화 없이 부드럽게.
약2.0초: 조종간 클릭1회, 조종 동작에 맞춤.
약2.2–6.5초: 추진음이 서서히 올라갔다 안정.
약3.5초/5.5초: 입자 스침을 아주 작게1회씩 선택.
6.0–8.0초: BGM 기대감 조금 상승.
8.0초: S02로 컷. 엔진음은 실내에서 더 부드럽고 조금 먹먹한 톤으로 이어짐.
8.3–8.6초: 수신음1회. 이 소리에 외지몽이 고개를 조금 돌리기 시작.
8.5–11.0초: 음악은 한 단계 얇게. 반응을 강조하되 음성 감탄사 없음.

믹스
효과음이 얼굴/서사보다 과하게 튀지 않도록 엔진은 음악 아래 배치.
조종간 클릭과 수신음은 짧게 식별되게 하되 놀라게 큰 피크 금지.
장면 전환에 같은 음악과 엔진음을 이어서 붙이고 소리 갑자기 끊기지 않게.
선택 영상 도구에 오디오 생성/제어 기능이 없거나 정확한 타이밍이 안 맞으면 영상과 음악/SFX를 별도로 제작해 편집.
아직 이 패키지에 실제 오디오 파일은 없음. 이 문서는 생성/편집 프롬프트.
"""
(vdir/'01_S01_8초_영상프롬프트.txt').write_text(video_s01)
(vdir/'02_S02_3초_영상프롬프트.txt').write_text(video_s02)
(vdir/'03_BGM_효과음_프롬프트.txt').write_text(audio)

claude="""첨부 자료로 S01 지구 접근8초와 다음 S02 조종석3초를 제작해줘.
먼저 이 패키지의 파일 상태를 확인해. G01만 실제 생성됐고 G02~G06은 이미지 생성 한도로 아직 없는 상태야. 없는 이미지를 첨부한 것처럼 말하지 마.

작업 순서:
1. 00_첨부순서와파일상태.txt 확인.
2. 원본R01~R04와 이미지별프롬프트로 G04(종료)를 먼저 생성해. G01/원본을 첨부하고 얼굴/우주선/아시아를 검수.
3. G01/G04 양끝이 정해지면 G02/G03 중간 이미지와 G05 S02 시작을 생성.
4. G05가 검수되면 G06 S02 종료 포즈 생성.
5. 원본 얼굴, 닫힌 우주선, 세 크기 변화, 마지막 아시아, S02 지구/빛/시선 연결 확인.
6. 실제 연결된 Higgsfield 모델의 입력·참조·지원 길이를 확인한 뒤 04_영상과음향프롬프트의 지시로 영상 제작.
7. 지원되는 start/end 또는 다중키프레임만 사용. 파일을 전부 한꺼번에 역할 없이 넣지 마.
8. 실제 오디오 기능에 따라 BGM/SFX를 생성하거나 별도 편집용으로 분리.

최신 핵심:
작은 얼라별은 뒤로 멀어지며 축소, 우주선과 외지몽은 함께 확대, 앞쪽 지구도 접근하며 확대.
배경까지 한 장으로 확대하는 줌이 아니라 행성 자전·실제 전진·조종간 조작·깊이에 따른 상대 이동.
마지막에는 아시아가 보이고 S02 창밖 오른쪽에도 같은 아시아 방향/회전/푸른빛.
캐노피는 항상 한 개가 닫혀 있음. 새 뚜껑·초록 아치·두 번째 유리·새 레이더 계기판 금지.
사운드: 보컬 없는 귀여운 모험 BGM, 낮은 엔진·조종간 클릭·추진음·입자 스침. 수신음은 S02부터.

이미지나 영상 생성 도구가 없다면 실행했다고 하지 말고 필요한 단계와 첨부할 파일을 알려줘.
생성 결과가 틀리면 원본 기준으로 그 항목을 고치고, 실패 이미지를 새 캐릭터 기준으로 누적하지 마.
"""
(OUT/'05_Claude_전체작업시작프롬프트.txt').write_text(claude)

readme="""S01/S02 지구 접근 · 레퍼런스와 상세 프롬프트 v03

현재 실제 파일 상태
생성 완료: G01_S01_00초_START.png 1장.
미생성: G02/G03/G04/G05/G06 5장. 내장 이미지 도구의 usage_limit_reached로 중단.
끝 프레임을 생성한 것처럼 사용하지 말 것. 이 패키지는 생성 완료 이미지1장과 원본4장, 스토리보드1장, 나머지 재개용 프롬프트 전체를 포함.
실제 영상/BGM/효과음은 생성하지 않음.

왜 이 이미지들이 필요한가
G01: 출발 크기와 초기 구도.
G04: 도착 직전 크기·아시아 방향과 다음 S02 연결의 기준. G02/G03보다 먼저 제작해야 함.
G02/G03: 시작/끝 사이의 일관된 접근과 자전을 설명. 모델의 실제 중간키프레임/참조 지원 여부에 따라 입력하거나 동작설명에만 활용.
G05: 닫힌 우주선 실내. G04의 아시아 위치/회전/빛/진행 방향이 연결됨.
G06: S02에서 조금 고개를 돌린 종료 포즈. G05와 같은 카메라/조종석.

이미지 생성 순서(입력4~5개)
G01: R01,R02,R03,R04,R05 / 현재 생성됨.
G04: G01,R01,R02,R03,R04 / 다음 실행할 단계.
G02: G01,G04,R01,R03,R04.
G03: G01,G04,R01,R03,R04.
G05: G04,R01,R02,R03.
G06: G05,G04,R01,R02,R03.
입력 모델의 실제 허용 개수를 확인. 이것은 각 파일의 용도 지정이며 모든 도구가5장 참조를 지원한다는 뜻이 아님.
파일 경로만 Claude에 붙이는 것으로 이미지를 첨부했다고 가정하지 않음. 실제 PNG를 업로드.
R05 스토리보드는 설명용. 글씨·화살표가 있는 원페이지를 영상 시작프레임으로 넣지 않음.

참조 우선순위
성체 얼굴/몸은 R01+R02. 우주선 구조는 R03. 얼라별 외형은 R04.
생성된 G01은 장면/빛/배치 기준이며 원본보다 우선하는 캐릭터 재설계 자료가 아님.
G04의 지구는 S02 지구 방향의 직접 기준. 모델이 G04와 다른 아시아를 만들면 영상 전에 고침.

권장 사용자 실행
압축을 푼 뒤 05_Claude_전체작업시작프롬프트.txt를 복사.
다음 단계는 G04이므로 현재 있는 G01 + R01/R02/R03/R04 네 원본을 첨부해 생성 요청.
G04 생성 후 03_이미지별프롬프트/G04_이미지생성_EN.txt 내용으로 확인.
양끝이 맞으면 나머지 이미지 생성→검수→영상 생성.

스타일/공간
처음 우주 구간은 만화 같은 귀여운3D. 영상9:16.
얼라별은 좌상단 뒤, 지구는 오른쪽 앞, 우주선은 지구를 향한3/4 구도.
크기 변화의 숫자는 연출 비교용이며 물리적 천체거리·동일 픽셀/3D 재현을 보장하는 값 아님.
G01 시작 생성물은 아시아가 이미 일부 보임. 최종에는 아시아가 더 분명히 보이며 같은 지형이 연속 회전하도록 연결.
얼라별이 축소되고 우주선/외지몽·지구는 확대되는 흐름이 핵심. 우주선만 확대하거나 크기를 일정하게 유지하는 이전 지시는 폐기.

검수 체크
□ 지구가 얼라별보다 크고 앞에 있는가?
□ G01→G04에서 얼라별은 축소, 우주선/외지몽과 지구는 확대되는가?
□ 두 행성의 표면이 형태변형 없이 회전하는가?
□ 우주선이 지구 쪽으로 전진하고 조종 동작이 보이는가?
□ 외지몽 얼굴/눈별/주둥이/귀/안테나가 원본과 일치하는가?
□ 한 개의 닫힌 캐노피, 원래 좌석/조종간 구조인가?
□ 마지막 지구는 아시아이고 S02와 방향/빛이 이어지는가?
□ 글씨·화살표·지도핀·이중유리·불필요한 계기판이 없는가?
□ BGM/SFX가 포함됐거나 분리 편집 대상으로 명확히 전달됐는가?

오류 없는 결과를 자동 보장할 수 없음. 이미지별 선행 기준을 고정하고 실제 생성물에 위 검수를 적용.
"""
(OUT/'00_첨부순서와파일상태.txt').write_text(readme)

# Remove incidental mixed-language placeholders from internal metadata only.
for j in jobs:
    j.pop('role',None)
    j['name']=j['file_name'].removesuffix('.png')
    j['exists']=(imgdir/j['file_name']).exists()
manifest={'version':'v03','scope':'S01 8초 + S02 3초','generated_count':1,'pending_count':5,'images':jobs,'references':refs,'tool':'built-in image_gen','failure':'usage_limit_reached while generating G04 endpoint','generation_order':['G01','G04','G02','G03','G05','G06']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
cards=[]
byid={j['id']:j for j in jobs}
for jid in ['G01','G02','G03','G04','G05','G06']:
    j=byid[jid];exists=(imgdir/j['file_name']).exists()
    pic='<img src="'+html.escape('02_생성이미지/'+j['file_name'],quote=True)+'">' if exists else '<div class="pending">이미지 미생성<br><small>재개용 프롬프트 준비됨</small></div>'
    cards.append('<article><h2>'+jid+' · '+html.escape(j['ko_role'])+'</h2><p>'+html.escape(j['time'])+' / '+('생성됨' if exists else '한도로 미생성')+'</p>'+pic+'<p>첨부 순서: '+', '.join(j['attachments'])+'</p><details><summary>이미지 프롬프트 EN</summary><pre>'+html.escape(j['prompt_full'])+'</pre></details></article>')
doc='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>S01 S02 제작자료 v03</title><style>body{font-family:-apple-system,sans-serif;background:#edf2ec;color:#183d30;margin:28px;line-height:1.65}main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}article{background:white;padding:18px;border:1px solid #cddccd;border-radius:12px}h2{font-size:17px}img{width:100%;border-radius:8px}.pending{aspect-ratio:9/16;background:#e7ebe7;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#526252;border:1px dashed #9cac9c;border-radius:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3ef;padding:14px;font-size:12px}summary{cursor:pointer}.warn{background:#fff0da;border-left:5px solid #c18c4c;padding:14px;margin-bottom:22px}@media(max-width:800px){main{grid-template-columns:1fr}}</style><h1>S01 지구 접근 → S02 조종석</h1><div class="warn">새 장면 이미지1장 생성. 나머지5장은 이미지 사용 한도로 미생성입니다. 회색 칸은 실제 생성 이미지가 아니며, 각각의 재개용 프롬프트를 열어 볼 수 있습니다.</div><main>'''+''.join(cards)+'</main></html>'
(OUT/'자료미리보기.html').write_text(doc)

generated=list(imgdir.glob('*.png'));assert len(generated)==1
for p in generated:
    with p.open('rb') as f:h=f.read(24)
    assert h[:8]==b'\x89PNG\r\n\x1a\n'
    w,ht=struct.unpack('>II',h[16:24]);assert abs(w/ht-9/16)<.01
assert len(list(pdir.glob('*.txt')))==6
assert all(len(j['attachments'])<=5 for j in jobs)
assert sum(j['exists'] for j in jobs)==1
archive=OUT.parent/'S01_S02_지구접근_레퍼런스와상세프롬프트_v03.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file() and p.name!='build_package.py':z.write(p,Path(OUT.name)/p.relative_to(OUT))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'generated':1,'pending':5,'original_refs':4,'board_reference':1,'image_prompts':6,'video_and_audio_prompts':3,'zip_bytes':archive.stat().st_size,'zip_path':str(archive.resolve())},ensure_ascii=False))
