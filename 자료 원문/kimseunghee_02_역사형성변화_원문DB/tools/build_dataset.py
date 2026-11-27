# -*- coding: utf-8 -*-
"""kimseunghee_02_역사형성변화.md 원문 대조 데이터 패키지 생성기(원문 프롬프트 v2 기준).

- ID는 이 파일에 고정(재실행해도 같음). kb 스키마를 다른 패키지와 함께 쓰므로 모든 ID에 K02 를 붙인다.
- 청크는 답변에 인용할 내용만 만든다(서지·공포일·시행일만 담은 청크 없음 — 그런 정보는 source_documents 컬럼).
- 청크 본문은 실행할 때마다 보관 원문에서 글자 그대로 있는지 다시 대조한다(공백만 무시).
- 기준 MD blob 이 현재 main 과 다르면 모든 주장을 stale 로 표시한다.

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
import subprocess
import sys

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PKG, "data")
PKG_CODE = "K02"
ACCESSED = "2026-11-27"
VERSION = "v1"

MD_ID = "MD-K02"
MD_PATH = "local 리서치/kimseunghee_02_역사형성변화.md"
MD_LAST_COMMIT = "5f61dc486f15fe7db07c025d9e9d065fcc32dda0"
MD_MAIN_HEAD = "a7043e7b98f0d1c61f7ea7bc1355f7be8e1aedb0"
MD_BLOB = "caea051defb02631e2b0599b05e26f3ce450cbd4"
MD_SOURCE_ID = "SRC-K02-MD"
MD_TITLE = "02. 대구 방언의 역사·형성·변화"
MD_WRITTEN = "2026-10-31"
MD_VERSION = "사투리_v02_V4"
MD_NOTES = "written_date 는 문서의 '자료 기준일'. 기준 main a7043e7, blob caea051. 원본은 originals/SRC-K02-MD.md"


def _current_blob():
    try:
        r = subprocess.run(["git", "rev-parse", "--verify", "-q", "origin/main:" + MD_PATH], cwd=PKG, capture_output=True, text=True)
        out = r.stdout.strip()
        return out if r.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", out) else ""
    except Exception:  # noqa: BLE001
        return ""


_CUR = _current_blob()
STALE = bool(_CUR) and _CUR != MD_BLOB


def S(id_, title, publisher, doc_type, grade, url, pub, basis, ver, retrieval, ostatus, approval, rights, notes,
      attach="", period="", snapshot="", snapshot_sha=""):
    d = dict(id=id_, title=title, publisher=publisher, doc_type=doc_type, grade=grade, url=url, attach=attach, pub=pub,
             pub_basis=basis, period=period, ver=ver, retrieval=retrieval, ostatus=ostatus, snapshot=snapshot,
             approval=approval, rights=rights, notes=notes)
    if snapshot_sha:
        d["snapshot_sha"] = snapshot_sha
    return d


NEWS_R = "언론사 저작물 — 원문 재배포 안 함, URL과 짧은 발췌만 기록"
SOURCES = [
    S("SRC-K02-MD", "02. 대구 방언의 역사·형성·변화 (kimseunghee_02_역사형성변화.md)", "팀 내부(작성자 kimseunghee)", "user_authored",
      "U", "", "2026-10-31", "문서 '자료 기준일: 2026-10-31'", f"git blob {MD_BLOB}", "git show origin/main:<path>", "stored",
      "internal", "팀 내부 문서", "사용자 작성 원본. 판정·규칙의 원본으로만 사용"),
    S("SRC-K02-NKLIFE1998", "동남 방언(새국어생활 제8권 제4호, 1998 겨울)", "국립국어원(필자 이상규)", "official_web", "S",
      "https://www.korean.go.kr/nkview/nklife/1998_4/8-6.html", "", "본문에 발행일 없음(K01 패키지에서 목차로 1998_4호 확인)",
      "확인일 현재 웹페이지", "curl(K01 보관본 재사용)", "stored", "approved", "공공기관 웹페이지",
      "02-01 은 01-01 과 같은 자료"),
    S("SRC-K02-LAW-KUKEO", "국어기본법(본문 전체, 현행)", "법제처 국가법령정보센터 / 문화체육관광부(국어정책과)", "law", "S",
      "https://www.law.go.kr/법령/국어기본법", "2026-04-28", "'[법률 제21586호, 2026. 4. 28., 일부개정]'(공포일)",
      "법률 제21586호(시행 2026-10-29)", "aside + curl", "stored", "approved", "법령(저작권 보호 대상 아님)",
      "본문 HTML(lsInfoR.do?lsiSeq=285635)을 보관 — 조문 전체 포함. 제4조는 [전문개정 2011. 4. 14.]",
      attach="https://www.law.go.kr/LSW/lsInfoR.do?lsiSeq=285635&efYd=20261029", period="시행 2026-10-29~"),
    S("SRC-K02-ORD-JEJU-BODY", "제주어 보전 및 육성 조례(현행 본문)", "제주특별자치도 / 국가법령정보센터(자치법규)", "law", "S",
      "https://www.law.go.kr/LSW/ordinInfoR.do?ordinSeq=2023071", "2025-03-19", "'[제주특별자치도조례 제3919호, 2025. 3. 19., 일부개정]'",
      "조례 제3919호(시행 2025-03-19)", "aside + curl", "stored", "approved", "자치법규", "조문 전체 보관", period="시행 2025-03-19~"),
    S("SRC-K02-ORD-JEJU-HIST", "제주어 보전 및 육성 조례 연혁", "국가법령정보센터(자치법규)", "law", "S",
      "https://www.law.go.kr/LSW/ordinHstListR.do?ordinId=2117250", "2007-09-27", "연혁 '[조례 제280호, 2007. 9. 27., 제정]'(최초 제정)",
      "연혁 목록", "aside + curl", "stored", "approved", "자치법규", "연혁(제정·개정 이력)만 담은 표 — 청크로 만들지 않고 제정일 근거로만 사용"),
    S("SRC-K02-ORD-JEJU-2007", "제주어 보전 및 육성 조례(2007 제정본 본문)", "행정안전부 자치법규정보시스템(ELIS)", "law", "S",
      "https://www.elis.go.kr/allalr/selectAlrBdtOne?alrNo=50000007008080&histNo=001&menuNm=main", "2007-09-27",
      "'(제정) 2007-09-27 조례 제 280호'", "조례 제280호(제정본)", "aside + curl", "stored", "approved", "자치법규",
      "제정본 제1조가 국어기본법 제4조를 근거로 명시"),
    S("SRC-K02-UNESCO-2010", "New interactive atlas adds two more endangered languages (UNESCOPRESS, 웹 보관본)", "UNESCO (Internet Archive 2010-12-17 보관본)",
      "press_release", "S", "http://www.unesco.org/new/en/media-services/single-view/news/new_interactive_atlas_adds_two_more_endangered_languages",
      "2010-12-08", "페이지 표기 '08.12.2010'", "UNESCO 원 페이지는 현재 접속 불가 — 2010-12-17 보관본",
      "aside + curl", "stored", "approved", "UNESCO 보도자료", "보관본 URL: http://web.archive.org/web/20101217215446/...",
      attach="http://web.archive.org/web/20101217215446/http://www.unesco.org:80/new/en/media-services/single-view/news/new_interactive_atlas_adds_two_more_endangered_languages"),
    S("SRC-K02-UNESCO-ATLAS", "UNESCO Atlas of the World's Languages in Danger — Jeju(language-id-2724, 웹 보관본)", "UNESCO (Internet Archive 2022-05-20 보관본)",
      "official_web", "S", "http://www.unesco.org/languages-atlas/en/atlasmap/language-id-2724.html", "", "발행일 없음(보관본 수집 2022-05-20)",
      "2022-05-20 보관본(현행 WAL 접속 불가 — Aside)", "aside + curl", "stored", "approved", "UNESCO 웹페이지",
      "국가 목록에 'Republic of Korea(1)' — 등재 언어는 제주어 1개. 항목 상세 등급 문구는 스크립트로 불러와 보관본에 없음",
      attach="http://web.archive.org/web/20220520152241/http://www.unesco.org/languages-atlas/en/atlasmap/language-id-2724.html"),
    S("SRC-K02-RISS-A06", "한반도 영남지역의 基層方言圈 연구 시론(김덕호·이철희, 『영남학』 97, 2026)", "RISS — 경북대학교 영남문화연구원",
      "official_web", "A", "https://www.riss.kr/search/detail/DetailView.do?p_mat_type=1a0202e37d52c72d&control_no=19458f956808a364b7998d826d417196",
      "", "RISS 'No.97 [2026]'(월 없음)", "영남학 97", "aside + curl", "stored", "approved", "학술 서지·초록 페이지",
      "초록 공개. 본문 PDF는 미확보(로그인 필요 여부 미확인)"),
    S("SRC-K02-RISS-A05", "慶尙方言의 形成과 音韻的 分化(백두현, 『인문과학』 11, 1997)", "RISS — 경북대학교 인문과학연구소", "official_web", "A",
      "https://www.riss.kr/search/detail/DetailView.do?p_mat_type=1a0202e37d52c72d&control_no=4570861f03a7ec4cffe0bdc3ef48d419", "",
      "RISS 'Vol.11 [1997]'", "인문과학 11, 99-140", "aside + curl", "stored", "pending", "학술 서지 페이지",
      "서지만 있고 초록 없음 — 답변용 청크 없음. 본문 미확보(확보 계획: 경북대 학술지 원문 또는 도서관 열람)"),
    S("SRC-K02-NEWS-METRO-20240311", "창원시의회, '사투리' 보전 제도화 나선다… 개정안 가결", "메트로신문", "news", "B",
      "https://www.metroseoul.co.kr/article/20240311500609", "2024-03-11", "기사 '2024-03-11 16:39:17'", "확인일 현재 기사",
      "curl", "url_only_copyright", "reference_only", NEWS_R, "MD 02-02 출처", snapshot="metro_20240311.html",
      snapshot_sha="fead55b89e8efb4583c4129525a79232ddbbe3e838a0b0a01fe8fd1b2e7ae059"),
    S("SRC-K02-NEWS-SEOUL-20160822", "[명인·명물을 찾아서] 소멸 위기 제주語 연구 '외길'…", "서울신문", "news", "B",
      "https://m.go.seoul.co.kr/news/2016/08/22/20160822012003", "2016-08-21", "기사 '입력 2016-08-21 17:26'(URL 날짜 08-22)", "확인일 현재 기사",
      "curl", "url_only_copyright", "reference_only", NEWS_R, "MD 02-03 출처. 조례 '2008년'은 공식 연혁(2007)과 다름",
      snapshot="seoul_20160822.html", snapshot_sha="cffdb150c91a1b5107226d98acf8d56fd0dfe5b59f827bac5784073bd42d1d58"),
    S("SRC-K02-NEWS-KB-20241223", "사투리 글쓰기를 지역 문화운동으로(이상규 칼럼)", "경북매일", "news", "B",
      "https://kbmaeil.com/article/202412230414803", "2024-12-24", "기사 '등록일 2024-12-23 19:45, 게재일 2024-12-24'", "확인일 현재 기사",
      "curl", "url_only_copyright", "reference_only", NEWS_R, "MD 02-04 출처(③ 칼럼)", snapshot="kb_20241223.html",
      snapshot_sha="cdf6159e6a92a68dafe5b92bec44c506bf9bcd817cdd43903fdfdf2ea16f44a3"),
    S("SRC-K02-NEWS-YN-20220217", "[우리말과 한국문학] 경북 방언의 뿌리는(김덕호 칼럼)", "영남일보", "news", "B",
      "https://www.yeongnam.com/web/view.php?key=20220216010001819", "2022-02-17", "기사 '2022-02-17 07:21'", "확인일 현재 기사",
      "aside + curl", "url_only_copyright", "reference_only", NEWS_R, "Aside 발견. 대구 지역 고대 소국(달벌국) 언급",
      snapshot="yn_20220216.html", snapshot_sha="988f066d3b9fcb426e886745d0c57b34b98168c2d1233435da4cecb29e8d849a"),
]

C = []


def ch(cid, sid, sec, blk, btype, itype, title, text, ctx, region, applies="", cond="", period="", loc="", rel=()):
    C.append(dict(chunk_id=cid, source_id=sid, sec=sec, blk=blk, btype=btype, info_type=itype, short_title=title,
                  text_original=text, search_context=ctx, region=region, applies_to=applies, condition_text=cond,
                  period_text=period, locator=loc, related=list(rel)))


def nch(cid, sid, blk, itype, title, text, ctx, region, applies="", period="", rel=()):
    ch(cid, sid, "기사 본문", blk, "sentence", itype, title, text, ctx, region, applies, "", period, "본문", rel)


S98 = "SRC-K02-NKLIFE1998"
ch("CHK-K02-NK98-001", S98, "동남 방언", "방언 분화 문단", "sentence", "fact", "경상 방언은 낙동강을 경계로 동서로 나뉨",
   "김해-밀양-창녕-의령-합천-고령-성주-칠곡-선산-상주로 이어지는 낙동강을 경계로 하여 동과 서로 구분되고 있어 자연 환경과 방언 분화의 상관 관계를 알 수 있다.",
   "경상(동남) 방언의 동서 구분 경계는 낙동강(이상규, 국립국어원 새국어생활)", "경상", applies="경상 방언", loc="본문", rel=("CHK-K02-NK98-002",))
ch("CHK-K02-NK98-002", S98, "동남 방언", "음운 문단", "sentence", "fact", "대구 등 낙동강 동쪽은 ㅅ·ㅆ을 구별하지 않음",
   "청도, 경산, 달성, 칠곡, 고령,  군위, 영천, 경주, 청송, 포항, 영덕 지역, 곧 낙동강의 동쪽 지역으로 'ㅅ'과 'ㅆ'이 비변별적이다.",
   "대구를 중심으로 한 낙동강 동쪽 지역은 ㅅ과 ㅆ 발음을 구별하지 않음(문장 앞부분 '대구를 중심으로 하여')", "대구", applies="대구·경북 동남부",
   loc="본문(각주 5 앞)", rel=("CHK-K02-NK98-001",))
ch("CHK-K02-LAW-001", "SRC-K02-LAW-KUKEO", "제1장 총칙", "제4조(국가와 지방자치단체의 책무)", "article", "rule", "국가·지자체의 지역어 보전 노력 의무",
   "① 국가와 지방자치단체는 변화하는 언어 사용 환경에 능동적으로 대응하고, 국민의 국어능력 향상과 지역어 보전 등 국어의 발전과 보전을 위하여 노력하여야 한다.",
   "국어기본법 제4조 제1항: 지방자치단체(대구시 포함)는 지역어(사투리·방언) 보전 등을 위해 노력해야 함. 노력 의무이며 구체적 사업은 정하지 않음",
   "전국", applies="국가·지방자치단체", cond="노력 의무(강제 규정 아님)", period="현행(시행 2026-10-29), 제4조 전문개정 2011-04-14",
   loc="국어기본법 제4조 제1항")
ch("CHK-K02-JEJU-001", "SRC-K02-ORD-JEJU-BODY", "본문", "제1조(목적)", "article", "rule", "제주어 조례의 목적(현행)",
   "이 조례는 사라져가는 제주어의 보전과 육성을 통하여 지역의 문화와 역사를 계승하고, 이를 전승하고 발전시키기 위하여 필요한 사항을 규정함으로써 향토문화의 발전에 이바지함을 목적으로 한다.",
   "제주특별자치도 제주어 보전 및 육성 조례 제1조(현행 2025-03-19). 대구 조례 아님", "제주", applies="제주특별자치도",
   period="시행 2025-03-19~", loc="제1조", rel=("CHK-K02-JEJU-002",))
ch("CHK-K02-JEJU-002", "SRC-K02-ORD-JEJU-2007", "본문", "제1조(목적)", "article", "rule", "제주어 조례 제정본(2007)의 근거 법률",
   "이 조례는 「국어기본법」 제4조에 의거 제주어의 보전 및 육성을 통하여 지역의 문화와 역사를 계승하고",
   "2007-09-27 제정된 제주어 조례(조례 제280호) 제1조는 국어기본법 제4조를 근거로 명시. 제정 연도 2007의 근거 문서", "제주",
   applies="제주특별자치도", period="2007-09-27 제정본", loc="제정본 제1조", rel=("CHK-K02-LAW-001", "CHK-K02-JEJU-001"))
ch("CHK-K02-UN-001", "SRC-K02-UNESCO-2010", "보도자료 본문", "제주어 문단", "sentence", "fact", "유네스코: 제주어는 '아주 심각한 위기' 언어",
   "As for Jeju, it is a critically endangered language spoken by no more than 10,000 people on Jeju Island in the Republic of Korea.",
   "UNESCO 2010-12-08 발표: 제주어는 critically endangered(아주 심각한 위기), 사용자 1만 명 이하. 경상 방언이 아님", "제주",
   applies="제주어", period="2010-12", loc="UNESCOPRESS 2010-12-08 본문", rel=("CHK-K02-UN-002",))
ch("CHK-K02-UN-002", "SRC-K02-UNESCO-2010", "보도자료 본문", "도입 문단", "sentence", "fact", "제주어가 유네스코 위기 언어 아틀라스에 추가됨",
   "Koro (Arunachal Pradesh, India) and Jeju (Jeju Island, Republic of Korea) have just been included in UNESCO’s new enhanced online Atlas of the World’s Languages in Danger.",
   "2010년 12월 유네스코 위기 언어 아틀라스에 제주어 추가", "제주", applies="제주어", period="2010-12", loc="UNESCOPRESS 첫 문장",
   rel=("CHK-K02-UN-001",))
ch("CHK-K02-UN-003", "SRC-K02-UNESCO-ATLAS", "아틀라스 검색", "국가 필터 목록", "list", "fact", "아틀라스의 한국 등재 언어 수",
   "Republic of Korea(1)\nNumber of languages found : 1\nJeju",
   "UNESCO 위기 언어 아틀라스(2022 보관본)에 한국 언어는 제주어 1개뿐 — 경상 방언은 등재되지 않음", "제주", applies="대한민국 언어",
   loc="atlasmap 국가 필터·검색 결과", rel=("CHK-K02-UN-001",))
ch("CHK-K02-RISS06-001", "SRC-K02-RISS-A06", "초록(국문)", "결과 문단", "sentence", "fact", "영남 기층방언권과 진한·변한 대응",
   "또한 각 기층방언권은 고대 진한･변한의 정치･문화권과 일정한 대응성을 보여, 고대 사회의 공간 질서가 후대 언어문화 속에 변형된 형태로 집적되었음을 시사하고 있다.",
   "김덕호·이철희(2026): 영남 방언권이 고대 진한·변한 정치·문화권과 대응. 대구만 따로 다루지 않음", "영남", applies="영남 방언",
   loc="RISS 초록", rel=("CHK-K02-RISS06-002",))
ch("CHK-K02-RISS06-002", "SRC-K02-RISS-A06", "초록(국문)", "결과 문단", "sentence", "fact", "방언 경계는 역사적 축적의 결과",
   "이는 현재의 방언 경계가 현대적 산물만이 아니라 역사적 층위의 축적된 결과임을 의미한다.", "영남 방언 경계는 고대부터 쌓인 결과라는 해석",
   "영남", applies="영남 방언", loc="RISS 초록", rel=("CHK-K02-RISS06-001",))
nch("CHK-K02-METRO-001", "SRC-K02-NEWS-METRO-20240311", "국어기본법 문단", "fact", "기사: 국어기본법의 방언 보전 노력",
    "이와 관련해 국어기본법은 지방자치단체가 '사투리', '방언' 등의 보전을 위해 노력할 것을 명시하고 있으나, 창원시에는 조례와 구체적인 계획, 사업이 없었다.",
    "창원시 조례 개정 기사(2024). 법 조문 원문은 CHK-K02-LAW-001", "전국", applies="지방자치단체", rel=("CHK-K02-LAW-001",))
nch("CHK-K02-SEOUL-001", "SRC-K02-NEWS-SEOUL-20160822", "유네스코 문단", "fact", "기사: 2010년 12월 제주어 등록",
    "유네스코는 2010년 12월 제주어를 ‘소멸 위기의 언어’로 등록했다.", "서울신문 2016", "제주", period="2010-12", rel=("CHK-K02-SEOUL-002",))
nch("CHK-K02-SEOUL-002", "SRC-K02-NEWS-SEOUL-20160822", "유네스코 문단", "fact", "기사: 4단계 '아주 심각하게 위기에 처한 언어'",
    "4단계인 ‘아주 심각하게 위기에 처한 언어’로 분류했다.", "기사의 '4단계'는 기사 표현(유네스코 원문은 critically endangered)", "제주",
    rel=("CHK-K02-SEOUL-001", "CHK-K02-UN-001"))
nch("CHK-K02-SEOUL-003", "SRC-K02-NEWS-SEOUL-20160822", "조례 문단", "fact", "기사: 2008년 제주어 조례(공식 연혁과 다름)",
    "제주도가 2008년 마련한 ‘제주어 육성 보존 조례’가 형식에 치우친 면이 없지 않다", "인터뷰 인용. 공식 연혁상 제정은 2007-09-27 — 이 연도는 쓰지 않음",
    "제주", rel=("CHK-K02-JEJU-002",))
nch("CHK-K02-KB1223-001", "SRC-K02-NEWS-KB-20241223", "칼럼 본문", "fact", "1933년 이후 표준어 교육과 방언 억제",
    "1933년 국어맞춤법통일안이 제정되면서 서울 중심, 교양인 중심의 표준어 교육이 자리를 차지하면서 방언은 저절로 금기시되었고 억제되었다.",
    "이상규 칼럼(③ 비공식): 1933년 이후 방언 억제. '표준어 제정'이라는 표현은 원문에 없음", "전국", rel=("CHK-K02-KB1223-002",))
nch("CHK-K02-KB1223-002", "SRC-K02-NEWS-KB-20241223", "칼럼 본문", "fact", "드라마에서 방언을 계급적 상징으로 사용",
    "심지어 드라마에서는 출연 인물의 신분이나 직업적 특성에 따라 특정 지역 사투리 사용자로 배정하여 방언을 계급적 상징으로 다루기도 하였다.",
    "이상규 칼럼: 드라마 속 사투리 배정", "전국", rel=("CHK-K02-KB1223-001",))
nch("CHK-K02-YN-001", "SRC-K02-NEWS-YN-20220217", "칼럼 본문", "fact", "대구 지역 고대 소국 달벌국",
    "골벌국(영천), 압독국(경산), 달벌국(대구·달성), 실직국(울진)이다.", "김덕호 칼럼: 1~2세기 초 사로국에 병합된 소국 가운데 달벌국(대구·달성)",
    "대구", rel=("CHK-K02-YN-002",))
nch("CHK-K02-YN-002", "SRC-K02-NEWS-YN-20220217", "칼럼 본문", "fact", "경북 고대 소국 12개와 낙동강 동서 문화",
    "고대 소국은 대략 12개인데, 낙동강을 기준으로 동부와 서부의 문화나 문명이 형성되었다고 볼 수 있다.", "김덕호 칼럼: 경북 중심 고대 소국 약 12개",
    "경북", rel=("CHK-K02-YN-001",))

M = "SRC-K02-MD"


def mch(cid, sec, itype, title, text, ctx, rel=()):
    ch(cid, M, sec, sec, "md_text", itype, title, text, ctx, "대구", applies="사투리 조사 02(역사·형성)", loc=f"MD {sec}", rel=rel)


mch("CHK-K02-MD-001", "2. 판정", "rule", "경상 방언 소멸위기 표현 금지",
    "경상 방언의 유네스코 등급은 검색에서 확인되지 않음 → **\"경상 방언이 소멸위기\"라고 쓰지 않음** [미확인]",
    "작성자 규칙: 제주어 등급을 경상·대구 방언에 옮기지 않음")
mch("CHK-K02-MD-002", "2. 판정", "fact", "역사·형성 자료는 정보", "모두 **정보**. 역사·형성은 반복·운영·수치 개념이 없어 자산 판정 대상이 아님 [해석]",
    "작성자 판정")

CLAIMS, LINKS = [], []


def cl(cid, sec, row, ctype, text, grade, cited, links):
    CLAIMS.append(dict(claim_id=cid, md_section=sec, row_key=row, claim_type=ctype, claim_text=text,
                       md_stated_grade=grade, md_stated_source=cited))
    for l in links:
        LINKS.append((cid,) + tuple(l))


ORI, ALT, USR, UNV = "original_confirmed", "alternative_official", "user_authored", "unverifiable"
cl("CLM-K02-0201-01", "1. 표준어 정책과 방언", "02-01", "fact", "경북·경남 방언 계통, 낙동강 경계(01-01과 같은 자료)", "①", "새국어생활 1998-4",
   [("SRC-K02-NKLIFE1998", "CHK-K02-NK98-001", ORI, "match", ""), ("SRC-K02-NKLIFE1998", "CHK-K02-NK98-002", ORI, "match", "")])
cl("CLM-K02-0202-01", "1. 표준어 정책과 방언", "02-02", "rule", "국어기본법이 지방자치단체가 사투리·방언 보전을 위해 노력하도록 명시(창원시 기사 인용)", "①(요약 기반)", "메트로신문 2024-03-11",
   [("SRC-K02-NEWS-METRO-20240311", "CHK-K02-METRO-001", ORI, "match", ""),
    ("SRC-K02-LAW-KUKEO", "CHK-K02-LAW-001", ALT, "faithful_summary", "법 조문은 '지역어 보전'(사투리·방언이라는 말은 없음). 노력 의무. MD의 '법령 원문 대조 필요' 해소")])
cl("CLM-K02-0203-01", "1. 표준어 정책과 방언", "02-03", "fact", "유네스코가 제주어를 2010년 12월 '아주 심각하게 위기에 처한 언어' 4단계로 등록", "②", "서울신문 2016-08-22",
   [("SRC-K02-NEWS-SEOUL-20160822", "CHK-K02-SEOUL-001", ORI, "match", ""),
    ("SRC-K02-NEWS-SEOUL-20160822", "CHK-K02-SEOUL-002", ORI, "match", ""),
    ("SRC-K02-UNESCO-2010", "CHK-K02-UN-001", ALT, "faithful_summary", "UNESCO 원문은 'critically endangered'. '4단계'는 기사의 표현"),
    ("SRC-K02-UNESCO-2010", "CHK-K02-UN-002", ALT, "match", "2010-12-08 발표")])
cl("CLM-K02-0203-02", "1. 표준어 정책과 방언", "02-03", "fact", "제주어 조례 제정 연도는 출처별로 2007/2008로 불일치(기사는 '2008년')", "②", "서울신문 2016-08-22",
   [("SRC-K02-NEWS-SEOUL-20160822", "CHK-K02-SEOUL-003", ORI, "match", "기사는 '2008년'"),
    ("SRC-K02-ORD-JEJU-2007", "CHK-K02-JEJU-002", ALT, "match", "공식 연혁: 2007-09-27 제정(조례 제280호) — 불일치는 2007로 정리됨. 2008은 쓰지 않음")])
cl("CLM-K02-0204-01", "1. 표준어 정책과 방언", "02-04", "fact", "1933년 국어맞춤법통일안 이후 표준어 중심 교육과 방언 억제, 드라마에서 방언을 계급적 상징으로 다룸", "③", "경북매일 칼럼 2024-12-23",
   [("SRC-K02-NEWS-KB-20241223", "CHK-K02-KB1223-001", ORI, "match", "원문에 '표준어 제정'이라는 표현 없음(MD 기록과 같음)"),
    ("SRC-K02-NEWS-KB-20241223", "CHK-K02-KB1223-002", ORI, "match", "")])
cl("CLM-K02-S0-01", "0. 핵심 요약", "형성사", "fact", "대구 방언의 형성사를 직접 다룬 자료는 확보하지 못함", "", "작성자 검색",
   [("SRC-K02-RISS-A06", "CHK-K02-RISS06-001", ALT, "scope_mismatch", "영남 방언권의 형성(진한·변한 대응)을 다룬 2026 논문이 있음 — 대구만 따로는 아님"),
    ("SRC-K02-NEWS-YN-20220217", "CHK-K02-YN-001", ALT, "scope_mismatch", "칼럼(참고)에 대구 지역 고대 소국 달벌국 언급"),
    ("SRC-K02-RISS-A05", "", ALT, "unverifiable", "백두현(1997) '경상방언의 형성과 음운적 분화' — 서지만, 본문 미확보")])
cl("CLM-K02-J-01", "2. 판정", "유네스코", "rule", "경상 방언의 유네스코 등급은 확인되지 않음 → '경상 방언이 소멸위기'라고 쓰지 않음", "", "작성자 판정",
   [("SRC-K02-UNESCO-ATLAS", "CHK-K02-UN-003", ALT, "match", "아틀라스에 한국 언어는 제주어 1개뿐 — 경상 방언 미등재 확인"),
    ("SRC-K02-MD", "CHK-K02-MD-001", USR, "interpretation", "작성자 규칙")])
cl("CLM-K02-J-02", "2. 판정", "자산", "proposal", "역사·형성 자료는 모두 정보(자산 판정 대상 아님)", "", "작성자 판정",
   [("SRC-K02-MD", "CHK-K02-MD-002", USR, "interpretation", "")])

FIG = []


def fg(rid, domain, subject, metric, num, text, unit, cur="", vat="not_stated", qty="", year="", ps="", pe="",
       status="reported", sid="", cid="", clm="", note=""):
    FIG.append(dict(record_id=rid, domain=domain, subject=subject, metric=metric, value_numeric=num, value_text=text,
                    unit=unit, currency=cur, vat_basis=vat, quantity_basis=qty, base_year=year, period_start=ps,
                    period_end=pe, value_status=status, source_id=sid, chunk_id=cid, claim_id=clm, note=note))


fg("FIG-K02-001", "statistic", "제주어(UNESCO 2010)", "사용자 수 상한", "", "no more than 10,000 people", "persons", year="2010",
   sid="SRC-K02-UNESCO-2010", cid="CHK-K02-UN-001", clm="CLM-K02-0203-01", note="'이하' 상한값이라 숫자 칸 비움")
fg("FIG-K02-002", "statistic", "UNESCO 위기 언어 아틀라스(2010-12)", "등재 언어 수", "2473", "2473 languages", "languages", year="2010",
   sid="SRC-K02-UNESCO-2010", cid="CHK-K02-UN-002", note="As of December 2010")
fg("FIG-K02-003", "statistic", "UNESCO 아틀라스(2022 보관본)", "대한민국 등재 언어 수", "1", "Republic of Korea(1)", "languages",
   sid="SRC-K02-UNESCO-ATLAS", cid="CHK-K02-UN-003", clm="CLM-K02-J-01")
fg("FIG-K02-004", "program", "제주어 보전 및 육성 조례", "최초 제정일", "", "2007-09-27", "date", ps="2007-09-27", sid="SRC-K02-ORD-JEJU-2007",
   cid="CHK-K02-JEJU-002", clm="CLM-K02-0203-02")
fg("FIG-K02-005", "statistic", "경북 고대 소국(칼럼)", "소국 수", "", "대략 12개", "polities", sid="SRC-K02-NEWS-YN-20220217", cid="CHK-K02-YN-002",
   note="어림값")

PLACE_LISTS = []
CONFLICT_PAIRS = [("CHK-K02-SEOUL-003", "CHK-K02-JEJU-002")]
EXCEPTION_PAIRS = []
RULE_ABOUT_PAIRS = [("CHK-K02-MD-001", "CHK-K02-UN-001")]
ASIDE_ONLY = set()


def rule(rid, scope, text, enf, cond, src, chk, targets="", col="", op="", val="", warn=""):
    return dict(rule_id=rid, rule_scope=scope, rule_text=text, enforcement=enf, condition_text=cond, rule_source_id=src,
                rule_chunk_id=chk, target_chunk_ids=targets, match_column=col, match_operator=op, match_value=val,
                warning_text=warn)


RULES = [
    rule("RULE-K02-001", "region", "대구가 아닌 지역(제주·창원·전국·영남 등) 원문은 대구의 사실로 일반화하지 않는다.", "warn", "region <> '대구'",
         "SRC-K02-MD", "CHK-K02-MD-001", col="region", op="<>", val="대구", warn="대구가 아닌 지역 자료 — 대구 사실로 쓰지 말 것"),
    rule("RULE-K02-002", "source_grade", "언론·칼럼(B)은 확정 사실로 답하지 않는다.", "block_as_fact", "source_grade = 'B'", "", "",
         col="source_grade", op="=", val="B", warn="언론 보도 기준 — 확정 사실로 답하지 말 것"),
    rule("RULE-K02-003", "wrong_fact", "공식 연혁과 다른 '2008년 제주어 조례' 표현은 쓰지 않는다(제정 2007-09-27).", "block", "대상 청크 지정",
         "SRC-K02-ORD-JEJU-2007", "CHK-K02-JEJU-002", targets="CHK-K02-SEOUL-003"),
    rule("RULE-K02-004", "scope", "유네스코 위기 등급은 제주어에 대한 것이다. 경상·대구 방언에 옮겨 쓰지 않는다.", "warn", "대상 청크 지정",
         "SRC-K02-MD", "CHK-K02-MD-001", targets="CHK-K02-UN-001;CHK-K02-UN-002;CHK-K02-SEOUL-002",
         warn="제주어 등급 — 경상·대구 방언 등급 아님"),
]
RULE_TESTS = [
    dict(test_id="RT-K02-01", rule_id="RULE-K02-001", blocked_chunk_id="CHK-K02-JEJU-001", passing_chunk_id="CHK-K02-NK98-002",
         note="제주 조례는 경고, 대구 ㅅ/ㅆ 청크는 통과"),
    dict(test_id="RT-K02-02", rule_id="RULE-K02-002", blocked_chunk_id="CHK-K02-KB1223-001", passing_chunk_id="CHK-K02-LAW-001",
         note="칼럼은 확정 사실 불가, 법 조문은 통과"),
    dict(test_id="RT-K02-03", rule_id="RULE-K02-003", blocked_chunk_id="CHK-K02-SEOUL-003", passing_chunk_id="CHK-K02-JEJU-002",
         note="2008 기사 표현 차단, 2007 제정본 통과"),
    dict(test_id="RT-K02-04", rule_id="RULE-K02-004", blocked_chunk_id="CHK-K02-UN-001", passing_chunk_id="CHK-K02-NK98-001",
         note="제주어 등급 경고, 낙동강 경계는 통과"),
]

ISSUES = [
    ("ISS-K02-001", "resolved", "CLM-K02-0203-02", "SRC-K02-ORD-JEJU-2007", "제주어 조례 2007/2008 → 공식 연혁상 2007-09-27 제정(조례 제280호)", "MD 02-03·0절 '불일치'를 '2007(기사의 2008은 오기)'로 갱신"),
    ("ISS-K02-002", "resolved", "CLM-K02-0202-01", "SRC-K02-LAW-KUKEO", "국어기본법 원문 대조 완료: 제4조① '지역어 보전 등 … 노력하여야 한다'", "MD 02-02 '요약 기반·대조 필요' 해제"),
    ("ISS-K02-003", "scope_mismatch", "CLM-K02-S0-01", "SRC-K02-RISS-A06", "대구만 다룬 형성사는 없지만 영남·경상 방언 형성 연구는 있음(김덕호·이철희 2026, 백두현 1997)", "MD 0절·3절 보완, 백두현 1997 본문 확보"),
    ("ISS-K02-004", "not_retrieved", "CLM-K02-S0-01", "SRC-K02-RISS-A05", "백두현(1997) 본문 미확보 — 서지만 있어 청크 없음", "경북대 『인문과학』 원문 열람"),
    ("ISS-K02-005", "official_source_archive", "CLM-K02-0203-01", "SRC-K02-UNESCO-2010", "UNESCO 원 페이지는 접속 불가 — Internet Archive 보관본 사용", "현행 WAL 접속 가능 시 재확인"),
    ("ISS-K02-006", "broken_links", "", "SRC-K02-MD", "MD의 [00_개요.md] 링크가 파일명 정리 이후 없는 경로", "kimseunghee_00_개요.md 로 수정"),
    ("ISS-K02-007", "ocr_unreviewed", "", "", "OCR 대상 없음(해당 없음)", ""),
]

SEARCH_TESTS = [
    dict(test_id="ST-K02-01", query="지역어 보전", query_type="keyword", include_reference="false", expected_chunk_id="CHK-K02-LAW-001", expect="hit", note="국어기본법 제4조"),
    dict(test_id="ST-K02-02", query="낙동강", query_type="keyword", include_reference="false", expected_chunk_id="CHK-K02-NK98-001", expect="hit", note=""),
    dict(test_id="ST-K02-03", query="critically endangered", query_type="keyword", include_reference="false", expected_chunk_id="CHK-K02-UN-001", expect="hit", note=""),
    dict(test_id="ST-K02-04", query="기층방언권", query_type="keyword", include_reference="false", expected_chunk_id="CHK-K02-RISS06-001", expect="hit", note=""),
    dict(test_id="ST-K02-05", query="국어맞춤법통일안", query_type="keyword", include_reference="true", expected_chunk_id="CHK-K02-KB1223-001", expect="hit", note="칼럼(참고)"),
    dict(test_id="ST-K02-06", query="지자체가 사투리를 지켜야 한다는 법이 있어?", query_type="sentence", include_reference="false", expected_chunk_id="CHK-K02-LAW-001", expect="hit", note=""),
    dict(test_id="ST-K02-07", query="대구 사투리는 어디서부터 경상도 다른 말과 갈라져?", query_type="sentence", include_reference="false", expected_chunk_id="CHK-K02-NK98-001", expect="hit", note=""),
    dict(test_id="ST-K02-08", query="대구 사람들은 ㅅ이랑 ㅆ을 구별해서 말해?", query_type="sentence", include_reference="false", expected_chunk_id="CHK-K02-NK98-002", expect="hit", note=""),
    dict(test_id="ST-K02-09", query="제주어는 유네스코에서 얼마나 위험한 언어로 봤어?", query_type="sentence", include_reference="false", expected_chunk_id="CHK-K02-UN-001", expect="warn", note="RULE-K02-001·004 경고 동반"),
    dict(test_id="ST-K02-10", query="제주어 조례는 언제 처음 만들어졌어?", query_type="sentence", include_reference="false", expected_chunk_id="CHK-K02-JEJU-002", expect="warn", note="제주 자료 — 지역 경고"),
    dict(test_id="ST-K02-11", query="영남 사투리 경계는 옛날 나라와 관련 있어?", query_type="sentence", include_reference="false", expected_chunk_id="CHK-K02-RISS06-001", expect="warn", note="영남 자료 — 지역 경고"),
    dict(test_id="ST-K02-12", query="사투리가 표준어 때문에 억눌린 건 언제부터야?", query_type="sentence", include_reference="true", expected_chunk_id="CHK-K02-KB1223-001", expect="hit", note="칼럼 — 확정 사실 아님 경고"),
    dict(test_id="ST-K02-13", query="드라마에서 사투리를 어떻게 다뤘어?", query_type="sentence", include_reference="true", expected_chunk_id="CHK-K02-KB1223-002", expect="hit", note=""),
    dict(test_id="ST-K02-14", query="대구 지역에 옛날에 어떤 나라가 있었어?", query_type="sentence", include_reference="true", expected_chunk_id="CHK-K02-YN-001", expect="hit", note="칼럼(참고)"),
    dict(test_id="ST-K02-15", query="경상도 사투리도 유네스코 소멸위기 언어야?", query_type="blocked", include_reference="false", expected_chunk_id="CHK-K02-UN-003", expect="warn",
         note="제주어 1개만 등재 — '경상 방언 소멸위기'로 답하면 안 됨"),
    dict(test_id="ST-K02-16", query="제주어 조례는 2008년에 만들어졌지?", query_type="blocked", include_reference="true", expected_chunk_id="CHK-K02-SEOUL-003", expect="blocked",
         note="2008 기사 청크는 RULE-K02-003으로 결과에서 빠져야 함"),
    dict(test_id="ST-K02-17", query="대구 사투리도 제주어처럼 아주 심각한 위기야?", query_type="blocked", include_reference="false", expected_chunk_id="CHK-K02-UN-001", expect="warn",
         note="제주 등급을 대구에 옮기면 안 됨(RULE-K02-004)"),
]

TEMPLATE = {
    "template_id": "TPL-K02-TOPIC",
    "md_id": MD_ID,
    "description": "kimseunghee 하위 키워드 문서 고정 양식(02 역사·형성). 값이 아니라 양식만 담음",
    "front_matter": ["확장 키워드", "자료 기준일·등급 정의"],
    "sections": [
        {"key": "S0", "title": "0. 핵심 요약", "kind": "list"},
        {"key": "S1", "title": "1. 표준어 정책과 방언", "kind": "grade_tables", "subsections": ["① 공식", "② 기사", "③ 비공식"],
         "columns": ["ID", "자료", "내용", "수치", "라벨", "출처"]},
        {"key": "S2", "title": "2. 판정", "kind": "list"},
        {"key": "S3", "title": "3. 부족한 점", "kind": "list"},
    ],
}
TEMPLATE_FILE = "json/md_template_kimseunghee_02.json"
MD_CODES = {
    "source_grade_md": {"①": "공식·학술", "②": "기사", "③": "비공식(칼럼 등)"},
    "region": ["대구", "경북", "경상", "영남", "전국", "제주", "창원"],
}
RULE_TARGETS = {}

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
            source_block_id=c["source_block_id"], order_no=order[c["source_id"]], info_type=c["info_type"], region=c["region"],
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
        r["link_id"] = f"CLK-{PKG_CODE}-{i:04d}"

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
        claim_rows.append(dict(c, md_id=MD_ID, stale="true" if STALE else "false", is_external="false" if c["claim_type"] == "proposal" else "true",
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
                             storage_object_path=(f"research-originals/kimseunghee_02/{os.path.basename(s['original_file_path'])}"
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
         "md_stated_source", "overall_verdict", "overall_verdict_ko", "evidence_count", "stale"], claim_rows)
    n["evidence_links.csv"] = write_csv("evidence_links.csv", list(ev_rows[0].keys()), ev_rows)
    n["source_sections.csv"] = write_csv("source_sections.csv",
        ["section_id", "source_id", "parent_section_id", "level", "order_no", "title", "block_type", "locator"], rows_sec)
    n["knowledge_chunks.csv"] = write_csv("knowledge_chunks.csv", list(chunk_rows[0].keys()), chunk_rows)
    n["chunk_links.csv"] = write_csv("chunk_links.csv", ["link_id", "from_chunk_id", "to_chunk_id", "relation"], uniq)
    n["domain_figures.csv"] = write_csv("domain_figures.csv", list(FIG[0].keys()), FIG)
    n["domain_places.csv"] = write_csv("domain_places.csv", ["place_id", "list_name", "list_order", "name", "place_kind", "district", "source_id", "chunk_id", "approval_status", "note"], place_rows)
    n["operating_rules.csv"] = write_csv("operating_rules.csv",
        ["rule_id", "rule_scope", "rule_text", "enforcement", "condition_text", "rule_source_id", "rule_chunk_id",
         "target_chunk_ids", "match_column", "match_operator", "match_value", "warning_text", "approval_status"],
        [dict(r, approval_status="approved") for r in RULES])
    n["rule_tests.csv"] = write_csv("rule_tests.csv", ["test_id", "rule_id", "blocked_chunk_id", "passing_chunk_id", "note"], RULE_TESTS)
    n["review_issues.csv"] = write_csv("review_issues.csv",
        ["issue_id", "issue_type", "claim_ids", "source_ids", "description", "next_action"],
        [dict(issue_id=i[0], issue_type=i[1], claim_ids=i[2], source_ids=i[3], description=i[4], next_action=i[5]) for i in ISSUES])

    n["search_tests.csv"] = write_csv("search_tests.csv",
        ["test_id", "query", "query_type", "include_reference", "expected_chunk_id", "expect", "note"], SEARCH_TESTS)

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
