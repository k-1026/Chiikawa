-- 2027 대구 사투리 축제 안내 페이지 — 시드 데이터
-- schema.sql을 먼저 실행한 뒤 실행하세요.
-- 내용 출처: 안내 페이지 시안(index.html), 03_기획안.md, 00_결정기록 D-01·D-02
--
-- ⚠ 실행하면 표 내용을 모두 지우고 아래 내용으로 다시 채워요.
--   Supabase 화면에서 직접 고친 내용도 사라지니, 고칠 내용은 이 파일에 반영하세요.
-- 일정·장소·혜택은 확정 전 시안이에요. 마스코트 이름(냥이·멍이)과 팀 이름은 임시예요.

begin;

truncate table public.festivals restart identity cascade;

insert into public.festivals
  (id, year, name, theme, tagline, summary, start_date, end_date, venue, hours_note, admission_note, host_name, organizer_name, status)
values
  ('dialect-2027', 2027, '2027 대구 사투리 축제', '타지에서 온 말손님',
   '대구말, 함 붙어 보까?',
   '타지역 2030이 온라인 대구 사투리 능력고사로 먼저 대구말을 배우고, 현장에 말손님으로 와서 대구 토박이와 토론으로 맞붙는 사흘.',
   '2027-08-20', '2027-08-22', '두류공원 일원',
   '금·토 11:00~23:00 / 일 11:00~21:00. 낮 12~16시는 실내 말손님 사랑방 중심 운영(폭염 대응)',
   '무료 · 토론 결승 관람은 사전 예약 + 현장 선착순',
   null, null, 'draft');

insert into public.mascots
  (id, festival_id, name, team, role_label, description, image_path, sort_order)
values
  ('2027-cat', 'dialect-2027', '토박이 냥이', 'local', '토박이 팀 · 길잡이',
   '대구 나고 자란 토박이. 축제 안내랑 대구말 문제는 냥이가 맡아요.', 'assets/cat.png', 1),
  ('2027-dog', 'dialect-2027', '말손님 멍이', 'guest', '말손님 팀 · 여행자',
   '타지에서 놀러 온 손님. 대구말 배워서 토박이랑 한판 붙어 보려고요.', 'assets/dog.png', 2);

insert into public.zones
  (id, festival_id, name, place_name, icon, open_hours, description, map_x, map_y, map_width, map_height, sort_order)
values
  ('2027-music', 'dialect-2027', '말판 무대', '코오롱 야외음악당', '🎤', '금 19:00~21:00 / 토 17:00~21:15 / 일 19:00~20:30',
   '토론 16강(금 19:20) · 8강·4강·결승(토 17:00~21:15) · 폐막 갈라(일 19:00)', 150, 40, 160, 110, 1),
  ('2027-plaza', 'dialect-2027', '10미 포장마차', '2.28 자유광장', '🍢', '금·토 17:00~23:00 / 일 17:00~21:00',
   '대구 10미를 한자리에서. 웹앱으로 대기 번호 확인', 190, 230, 140, 120, 2),
  ('2027-lawn', 'dialect-2027', '대구 로컬 장터', '잔디광장', '🛍', '매일 15:00~22:00',
   '대구 소상공인·로컬 브랜드 플리마켓', 20, 230, 150, 130, 3),
  ('2027-hall', 'dialect-2027', '말손님 사랑방', '실내', '🏠', '매일 11:00~18:00',
   '현장 고사·사진관·냉방 쉼터 · 비 오면 토론 대체 무대', 20, 40, 110, 120, 4);

insert into public.map_pois (festival_id, kind, x, y)
values
  ('dialect-2027', 'stage', 230, 125),
  ('dialect-2027', 'food', 230, 325),
  ('dialect-2027', 'food', 295, 325),
  ('dialect-2027', 'wc', 175, 190),
  ('dialect-2027', 'wc', 180, 380),
  ('dialect-2027', 'wc', 330, 215),
  ('dialect-2027', 'cool', 110, 145),
  ('dialect-2027', 'cool', 140, 250),
  ('dialect-2027', 'med', 300, 190);

insert into public.programs
  (id, festival_id, category, title, description, zone_id, sort_order)
values
  ('2027-debate', 'dialect-2027', 'core', '토박이 vs 말손님 사투리 토론 대회',
   '2인 1팀 16팀 토너먼트. 유머·지역문화 표현력으로 겨루는 예능형 토론. 심사위원 60% + 관객 투표 40%. 결승은 토요일 밤 8시 30분.', '2027-music', 1),
  ('2027-pojangmacha', 'dialect-2027', 'core', '말로 주문하는 10미 포장마차',
   '대구 10미를 한자리에서. 대구말로 주문하면 스탬프 1개(표준어 주문도 똑같이 받아요).', '2027-plaza', 2),
  ('2027-market', 'dialect-2027', 'core', '대구 로컬 장터',
   '대구 소상공인·로컬 브랜드 플리마켓. 오후 3시부터 잔디광장 그늘 구역에서.', '2027-lawn', 3),
  ('2027-sarangbang', 'dialect-2027', 'side', '말손님 사랑방',
   '실내에서 즐기는 현장 고사, 사투리 사진관, 냉방 쉼터.', '2027-hall', 4),
  ('2027-graduation', 'dialect-2027', 'side', '말손님 수료식',
   '토요일 결승 후. 스탬프 3개를 모으면 말손님 수료증을 받아요.', '2027-music', 5),
  ('2027-open-mic', 'dialect-2027', 'side', '한 마디 토론',
   '누구나 1분 오픈 마이크(일 14:00).', '2027-hall', 6);

insert into public.schedule_items
  (festival_id, day, start_time, end_time, zone_id, title, kind, is_highlight, sort_order)
values
  -- 8/20(금)
  ('dialect-2027', '2027-08-20', '11:00', null,    '2027-hall',  '사랑방 개관',                 'program',  false, 1),
  ('dialect-2027', '2027-08-20', '12:00', '16:00', '2027-music', '폭염 · 야외 쉼',              'heat',     false, 2),
  ('dialect-2027', '2027-08-20', '12:00', '16:00', '2027-hall',  '현장 능력고사 · 사진관',      'program',  false, 3),
  ('dialect-2027', '2027-08-20', '15:00', null,    '2027-lawn',  '로컬 장터 개장',              'market',   false, 4),
  ('dialect-2027', '2027-08-20', '17:00', null,    '2027-plaza', '10미 포장마차 오픈',          'food',     false, 5),
  ('dialect-2027', '2027-08-20', '19:00', null,    '2027-music', '개막식',                      'ceremony', false, 6),
  ('dialect-2027', '2027-08-20', '19:20', '21:00', '2027-music', '토론 16강 (8경기)',           'debate',   true,  7),
  ('dialect-2027', '2027-08-20', '23:00', null,    null,         '마감',                        'close',    false, 8),
  -- 8/21(토)
  ('dialect-2027', '2027-08-21', '11:00', null,    '2027-hall',  '현장 능력고사 · 사진관',      'program',  false, 1),
  ('dialect-2027', '2027-08-21', '12:00', '16:00', '2027-music', '폭염 · 야외 쉼',              'heat',     false, 2),
  ('dialect-2027', '2027-08-21', '12:00', '16:00', '2027-hall',  '억양 맞히기 게임',            'program',  false, 3),
  ('dialect-2027', '2027-08-21', '17:00', '18:00', '2027-music', '토론 8강 (4경기)',            'debate',   false, 4),
  ('dialect-2027', '2027-08-21', '19:30', '20:00', '2027-music', '토론 4강 (2경기)',            'debate',   false, 5),
  ('dialect-2027', '2027-08-21', '20:30', '21:15', '2027-music', '결승',                        'debate',   true,  6),
  ('dialect-2027', '2027-08-21', '21:15', null,    '2027-music', '시상 · 말손님 수료식',        'ceremony', false, 7),
  ('dialect-2027', '2027-08-21', '23:00', null,    null,         '마감 · 야간 셔틀',            'close',    false, 8),
  -- 8/22(일)
  ('dialect-2027', '2027-08-22', '11:00', null,    '2027-hall',  '원조가게 스탬프투어 출발',    'program',  false, 1),
  ('dialect-2027', '2027-08-22', '12:00', '16:00', '2027-music', '폭염 · 야외 쉼',              'heat',     false, 2),
  ('dialect-2027', '2027-08-22', '12:00', '16:00', '2027-hall',  '사투리 사진관',               'program',  false, 3),
  ('dialect-2027', '2027-08-22', '14:00', null,    '2027-hall',  '한 마디 토론 (오픈 마이크)',  'program',  false, 4),
  ('dialect-2027', '2027-08-22', '17:00', null,    '2027-plaza', '포장마차 오픈',               'food',     false, 5),
  ('dialect-2027', '2027-08-22', '19:00', '20:30', '2027-music', '폐막 갈라 · 명장면 다시 보기', 'ceremony', true,  6),
  ('dialect-2027', '2027-08-22', '21:00', null,    null,         '폐막',                        'close',    false, 7);

insert into public.debate_topics
  (id, festival_id, title, pro_argument, con_argument, difficulty, minutes, audience_mode, is_final, sort_order)
values
  ('2027-t1', 'dialect-2027', '처음 만난 사이 "밥 뭇나?"는 인사다 vs 진짜 질문이다',
   '대답 안 기다리는 안부 인사', '안 먹었다 하면 진짜 밥 사 준다', '하', 12, '경험담 QR 투표', false, 1),
  ('2027-t2', 'dialect-2027', '야끼우동, 이름만 우동이지 볶음면이다 vs 그래도 우동이다',
   '국물이 없다', '면이 우동면이다', '하', 12, '현장 시식 후 투표', false, 2),
  ('2027-t3', 'dialect-2027', '납작만두, 간장 찍어야 원조다 vs 떡볶이 국물이 정답이다',
   '원조 방식', '요즘 먹는 방식', '하', 12, '포장마차 연계 투표', false, 3),
  ('2027-t4', 'dialect-2027', '"됐나?" "됐다." 두 마디면 대화 끝난다 vs 안 된다',
   '짧고 정확하다', '타지 사람은 뜻을 모른다', '중', 12, '관객이 상황극 제시', false, 4),
  ('2027-t5', 'dialect-2027', '첫 대구 여행, 막창 먼저다 vs 뭉티기 먼저다',
   '입문용', '대구에만 있는 맛', '중', 12, '10미 스탬프 연계', false, 5),
  ('2027-t6', 'dialect-2027', '대구말 배울 때, 억양이 먼저다 vs 단어가 먼저다',
   '억양이 뜻을 바꾼다', '단어를 알아야 대화가 된다', '상', 15, '관객 투표 40%', true, 6);

insert into public.debate_teams (id, festival_id, side, display_name, sort_order)
values
  ('2027-local-a', 'dialect-2027', 'local', '토박이 A', 1),
  ('2027-guest-a', 'dialect-2027', 'guest', '말손님 A', 2),
  ('2027-local-b', 'dialect-2027', 'local', '토박이 B', 3),
  ('2027-guest-b', 'dialect-2027', 'guest', '말손님 B', 4),
  ('2027-local-c', 'dialect-2027', 'local', '토박이 C', 5),
  ('2027-guest-c', 'dialect-2027', 'guest', '말손님 C', 6),
  ('2027-local-d', 'dialect-2027', 'local', '토박이 D', 7),
  ('2027-guest-d', 'dialect-2027', 'guest', '말손님 D', 8),
  ('2027-local-e', 'dialect-2027', 'local', '토박이 E', 9),
  ('2027-guest-e', 'dialect-2027', 'guest', '말손님 E', 10),
  ('2027-local-f', 'dialect-2027', 'local', '토박이 F', 11),
  ('2027-guest-f', 'dialect-2027', 'guest', '말손님 F', 12),
  ('2027-local-g', 'dialect-2027', 'local', '토박이 G', 13),
  ('2027-guest-g', 'dialect-2027', 'guest', '말손님 G', 14),
  ('2027-local-h', 'dialect-2027', 'local', '토박이 H', 15),
  ('2027-guest-h', 'dialect-2027', 'guest', '말손님 H', 16);

-- 8강부터는 16강 결과가 나와야 정해지므로 팀을 비워 둬요.
insert into public.debate_matches
  (id, festival_id, round, match_no, match_day, team_a_id, team_b_id, winner_team_id, topic_id)
values
  ('2027-r16-1', 'dialect-2027', '16강', 1, '2027-08-20', '2027-local-a', '2027-guest-a', null, null),
  ('2027-r16-2', 'dialect-2027', '16강', 2, '2027-08-20', '2027-local-b', '2027-guest-b', null, null),
  ('2027-r16-3', 'dialect-2027', '16강', 3, '2027-08-20', '2027-local-c', '2027-guest-c', null, null),
  ('2027-r16-4', 'dialect-2027', '16강', 4, '2027-08-20', '2027-local-d', '2027-guest-d', null, null),
  ('2027-r16-5', 'dialect-2027', '16강', 5, '2027-08-20', '2027-local-e', '2027-guest-e', null, null),
  ('2027-r16-6', 'dialect-2027', '16강', 6, '2027-08-20', '2027-local-f', '2027-guest-f', null, null),
  ('2027-r16-7', 'dialect-2027', '16강', 7, '2027-08-20', '2027-local-g', '2027-guest-g', null, null),
  ('2027-r16-8', 'dialect-2027', '16강', 8, '2027-08-20', '2027-local-h', '2027-guest-h', null, null),
  ('2027-qf-1', 'dialect-2027', '8강', 1, '2027-08-21', null, null, null, null),
  ('2027-qf-2', 'dialect-2027', '8강', 2, '2027-08-21', null, null, null, null),
  ('2027-qf-3', 'dialect-2027', '8강', 3, '2027-08-21', null, null, null, null),
  ('2027-qf-4', 'dialect-2027', '8강', 4, '2027-08-21', null, null, null, null),
  ('2027-sf-1', 'dialect-2027', '4강', 1, '2027-08-21', null, null, null, null),
  ('2027-sf-2', 'dialect-2027', '4강', 2, '2027-08-21', null, null, null, null),
  ('2027-final', 'dialect-2027', '결승', 1, '2027-08-21', null, null, null, '2027-t6');

insert into public.menu_items (festival_id, name, order_phrase, sort_order)
values
  ('dialect-2027', '따로국밥', '따로국밥 한 그릇 주이소', 1),
  ('dialect-2027', '막창구이', '막창 2인분 주이소', 2),
  ('dialect-2027', '뭉티기', '뭉티기 한 접시 주이소', 3),
  ('dialect-2027', '동인동찜갈비', '찜갈비 맵게 해 주이소', 4),
  ('dialect-2027', '논메기매운탕', '매운탕 하나 주이소', 5),
  ('dialect-2027', '복어불고기', '복불고기 하나 주이소', 6),
  ('dialect-2027', '누른국수', '누른국수 두 개 주이소', 7),
  ('dialect-2027', '무침회', '무침회 하나 주이소', 8),
  ('dialect-2027', '야끼우동', '야끼우동 억수로 맵게요', 9),
  ('dialect-2027', '납작만두', '납작만두 하나 주이소', 10);

insert into public.benefits (id, festival_id, title, amount_won, summary, steps, sort_order)
values
  ('2027-stay', 'dialect-2027', '하룻밤 묵고 가면 2만 원', 20000,
   '8/20(금)·8/21(토) 대구 숙박 영수증을 앱에서 인증하면 대구로페이 2만 원 + 결승 관람석 우선 입장.',
   array['현장 체크인 후 숙박 인증 선택', '숙소 영수증 촬영 (결제 정보는 가려 주세요)', '확인 후 대구로페이 지급 · 이미지는 즉시 삭제'], 1),
  ('2027-tour', 'dialect-2027', '원조가게 스탬프투어', 10000,
   '포장마차 부스의 원조가게 카드 QR로 시내 원조 가게를 찾아가 보세요. 3곳 들르면 대구로페이 1만 원.',
   array['포장마차 부스에서 원조가게 카드 QR 스캔', '시내 원조가게 3곳 방문', '스탬프 3개를 모아 대구로페이 받기'], 2);

insert into public.quiz_questions (id, festival_id, prompt_word, question, sort_order)
values
  ('2027-q1', 'dialect-2027', '단디 해라', '무슨 뜻일까요?', 1),
  ('2027-q2', 'dialect-2027', '정구지', '무슨 채소일까요?', 2),
  ('2027-q3', 'dialect-2027', '억수로', '어떤 뜻일까요?', 3),
  ('2027-q4', 'dialect-2027', '마카 다 온나', '누구보고 오라는 걸까요?', 4),
  ('2027-q5', 'dialect-2027', '파이다', '어떤 상황에서 쓸까요?', 5);

insert into public.quiz_options (question_id, label, is_correct, sort_order)
values
  ('2027-q1', '단단하게 묶어라', false, 1),
  ('2027-q1', '확실히·똑바로 해라', true, 2),
  ('2027-q1', '빨리 해라', false, 3),
  ('2027-q2', '부추', true, 1),
  ('2027-q2', '시금치', false, 2),
  ('2027-q2', '깻잎', false, 3),
  ('2027-q3', '비가 많이', false, 1),
  ('2027-q3', '아주·매우', true, 2),
  ('2027-q3', '억지로', false, 3),
  ('2027-q4', '마카라는 사람', false, 1),
  ('2027-q4', '모두 다', true, 2),
  ('2027-q4', '말 타고', false, 3),
  ('2027-q5', '파이를 먹을 때', false, 1),
  ('2027-q5', '별로라서 아쉬울 때', true, 2),
  ('2027-q5', '기분이 좋을 때', false, 3);

insert into public.quiz_grades (id, festival_id, min_score, title, message, image_path)
values
  ('2027-grade-local', 'dialect-2027', 5, '토박이', '냥이랑 같은 토박이 급이네예! 토박이 팀으로 나가도 되겠는데요?', 'assets/cat.png'),
  ('2027-grade-half', 'dialect-2027', 3, '반쯤 대구 사람', '이 정도면 대구 와서 길 잃을 일은 없겠네예.', 'assets/pair.png'),
  ('2027-grade-guest', 'dialect-2027', 0, '귀한 말손님', '멍이랑 같은 말손님이네예. 처음엔 다 그래요, 현장 와서 배워 가이소!', 'assets/dog.png');

insert into public.dialect_rules (festival_id, standard_terms, dialect_text, sort_order)
values
  ('dialect-2027', array['정말', '진짜', '매우', '아주', '엄청'], '억수로', 1),
  ('dialect-2027', array['똑바로', '확실히', '제대로'], '단디', 2),
  ('dialect-2027', array['맛있다'], '맛있데이', 3),
  ('dialect-2027', array['모두', '전부'], '마카', 4),
  ('dialect-2027', array['왜 그래', '왜 이래'], '와 이카노', 5),
  ('dialect-2027', array['별로다', '별로야'], '파이다', 6),
  ('dialect-2027', array['부추'], '정구지', 7),
  ('dialect-2027', array['밥 먹었어'], '밥 뭇나', 8),
  ('dialect-2027', array['됐어?'], '됐나?', 9),
  ('dialect-2027', array['주세요'], '주이소', 10),
  ('dialect-2027', array['와라'], '온나', 11),
  ('dialect-2027', array['나랑'], '내캉', 12),
  ('dialect-2027', array['아니에요'], '어데예', 13),
  ('dialect-2027', array['뭐 해'], '머 하노', 14);

insert into public.faq_entries (festival_id, keywords, answer, sort_order)
values
  ('dialect-2027', array['시간', '언제', '몇 시', '일정'],
   '8/20(금)~22(일)이고, 금·토는 11시~23시, 일요일은 21시까지예요. 토론 결승은 토요일 저녁 8시 30분! 시간표 탭에서 자세히 볼 수 있어요.', 1),
  ('dialect-2027', array['결승', '토론', '대진', '참가', '신청', '예선'],
   '토론 예선은 6/1~7/6 영상 접수예요(2인 1팀). 토박이 팀은 대구·경북 거주, 말손님 팀은 그 외 지역이에요. 결승은 토요일 20:30 말판 무대.', 2),
  ('dialect-2027', array['숙박', '호텔', '자고', '1박', '묵'],
   '8/20·21 대구 숙박 영수증을 인증하면 대구로페이 2만 원이랑 결승 관람석 우선 입장! 행사개요 → 숙박·혜택에서 볼 수 있어요.', 3),
  ('dialect-2027', array['먹', '포장마차', '10미', '막창', '음식'],
   '2.28 자유광장 10미 포장마차는 17시부터예요. 대구말로 주문하면 스탬프 1개! 웹앱에서 대기 번호도 확인돼요.', 4),
  ('dialect-2027', array['덥', '폭염', '더위', '쉼터', '에어컨'],
   '낮 12~16시는 실내 말손님 사랑방에서 노이소. 냉방 쉼터 위치는 지도 탭 ❄️ 표시예요. 물 자주 드시고예!', 5),
  ('dialect-2027', array['비 오', '비오', '비가', '우천'],
   '비 오면 토론은 실내 사랑방 무대로 옮기고, 결승은 일요일 19시 예비일이 있어요. (시안 기준)', 6),
  ('dialect-2027', array['화장실', '주차', '교통', '셔틀', '지하철'],
   '화장실은 지도 탭 🚻 필터로 볼 수 있어요. 교통·주차·셔틀 노선은 아직 확정 전이에요(시안).', 7),
  ('dialect-2027', array['고사', '퀴즈', '시험'],
   '능력고사 탭에서 5문제 맛보기 고사를 풀 수 있어요. 등급이 토박이 / 반쯤 대구 사람 / 귀한 말손님으로 나와요.', 8),
  ('dialect-2027', array['스탬프', '수료', '원조'],
   '스탬프 3개 모으면 말손님 수료증! 일요일엔 원조가게 3곳 들르면 대구로페이 1만 원이에요.', 9);

commit;
