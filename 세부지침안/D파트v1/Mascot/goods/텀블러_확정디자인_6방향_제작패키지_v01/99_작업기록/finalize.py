from pathlib import Path
import json, hashlib, zipfile, html
from PIL import Image
from pypdf import PdfReader

base=Path(__file__).resolve().parents[1]
skus=['DK900','OM900','DK350','OM350']
codes=['01_FRONT','02_LEFT','03_RIGHT','04_LEFT45','05_RIGHT45','06_BACK']
manifest=[]
for sku in skus:
 for code in codes:
  p=base/'01_제품사진'/sku/f'{sku}_{code}.png'
  im=Image.open(p);im.verify()
  manifest.append({'sku':sku,'view':code,'path':str(p.relative_to(base)),'pixels':list(Image.open(p).size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert len(manifest)==24
for p,n in [(base/'02_디자인시트/텀블러_4종_디자인시트_v01.pdf',11),(base/'03_제작사양서/텀블러_4종_샘플제작사양서_v01.pdf',6)]:
 r=PdfReader(p);assert len(r.pages)==n
 assert all((page.extract_text() or '').strip() for page in r.pages)
 assert any('제안' in (page.extract_text() or '') for page in r.pages)

generation=[('DK900','exec-2dfdba20-444b-440a-af17-adcb3e2d2907.png',['00_승인기준/DK900_정면참고.png']),('OM900','exec-cf02220b-c7fe-4061-8cee-4f39ecb90db9.png',['00_승인기준/OM900_정면참고.png','01_제품사진/DK900/DK900_6방향_생성원본.png']),('DK350','exec-ff9eaf55-170b-4f40-ab68-febe42908e6e.png',['00_승인기준/DK350_정면참고.png']),('OM350','exec-4bf283c7-b807-4810-9f65-a2e9de467fc8.png',['00_승인기준/OM350_정면참고.png','01_제품사진/DK350/DK350_6방향_생성원본.png'])]
(base/'04_AI재현규칙/생성입력_대응표.json').write_text(json.dumps([{'sku':s,'tool':'built-in image_gen','source_generated_filename':f,'input_images_in_order':refs,'prompt':f'04_AI재현규칙/{s}_6방향_생성프롬프트.txt'} for s,f,refs in generation],ensure_ascii=False,indent=2),encoding='utf-8')
(base/'제품사진_파일목록.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
cards=''
for sku in skus:
 sheet=f'01_제품사진/{sku}/{sku}_6방향_라벨시트.png'
 cards+=f'<section><h2>{sku}</h2><a href="{sheet}"><img src="{sheet}" alt="{sku} 6방향"></a><p>'
 for code in codes:cards+=f'<a href="01_제품사진/{sku}/{sku}_{code}.png">{code}</a> '
 cards+='</p></section>'
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>텀블러 확정 디자인 제작 패키지 v01</title>
<style>body{max-width:1100px;margin:40px auto;padding:0 24px;font-family:Arial,sans-serif;color:#273c44;line-height:1.7}h1{font-size:28px}a{color:#336b7a}section{display:inline-block;width:46%;margin:1%;vertical-align:top;border:1px solid #dae3e3;padding:10px;box-sizing:border-box}img{width:100%}section p{font-size:12px}.note{padding:18px;background:#f3f7f7}h2{margin:0}</style>
<h1>대키미 · 외지몽 텀블러 제작 패키지 v01</h1><p>실리콘 밴드형 / 900mL · 350mL / 4종 · 24방향 컷</p>
<p><a href="02_디자인시트/텀블러_4종_디자인시트_v01.pdf">디자인시트 PDF · 11쪽</a>　|　<a href="03_제작사양서/텀블러_4종_샘플제작사양서_v01.pdf">샘플제작사양서 PDF · 6쪽</a>　|　<a href="패키지_사용안내.txt">사용 안내</a></p>
<div class="note">승인 원본이 외형 최우선 기준입니다. 아래 6방향은 AI 외관 시안이며 사용자 최종 검토 전입니다. 치수·색 코드·소재·공법은 제조사 확인 전 제안값입니다. 정밀 CAD, 성능 및 양산 승인을 대신하지 않습니다.</div>'''+cards+'</html>'
(base/'시작하기.html').write_text(page,encoding='utf-8')
audit='''검수 결과 v01
파일 검증: 4종 x 6방향 개별 PNG 24개 정상 읽기 확인.
모음: 제품별 라벨시트 4개, 생성원본 4개 보존.
문서: 디자인시트 11쪽, 샘플제작사양서 6쪽. 전체 페이지 PDFium 렌더링 확인.
시각 검수: 전체 17쪽 모음과 주요 치수/상세/BOM 페이지 확대 확인, 한글·표·본문 잘림 없음.
앞뒤: 4종 후면 얼굴/리본/우주선 복제 없음 확인, 밴드 연속 유지.
좌우: 큰 손잡이 front right/back left, 측면 가림; 작은 고리 측면 edge-on 확인.
의도적 한계: 모든 방향은 생성 시안으로 각도·두께·색·곡률·고리 형상 완전 일치 미보장. 승인원본과 문서 규칙 우선.
제조: 용량 실측/CAD/내통/단열층/나사/패킹/하중/접착·세척·식품접촉 적합성 자료는 업체 확인 전.
ZIP에는 작업 스크립트와 PDF QA 중간 이미지를 제외하고 사용자 전달 파일만 포함.
'''
(base/'검수기록.txt').write_text(audit,encoding='utf-8')
files=[p for p in base.rglob('*') if p.is_file() and '99_작업기록' not in p.relative_to(base).parts]
checks=[]
for p in sorted(files):checks.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(base)))
(base/'SHA256SUMS.txt').write_text('\n'.join(checks)+'\n',encoding='utf-8')
archive=base.parent/'대키미_외지몽_텀블러_6방향_디자인제작패키지_v01.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in base.rglob('*'):
  if p.is_file() and '99_작업기록' not in p.relative_to(base).parts:z.write(p,str(Path(base.name)/p.relative_to(base)))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert len([n for n in z.namelist() if any(n.endswith(f'_{c}.png') for c in codes)])==24
 print('ZIP members:',len(z.namelist()))
print('Verified PNG count:',len(manifest))
print('Native PNG sizes:',sorted(set(tuple(x['pixels']) for x in manifest)))
print('Archive:',archive)
print('Size MB:',round(archive.stat().st_size/1024**2,2))
