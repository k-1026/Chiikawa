from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from collections import Counter
import re,hashlib,json,posixpath
b=Path(__file__).resolve().parent
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
def scan(p):
 with ZipFile(p) as z:
  texts=[];pics=[]
  for i in range(1,27):
   r=etree.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
   texts.append(Counter(''.join(s.xpath('.//a:t/text()',namespaces=ns)) for s in r.findall('.//p:sp',ns) if s.xpath('.//a:t',namespaces=ns)))
   pics.append(len(r.findall('.//p:pic',ns)))
  hashes={hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('ppt/media/')}
 return texts,pics,hashes
old,op,oh=scan(b/'source_v03.pptx');new,np,nh=scan(b/'candidate.pptx')
for i in range(26):
 delta=new[i]-old[i];removed=old[i]-new[i]
 assert not removed,(i+1,'removed',removed)
 assert delta==(Counter({'텀블벅 준비':1}) if i==3 else Counter()),(i+1,'added',delta)
assert op==np,(op,np)
assert oh==nh,'Source image resources changed'
report={'slides':26,'all_original_text_preserved':True,'only_added_slide_text':{'slide':4,'text':'텀블벅 준비'},'picture_count':sum(np),'image_resources_identical':True,'source_sha256':hashlib.sha256((b/'source_v03.pptx').read_bytes()).hexdigest()}
(b/'content_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
