from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,re,posixpath
b=Path(__file__).resolve().parent
with ZipFile(b/'candidate.pptx') as z:
 raw={n:z.read(n) for n in z.namelist()}
seen={};replacements={}
for n,data in raw.items():
 if n.startswith('ppt/media/'):
  k=hashlib.sha256(data).hexdigest()
  if k in seen:replacements[n]=seen[k]
  else:seen[k]=n
for n,data in list(raw.items()):
 if n.endswith('.rels'):
  folder=posixpath.dirname(posixpath.dirname(n))
  def sub(m):
   target=m.group(1);resolved=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(folder,target))
   if resolved in replacements:return 'Target="'+posixpath.relpath(replacements[resolved],folder)+'"'
   return m.group(0)
  raw[n]=re.sub(r'Target="([^"]+)"',sub,data.decode()).encode()
for n in replacements:del raw[n]
# Remove ContentType declarations for media duplicates only.
ct=raw['[Content_Types].xml'].decode()
for n in replacements:ct=re.sub(r'<Override\b[^>]*PartName="/'+re.escape(n)+r'"[^>]*/>','',ct)
raw['[Content_Types].xml']=ct.encode()
with ZipFile(b/'candidate_compact.pptx','w',ZIP_DEFLATED) as z:
 for n,data in raw.items():z.writestr(n,data)
print('media duplicate references merged:',len(replacements),'size MB:',round((b/'candidate_compact.pptx').stat().st_size/1024**2,1))
