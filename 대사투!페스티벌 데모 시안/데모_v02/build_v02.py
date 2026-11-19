#!/usr/bin/env python3
"""index.src_v02.html 을 단일 파일 index_v02.html 로 만든다.
  {{JS:경로}}   -> 그 파일의 내용을 그대로 삽입
  {{IMG:경로}}  -> assets 이미지를 base64 data URI 로 삽입
사용: python3 build_v02.py"""
import base64, mimetypes, pathlib, re
here = pathlib.Path(__file__).parent
src = (here / 'index.src_v02.html').read_text(encoding='utf-8')
src = re.sub(r'\{\{JS:([^}]+)\}\}', lambda m: (here / m.group(1)).read_text(encoding='utf-8'), src)
def embed(m):
    f = here / m.group(1)
    mime = mimetypes.guess_type(f.name)[0] or 'application/octet-stream'
    return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
out = re.sub(r'\{\{IMG:([^}]+)\}\}', embed, src)
(here / 'index_v02.html').write_text(out, encoding='utf-8')
print('index_v02.html', round(len(out) / 1024), 'KB')
