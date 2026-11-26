# -*- coding: utf-8 -*-
"""kimseunghee_00_개요.md 원문 대조 데이터 패키지 생성기.

- 모든 ID는 이 파일에 고정(재실행해도 같음). kb 스키마를 다른 패키지와 함께 쓰므로 ID에 K00 을 붙인다.
- 청크 본문(text_original)은 실행할 때마다 원문 파일에서 글자 그대로 있는지 다시 대조한다(공백만 무시, 목록형은 줄마다).
- 언론 기사 HTML은 저작권 때문에 저장소에 넣지 않는다. --news-dir 로 스냅숏 폴더를 주면 기사 발췌도 대조한다.

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

MD_ID = "MD-K00"
MD_PATH = "local 리서치/kimseunghee_00_개요.md"
MD_LAST_COMMIT = "5f61dc486f15fe7db07c025d9e9d065fcc32dda0"
MD_MAIN_HEAD = "e1c6aca00f62c761820e7f9bd54a52548d8a53a4"
MD_BLOB = "239d2dd920e093f61debd0fc3bd360ac176aadfd"
MD_SOURCE_ID = "SRC-K00-MD"
MD_TITLE = "사투리_v02_V4 — 개요"
MD_WRITTEN = "2026-10-31"
MD_VERSION = "v02_V4"
MD_NOTES = "written_date 는 문서의 '자료 기준일'. 2026-11-26 main 기준. 원본은 originals/SRC-K00-MD.md"

# --------------------------------------------------------------------------
# 1. 원문 문서
# --------------------------------------------------------------------------
SOURCES = [
    dict(id="SRC-K00-MD", title="사투리_v02_V4 — 개요 (kimseunghee_00_개요.md)", publisher="팀 내부(작성자 kimseunghee)",
         doc_type="user_authored", grade="U", url="", attach="", pub="2026-10-31", pub_basis="문서 '자료 기준일: 2026-10-31'",
         period="조사 기간 2022-01 ~ 2026-10", ver=f"git blob {MD_BLOB}", retrieval="git show origin/main:<path>",
         ostatus="stored", snapshot="", approval="internal", rights="팀 내부 문서",
         notes="사용자 작성 원본. 등급·라벨·기간 예외·자산 판정 기준과 판단의 원본으로만 사용"),
    dict(id="SRC-K00-AIHUB-119", title="한국어 방언 발화(경상도)", publisher="한국지능정보사회진흥원(AI Hub)",
         doc_type="open_data", grade="A",
         url="https://aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&aihubDataSe=data&dataSetSn=119", attach="",
         pub="", pub_basis="페이지 '구축년도 : 2020', '갱신년월 : 2026-07'(발행일 표기 없음)", period="구축 2020, 갱신 2026-07",
         ver="갱신년월 2026-07", retrieval="curl", ostatus="stored", snapshot="", approval="approved",
         rights="공공 데이터 소개 페이지(데이터 자체는 이용 신청 필요)", notes="데이터셋 소개 페이지만 보관. 데이터 파일은 미다운로드"),
]


def news(id_, title, publisher, url, pub, basis, snapshot, sha, notes=""):
    return dict(id=id_, title=title, publisher=publisher, doc_type="news", grade="B", url=url, attach="",
                pub=pub, pub_basis=basis, period="", ver="확인일 현재 기사 페이지", retrieval="curl",
                ostatus="url_only_copyright", snapshot=snapshot, snapshot_sha=sha, approval="reference_only",
                rights="언론사 저작물 — 원문 재배포 안 함, URL과 짧은 발췌만 기록", notes=notes)


SOURCES += [
    news("SRC-K00-NEWS-NSIS-20260127", "국민 80% \"국어에서 가장 중요한 건 말하기\"…맞춤법·신조어 …", "뉴시스",
         "https://www.newsis.com/view/NISX20260127_0003491289", "2026-01-27", "기사 '등록 2026.01.27 10:26'",
         "nsis_20260127.html", "e3c7e0b035832a74a0bf76d8957aabfcb67e3895057d6a6bad823e6c35dc6f58",
         "MD(12번 CSV 03-01)가 인용한 기사. 국립국어원 '국민의 언어 의식 조사' 결과 보도. 제목은 페이지 <title> 앞부분"),
    news("SRC-K00-NEWS-IM-20260323", "[데이터로 보는 세상] '의리 지킨데이' 경북 청년 사투리 자부심", "매일신문",
         "https://www.imaeil.com/page/view/2026032316350730753", "2026-04-03", "기사 '입력 2026-04-03 12:00:00'(URL 숫자는 20260323)",
         "im_20260323.html", "c85e55840bfe3f25c0b6aa832c625d170ab97cc0c0d476213cb0b6cc0325bf1a",
         "MD(12번 CSV)는 발행일 2026-03-23으로 적음 — 기사 표시 날짜는 2026-04-03. 영주어문학회 논문 인용"),
    news("SRC-K00-NEWS-IM-20261008", "[한글날 100주년] 사투리 백일장부터 우리말 겨루기까지 '세종대왕님 뿌듯하겠네'", "매일신문",
         "https://www.imaeil.com/page/view/2026100810162109171", "2026-10-08", "기사 '입력 2026-10-08 14:43:20'",
         "im_20261008.html", "ff87b07e4af5b0b2a8dbe82fe2b1ae7ce4870ea4c75e463b560d66673224086d", "참가자 수는 기사에 없음"),
    news("SRC-K00-NEWS-KB-20230219", "\"대구굴기, 시민정신 힘으로\" 대구시민주간, 내일 막올라", "경북매일",
         "https://kbmaeil.com/article/202302190355367", "2023-02-20", "기사 '등록일 2023-02-19, 게재일 2023-02-20'",
         "kb_20230219.html", "7ba4c9e2245f227b7ca78017853e7812655bda104387c80ada40b6edeb37fe4b",
         "2023 대구시민주간 '사투리, 이쁘다 아이가' 프로그램. 참여 인원 없음"),
    news("SRC-K00-NEWS-HK-20260218", "대구시, 2026 대구시민주간 오는 21일부터 28일까지 운영", "헤럴드경제 미주판",
         "https://www.heraldk.com/article/2026021816043221660", "2026-02-18", "기사 '기사입력 : 2026-02-18 16:04'",
         "hk_20260218.html", "6c4408969baaf71517616d89153e787be3ef77dbf35c858b37944d35b3828d38",
         "2026 시민주간 기사 본문에 '사투리'가 나오지 않음(반복 운영 근거 없음)"),
    news("SRC-K00-NEWS-HK-20260621", "대구시, 2026 대구치맥페스티벌 다음달 1일 개막", "헤럴드경제 미주판",
         "https://www.heraldk.com/article/2026062113505078090", "2026-06-21", "기사 '기사입력 : 2026-06-21 13:50'",
         "hk_20260621.html", "cd7e12bc78659aeb795ec0e7d3a3f0febecff6f881181aca1369a4d798aeacfe",
         "MD(12번 CSV 08-04)가 '대구 사투리 축제 공백' 근거로 든 검색 결과 기사. 치맥 축제 기사이며 '사투리'는 나오지 않음"),
]

# --------------------------------------------------------------------------
# 2. 청크
# --------------------------------------------------------------------------
C = []


def ch(cid, sid, sec, blk, btype, itype, title, text, ctx, applies="", cond="", period="", loc="", rel=()):
    C.append(dict(chunk_id=cid, source_id=sid, sec=sec, blk=blk, btype=btype, info_type=itype, short_title=title,
                  text_original=text, search_context=ctx, applies_to=applies, condition_text=cond,
                  period_text=period, locator=loc, related=list(rel)))


def nch(cid, sid, blk, itype, title, text, ctx, applies="", cond="", period="", loc="본문", rel=()):
    ch(cid, sid, "기사 본문", blk, "sentence", itype, title, text, ctx, applies, cond, period, loc, rel)


K = "SRC-K00-NEWS-NSIS-20260127"
nch("CHK-K00-NSIS-001", K, "조사 개요 문단", "condition", "국민의 언어 의식 조사 대상",
    "국립국어원이 지난해 전국 만 20세 이상 69세 이하 성인 5000명을 대상으로 실시한 '국민의 언어 의식 조사'",
    "국립국어원 조사, 기사(2026-01-27) 기준 '지난해'=2025년, 전국 만 20~69세 성인 5,000명", applies="전국",
    period="2025", rel=("CHK-K00-NSIS-002", "CHK-K00-NSIS-004"))
nch("CHK-K00-NSIS-002", K, "방언 문단", "figure", "방언 유지 필요 응답 비율",
    "지역 방언의 유지·존속 필요성에 대해 '유지해야 한다'는 응답은 59.2%로 과반을 기록했다.",
    "방언 유지 필요 59.2%(전국 표본, 대구 분리 불가)", applies="전국", rel=("CHK-K00-NSIS-001", "CHK-K00-NSIS-003"))
nch("CHK-K00-NSIS-003", K, "방언 문단", "figure", "2020년 조사 대비 증가폭",
    "이는 지난 조사(2020년)보다 8.3%p 증가한 수치로", "직전 조사(2020) 대비 +8.3%p", applies="전국",
    rel=("CHK-K00-NSIS-002",))
nch("CHK-K00-NSIS-004", K, "방언 문단", "figure", "복수 표준어 인정 긍정 비율",
    "다만 지역 방언을 복수 표준어로 인정하는 데 대해서는 '긍정적이다'라는 응답이 47.7%로 집계돼",
    "지역 방언 복수 표준어 인정 긍정 47.7%", applies="전국", rel=("CHK-K00-NSIS-001",))
K = "SRC-K00-NEWS-IM-20260323"
nch("CHK-K00-IM0323-001", K, "연구 인용 문단", "fact", "인용 연구(영주어문학회)",
    "이 같은 정서는 영주어문학회가 올해 발행한 '경북 지역 청년층의 방언 태도와 표준어 사용' 연구에서도 확인됐다.",
    "기사가 인용한 학술 연구. 논문 원문은 별도 확인", applies="경북 20대",
    rel=("CHK-K00-IM0323-002", "CHK-K00-IM0323-003"))
nch("CHK-K00-IM0323-002", K, "연구 인용 문단", "figure", "상황별 방언 사용 비율",
    "부모나 고향 친구와 있을 때는 방언 사용이 각각 41.3%로 크게 늘어나지만, 교수(0%)나 아르바이트(2.7%) 등 격식 있는 자리에서는 방언 사용이 압도적으로",
    "경북 20대 상황별 방언 사용: 부모·고향 친구 각 41.3%, 교수 0%, 아르바이트 2.7%(경북 표본, 대구 단독 아님)",
    applies="경북 20대", rel=("CHK-K00-IM0323-001",))
nch("CHK-K00-IM0323-003", K, "연구 인용 문단", "figure", "방언 사용량 자가 평가 점수",
    "경북 20대의 방언 사용량 자가 평가 점수는 70.4점으로, 전북 지역 20대 37.8점에 비해 두 배 가량 높았",
    "경북 20대 70.4점 vs 전북 20대 37.8점", applies="경북·전북 20대", rel=("CHK-K00-IM0323-001",))
nch("CHK-K00-IM0323-004", K, "부제", "figure", "방언 보존 필요성 찬성 비율",
    "경북 20대 83.6%, 방언 보존의 필요성 찬성", "기사 부제", applies="경북 20대", rel=("CHK-K00-IM0323-001",))
nch("CHK-K00-IM0323-005", K, "사진 설명", "example", "앞산전망대 사투리 퀴즈 미디어보드",
    "대구 남구 앞산전망대를 찾은 한 시민이 미디어보드를 이용해 대구 사투리 퀴즈를 풀고 있다.",
    "사진 설명. 설치 시기·운영 주체·이용 수치는 기사에 없음", applies="대구 남구 앞산전망대")
K = "SRC-K00-NEWS-IM-20261008"
nch("CHK-K00-IM1008-001", K, "소제목", "fact", "경북대 사투리 백일장 개최", "경북대 사투리 백일장 개최",
    "2026 한글날 즈음 행사. 참가자 수·회차는 기사에 없음", applies="경북대", rel=("CHK-K00-IM1008-002",))
nch("CHK-K00-IM1008-002", K, "백일장 문단", "condition", "백일장 참가 방식",
    "참가자들은 행사 당일 공개되는 시제에 맞춰 경상 방언을 활용해 글을 쓰게 된다.", "경상 방언으로 글쓰기", applies="경북대",
    rel=("CHK-K00-IM1008-001",))
nch("CHK-K00-KB0219-001", "SRC-K00-NEWS-KB-20230219", "프로그램 문단", "fact", "2023 시민주간 사투리 프로그램",
    "대구 사투리를 재미있는 전시·공연으로 풀어낸 ‘사투리, 이쁘다 아이가’가 운영된다.",
    "2023 대구시민주간 프로그램. 참여 인원 없음", applies="대구", period="2023-02")
ch("CHK-K00-AIHUB-001", "SRC-K00-AIHUB-119", "데이터 소개", "데이터 개요", "paragraph", "figure", "경상도 방언 발화 데이터 규모",
   "2000명 이상의 10대 ~ 60대 의 연령별 화자가 발화한 3000 시간 이상의 음성 데이터",
   "AI Hub 한국어 방언 발화(경상도): 화자 2,000명 이상(10~60대), 3,000시간 이상(하한값). 대구만 따로 나뉘지 않음",
   applies="경상도", loc="aihub dataSetSn=119 > 소개", rel=("CHK-K00-AIHUB-002", "CHK-K00-AIHUB-003"))
ch("CHK-K00-AIHUB-002", "SRC-K00-AIHUB-119", "데이터 소개", "데이터 개요", "paragraph", "figure", "전사 어절 데이터 규모",
   "50 만건 이상 어절 데이터 셋", "방언-표준어 대응쌍 포함 전사 어절 50만 건 이상(하한값)", applies="경상도",
   loc="aihub dataSetSn=119 > 소개", rel=("CHK-K00-AIHUB-001",))
ch("CHK-K00-AIHUB-003", "SRC-K00-AIHUB-119", "데이터 소개", "메타 정보", "meta", "fact", "구축·갱신 시기",
   "구축년도 : 2020\n갱신년월 : 2026-07", "2020 구축, 2026-07 갱신", applies="경상도", loc="aihub dataSetSn=119 > 메타",
   rel=("CHK-K00-AIHUB-001",))

M = "SRC-K00-MD"


def mch(cid, sec, itype, title, text, ctx, rel=()):
    ch(cid, M, sec, sec, "md_text", itype, title, text, ctx, applies="사투리 조사(v02_V4)", loc=f"MD {sec}", rel=rel)


mch("CHK-K00-MD-001", "머리말", "rule", "조사 기간·기준일", "자료 기준일: 2026-10-31 / 조사 기간: 2022-01 ~ 2026-10 (예외는 아래 참조)",
    "작성자 규칙: 2022-01~2026-10 자료, 예외는 기간 예외 절")
mch("CHK-K00-MD-002", "출처 등급", "rule", "① 공식 등급",
    "| **① 공식** | 공공기관·지자체 원문/보도자료/통계, 학술논문·학회지·학술기관 보고서 | 가장 먼저 조사. 표에서 맨 위 |",
    "작성자 등급 ①: 공식·학술", rel=("CHK-K00-MD-003", "CHK-K00-MD-004"))
mch("CHK-K00-MD-003", "출처 등급", "rule", "② 기사 등급",
    "| **② 기사** | 언론 보도 | 공식 자료로 확인되지 않는 내용만 보충. 수치는 원자료 확인 전까지 \"요약 기반\" |",
    "작성자 등급 ②: 기사 수치는 원자료 확인 전 '요약 기반'", rel=("CHK-K00-MD-002",))
mch("CHK-K00-MD-004", "출처 등급", "rule", "③ 비공식 등급",
    "| **③ 비공식** | 전문가 칼럼, 기업·민간 발표, 민간 출판, 블로그·SNS | 반응·참고용으로만 사용. 링크 필수 |",
    "작성자 등급 ③: 반응·참고용만", rel=("CHK-K00-MD-002",))
mch("CHK-K00-MD-005", "출처 등급", "rule", "독립 근거 계산", "같은 필자·같은 기사·같은 원출처는 독립 근거 1건으로 셈",
    "작성자 규칙: 같은 원출처 중복 계산 금지")
mch("CHK-K00-MD-006", "라벨", "rule", "지역 라벨 일반화 금지", "B~D 자료는 대구의 사실로 일반화하지 않음",
    "작성자 규칙: 경북·전국·해외 자료를 대구 사실로 쓰지 않음")
mch("CHK-K00-MD-007", "라벨", "rule", "원문 확인과 요약 기반 구분",
    "**\"요약 기반\"**은 검색 결과 요약으로만 확인한 항목 (인용 전 원문 대조 필요)", "작성자 규칙: 요약 기반은 인용 전 원문 대조")
mch("CHK-K00-MD-008", "기간 예외", "rule", "기간 예외 범위",
    "지침 v2는 \"방언의 역사·형성·언어적 특성을 설명하는 과거 연구\"를 예외로 허용함", "작성자 규칙: 과거 연구 예외 허용 범위")
mch("CHK-K00-MD-009", "기간 예외", "rule", "기간외 자료 처리",
    "그 외 2022년 이전 자료는 \"기간외 참고\"로 표시하고 판정에서 뺌", "작성자 규칙: 2022년 이전 자료는 판정 제외",
    rel=("CHK-K00-MD-008",))
mch("CHK-K00-MD-010", "자산 판정", "rule", "고유성 기준",
    "| 고유성 | 지명·인물·역사·원산지 중 1개 이상 결합, **대구 직접 해당** |", "자산 판정 3질문 중 고유성",
    rel=("CHK-K00-MD-011", "CHK-K00-MD-012"))
mch("CHK-K00-MD-011", "자산 판정", "rule", "지속성 기준", "| 지속성 | 2회 이상 반복 또는 확인일 기준 운영 중(근거 필요) |",
    "자산 판정 3질문 중 지속성", rel=("CHK-K00-MD-010",))
mch("CHK-K00-MD-012", "자산 판정", "rule", "활용성 기준", "| 활용성 | 공식 수치(방문객·매출·참여자) 1개 이상, 규모 하한 없음 [가안] |",
    "자산 판정 3질문 중 활용성([가안])", rel=("CHK-K00-MD-010",))
mch("CHK-K00-MD-013", "전체 핵심", "fact", "대구 단독 자산 0건 판단",
    "**대구 단독 자산 0건**: 3질문을 모두 통과한 대구 사례가 없음.", "작성자 판단(해석). 근거는 후보 4건의 지속성·활용성 수치 부족")
mch("CHK-K00-MD-014", "전체 핵심", "fact", "정량 근거 부족 영역",
    "**정량 근거가 가장 약한 영역**: 사투리 굿즈·변환기 서비스·타지역 2030 인식 설문·대구 세대별 사용 통계는 미확보",
    "작성자 판단: 미확보 자료 목록")

# --------------------------------------------------------------------------
# 3. 주장과 근거
# --------------------------------------------------------------------------
CLAIMS, LINKS = [], []


def cl(cid, sec, row, ctype, text, grade, cited, links):
    CLAIMS.append(dict(claim_id=cid, md_section=sec, row_key=row, claim_type=ctype, claim_text=text,
                       md_stated_grade=grade, md_stated_source=cited))
    for l in links:
        LINKS.append((cid,) + tuple(l))


ORI, ALT, USR, UNV = "original_confirmed", "alternative_official", "user_authored", "unverifiable"
CORE = "전체 핵심"

# ---- 공식 원문(Aside가 찾고 curl로 다시 받아 대조)
def off(id_, title, publisher, doc_type, grade, url, attach, pub, basis, period, ver, notes, approval="approved"):
    return dict(id=id_, title=title, publisher=publisher, doc_type=doc_type, grade=grade, url=url, attach=attach, pub=pub,
                pub_basis=basis, period=period, ver=ver, retrieval="aside + curl", ostatus="stored", snapshot="",
                approval=approval, rights="공공기관 웹페이지", notes=notes)


SOURCES += [
    off("SRC-K00-NIKL-REPORT", "2025년 국민의 언어 의식 조사(연구 보고서 상세 페이지)", "국립국어원", "official_web", "S",
        "https://www.korean.go.kr/front/reportData/reportDataView.do?mn_id=45&pageIndex=1&report_seq=1209&searchOrder=",
        "https://www.korean.go.kr/common/download.do?file_path=reportData&c_file_name=84ba99e1-6aac-4fb8-afa1-b5b68ab87dfa.pdf&o_file_name=2025%EB%85%84%20%EA%B5%AD%EB%AF%BC%EC%9D%98%20%EC%96%B8%EC%96%B4%20%EC%9D%98%EC%8B%9D%20%EC%A1%B0%EC%82%AC_%EA%B2%B0%EA%B3%BC%20%EB%B3%B4%EA%B3%A0%EC%84%9C(F).pdf",
        "", "페이지 '펴낸 때 2025'(월·일 없음)", "조사 2025-09~2025-10(Aside: 보고서 3쪽)", "펴낸 때 2025",
        "상세 페이지만 보관. 결과 보고서 PDF(11.62MB)는 미다운로드 — 쪽·표 위치(19·71·72·79·80쪽 등)는 Aside 보고"),
    off("SRC-K00-NIKL-PRESS", "변화하는 언어 환경 속, 현재 우리 국민의 언어 의식은?(보도자료)", "국립국어원 어문연구과", "press_release", "S",
        "https://www.korean.go.kr/front/board/boardStandardView.do?board_id=6&mn_id=184&b_seq=1034",
        "https://www.korean.go.kr/common/download.do?file_path=recent&c_file_name=9fe998e6-582e-4835-b127-bde48d335881.hwpx",
        "2026-01-27", "게시판 '등록일 2026. 1. 27.'", "", "확인일 현재 게시물",
        "페이지 본문에 5,000명·59.2%·8.3%p 있음. 47.7%는 본문에 없고 첨부(hwpx)·보고서에 있다고 Aside 보고"),
    off("SRC-K00-KCI-PAPER", "경북 지역 청년층의 방언 태도와 표준어 사용(KCI 논문 상세)", "영주어문학회(『영주어문』 vol.62) / 한국연구재단 KCI",
        "official_web", "A", "https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003310657",
        "", "", "KCI '2026, vol.62, pp. 161-193'(월 표시 없음)", "", "vol.62 pp.161-193",
        "저자 이향원·하영우. 초록 공개. 초록의 조사 대상은 '대구 지역 20대 대학생 38명'. 41.3% 등 기사 수치는 초록에 없음(본문 미열람)"),
    off("SRC-K00-ORD-JEJU", "제주어 보전 및 육성 조례", "제주특별자치도 / 국가법령정보센터(자치법규)", "law", "S",
        "https://www.law.go.kr/ordinInfoP.do?ordinSeq=2023071", "", "2007-09-27", "Aside: '[조례 제280호, 2007. 9. 27., 제정]'(보관본은 현행판 머리)",
        "현행 시행 2025-03-19", "현행 제3919호(2025. 3. 19. 일부개정)", "보관 HTML은 현행판 머리만 글자 대조됨. 최초 제정 2007-09-27은 Aside 확인"),
    off("SRC-K00-ORD-JEONBUK", "전북특별자치도 국어 진흥 조례", "전북특별자치도 / 국가법령정보센터(자치법규)", "law", "S",
        "https://www.law.go.kr/ordinInfoP.do?ordinSeq=1900817", "", "2014-06-27", "Aside: 최초 제정 2014. 6. 27.(전라북도 국어 문화 진흥 조례)",
        "현행 시행 2024-01-18", "현행 제5399호(2023. 12. 8. 일부개정)", "2021. 11. 3.은 전부개정(제5027호) — Aside 확인. 보관본은 현행판 머리"),
    off("SRC-K00-ORD-CHANGWON", "창원시 국어 진흥과 지역어 보전에 관한 조례", "경상남도 창원시 / 국가법령정보센터(자치법규)", "law", "S",
        "https://www.law.go.kr/ordinInfoP.do?ordinSeq=2110177", "", "2013-12-30", "Aside: 최초 제정 2013. 12. 30.(창원시 국어 진흥 조례)",
        "현행 시행 2026-02-13", "현행 제2291호(2026. 2. 13. 일부개정)", "2024. 3. 29. 일부개정(제1964호)부터 지역어 보전 포함 이름 — Aside 확인"),
    off("SRC-K00-ORD-DAEGU", "대구광역시 국어 진흥 조례", "대구광역시 / 국가법령정보센터(자치법규)", "law", "S",
        "https://www.law.go.kr/ordinInfoP.do?ordinSeq=1415244", "", "2019-10-30", "'[대구광역시조례 제5354호, 2019. 10. 30., 제정]'",
        "시행 2019-10-30", "제5354호(제정, Aside: 개정 이력 없음)", "제3조② '지역어를 보전하고 발전시키기 위해 노력' 조항은 Aside 확인(보관본 본문은 스크립트로 그려져 미대조)"),
    off("SRC-K00-DGP-257024", "'앞산 전망대' 새단장 11월부터 개방", "대구광역시 관광과(대구시 뉴스룸)", "press_release", "S",
        "https://info.daegu.go.kr/newshome/mtnmain.php?mtnkey=articleview&mkey=scatelist&mkey2=1&aid=257024", "", "2022-10-31",
        "페이지 날짜 2022-10-31", "", "확인일 현재 게시물", "앞산 전망대 키오스크 사투리 퀴즈의 공식 근거(설치·개방 시기)"),
    off("SRC-K00-DGP-258646", "대구굴기 시민정신의 힘으로! 대구시민주간 개최", "대구광역시 문화예술정책과(대구시 뉴스룸)", "press_release", "S",
        "https://info.daegu.go.kr/newshome/mtnmain.php?mtnkey=articleview&mkey=scatelist&mkey2=1&aid=258646", "", "2023-02-20",
        "페이지 날짜 2023-02-20", "2023-02-21~28(Aside)", "확인일 현재 게시물", "2023 시민주간 '사투리, 이쁘다 아이가' 공식 근거"),
]

ch("CHK-K00-NIKLP-001", "SRC-K00-NIKL-PRESS", "보도자료 본문", "조사 개요", "sentence", "condition", "조사 대상(보도자료)",
   "이번 조사는 전국 만 20세 이상 69세 이하 남녀 5,000명을 대상으로 진행되었다.", "국립국어원 2025 국민의 언어 의식 조사 표본",
   applies="전국", period="2025-09~2025-10(조사 기간은 보고서 기준, Aside)", loc="보도자료 본문", rel=("CHK-K00-NIKLP-002",))
ch("CHK-K00-NIKLP-002", "SRC-K00-NIKL-PRESS", "보도자료 본문", "지역 방언 문단", "sentence", "figure", "방언 유지 긍정 59.2%(보도자료)",
   "유지하여야 한다는 긍정 응답이 59.2%로 과반을 넘겼고, 부정적인 응답은 10% 미만으로 나타났다.",
   "지역 방언 유지·존속 필요성 긍정 59.2%, 부정 10% 미만(보고서 기준 7.4%, Aside)", applies="전국",
   rel=("CHK-K00-NIKLP-001", "CHK-K00-NIKLP-003"))
ch("CHK-K00-NIKLP-003", "SRC-K00-NIKL-PRESS", "보도자료 본문", "지역 방언 문단", "sentence", "figure", "2020년 대비 약 8.3%p 증가",
   "이는 지난 2020년 조사에 비해 약 8.3%p 증가한 결과로, 지역 방언을 유지해야 한다는 인식이 5년 전에 비해 높아진 것으로 풀이된다.",
   "2020년 값은 50.9%(2020년 보고서, Aside)", applies="전국", rel=("CHK-K00-NIKLP-002",))
ch("CHK-K00-NIKLR-001", "SRC-K00-NIKL-REPORT", "연구 보고서 상세", "서지 정보", "meta", "fact", "보고서 서지",
   "2025년 국민의 언어 의식 조사\n연구책임자\n이은빈\n펴낸 곳\n국립국어원\n펴낸 때\n2025",
   "보고서 PDF는 미보관. 첨부 파일명 '2025년 국민의 언어 의식 조사_결과 보고서(F).pdf'", applies="전국", loc="보고서 상세 페이지")
ch("CHK-K00-KCI-001", "SRC-K00-KCI-PAPER", "논문 상세", "초록(국문)", "sentence", "condition", "논문 조사 대상",
   "이를 위해 대구 지역 20대 대학생 38명을 대상으로 본인 및 동일 세대의 언어 인식과 부모 세대와의 차이에 대한 설문 조사를 실시하였다.",
   "논문 표본은 '대구 지역 20대 대학생 38명' — 기사·MD의 '경북 20대(경북 표본)'와 다름", applies="대구 지역 20대 대학생 38명",
   loc="KCI ART003310657 > 초록", rel=("CHK-K00-KCI-002",))
ch("CHK-K00-KCI-002", "SRC-K00-KCI-PAPER", "논문 상세", "서지 정보", "meta", "fact", "논문 서지",
   "2026, vol.62,pp. 161-193 (33 pages)\n발행기관 :영주어문학회", "『영주어문』 62권 161~193쪽(2026)", applies="학술",
   loc="KCI ART003310657 > 서지", rel=("CHK-K00-KCI-001",))
for key, name in [("JEJU", "제주어 보전 및 육성 조례 [시행 2025. 3. 19.] [제주특별자치도조례 제3919호, 2025. 3. 19., 일부개정]"),
                  ("JEONBUK", "[시행 2024. 1. 18.] [전북특별자치도조례 제5399호, 2023. 12. 8., 일부개정]"),
                  ("CHANGWON", "[시행 2026. 2. 13.] [경상남도창원시조례 제2291호, 2026. 2. 13., 일부개정]"),
                  ("DAEGU", "[시행 2019. 10. 30.] [대구광역시조례 제5354호, 2019. 10. 30., 제정]")]:
    ch(f"CHK-K00-ORD-{key}-001", f"SRC-K00-ORD-{key}", "자치법규 머리", "현행판 정보", "meta", "fact", f"{key} 조례 현행판 머리",
       name, "현행판의 시행일·조례번호·개정 구분(최초 제정일은 source_documents.published_date, Aside 확인)",
       applies={"JEJU": "제주", "JEONBUK": "전북", "CHANGWON": "창원", "DAEGU": "대구"}[key], loc="law.go.kr 자치법규 본문 머리")
ch("CHK-K00-DGP257024-001", "SRC-K00-DGP-257024", "보도자료 본문", "앞산 전망대 문단", "sentence", "fact", "앞산 전망대 키오스크 사투리 퀴즈",
   "또한 앞산 전망대에서는 키오스크를 통한 대구 사투리퀴즈 등 콘텐츠 체험을 비롯해",
   "2022-10-31 대구시 발표: 새단장한 앞산 전망대(2022년 11월부터 개방)에 사투리 퀴즈 키오스크", applies="대구 남구 앞산 전망대",
   period="2022-11~", loc="보도자료 본문")
ch("CHK-K00-DGP258646-001", "SRC-K00-DGP-258646", "보도자료 본문", "프로그램 문단", "sentence", "fact", "2023 시민주간 사투리 프로그램(보도자료)",
   "▲사투리, 이쁘다 아이가가 운영된다", "2023 대구시민주간 프로그램(대구 사투리 전시·공연)", applies="대구", period="2023-02")

nch("CHK-K00-HK0621-001", "SRC-K00-NEWS-HK-20260621", "제목", "fact", "인용된 검색 결과 기사 제목",
    "대구시, 2026 대구치맥페스티벌 다음달 1일 개막", "MD가 '대구 사투리 축제 공백' 근거로 든 기사 — 치맥 축제 기사", applies="대구")

# ---- 주장
cl("CLM-K00-H-01", "머리말", "기준", "rule", "자료 기준일 2026-10-31, 조사 기간 2022-01 ~ 2026-10", "", "작성자 기준",
   [("SRC-K00-MD", "CHK-K00-MD-001", USR, "interpretation", "작성자 조사 범위 규칙")])
cl("CLM-K00-G-01", "출처 등급", "①②③", "rule", "출처 등급 ① 공식(학술 포함) / ② 기사 / ③ 비공식, 조사 순서와 사용 원칙", "", "작성자 기준",
   [("SRC-K00-MD", "CHK-K00-MD-002", USR, "interpretation", ""), ("SRC-K00-MD", "CHK-K00-MD-003", USR, "interpretation", ""),
    ("SRC-K00-MD", "CHK-K00-MD-004", USR, "interpretation", "")])
cl("CLM-K00-G-02", "출처 등급", "독립 근거", "rule", "같은 필자·기사·원출처는 독립 근거 1건", "", "작성자 기준",
   [("SRC-K00-MD", "CHK-K00-MD-005", USR, "interpretation", "")])
cl("CLM-K00-L-01", "라벨", "지역", "rule", "B~D 자료(경북·경상권·전국·해외)는 대구 사실로 일반화하지 않음", "", "작성자 기준",
   [("SRC-K00-MD", "CHK-K00-MD-006", USR, "interpretation", "")])
cl("CLM-K00-L-02", "라벨", "검증 수준", "rule", "'요약 기반'은 인용 전 원문 대조 필요", "", "작성자 기준",
   [("SRC-K00-MD", "CHK-K00-MD-007", USR, "interpretation", "")])
cl("CLM-K00-P-01", "기간 예외", "범위", "rule", "지침 v2는 방언의 역사·형성·언어적 특성 과거 연구를 예외로 허용, 그 외 2022년 이전은 기간외 참고", "", "사투리_리서치지침_v2",
   [("SRC-K00-MD", "CHK-K00-MD-008", USR, "interpretation", "지침 v2 원문(kimseunghee_사투리_리서치지침_v2.md)은 이 패키지에서 대조하지 않음"),
    ("SRC-K00-MD", "CHK-K00-MD-009", USR, "interpretation", "")])
cl("CLM-K00-A-01", "자산 판정", "3질문", "rule", "자산 판정 3질문: 고유성(대구 직접)·지속성(2회 이상 또는 운영 중)·활용성(공식 수치 1개 이상, 가안)", "", "작성자 기준",
   [("SRC-K00-MD", "CHK-K00-MD-010", USR, "interpretation", ""), ("SRC-K00-MD", "CHK-K00-MD-011", USR, "interpretation", ""),
    ("SRC-K00-MD", "CHK-K00-MD-012", USR, "interpretation", "")])
cl("CLM-K00-C1-01", CORE, "1", "proposal", "대구 단독 자산 0건(3질문 모두 통과한 대구 사례 없음)", "", "작성자 판단",
   [("SRC-K00-MD", "CHK-K00-MD-013", USR, "interpretation", "판정 기준 적용 결과. 외부 사실이 아님")])
cl("CLM-K00-C1-02", CORE, "1", "fact", "자산 후보: 경북대 사투리 백일장", "②", "매일신문 2026-10-08",
   [("SRC-K00-NEWS-IM-20261008", "CHK-K00-IM1008-001", ORI, "match", "참가자 수·회차 없음 — 활용성·지속성 근거 부족이라는 MD 판단과 맞음")])
cl("CLM-K00-C1-03", CORE, "1", "fact", "자산 후보: 대구시민주간 사투리 프로그램", "②", "경북매일 2023-02-19",
   [("SRC-K00-NEWS-KB-20230219", "CHK-K00-KB0219-001", ORI, "match", "2023년 1회"),
    ("SRC-K00-DGP-258646", "CHK-K00-DGP258646-001", ALT, "match", "대구시 보도자료(2023-02-20)"),
    ("SRC-K00-NEWS-HK-20260218", "", ALT, "unverifiable", "2026 시민주간 기사 본문에는 사투리 프로그램이 없음 — 반복 운영 근거 없음")])
cl("CLM-K00-C1-04", CORE, "1", "fact", "자산 후보: 앞산전망대 사투리 퀴즈 미디어보드", "②", "매일신문 2026-03-23",
   [("SRC-K00-NEWS-IM-20260323", "CHK-K00-IM0323-005", ORI, "match", "사진 설명"),
    ("SRC-K00-DGP-257024", "CHK-K00-DGP257024-001", ALT, "match", "대구시 보도자료(2022-10-31): 2022년 11월 개방 앞산 전망대에 사투리 퀴즈 키오스크 — MD 13번이 '설치 시기 없음'이라 한 부분의 공식 근거")])
cl("CLM-K00-C1-05", CORE, "1", "fact", "자산 후보: AI허브 경상 방언 데이터", "①", "aihub.or.kr",
   [("SRC-K00-AIHUB-119", "CHK-K00-AIHUB-001", ORI, "match", "경상도 단위 — 대구 단독 아님")])
cl("CLM-K00-C2-01", CORE, "2", "condition", "국립국어원 국민의 언어 의식 조사(2025), 20~69세 5,000명", "②(원자료 ① 확인 필요)", "뉴시스 2026-01-27",
   [("SRC-K00-NEWS-NSIS-20260127", "CHK-K00-NSIS-001", ORI, "match", ""),
    ("SRC-K00-NIKL-PRESS", "CHK-K00-NIKLP-001", ALT, "match", "국립국어원 보도자료로 공식 확인"),
    ("SRC-K00-NIKL-REPORT", "CHK-K00-NIKLR-001", ALT, "match", "보고서 존재·서지 확인")])
cl("CLM-K00-C2-02", CORE, "2", "figure", "방언 유지 필요 59.2%(2020 대비 +8.3%p)", "②", "뉴시스 2026-01-27",
   [("SRC-K00-NEWS-NSIS-20260127", "CHK-K00-NSIS-002", ORI, "match", ""),
    ("SRC-K00-NEWS-NSIS-20260127", "CHK-K00-NSIS-003", ORI, "match", ""),
    ("SRC-K00-NIKL-PRESS", "CHK-K00-NIKLP-002", ALT, "match", ""),
    ("SRC-K00-NIKL-PRESS", "CHK-K00-NIKLP-003", ALT, "match", "공식 표현은 '약 8.3%p'")])
cl("CLM-K00-C2-03", CORE, "2", "figure", "복수 표준어 인정 긍정 47.7%", "②", "뉴시스 2026-01-27",
   [("SRC-K00-NEWS-NSIS-20260127", "CHK-K00-NSIS-004", ORI, "match", ""),
    ("SRC-K00-NIKL-REPORT", "", ALT, "unverifiable", "보고서 19·79·80쪽(긍정 47.7%, 부정 11.7%)은 Aside 보고 — PDF 미보관")])
cl("CLM-K00-C3-01", CORE, "3", "figure", "경북 20대: 부모·고향 친구 41.3%, 교수 0%, 아르바이트 2.7%", "②(논문 원문 미확인)", "매일신문 2026-03-23",
   [("SRC-K00-NEWS-IM-20260323", "CHK-K00-IM0323-002", ORI, "match", "기사 수치와 일치. 기사 표시 날짜는 2026-04-03"),
    ("SRC-K00-KCI-PAPER", "", ALT, "unverifiable", "논문 초록·공개 미리보기에 이 수치 없음(본문 미열람)")])
cl("CLM-K00-C3-02", CORE, "3", "condition", "이 수치는 경북 표본이며 대구 단독 아님", "", "작성자 판단",
   [("SRC-K00-KCI-PAPER", "CHK-K00-KCI-001", ORI, "mismatch", "논문 초록의 조사 대상은 '대구 지역 20대 대학생 38명' — 기사 표현('경북 20대')을 따른 MD 판단과 다름. 표본 38명으로 소규모"),
    ("SRC-K00-NEWS-IM-20260323", "CHK-K00-IM0323-002", ALT, "faithful_summary", "MD가 직접 인용한 기사는 '경북 20대'로 씀(수치의 원래 출처는 논문)")])
cl("CLM-K00-C4-01", CORE, "4", "fact", "대구 사투리 축제는 검색에서 확인되지 않음(치맥·떡볶이·판타지아 등 다른 주제만 나옴, 검색 1회)", "②", "헤럴드경제 2026-06-21",
   [("SRC-K00-NEWS-HK-20260621", "CHK-K00-HK0621-001", ORI, "interpretation", "인용 기사는 치맥 축제 기사로 '사투리'가 없음 — '없음'은 검색 결과에 따른 판단. Aside가 대구시 누리집 '사투리' 검색(92건, 시정소식 56건 제목)에서도 사투리 축제를 찾지 못함 — 부재를 확정하지는 못함")])
cl("CLM-K00-C5-01", CORE, "5", "fact", "대구 지역어 조례는 찾지 못함(없다고 단정 불가)", "-", "law.go.kr",
   [("SRC-K00-ORD-DAEGU", "CHK-K00-ORD-DAEGU-001", ALT, "scope_mismatch", "지역어 단독 조례는 없지만(Aside: 사투리·방언·지역어 제목 검색 0건) 「대구광역시 국어 진흥 조례」(2019 제정)가 있고 제3조②에 지역어 보전 노력 조항이 있음(Aside 확인)")])
cl("CLM-K00-C5-02", CORE, "5", "fact", "창원 조례(2024) 확인", "②", "메트로서울 2024-03-11",
   [("SRC-K00-ORD-CHANGWON", "CHK-K00-ORD-CHANGWON-001", ALT, "scope_mismatch", "2013 제정 「창원시 국어 진흥 조례」를 2024-03-29 일부개정해 지역어 보전을 넣고 이름을 바꿈(Aside) — 2024는 제정 연도가 아님")])
cl("CLM-K00-C5-03", CORE, "5", "fact", "전북 조례(2021) 확인", "②", "전북일보 2025-06-07",
   [("SRC-K00-ORD-JEONBUK", "CHK-K00-ORD-JEONBUK-001", ALT, "mismatch", "최초 제정 2014-06-27, 2021-11-03은 전부개정(Aside). '2021 제정'은 틀림")])
cl("CLM-K00-C5-04", CORE, "5", "fact", "제주 조례(2007) 확인", "②", "서울신문 2016-08-22",
   [("SRC-K00-ORD-JEJU", "CHK-K00-ORD-JEJU-001", ALT, "match", "2007-09-27 제정(조례 제280호, Aside). MD 13번의 '서울신문 2008 vs 전북일보 2007' 충돌은 2007로 정리됨")])
cl("CLM-K00-C6-01", CORE, "6", "proposal", "정량 근거 미확보: 사투리 굿즈·변환기·타지역 2030 인식 설문·대구 세대별 사용 통계", "", "작성자 판단",
   [("SRC-K00-MD", "CHK-K00-MD-014", USR, "interpretation", "미확보 목록(외부 사실 아님)")])

# ---- 정형 데이터
FIG = []


def fg(rid, domain, subject, metric, num, text, unit, cur="", vat="not_stated", qty="", year="", ps="", pe="",
       status="reported", sid="", cid="", clm="", note=""):
    FIG.append(dict(record_id=rid, domain=domain, subject=subject, metric=metric, value_numeric=num, value_text=text,
                    unit=unit, currency=cur, vat_basis=vat, quantity_basis=qty, base_year=year, period_start=ps,
                    period_end=pe, value_status=status, source_id=sid, chunk_id=cid, claim_id=clm, note=note))


fg("FIG-K00-001", "statistic", "2025 국민의 언어 의식 조사", "표본 수", "5000", "5,000명", "persons", year="2025", ps="2025-09-01", pe="2025-10-31",
   sid="SRC-K00-NIKL-PRESS", cid="CHK-K00-NIKLP-001", clm="CLM-K00-C2-01", note="만 20~69세, 전국. 조사 기간은 보고서 기준(Aside)")
fg("FIG-K00-002", "statistic", "2025 국민의 언어 의식 조사", "지역 방언 유지 필요 긍정", "59.2", "59.2%", "percent", year="2025",
   sid="SRC-K00-NIKL-PRESS", cid="CHK-K00-NIKLP-002", clm="CLM-K00-C2-02", note="전국 표본, 대구 분리 불가")
fg("FIG-K00-003", "statistic", "2025 국민의 언어 의식 조사", "2020년 대비 증감", "8.3", "약 8.3%p", "percentage_point", year="2025",
   sid="SRC-K00-NIKL-PRESS", cid="CHK-K00-NIKLP-003", clm="CLM-K00-C2-02")
fg("FIG-K00-004", "statistic", "2020 국민의 언어 의식 조사", "지역 방언 유지 필요 긍정", "", "", "percent", year="2020", status="unconfirmed",
   note="Aside 보고 50.9%(2020년 보고서 77·78쪽) — 원문 미보관이라 값 칸 비움")
fg("FIG-K00-005", "statistic", "2025 국민의 언어 의식 조사", "복수 표준어 인정 긍정", "47.7", "47.7%", "percent", year="2025",
   sid="SRC-K00-NEWS-NSIS-20260127", cid="CHK-K00-NSIS-004", clm="CLM-K00-C2-03", note="공식 보고서 값은 Aside 보고(미보관)")
for i, (who, v) in enumerate([("부모", "41.3"), ("고향 친구", "41.3"), ("교수", "0"), ("아르바이트", "2.7")], 6):
    fg(f"FIG-K00-{i:03d}", "statistic", "청년층 상황별 방언 사용(기사 보도)", f"방언 사용 비율 — {who}", v, f"{v}%", "percent",
       status="actual_zero" if v == "0" else "reported", sid="SRC-K00-NEWS-IM-20260323", cid="CHK-K00-IM0323-002", clm="CLM-K00-C3-01",
       note="기사는 '경북 20대', 논문 초록은 '대구 지역 20대 대학생 38명'")
fg("FIG-K00-010", "statistic", "청년층 방언 사용량 자가 평가(기사 보도)", "점수 — 경북 20대(기사 표현)", "70.4", "70.4점", "points",
   sid="SRC-K00-NEWS-IM-20260323", cid="CHK-K00-IM0323-003")
fg("FIG-K00-011", "statistic", "청년층 방언 사용량 자가 평가(기사 보도)", "점수 — 전북 20대", "37.8", "37.8점", "points",
   sid="SRC-K00-NEWS-IM-20260323", cid="CHK-K00-IM0323-003")
fg("FIG-K00-012", "statistic", "청년층 방언 보존 필요성(기사 보도)", "찬성 비율", "83.6", "83.6%", "percent", sid="SRC-K00-NEWS-IM-20260323",
   cid="CHK-K00-IM0323-004")
fg("FIG-K00-013", "statistic", "논문 표본", "조사 대상 수", "38", "38명", "persons", year="2026", sid="SRC-K00-KCI-PAPER", cid="CHK-K00-KCI-001",
   clm="CLM-K00-C3-02", note="대구 지역 20대 대학생")
fg("FIG-K00-014", "spec", "AI Hub 한국어 방언 발화(경상도)", "화자 수(하한)", "", "2000명 이상", "persons", sid="SRC-K00-AIHUB-119",
   cid="CHK-K00-AIHUB-001", clm="CLM-K00-C1-05", note="'이상' 하한값이라 숫자 칸 비움")
fg("FIG-K00-015", "spec", "AI Hub 한국어 방언 발화(경상도)", "음성 시간(하한)", "", "3000 시간 이상", "hours", sid="SRC-K00-AIHUB-119",
   cid="CHK-K00-AIHUB-001", note="하한값")
fg("FIG-K00-016", "spec", "AI Hub 한국어 방언 발화(경상도)", "전사 어절(하한)", "", "50 만건 이상", "records", sid="SRC-K00-AIHUB-119",
   cid="CHK-K00-AIHUB-002", note="하한값")
for i, (key, name, d) in enumerate([("JEJU", "제주어 보전 및 육성 조례", "2007-09-27"), ("JEONBUK", "전북특별자치도 국어 진흥 조례", "2014-06-27"),
                                    ("CHANGWON", "창원시 국어 진흥과 지역어 보전에 관한 조례", "2013-12-30"),
                                    ("DAEGU", "대구광역시 국어 진흥 조례", "2019-10-30")], 17):
    fg(f"FIG-K00-{i:03d}", "program", name, "최초 제정일", "", d, "date", ps=d, sid=f"SRC-K00-ORD-{key}", cid=f"CHK-K00-ORD-{key}-001",
       clm={"JEJU": "CLM-K00-C5-04", "JEONBUK": "CLM-K00-C5-03", "CHANGWON": "CLM-K00-C5-02", "DAEGU": "CLM-K00-C5-01"}[key],
       note="대구는 보관본 머리에서 확인, 나머지 최초 제정일은 Aside 확인(현행판 머리만 보관)")
fg("FIG-K00-021", "statistic", "자산 후보 활용성 수치", "참가자·방문객 수(백일장·시민주간·앞산 퀴즈)", "", "", "persons", status="not_available",
   note="세 후보 모두 원문에 참가·이용 수치 없음")

PLACE_LISTS = []
CONFLICT_PAIRS = []
EXCEPTION_PAIRS = []
RULE_ABOUT_PAIRS = [("CHK-K00-MD-006", "CHK-K00-IM0323-002")]
ASIDE_ONLY = set()

RULES = [
    ("RULE-K00-001", "source_grade", "② 기사 수치는 원자료 확인 전까지 '요약 기반'으로 표시하고 확정 사실로 답하지 않는다.", "block_as_fact",
     "source_grade = 'B'", "SRC-K00-MD", "CHK-K00-MD-003"),
    ("RULE-K00-002", "source_grade", "③ 비공식 자료(칼럼·민간·블로그·SNS)는 반응·참고용으로만 쓰고 링크를 붙인다.", "warn", "비공식 출처", "SRC-K00-MD", "CHK-K00-MD-004"),
    ("RULE-K00-003", "region", "경북·경상권·전국·해외 자료는 대구의 사실로 일반화하지 않는다.", "block", "applies_to 가 대구가 아님", "SRC-K00-MD", "CHK-K00-MD-006"),
    ("RULE-K00-004", "count", "같은 필자·같은 기사·같은 원출처는 독립 근거 1건으로 센다.", "warn", "근거 수 계산", "SRC-K00-MD", "CHK-K00-MD-005"),
    ("RULE-K00-005", "period", "2022년 이전 자료는 방언 역사·형성·언어적 특성 연구를 빼고 '기간외 참고'로 판정에서 제외한다.", "warn",
     "발행일 < 2022-01-01", "SRC-K00-MD", "CHK-K00-MD-009"),
    ("RULE-K00-006", "sample", "청년층 방언 사용 수치(41.3% 등)는 표본 정의가 기사('경북 20대')와 논문 초록('대구 지역 20대 대학생 38명')이 다르므로 표본과 함께만 인용한다.",
     "warn", "chunk_id = 'CHK-K00-IM0323-002'", "", ""),
]
RULE_TARGETS = {}

ISSUES = [
    ("ISS-K00-001", "sample_mismatch", "CLM-K00-C3-02", "SRC-K00-KCI-PAPER", "논문 표본은 대구 대학생 38명인데 기사·MD는 '경북 20대(경북 표본)'로 적음", "MD 03·04번과 개요 수정"),
    ("ISS-K00-002", "mismatch", "CLM-K00-C5-03", "SRC-K00-ORD-JEONBUK", "전북 조례 '2021 제정' → 실제 2014 제정, 2021 전부개정", "MD 09번·개요 수정"),
    ("ISS-K00-003", "scope_mismatch", "CLM-K00-C5-02", "SRC-K00-ORD-CHANGWON", "창원 '2024 조례' → 2013 제정, 2024 일부개정으로 지역어 보전 추가", "표현 수정"),
    ("ISS-K00-004", "scope_mismatch", "CLM-K00-C5-01", "SRC-K00-ORD-DAEGU", "대구 지역어 단독 조례는 없으나 국어 진흥 조례(2019) 제3조②에 지역어 보전 노력 조항", "MD '찾지 못함'을 '단독 조례 없음, 국어 진흥 조례에 조항 있음'으로 수정"),
    ("ISS-K00-005", "date_mismatch", "CLM-K00-C3-01;CLM-K00-C1-04", "SRC-K00-NEWS-IM-20260323", "매일신문 기사: MD 발행일 2026-03-23(URL), 기사 표시 2026-04-03", "12번 CSV 날짜 수정"),
    ("ISS-K00-006", "resolved_conflict", "CLM-K00-C5-04", "SRC-K00-ORD-JEJU", "제주 조례 2007/2008 충돌 → 2007-09-27 제정으로 정리(Aside 확인)", "13번 파일 갱신"),
    ("ISS-K00-007", "new_official_source", "CLM-K00-C1-04", "SRC-K00-DGP-257024", "앞산 사투리 퀴즈 설치 시기 공식 근거 발견(2022-11 개방)", "자산 판정 지속성 재검토"),
    ("ISS-K00-008", "broken_links", "", "SRC-K00-MD", "MD의 상대 링크(01_방언특성변이.md, ../_rules.md, ../사투리_리서치지침_v2.md, minju/민주개인자료조사)가 2026-11-24 파일명 정리 이후 모두 없는 경로", "kimseunghee_ 접두 파일명으로 링크 수정"),
    ("ISS-K00-009", "not_stored", "CLM-K00-C2-03", "SRC-K00-NIKL-REPORT", "국립국어원 결과 보고서 PDF(11.62MB)·보도자료 hwpx 미보관 — 47.7%·2020년 50.9%·쪽 번호는 Aside 보고", "필요 시 PDF 내려받아 originals/에 추가"),
    ("ISS-K00-010", "unverified_detail", "CLM-K00-C3-01", "SRC-K00-KCI-PAPER", "41.3%·0%·2.7% 등은 논문 본문에서 미확인(초록에 없음)", "논문 원문 열람"),
    ("ISS-K00-011", "absence_claim", "CLM-K00-C4-01", "", "'대구 사투리 축제 없음'은 검색 기반 — 대구시 누리집 검색에서도 없음(Aside)이지만 부재를 확정할 수는 없음", "확정 표현 피하기"),
    ("ISS-K00-012", "official_internal_note", "CLM-K00-C2-01", "SRC-K00-NIKL-REPORT", "Aside 보고: '언어 예절' 관심도가 보도자료 68.7% vs 보고서 요약 69.7%로 다름(이 MD의 주장과는 무관)", "참고"),
    ("ISS-K00-013", "ocr_unreviewed", "", "", "OCR 대상 스캔 문서 없음(해당 없음)", ""),
]

SEARCH_TESTS = [
    ("ST-K00-01", "방언 유지", "false", "CHK-K00-NIKLP-002", "국립국어원 공식 수치"),
    ("ST-K00-02", "5,000명", "false", "CHK-K00-NIKLP-001", "조사 표본"),
    ("ST-K00-03", "8.3%p", "false", "CHK-K00-NIKLP-003", "2020 대비"),
    ("ST-K00-04", "복수 표준어", "true", "CHK-K00-NSIS-004", "기사 값(참고 포함)"),
    ("ST-K00-05", "대학생 38명", "false", "CHK-K00-KCI-001", "논문 표본"),
    ("ST-K00-06", "아르바이트", "true", "CHK-K00-IM0323-002", "상황별 사용 비율(기사)"),
    ("ST-K00-07", "사투리퀴즈", "false", "CHK-K00-DGP257024-001", "앞산 전망대 키오스크"),
    ("ST-K00-08", "이쁘다 아이가", "false", "CHK-K00-DGP258646-001", "시민주간 프로그램"),
    ("ST-K00-09", "백일장", "true", "CHK-K00-IM1008-001", "경북대 백일장(기사)"),
    ("ST-K00-10", "경상도 방언 발화", "false", "CHK-K00-AIHUB-001", "AI Hub 데이터"),
    ("ST-K00-11", "대구광역시조례", "false", "CHK-K00-ORD-DAEGU-001", "대구 국어 진흥 조례"),
    ("ST-K00-12", "제주특별자치도조례", "false", "CHK-K00-ORD-JEJU-001", "제주어 조례"),
]

TEMPLATE = {
    "template_id": "TPL-K00-OVERVIEW",
    "md_id": MD_ID,
    "description": "kimseunghee_00_개요.md 고정 양식(조사 묶음 개요 문서). 값이 아니라 양식만 담음",
    "front_matter": ["주제", "성격", "자료 기준일", "조사 기간", "작성 방식", "근거 문서"],
    "sections": [
        {"key": "FILES", "title": "파일 구성", "kind": "table", "columns": ["파일", "하위 키워드"]},
        {"key": "GRADE", "title": "출처 등급 (조사 순서)", "kind": "table", "columns": ["등급", "범위", "사용 원칙"]},
        {"key": "LABEL", "title": "라벨", "kind": "list", "groups": ["내용", "지역", "검증 수준"]},
        {"key": "PERIOD", "title": "기간 예외", "kind": "list"},
        {"key": "ASSET", "title": "자산 판정", "kind": "table", "columns": ["질문", "기준"]},
        {"key": "CORE", "title": "전체 핵심 (확인된 것만)", "kind": "ordered_list"},
    ],
}
TEMPLATE_FILE = "json/md_template_kimseunghee_00.json"
MD_CODES = {
    "source_grade_md": {"①": "공식(공공기관·지자체·통계·학술)", "②": "기사", "③": "비공식(칼럼·민간·블로그·SNS)"},
    "content_label": {"확인": "출처로 확인된 사실", "해석": "자료 기반 분석", "가설": "검증 필요", "추정": "계산·가정 수치", "미확인": "근거 미확보"},
    "region_label": ["대구 직접", "경북 참고", "경상권 참고", "전국 참고", "해외 참고"],
    "verification_level": {"원문 확인": "원문을 직접 열어 대조", "요약 기반": "검색 결과 요약으로만 확인"},
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
                             storage_object_path=(f"research-originals/kimseunghee_00/{os.path.basename(s['original_file_path'])}"
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
