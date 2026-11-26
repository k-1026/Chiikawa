# -*- coding: utf-8 -*-
"""kimseunghee_01_방언특성변이.md 원문 대조 데이터 패키지 생성기.

- 모든 ID는 이 파일에 고정(재실행해도 같음). kb 스키마를 다른 패키지와 함께 쓰므로 ID에 K01 을 붙인다.
- 청크 본문은 실행할 때마다 원문 파일에서 글자 그대로 있는지 다시 대조한다(공백만 무시, 목록형은 줄마다).
- 언론 기사 HTML은 저장소에 넣지 않는다. --news-dir 로 스냅숏 폴더를 주면 기사 발췌도 대조한다.

사용:
  python -I tools/build_dataset.py
  python -I tools/build_dataset.py --news-dir <기사 스냅숏 폴더>
"""
import argparse
import csv
import hashlib
import html
import json
import os
import re
import sys

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PKG, "data")
ACCESSED = "2026-11-26"
VERSION = "v1"

MD_ID = "MD-K01"
MD_PATH = "local 리서치/kimseunghee_01_방언특성변이.md"
MD_LAST_COMMIT = "5f61dc486f15fe7db07c025d9e9d065fcc32dda0"
MD_MAIN_HEAD = "4e59da85f1885e108881d939448706f18b049a90"
MD_BLOB = "c05200d409356beb086acf2a686f40641a43f121"
MD_SOURCE_ID = "SRC-K01-MD"
MD_TITLE = "01. 대구 방언의 언어적 특성 및 지역별 변이"
MD_WRITTEN = "2026-10-31"
MD_VERSION = "사투리_v02_V4"
MD_NOTES = "written_date 는 문서의 '자료 기준일'. 2026-11-26 main 기준. 원본은 originals/SRC-K01-MD.md"

SOURCES = [
    dict(id="SRC-K01-MD", title="01. 대구 방언의 언어적 특성 및 지역별 변이 (kimseunghee_01_방언특성변이.md)",
         publisher="팀 내부(작성자 kimseunghee)", doc_type="user_authored", grade="U", url="", attach="",
         pub="2026-10-31", pub_basis="문서 '자료 기준일: 2026-10-31'", period="", ver=f"git blob {MD_BLOB}",
         retrieval="git show origin/main:<path>", ostatus="stored", snapshot="", approval="internal", rights="팀 내부 문서",
         notes="사용자 작성 원본. 교차검증 메모·자산 판정·부족한 점의 원본으로만 사용"),
    dict(id="SRC-K01-NKLIFE1998", title="동남 방언", publisher="국립국어원 『새국어생활』(필자 李相揆, 경북대학교 국어국문학과)",
         doc_type="official_web", grade="S", url="https://www.korean.go.kr/nkview/nklife/1998_4/8-6.html", attach="",
         pub="", pub_basis="본문에 발행일 표기 없음(URL 경로 1998_4)", period="", ver="확인일 현재 웹페이지", retrieval="curl",
         ostatus="stored", snapshot="", approval="approved", rights="공공기관 웹페이지",
         notes="본문의 서재극 인용 표기는 원문 그대로 '서재극(19620)'(오기로 보임, MD는 1962로 적음)"),
    dict(id="SRC-K01-KU-125264", title="대구 방언 화자의 /ㅡ/와 /ㅓ/ 지각에 관한 연구", publisher="고려대학교 학술 저장소(원 게재: 한국어학회 『한국어학』 41권)",
         doc_type="official_web", grade="A", url="https://scholar.korea.ac.kr/handle/2021.sw.korea/125264?mode=full", attach="",
         pub="2008", pub_basis="저장소 '발행일 2008'(월·일 없음)", period="", ver="한국어학 41, pp.381-402", retrieval="curl",
         ostatus="stored", snapshot="", approval="approved", rights="대학 학술 저장소 서지·초록 페이지",
         notes="저자 장혜진·차재은·신지영. 초록은 영문만 확인"),
    dict(id="SRC-K01-KS-2026", title="경북 방언 어두 폐쇄음 음향 특징의 세대별 변화 양상 연구", publisher="KoreaScience(원 게재: 한국음성학회 『말소리와 음성과학』 18권 2호)",
         doc_type="official_web", grade="A", url="https://www.koreascience.kr/article/JAKO202622461389591.page", attach="",
         pub="2026-06-30", pub_basis="'Published : 2026.06.30'", period="", ver="Vol.18 Issue 2, pp.13-25", retrieval="curl",
         ostatus="stored", snapshot="", approval="approved", rights="학술 서지·초록 페이지",
         notes="저자 서민정(류코쿠대학교 경영학부). 초록에 '대구' 없음. 화자 수는 초록에 없음"),
    dict(id="SRC-K01-NEWS-KB-20240715", title="민경탁 시인의 \"다음 김천 장날 또 바여\"(이상규의 詩와 方言이야기)", publisher="경북매일",
         doc_type="news", grade="B", url="https://kbmaeil.com/article/202407150399698", attach="", pub="2024-07-16",
         pub_basis="기사 '등록일 2024-07-15 18:29, 게재일 2024-07-16'", period="", ver="확인일 현재 기사 페이지", retrieval="curl",
         ostatus="url_only_copyright", snapshot="kb_20240715.html",
         snapshot_sha="a831b9b9902d067f6a7b72b6ce1ca8d12758706fac3907db50110e9e9cf2ce27", approval="reference_only",
         rights="언론사 저작물 — 원문 재배포 안 함, URL과 짧은 발췌만 기록",
         notes="필자 이상규(연재 칼럼). MD는 ③ 비공식(칼럼)으로 분류"),
]

C = []


def ch(cid, sid, sec, blk, btype, itype, title, text, ctx, applies="", cond="", period="", loc="", rel=()):
    C.append(dict(chunk_id=cid, source_id=sid, sec=sec, blk=blk, btype=btype, info_type=itype, short_title=title,
                  text_original=text, search_context=ctx, applies_to=applies, condition_text=cond,
                  period_text=period, locator=loc, related=list(rel)))


S98 = "SRC-K01-NKLIFE1998"
ch("CHK-K01-NK98-001", S98, "동남 방언", "머리", "meta", "fact", "글 제목·필자", "동남 방언\n李相揆 경북대학교 국어국문학과 교수",
   "새국어생활 '동남 방언', 필자 이상규(李相揆, 경북대 교수). 원문의 '李'는 호환 한자(U+F9E1) 그대로 둠. 발행 연도는 본문에 없음", applies="경상 방언", loc="새국어생활 1998_4/8-6 머리")
ch("CHK-K01-NK98-002", S98, "동남 방언", "방언 분화 문단", "sentence", "fact", "낙동강 경계 방언 분화",
   "김해-밀양-창녕-의령-합천-고령-성주-칠곡-선산-상주로 이어지는 낙동강을 경계로 하여 동과 서로 구분되고 있어 자연 환경과 방언 분화의 상관 관계를 알 수 있다.",
   "경상 방언이 낙동강을 경계로 동·서로 나뉨", applies="경상 방언", loc="본문", rel=("CHK-K01-NK98-003",))
ch("CHK-K01-NK98-003", S98, "동남 방언", "음운 문단", "sentence", "fact", "ㅅ/ㅆ 비변별 지역",
   "청도, 경산, 달성, 칠곡, 고령,  군위, 영천, 경주, 청송, 포항, 영덕 지역, 곧 낙동강의 동쪽 지역으로 'ㅅ'과 'ㅆ'이 비변별적이다.",
   "대구를 중심으로 한 낙동강 동쪽 지역은 ㅅ·ㅆ을 구별하지 않음(문장 앞부분 '대구를 중심으로 하여'와 이어짐)",
   applies="대구·경북 동남부", loc="본문(각주 5 앞)", rel=("CHK-K01-NK98-002", "CHK-K01-NK98-004"))
ch("CHK-K01-NK98-004", S98, "동남 방언", "각주 5", "footnote", "fact", "서재극 ㅅ/ㅆ 구획선(각주)",
   "서재극(19620), ｢경북 방언 연구｣,『어문학』 8호. p. 73. 에서 /ㅅ/ : /ㅆ/ 변별 방언권을 의성, 안동, 영양, 청송을 연결하는 지역과 대구, 경산, 영천, 경주를 연결하는 구획선으로 끊고 있다.",
   "이상규 글의 각주 5가 인용한 서재극 『어문학』 8호의 ㅅ/ㅆ 구획선. 연도 '19620'은 원문 오기(1962로 읽힘)",
   applies="경북", loc="각주 5", rel=("CHK-K01-NK98-003",))
ch("CHK-K01-NK98-005", S98, "동남 방언", "어미 문단", "sentence", "fact", "하소체 어미 '-는구마'",
   "'집에 가는 구마', '집에 가느마'라고 하여 '-는구마' 또는 '-느마'를 하소체 어미로 특별히 쓴다.",
   "해당 지역의 하소체 어미 '-는구마/-느마'(앞 문장의 지역 지시는 원문 문맥 참고)", applies="대구 지역 말", loc="본문 어미 설명")
SKU = "SRC-K01-KU-125264"
ch("CHK-K01-KU-001", SKU, "서지", "서지 정보", "meta", "fact", "논문 서지",
   "장혜진;차재은;신지영\n발행일\n2008\n저널명\n한국어학\n권\n41\n페이지\n381 ~ 402\n출판사\n한국어학회",
   "한국어학 41권 381~402쪽, 2008, 한국어학회", applies="학술", loc="고려대 학술 저장소 상세", rel=("CHK-K01-KU-002",))
ch("CHK-K01-KU-002", SKU, "초록(영문)", "결과 문단", "sentence", "fact", "젊은 층이 /ɯ/·/ʌ/를 더 잘 지각",
   "The younger subjects perceive these vowels better than the older subjects.",
   "대구 방언 화자 중 젊은 층(20대)이 나이 든 층(40대 이상)보다 /ㅡ/·/ㅓ/를 더 잘 지각", applies="대구 방언 화자",
   loc="초록(영문)", rel=("CHK-K01-KU-001", "CHK-K01-KU-003"))
ch("CHK-K01-KU-003", SKU, "초록(영문)", "실험 문단", "sentence", "procedure", "실험 I: 인명 지각",
   "Experiment I is a perception test on human names.", "실험 I은 사람 이름 자극", applies="대구 방언 화자", loc="초록(영문)",
   rel=("CHK-K01-KU-002",))
SKS = "SRC-K01-KS-2026"
ch("CHK-K01-KS-001", SKS, "서지", "서지 정보", "meta", "fact", "논문 서지",
   "Phonetics and Speech Sciences(말소리와 음성과학)\nVolume 18\nIssue 2/Pages.13-25/2026\nPublished : 2026.06.30",
   "말소리와 음성과학 18권 2호 13~25쪽, 2026-06-30", applies="학술", loc="KoreaScience 상세", rel=("CHK-K01-KS-002",))
ch("CHK-K01-KS-002", SKS, "초록(영문)", "결과 문단", "sentence", "fact", "젊은 세대일수록 평음 VOT 증가",
   "The results show that VOT values for lenis stops increase in younger generations, leading to a gradual convergence between the VOT of lenis and aspirated stops.",
   "경북 방언 1950~2000년대생 비교: 젊을수록 평음 VOT가 길어져 격음과 가까워짐. 초록에 '대구' 명시 없음",
   applies="경북 방언 화자", loc="초록(영문)", rel=("CHK-K01-KS-001",))
ch("CHK-K01-KB0715-001", "SRC-K01-NEWS-KB-20240715", "기사 본문", "권역 문단", "sentence", "fact", "경북 방언 3개 권역",
   "의문형어미를 중심으로 3개 권역으로 나누어진다.", "이상규 칼럼: 경북 방언은 의문형 어미 기준 3개 권역", applies="경북",
   loc="본문", rel=("CHK-K01-KB0715-002",))
ch("CHK-K01-KB0715-002", "SRC-K01-NEWS-KB-20240715", "기사 본문", "권역 문단", "sentence", "fact", "권역별 의문형 어미",
   "안동을 중심으로 경북북부권은 ‘-니껴’권이고 대구경주권은 ‘-능교’(-능게)권이다. 낙동강 우측 선산에서 김천, 의성 일부지역은 ‘-여’권으로 나누어진다.",
   "북부 -니껴, 대구·경주 -능교(-능게), 선산~김천·의성 일부 -여", applies="경북", loc="본문", rel=("CHK-K01-KB0715-001",))

M = "SRC-K01-MD"


def mch(cid, sec, itype, title, text, ctx, rel=()):
    ch(cid, M, sec, sec, "md_text", itype, title, text, ctx, applies="사투리 조사 01(언어 특성)", loc=f"MD {sec}", rel=rel)


mch("CHK-K01-MD-001", "머리말", "rule", "기간 예외 적용", "기간 예외: 언어적 특성 설명용 과거 연구는 허용(지침 v2 §1)",
    "작성자 규칙: 언어 특성 과거 연구는 2022년 이전이어도 사용")
mch("CHK-K01-MD-002", "2. 교차검증·불일치", "fact", "대구 어미 표기 차이 메모",
    "01-01은 `-는구마`(하소체 어미), 01-07은 `-능교`(대구·경주권 의문형)로 표기", "작성자 교차검증 메모: 두 자료의 어미 범주가 다를 수 있음")
mch("CHK-K01-MD-003", "2. 교차검증·불일치", "fact", "세대 간 모음 비교 보류",
    "01-03(2008, 대구 20대가 더 구별)과 01-06(2026, 경북 젊은층은 서울형으로 수렴)은 대상 변수가 달라 비교 불가",
    "작성자 판단: 변수가 달라 비교 보류")
mch("CHK-K01-MD-004", "3. 자산/정보 판정", "fact", "언어 특성 자료는 정보",
    "01-01~01-07 모두 **정보** (활용성 수치 없음, 반복·운영 개념에 해당하지 않음)", "작성자 판정")
mch("CHK-K01-MD-005", "4. 부족한 점", "fact", "부족한 자료 목록",
    "대구 시내 구·군별 변이 자료", "작성자: 미확보 자료")

CLAIMS, LINKS = [], []


def cl(cid, sec, row, ctype, text, grade, cited, links):
    CLAIMS.append(dict(claim_id=cid, md_section=sec, row_key=row, claim_type=ctype, claim_text=text,
                       md_stated_grade=grade, md_stated_source=cited))
    for l in links:
        LINKS.append((cid,) + tuple(l))


ORI, ALT, USR, UNV = "original_confirmed", "alternative_official", "user_authored", "unverifiable"
T1 = "1. 계통·방언권"

# ---- 추가 원문(Aside가 찾고 curl로 다시 받아 대조) + Aside 보고만 있는 원문
SOURCES += [
    dict(id="SRC-K01-NKLIFE1998-TOC", title="새국어생활 1998년 4호 목차", publisher="국립국어원", doc_type="official_web", grade="S",
         url="https://www.korean.go.kr/nkview/nklife/1998_4.htm", attach="", pub="", pub_basis="목차 페이지에 연도 표기 없음",
         period="", ver="확인일 현재 웹페이지", retrieval="aside + curl", ostatus="stored", snapshot="", approval="approved",
         rights="공공기관 웹페이지", notes="'동남 방언 … 李相揆' 항목 확인. Aside 보고: 국립국어원 총목록에 '제8권 제4호(1998. 겨울)'"),
    dict(id="SRC-K01-NKLIFE2005", title="경상북도 방언 이야기(새국어생활 제15권 제4호, 2005 겨울, 123~129쪽)", publisher="국립국어원(필자 이상규)",
         doc_type="official_attachment", grade="S", url="https://www.korean.go.kr/nkview/nklife/2005_4/2005_0410.pdf",
         attach="https://www.korean.go.kr/nkview/nklife/2005_4/2005_0410.pdf", pub="", pub_basis="Aside: '제15권 제4호(2005년 겨울)'",
         period="", ver="", retrieval="aside", ostatus="not_retrieved", snapshot="", approval="pending", rights="",
         notes="PDF를 Aside만 읽음(미보관). HTML판 없음(Aside)"),
    dict(id="SRC-K01-RISS-0104", title="한국어 방언의 문말 억양 연구 : 대구 방언과 광주 방언의 문말 억양 비교", publisher="RISS(한국교육학술정보원) — 경북대학교 석사학위논문",
         doc_type="official_web", grade="A",
         url="https://www.riss.kr/search/detail/DetailView.do?p_mat_type=be54d9b8bc7cdb09&control_no=09820c915d07b178", attach="",
         pub="2000", pub_basis="RISS '발행사항 大邱 : 慶北大學校, 2000'", period="", ver="석사학위논문", retrieval="aside + curl",
         ostatus="stored", snapshot="", approval="approved", rights="학술 서지 페이지", notes="저자 이승현. 전공란은 RISS 표시 '현대문학전공' 그대로"),
    dict(id="SRC-K01-RISS-0105", title="대구 방언 20대 화자의 단모음 실현 양상에 나타난 표준어 지향성의 성별적 차이", publisher="RISS(한국교육학술정보원) — 한국어학회 『한국어학』 36",
         doc_type="official_web", grade="A",
         url="https://www.riss.kr/search/detail/DetailView.do?p_mat_type=1a0202e37d52c72d&control_no=24674fb5773c4f1ae9810257f7042666",
         attach="", pub="2007", pub_basis="RISS 'Vol.36 [2007]'(KCI 2007.08, Aside)", period="", ver="한국어학 36, pp.289-314",
         retrieval="aside + curl", ostatus="stored", snapshot="", approval="approved", rights="학술 서지 페이지", notes="저자 장혜진·신지영"),
    dict(id="SRC-K01-KS-2026-PDF", title="경북 방언 어두 폐쇄음 음향 특징의 세대별 변화 양상 연구(본문 PDF)", publisher="한국음성학회 『말소리와 음성과학』 18(2)",
         doc_type="official_attachment", grade="A", url="https://doi.org/10.13064/KSSS.2026.18.2.013", attach="", pub="2026-06-30",
         pub_basis="Aside: PDF 표지 '2026. 6. 30.'", period="", ver="", retrieval="aside", ostatus="not_retrieved", snapshot="",
         approval="pending", rights="", notes="본문을 Aside만 읽음(미보관): 화자 50명(여성), '대구시 및 경상북도에서 태어나 자란' 화자"),
    dict(id="SRC-K01-KCI-SEARCH", title="KCI 논문검색 결과(2026-11-26): '대구 방언'·'대구 지역어', 2022~2026", publisher="한국연구재단 KCI",
         doc_type="statistics", grade="A", url="https://www.kci.go.kr/kciportal/po/search/poArtiSearList.kci", attach="", pub="",
         pub_basis="검색 결과(발행일 없음)", period="2022~2026", ver="", retrieval="aside", ostatus="not_retrieved", snapshot="",
         approval="pending", rights="", notes="검색 결과 페이지는 Aside만 확인(미보관). 개별 논문 원문은 미대조"),
]

ch("CHK-K01-TOC-001", "SRC-K01-NKLIFE1998-TOC", "목차", "특집·방언", "list", "fact", "목차의 '동남 방언' 필자",
   "동남 방언\n李相揆", "새국어생활 1998_4 목차의 '동남 방언 … 李相揆'", applies="학술", loc="1998_4 목차")
ch("CHK-K01-NK05-001", "SRC-K01-NKLIFE2005", "본문", "말씨권 문단", "sentence", "fact", "의문형 종결 어미 기준 3가지 말씨",
   "의문형 종결 어미의 사용 양상에 따라 대개 3가지 말씨로",
   "Aside 인용: 안동 중심 북동부 '하니껴체', 경주 중심 남동부 '하능교체', 상주·김천 중심 서북부 '해여체'. 대구는 따로 언급 없음",
   applies="경북", loc="새국어생활 2005-4, 123~129쪽(쪽 미상)")
ch("CHK-K01-RISS04-001", "SRC-K01-RISS-0104", "서지", "서지 정보", "meta", "fact", "학위논문 서지",
   "한국어 방언의 문말 억양 연구 : 대구 방언과 광주 방언의 문말 억양 비교\n이승현\n大邱 : 慶北大學校, 2000\n학위논문(석사) --경북대학교 대학원,국어국문학과 현대문학전공, 2000",
   "이승현 2000 경북대 석사. 제목은 '문말 억양'(MD의 '문미억양' 아님)", applies="대구·광주 방언", loc="RISS 상세")
ch("CHK-K01-RISS05-001", "SRC-K01-RISS-0105", "서지", "서지 정보", "meta", "fact", "논문 서지",
   "대구 방언 20대 화자의 단모음 실현 양상에 나타난 표준어 지향성의 성별적 차이\nVol.36No.-[2007]\n289-314(26쪽)",
   "장혜진·신지영, 한국어학 36, 289~314쪽, 2007", applies="대구 방언 20대", loc="RISS 상세")
ch("CHK-K01-KSPDF-001", "SRC-K01-KS-2026-PDF", "본문", "연구 대상", "sentence", "condition", "화자 출신 지역",
   "대구시 및 경상북도에서 태어나 자란", "Aside 인용: 경북 방언 여성 모어 화자 50명(1950~2000년대생), 대구 출신 수는 미기재",
   applies="경북 방언 화자(대구 포함)", loc="본문 연구 방법(쪽 미상)")
ch("CHK-K01-KCI-001", "SRC-K01-KCI-SEARCH", "검색 결과", "2022~2026 음운·억양·어휘", "list", "fact", "2022~2026 대구 방언 음운·억양 관련 논문(Aside)",
   "대구 방언 /ㅡ/와 /ㅓ/의 세대별 음운 지각 및 산출 양상\nTonology of Daegu Korean and an OT solution\n韓国語大邱･慶州方言の複合名詞アクセント\n지역민의 방언 의식에 기반한 대표 방언 어휘 선정을 위한 시론-대구광역시의 사례를 중심으로-",
   "Aside가 KCI에서 찾은 2022~2026 논문 제목(박지윤 2022 언어연구 38(2), 손재현 2022·2023, 이재섭·강민지 2024 공공언어학 12). 개별 논문은 미대조",
   applies="대구 방언", period="2022~2026", loc="KCI 검색 결과")
ASIDE_ONLY = {"CHK-K01-NK05-001", "CHK-K01-KSPDF-001", "CHK-K01-KCI-001"}

# ---- 주장
cl("CLM-K01-H-01", "머리말", "기간 예외", "rule", "언어적 특성 설명용 과거 연구는 기간 예외로 허용", "", "지침 v2 §1",
   [("SRC-K01-MD", "CHK-K01-MD-001", USR, "interpretation", "작성자 규칙(지침 v2 원문은 이 패키지에서 대조하지 않음)")])
cl("CLM-K01-0101-01", T1, "01-01", "fact", "동남 방언(국립국어원 새국어생활, 이상규): 경북·경남 방언이 낙동강을 경계로 나뉨", "①", "새국어생활 1998-4",
   [("SRC-K01-NKLIFE1998", "CHK-K01-NK98-002", ORI, "match", ""), ("SRC-K01-NKLIFE1998", "CHK-K01-NK98-001", ORI, "match", "필자 이상규 확인")])
cl("CLM-K01-0101-02", T1, "01-01", "fact", "낙동강 경계를 ㅅ/ㅆ 변별 경계로 서술", "①", "새국어생활 1998-4",
   [("SRC-K01-NKLIFE1998", "CHK-K01-NK98-003", ORI, "faithful_summary", "원문은 '낙동강의 동쪽 지역으로 ㅅ과 ㅆ이 비변별적'")])
cl("CLM-K01-0101-03", T1, "01-01", "fact", "대구 말의 하소체 어미 '-는구마'", "①", "새국어생활 1998-4",
   [("SRC-K01-NKLIFE1998", "CHK-K01-NK98-005", ORI, "match", "원문은 '-는구마' 또는 '-느마'")])
cl("CLM-K01-0101-04", T1, "01-01", "fact", "서재극(1962) 인용: ㅅ/ㅆ 구획선(의성·안동·영양·청송선, 대구·경산·영천·경주선) → 대구는 경계 지역", "①", "새국어생활 1998-4",
   [("SRC-K01-NKLIFE1998", "CHK-K01-NK98-004", ORI, "match", "각주 5. 원문 연도 표기 '19620'(오기). '대구는 경계 지역'은 MD의 해석")])
cl("CLM-K01-0101-05", T1, "01-01", "fact", "발행연도는 본문에 없음(경로·인용으로 1998 추정)", "", "작성자 메모",
   [("SRC-K01-NKLIFE1998", "CHK-K01-NK98-001", ORI, "match", "본문에 연도 없음 확인"),
    ("SRC-K01-NKLIFE1998-TOC", "CHK-K01-TOC-001", ALT, "match", "목차로 1998_4호 수록 확인. Aside: 총목록 '제8권 제4호(1998. 겨울)'")])
cl("CLM-K01-0102-01", T1, "01-02", "fact", "경상북도 방언 이야기(새국어생활 2005): 의문형 어미 기준 3개 말씨권 — PDF 추출 실패로 인용 보류", "①", "새국어생활 2005-4",
   [("SRC-K01-NKLIFE2005", "CHK-K01-NK05-001", ORI, "match", "Aside가 PDF에서 확인: 필자 이상규, 15권 4호(2005 겨울) 123~129쪽, 3가지 말씨(니껴·능교·해여체). 원문 미보관이라 승인 보류 유지")])
cl("CLM-K01-0103-01", T1, "01-03", "fact", "장혜진·차재은·신지영, 『한국어학』 41권 pp.381-402, 한국어학회, 2008", "①", "고려대 학술",
   [("SRC-K01-KU-125264", "CHK-K01-KU-001", ORI, "match", "KCI 발행 2008.11(Aside)")])
cl("CLM-K01-0103-02", T1, "01-03", "fact", "20대가 40·50대보다 /ㅡ/·/ㅓ/를 더 잘 지각. 실험 I 인명, 실험 II 무의미어", "①", "고려대 학술",
   [("SRC-K01-KU-125264", "CHK-K01-KU-002", ORI, "faithful_summary", "원문은 younger/older. 대상 집단(20대, 40~50대)은 Aside 확인"),
    ("SRC-K01-KU-125264", "CHK-K01-KU-003", ORI, "match", "실험 I 인명. 실험 II 무의미어는 보관 초록에서 문장 미대조")])
cl("CLM-K01-0104-01", T1, "01-04", "fact", "한국어 방언의 문미억양 연구 — 대구·광주 비교(이승현, 경북대 석사), 서지 미확인", "①", "링크 없음",
   [("SRC-K01-RISS-0104", "CHK-K01-RISS04-001", ALT, "faithful_summary", "서지 확인: 정확한 제목은 '문말 억양 연구'(MD '문미억양'), 경북대 석사 2000")])
cl("CLM-K01-0105-01", T1, "01-05", "fact", "장혜진·신지영, 대구 방언 20대 화자 단모음 표준어 지향성 성별 차이 — 서지 미확인", "①", "링크 없음",
   [("SRC-K01-RISS-0105", "CHK-K01-RISS05-001", ALT, "match", "서지 확인: 한국어학 36, 289~314쪽, 2007")])
cl("CLM-K01-0106-01", T1, "01-06", "fact", "서민정, 『말소리와 음성과학』 18권 2호 pp.13-25, 한국음성학회, 2026-06-30", "①", "KoreaScience",
   [("SRC-K01-KS-2026", "CHK-K01-KS-001", ORI, "match", "")])
cl("CLM-K01-0106-02", T1, "01-06", "fact", "1950~2000년대생 비교, 젊을수록 평음 VOT가 길어져 평음·격음 VOT 근접", "①", "KoreaScience",
   [("SRC-K01-KS-2026", "CHK-K01-KS-002", ORI, "match", "")])
cl("CLM-K01-0106-03", T1, "01-06", "condition", "초록에 대구 명시 없음, 대구 포함 가능성만 있음", "", "작성자 판단",
   [("SRC-K01-KS-2026", "CHK-K01-KS-002", ORI, "match", "초록에 '대구' 없음은 사실"),
    ("SRC-K01-KS-2026-PDF", "CHK-K01-KSPDF-001", ALT, "scope_mismatch", "본문은 '대구시 및 경상북도에서 태어나 자란' 화자 — 대구 포함(가능성이 아니라 포함). Aside 보고, 미보관")])
cl("CLM-K01-0107-01", T1, "01-07", "fact", "경북 방언 3권역: 북부 -니껴, 대구·경주권 -능교, -여권은 선산에서 김천·의성 일부", "③", "경북매일 칼럼 2024-07-15",
   [("SRC-K01-NEWS-KB-20240715", "CHK-K01-KB0715-001", ORI, "match", ""),
    ("SRC-K01-NEWS-KB-20240715", "CHK-K01-KB0715-002", ORI, "match", "원문 '-능교'(-능게)"),
    ("SRC-K01-NKLIFE2005", "CHK-K01-NK05-001", ALT, "faithful_summary", "같은 필자의 2005 글(Aside)은 '경주 중심 남동부 하능교체'로 대구를 따로 적지 않음")])
cl("CLM-K01-S0-01", "0. 핵심 요약", "미확인", "fact", "2022~2026년 대구 방언 음운·억양 연구는 이번 검색에서 찾지 못함(KCI·RISS 직접 검색 필요)", "", "작성자 검색",
   [("SRC-K01-KCI-SEARCH", "CHK-K01-KCI-001", ALT, "mismatch", "Aside KCI 검색에서 2022~2026 관련 논문 확인(박지윤 2022 /ㅡ/·/ㅓ/ 지각·산출, 손재현 2022·2023 성조·악센트 등). 개별 원문은 미대조")])
cl("CLM-K01-S0-02", "0. 핵심 요약", "부족", "fact", "대구 방언 내부의 구·군별 변이를 다룬 자료는 확보하지 못함", "", "작성자 검색",
   [("SRC-K01-MD", "CHK-K01-MD-005", USR, "interpretation", "미확보 목록. Aside 검색 목록에도 구·군별 변이 연구는 없음(부재 확정 아님)")])
cl("CLM-K01-X-01", "2. 교차검증·불일치", "어미", "proposal", "01-01 '-는구마'(하소체)와 01-07 '-능교'(의문형)는 범주가 다를 수 있음 — 확정 불가", "", "작성자 판단",
   [("SRC-K01-MD", "CHK-K01-MD-002", USR, "interpretation", "원문 대조 결과 두 어미는 실제로 다른 범주(하소체 평서 vs 의문형)로 서술됨 — '부분 일치' 판단은 해소 가능")])
cl("CLM-K01-X-02", "2. 교차검증·불일치", "세대", "proposal", "01-03(2008)과 01-06(2026)은 변수가 달라 비교 불가", "", "작성자 판단",
   [("SRC-K01-MD", "CHK-K01-MD-003", USR, "interpretation", "")])
cl("CLM-K01-J-01", "3. 자산/정보 판정", "판정", "proposal", "01-01~01-07 모두 정보(자산 아님), 다른 자산의 근거 정보로 사용", "", "작성자 판단",
   [("SRC-K01-MD", "CHK-K01-MD-004", USR, "interpretation", "")])

FIG = []


def fg(rid, domain, subject, metric, num, text, unit, cur="", vat="not_stated", qty="", year="", ps="", pe="",
       status="reported", sid="", cid="", clm="", note=""):
    FIG.append(dict(record_id=rid, domain=domain, subject=subject, metric=metric, value_numeric=num, value_text=text,
                    unit=unit, currency=cur, vat_basis=vat, quantity_basis=qty, base_year=year, period_start=ps,
                    period_end=pe, value_status=status, source_id=sid, chunk_id=cid, claim_id=clm, note=note))


fg("FIG-K01-001", "spec", "장혜진 외(2008) 한국어학 41", "수록 쪽", "", "381 ~ 402", "pages", year="2008", sid="SRC-K01-KU-125264",
   cid="CHK-K01-KU-001", clm="CLM-K01-0103-01")
fg("FIG-K01-002", "spec", "장혜진·신지영(2007) 한국어학 36", "수록 쪽", "", "289-314(26쪽)", "pages", year="2007", sid="SRC-K01-RISS-0105",
   cid="CHK-K01-RISS05-001", clm="CLM-K01-0105-01")
fg("FIG-K01-003", "spec", "서민정(2026) 말소리와 음성과학 18(2)", "수록 쪽", "", "13-25", "pages", year="2026", sid="SRC-K01-KS-2026",
   cid="CHK-K01-KS-001", clm="CLM-K01-0106-01")
fg("FIG-K01-004", "statistic", "서민정(2026) 연구 대상", "화자 수", "", "", "persons", year="2026", status="unconfirmed",
   sid="SRC-K01-KS-2026-PDF", cid="CHK-K01-KSPDF-001", note="Aside 보고 50명(여성, 1950년대 8·60년대 6·70년대 7·80년대 7·90년대 12·2000년대 10) — 원문 미보관")
fg("FIG-K01-005", "statistic", "장혜진 외(2008) 초록", "실험 수치", "", "", "", status="not_available", sid="SRC-K01-KU-125264",
   cid="CHK-K01-KU-002", note="초록에 수치 없음(MD와 같음)")

PLACE_LISTS = []
CONFLICT_PAIRS = []
EXCEPTION_PAIRS = []
RULE_ABOUT_PAIRS = []

RULES = [
    ("RULE-K01-001", "region", "경북 방언 연구(01-06·01-07 등)는 대구 방언의 사실로 일반화하지 않는다. 대구 포함 여부는 원문 표본 정의로 확인한다.", "warn",
     "applies_to 에 경북·경상", "SRC-K01-MD", "CHK-K01-MD-001"),
    ("RULE-K01-002", "citation", "서지가 확인되지 않은 논문은 인용하지 않는다(01-04·01-05는 RISS로 서지 확인 후 사용).", "block", "서지 미확인", "", ""),
    ("RULE-K01-003", "independence", "같은 필자(이상규)의 글은 독립 근거 1건으로 센다(01-01·01-02·01-07).", "warn", "필자 동일", "", ""),
]
RULE_TARGETS = {}

ISSUES = [
    ("ISS-K01-001", "mismatch", "CLM-K01-S0-01", "SRC-K01-KCI-SEARCH", "'2022~2026 대구 방언 음운·억양 연구 못 찾음' → Aside KCI 검색에서 박지윤(2022)·손재현(2022·2023) 등 발견", "MD 갱신, 개별 논문 원문 확인"),
    ("ISS-K01-002", "title_mismatch", "CLM-K01-0104-01", "SRC-K01-RISS-0104", "01-04 제목 '문미억양' → 실제 '문말 억양 연구', 경북대 석사 2000", "MD 서지 보완"),
    ("ISS-K01-003", "resolved", "CLM-K01-0105-01", "SRC-K01-RISS-0105", "01-05 서지 확인: 한국어학 36, 289~314쪽, 2007", "MD 서지 보완"),
    ("ISS-K01-004", "scope_mismatch", "CLM-K01-0106-03", "SRC-K01-KS-2026-PDF", "01-06 본문은 '대구시 및 경상북도' 출신 화자 — 대구 포함(Aside, 미보관)", "MD 라벨 '대구 포함 가능성' → '대구 포함(인원 미상)'"),
    ("ISS-K01-005", "resolved", "CLM-K01-0102-01", "SRC-K01-NKLIFE2005", "01-02 PDF 확인(Aside): 이상규, 15권 4호(2005 겨울) 123~129쪽, 3가지 말씨 — 대구는 따로 언급 없음", "PDF 저장 후 인용 보류 해제 검토"),
    ("ISS-K01-006", "official_typo", "CLM-K01-0101-04", "SRC-K01-NKLIFE1998", "1998 글 각주의 서재극 연도가 '19620'으로 오기", "인용 시 1962로 표기하고 원문 오기 주석"),
    ("ISS-K01-007", "resolved_note", "CLM-K01-X-01", "SRC-K01-NKLIFE1998;SRC-K01-NEWS-KB-20240715", "'-는구마'(하소체)와 '-능교'(의문형)는 원문상 다른 범주 — '부분 일치' 판단 해소 가능", "MD 2절 갱신"),
    ("ISS-K01-008", "broken_links", "", "SRC-K01-MD", "MD의 [00_개요.md] 링크가 파일명 정리 이후 없는 경로(실제 kimseunghee_00_개요.md)", "링크 수정"),
    ("ISS-K01-009", "ocr_unreviewed", "", "", "OCR 대상 없음. 단, Aside 보고로 1998 PDF 일부 쪽 머리글에 OCR 오류가 있음(이 패키지는 HTML판 사용)", ""),
]

SEARCH_TESTS = [
    ("ST-K01-01", "낙동강", "false", "CHK-K01-NK98-002", "낙동강 경계"),
    ("ST-K01-02", "비변별", "false", "CHK-K01-NK98-003", "ㅅ/ㅆ 비변별 지역"),
    ("ST-K01-03", "서재극", "false", "CHK-K01-NK98-004", "구획선 각주"),
    ("ST-K01-04", "하소체", "false", "CHK-K01-NK98-005", "-는구마"),
    ("ST-K01-05", "perceive", "false", "CHK-K01-KU-002", "모음 지각 결과"),
    ("ST-K01-06", "한국어학", "false", "CHK-K01-KU-001", "2008 서지"),
    ("ST-K01-07", "VOT", "false", "CHK-K01-KS-002", "세대별 VOT"),
    ("ST-K01-08", "문말 억양", "false", "CHK-K01-RISS04-001", "이승현 석사"),
    ("ST-K01-09", "성별적 차이", "false", "CHK-K01-RISS05-001", "장혜진·신지영 2007"),
    ("ST-K01-10", "능교", "true", "CHK-K01-KB0715-002", "3권역 의문형 어미(칼럼)"),
    ("ST-K01-11", "이상규", "false", "CHK-K01-NK98-001", "필자(검색 보조 설명의 한글 이름)"),
]

TEMPLATE = {
    "template_id": "TPL-K01-TOPIC",
    "md_id": MD_ID,
    "description": "kimseunghee 하위 키워드 문서(01~09) 고정 양식. 값이 아니라 양식만 담음",
    "front_matter": ["확장 키워드", "자료 기준일·출처 등급", "기간 예외"],
    "sections": [
        {"key": "S0", "title": "0. 핵심 요약", "kind": "list", "item_label": "[라벨] 내용"},
        {"key": "S1", "title": "1. (주제별 절)", "kind": "grade_tables", "subsections": ["① 공식·학술", "② 기사", "③ 비공식"],
         "columns": ["ID", "자료", "내용", "수치", "라벨", "출처"]},
        {"key": "S2", "title": "2. 교차검증·불일치", "kind": "table", "columns": ["항목", "내용", "상태"]},
        {"key": "S3", "title": "3. 자산/정보 판정 (v1 3질문)", "kind": "list"},
        {"key": "S4", "title": "4. 부족한 점", "kind": "list"},
    ],
}
TEMPLATE_FILE = "json/md_template_kimseunghee_01.json"
MD_CODES = {
    "source_grade_md": {"①": "공식·학술", "②": "기사", "③": "비공식(칼럼 등)"},
    "content_label": {"확인": "출처로 확인된 사실", "해석": "자료 기반 분석", "미확인": "근거 미확보"},
    "region_label": ["대구 직접", "경북 참고", "경상권 참고", "전국 참고", "해외 참고"],
}

# ==========================================================================
# 생성 로직
# ==========================================================================
def html_to_text(raw):
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>|<!--.*?-->", "", raw)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return t

def squash(s):
    return re.sub(r"\s+", "", s)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()

def load_text(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    return squash(html_to_text(raw) if path.endswith(".html") else raw)

def write_csv(name, fields, rows):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    return len(rows)

VERDICT_KO = {"match": "일치", "faithful_summary": "의미를 유지한 요약", "interpretation": "해석·제안",
              "overgeneralization": "과도한 일반화", "scope_mismatch": "적용 범위 다름", "mismatch": "불일치",
              "unverifiable": "확인 불가"}
RELATION_KO = {ORI: "원래 출처 확인", ALT: "원래 출처 불명확·대체 근거 확보", USR: "사용자 작성 원본", UNV: "원문 확인 불가"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--news-dir", default="", help="언론 기사 HTML 스냅숏 폴더(선택)")
    args = ap.parse_args()

    src_by_id = {s["id"]: s for s in SOURCES}
    # 이전 실행의 기사 대조 결과 보존
    prev_check = {}
    prev_path = os.path.join(DATA_DIR, "knowledge_chunks.csv")
    if os.path.exists(prev_path):
        with open(prev_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                prev_check[r["chunk_id"]] = r.get("text_check", "")

    # --- 원문 해시
    for s in SOURCES:
        s["original_file_path"] = ""
        s["original_sha256"] = ""
        if s["ostatus"] == "stored":
            ext = ".md" if s["doc_type"] == "user_authored" else ".html"
            rel = f"originals/{s['id']}{ext}"
            s["original_file_path"] = rel
            s["original_sha256"] = sha256(os.path.join(PKG, rel))
        elif s.get("snapshot_sha"):
            s["original_sha256"] = s["snapshot_sha"]

    # --- 청크 원문 대조
    text_cache = {}
    def hay(sid):
        if sid in text_cache:
            return text_cache[sid]
        s = src_by_id[sid]
        t = None
        if s["original_file_path"]:
            t = load_text(os.path.join(PKG, s["original_file_path"]))
        elif s.get("snapshot") and args.news_dir:
            p = os.path.join(args.news_dir, s["snapshot"])
            if os.path.exists(p):
                if sha256(p) != s.get("snapshot_sha"):
                    print(f"[경고] 스냅숏 해시 불일치: {sid}", file=sys.stderr)
                t = load_text(p)
        text_cache[sid] = t
        return t

    failures = []
    for c in C:
        s = src_by_id[c["source_id"]]
        if c["chunk_id"] in ASIDE_ONLY:
            c["text_check"] = "reported_by_aside_not_stored"
            continue
        h = hay(c["source_id"])
        if h is None:
            c["text_check"] = prev_check.get(c["chunk_id"]) or "not_checked"
            continue
        missing = [ln for ln in c["text_original"].split("\n") if squash(ln) not in h]
        if missing:
            c["text_check"] = "not_found_in_original"
            failures.append((c["chunk_id"], missing))
        else:
            c["text_check"] = ("verified_in_stored_original" if s["original_file_path"]
                               else "verified_in_snapshot_not_stored")

    # --- 절·블록 계층
    sections, blocks = {}, {}
    rows_sec = []
    for s in SOURCES:
        rid = f"SEC-{s['id'][4:]}-00"
        sections[(s["id"], None)] = rid
        rows_sec.append(dict(section_id=rid, source_id=s["id"], parent_section_id="", level="document",
                             order_no=0, title=s["title"], block_type="", locator="문서 전체"))
    for c in C:
        sid = c["source_id"]
        key = (sid, c["sec"])
        if key not in sections:
            n = sum(1 for k in sections if k[0] == sid and k[1] is not None) + 1
            rid = f"SEC-{sid[4:]}-{n:02d}"
            sections[key] = rid
            rows_sec.append(dict(section_id=rid, source_id=sid, parent_section_id=sections[(sid, None)],
                                 level="section", order_no=n, title=c["sec"], block_type="", locator=c["sec"]))
        bkey = (sid, c["sec"], c["blk"])
        if bkey not in blocks:
            sec_id = sections[key]
            n = sum(1 for k in blocks if k[0] == sid and k[1] == c["sec"]) + 1
            bid = f"BLK-{sec_id[4:]}-{n:02d}"
            blocks[bkey] = bid
            rows_sec.append(dict(section_id=bid, source_id=sid, parent_section_id=sec_id, level="block",
                                 order_no=n, title=c["blk"], block_type=c["btype"], locator=c["locator"]))
        c["parent_section_id"] = sections[key]
        c["source_block_id"] = blocks[bkey]

    # --- 청크 행
    rel_rows = []
    order = {}
    chunk_rows = []
    for c in C:
        s = src_by_id[c["source_id"]]
        order[c["source_id"]] = order.get(c["source_id"], 0) + 1
        if s["grade"] in ("S", "A") and c["text_check"] == "verified_in_stored_original":
            appr, ver = "approved", "verified"
        elif s["grade"] == "U":
            appr, ver = "internal", "verified" if c["text_check"].startswith("verified") else "unverified"
        elif s["grade"] == "B":
            appr = "reference_only"
            ver = "verified" if c["text_check"].startswith("verified") else "unverified"
        elif c["text_check"] == "reported_by_aside_not_stored":
            appr, ver = "pending", "aside_reported"
        else:
            appr, ver = "pending", "unverified"
        if c["text_check"] == "not_found_in_original":
            appr, ver = "pending", "unverified"
        chunk_rows.append(dict(
            chunk_id=c["chunk_id"], source_id=c["source_id"], md_id=MD_ID, parent_section_id=c["parent_section_id"],
            source_block_id=c["source_block_id"], order_no=order[c["source_id"]], info_type=c["info_type"],
            short_title=c["short_title"], text_original=c["text_original"],
            text_is_excerpt="true" if s["doc_type"] == "news" else "false",
            text_format="lines" if "\n" in c["text_original"] else "text",
            search_context=c["search_context"], summary="", author_interpretation="",
            applies_to=c["applies_to"], condition_text=c["condition_text"], period_text=c["period_text"],
            locator=c["locator"], related_chunk_ids=";".join(c["related"]), source_grade=s["grade"],
            text_check=c["text_check"], verification_status=ver, approval_status=appr, version=VERSION,
            char_count=len(c["text_original"])))
        for r in c["related"]:
            rel_rows.append(dict(from_chunk_id=c["chunk_id"], to_chunk_id=r, relation="must_read_with"))
    # 충돌 관계
    for a, b in CONFLICT_PAIRS:
        rel_rows.append(dict(from_chunk_id=a, to_chunk_id=b, relation="conflicts_with"))
        rel_rows.append(dict(from_chunk_id=b, to_chunk_id=a, relation="conflicts_with"))
    # 예외 관계
    for a, b in EXCEPTION_PAIRS:
        rel_rows.append(dict(from_chunk_id=a, to_chunk_id=b, relation="exception_of"))
    # 같은 사실 다른 출처
    for a, b in RULE_ABOUT_PAIRS:
        rel_rows.append(dict(from_chunk_id=a, to_chunk_id=b, relation="rule_about"))
    seen, uniq = set(), []
    for r in rel_rows:
        k = (r["from_chunk_id"], r["to_chunk_id"], r["relation"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    for i, r in enumerate(uniq, 1):
        r["link_id"] = f"CLK-{i:04d}"

    # --- 근거 연결 행
    chunk_by_id = {c["chunk_id"]: c for c in chunk_rows}
    claim_by_id = {c["claim_id"]: c for c in CLAIMS}
    ev_rows = []
    per_claim = {}
    for (cid, sid, chk, relation, verdict, note) in LINKS:
        per_claim[cid] = per_claim.get(cid, 0) + 1
        s = src_by_id[sid]
        k = chunk_by_id.get(chk) if chk else None
        clm = claim_by_id[cid]
        ev_rows.append(dict(
            link_id=f"EVL-{cid[4:]}-{per_claim[cid]:02d}", claim_id=cid, md_id=MD_ID, md_path=MD_PATH,
            md_commit_sha=MD_LAST_COMMIT, md_section=clm["md_section"], md_row_key=clm["row_key"],
            claim_text=clm["claim_text"], source_id=sid, chunk_id=chk, source_title=s["title"], publisher=s["publisher"],
            official_url=s["url"], direct_attachment_url=s["attach"], published_date=s["pub"],
            effective_period=s["period"], accessed_at=ACCESSED, original_file_path=s["original_file_path"],
            original_sha256=s["original_sha256"], locator=k["locator"] if k else "",
            excerpt=k["text_original"] if k else "", source_relation=relation, source_relation_ko=RELATION_KO[relation],
            verdict=verdict, verdict_ko=VERDICT_KO[verdict], review_note=note))
    claim_rows = []
    for c in CLAIMS:
        mine = [l for l in LINKS if l[0] == c["claim_id"]]
        vs = [l[4] for l in mine]
        # 대표 판정: 원래 출처(ORI) 근거가 있으면 그 안에서 가장 나쁜 판정,
        # 없으면 대체 근거·사용자 원본 중 가장 나쁜 판정, 아무것도 없으면 확인 불가.
        # (다른 시점 기사처럼 '참고로 붙인' 대체 근거가 원래 출처 판정을 덮지 않게 함)
        rank = ["mismatch", "overgeneralization", "scope_mismatch", "interpretation", "faithful_summary", "match"]
        pool = []
        for tier in (ORI, ALT, USR):
            pool = [l[4] for l in mine if l[3] == tier and l[4] != "unverifiable"]
            if pool:
                break
        overall = min(pool, key=rank.index) if pool else "unverifiable"
        claim_rows.append(dict(c, md_id=MD_ID, is_external="false" if c["claim_type"] == "proposal" else "true",
                               overall_verdict=overall, overall_verdict_ko=VERDICT_KO[overall], evidence_count=len(vs)))

    # --- 장소 목록
    place_rows = []
    for list_name, cid, kind in PLACE_LISTS:
        c = chunk_by_id[cid]
        for i, name in enumerate(c["text_original"].split("\n"), 1):
            place_rows.append(dict(place_id=f"PLC-{cid[4:]}-{i:02d}", list_name=list_name, list_order=i, name=name,
                                   place_kind=kind, district="", source_id=c["source_id"], chunk_id=cid,
                                   approval_status=c["approval_status"], note=""))

    # --- 정형 데이터 승인 상태
    for f_ in FIG:
        if f_["chunk_id"]:
            f_["approval_status"] = chunk_by_id[f_["chunk_id"]]["approval_status"]
        else:
            f_["approval_status"] = "pending"

    # --- 쓰기
    src_fields = ["source_id", "title", "publisher", "doc_type", "source_grade", "official_url", "direct_attachment_url",
                  "published_date", "published_date_basis", "effective_period", "version_label", "accessed_at",
                  "retrieval_method", "original_status", "original_file_path", "original_sha256", "storage_object_path",
                  "approval_status", "rights_note", "revision_check", "notes"]
    src_rows = []
    for s in SOURCES:
        src_rows.append(dict(source_id=s["id"], title=s["title"], publisher=s["publisher"], doc_type=s["doc_type"],
                             source_grade=s["grade"], official_url=s["url"], direct_attachment_url=s["attach"],
                             published_date=s["pub"], published_date_basis=s["pub_basis"], effective_period=s["period"],
                             version_label=s["ver"], accessed_at=ACCESSED if s["retrieval"] not in ("not_retrieved", "not_found") else "",
                             retrieval_method=s["retrieval"], original_status=s["ostatus"],
                             original_file_path=s["original_file_path"], original_sha256=s["original_sha256"],
                             storage_object_path=(f"research-originals/kimseunghee_01/{os.path.basename(s['original_file_path'])}"
                                                  if s["original_file_path"] else ""),
                             approval_status=s["approval"], rights_note=s["rights"],
                             revision_check=("정정·개정 표시 없음(확인일 현재본)" if s["ostatus"] != "not_retrieved" else "확인 못 함"),
                             notes=s["notes"]))
    n = {}
    n["source_documents.csv"] = write_csv("source_documents.csv", src_fields, src_rows)
    n["md_documents.csv"] = write_csv("md_documents.csv",
        ["md_id", "repo_path", "git_branch", "last_commit_sha", "branch_head_sha", "git_blob_sha", "file_sha256",
         "title", "written_date", "md_version", "source_id", "notes"],
        [dict(md_id=MD_ID, repo_path=MD_PATH, git_branch="main", last_commit_sha=MD_LAST_COMMIT,
              branch_head_sha=MD_MAIN_HEAD, git_blob_sha=MD_BLOB,
              file_sha256=src_by_id[MD_SOURCE_ID]["original_sha256"],
              title=MD_TITLE, written_date=MD_WRITTEN, md_version=MD_VERSION,
              source_id=MD_SOURCE_ID, notes=MD_NOTES)])
    n["md_claims.csv"] = write_csv("md_claims.csv",
        ["claim_id", "md_id", "md_section", "row_key", "claim_type", "is_external", "claim_text", "md_stated_grade",
         "md_stated_source", "overall_verdict", "overall_verdict_ko", "evidence_count"], claim_rows)
    n["evidence_links.csv"] = write_csv("evidence_links.csv", list(ev_rows[0].keys()), ev_rows)
    n["source_sections.csv"] = write_csv("source_sections.csv",
        ["section_id", "source_id", "parent_section_id", "level", "order_no", "title", "block_type", "locator"], rows_sec)
    n["knowledge_chunks.csv"] = write_csv("knowledge_chunks.csv", list(chunk_rows[0].keys()), chunk_rows)
    n["chunk_links.csv"] = write_csv("chunk_links.csv", ["link_id", "from_chunk_id", "to_chunk_id", "relation"], uniq)
    n["domain_figures.csv"] = write_csv("domain_figures.csv", list(FIG[0].keys()), FIG)
    n["domain_places.csv"] = write_csv("domain_places.csv", ["place_id", "list_name", "list_order", "name", "place_kind", "district", "source_id", "chunk_id", "approval_status", "note"], place_rows)
    n["operating_rules.csv"] = write_csv("operating_rules.csv",
        ["rule_id", "rule_scope", "rule_text", "enforcement", "condition_text", "rule_source_id", "rule_chunk_id",
         "target_chunk_ids", "approval_status"],
        [dict(rule_id=r[0], rule_scope=r[1], rule_text=r[2], enforcement=r[3], condition_text=r[4], rule_source_id=r[5],
              rule_chunk_id=r[6], target_chunk_ids=RULE_TARGETS.get(r[0], ""), approval_status="approved") for r in RULES])
    n["review_issues.csv"] = write_csv("review_issues.csv",
        ["issue_id", "issue_type", "claim_ids", "source_ids", "description", "next_action"],
        [dict(issue_id=i[0], issue_type=i[1], claim_ids=i[2], source_ids=i[3], description=i[4], next_action=i[5]) for i in ISSUES])

    n["search_tests.csv"] = write_csv("search_tests.csv",
        ["test_id", "query", "include_reference", "expected_chunk_id", "note"],
        [dict(test_id=s_[0], query=s_[1], include_reference=s_[2], expected_chunk_id=s_[3], note=s_[4]) for s_ in SEARCH_TESTS])

    # --- JSON
    template = TEMPLATE
    codes = {
        "source_grade": {"S": "공식", "A": "통계·공공데이터", "B": "언론", "D": "개인", "E": "AI생성", "U": "사용자 작성 원본(이 패키지에서 추가)"},
        "md_codes": MD_CODES,
        "verdict": VERDICT_KO,
        "source_relation": RELATION_KO,
        "approval_status": {"approved": "공식 원문을 보관하고 글자 대조까지 끝남 — 확정 근거 사용 가능",
                            "reference_only": "언론 보도 — 참고용, 확정 사실로 쓰지 않음",
                            "internal": "팀 내부 작성 원본 — 규칙·판정의 근거",
                            "pending": "원문 미확보 또는 대조 실패 — 사용 금지"},
        "value_status": {"reported": "원문에 값이 있음", "not_available": "원문(자료)에 해당 값이 없음",
                         "unconfirmed": "원문을 확보하지 못해 확인 못 함", "not_applicable": "해당 없음",
                         "actual_zero": "실제 값이 0(무료 등)"},
        "info_type": {"fact": "사실", "rule": "규칙", "condition": "조건", "exception": "예외", "figure": "수치",
                      "procedure": "절차", "example": "사례"},
        "text_check": {"verified_in_stored_original": "originals/의 원문에서 글자 대조 완료",
                       "verified_in_snapshot_not_stored": "기사 스냅숏에서 글자 대조 완료(스냅숏은 저작권 때문에 미보관, SHA-256만 기록)",
                       "reported_by_aside_not_stored": "Aside(사용자 브라우저)로 열람한 인용값, 원문 미보관 — 승인 보류",
                       "not_found_in_original": "원문에서 찾지 못함 — 승인 제외", "not_checked": "대조 안 함"},
        "verification_status": {"verified": "원문 글자 대조 완료", "aside_reported": "Aside 보고만 있음",
                                "unverified": "대조 안 됨"},
    }
    for name, obj in [(TEMPLATE_FILE, template), ("json/code_lists.json", codes)]:
        with open(os.path.join(PKG, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write("\n")

    for k, v in n.items():
        print(f"{k}: {v}")
    if failures:
        print("\n[원문 대조 실패]")
        for cid, miss in failures:
            print(" ", cid, miss)
        sys.exit(2)

if __name__ == "__main__":
    main()
