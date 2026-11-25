"""Package only public assets. Runtime DB, source, and API secrets stay local."""
import argparse
import json
import re
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLIC_FILES=('index_v06.html','app_v06.js','journey_v06.js','goods_v06.js','style_v06.css','plan_template_v06.json')

def make_conf(backend,build=False):
    """vercel.json 내용. build=True 이면 GitHub 연결 자동 빌드용(저장소 루트 vercel.json)으로 만든다."""
    routes = [{'source':'/api/:path*','destination':backend+'/api/:path*'},
               {'source':'/reference_v06.html','destination':backend+'/reference_v06.html'}]
    conf={'$schema':'https://openapi.vercel.sh/vercel.json','framework':None,'buildCommand':None,'outputDirectory':'.',
          'rewrites':routes,'headers':[{'source':'/(.*)','headers':[
              {'key':'Cache-Control','value':'no-store'},
              {'key':'X-Content-Type-Options','value':'nosniff'},
              {'key':'Referrer-Policy','value':'same-origin'},
              {'key':'X-Robots-Tag','value':'noindex, nofollow, noarchive'}]}]}
    if build:
        conf['buildCommand']='python3 tools/package_vercel.py --destination public --backend '+backend
        conf['outputDirectory']='public'
    return conf

def package(destination,backend):
    if not re.fullmatch(r'https://[a-z0-9-]+\.(?:trycloudflare|onrender)\.com',backend):
        raise ValueError('Expected exact HTTPS server origin (onrender.com or trycloudflare.com)')
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    for name in PUBLIC_FILES:shutil.copy2(ROOT/name,destination/name)
    shutil.copytree(ROOT/'assets_v06',destination/'assets_v06',dirs_exist_ok=True)
    shutil.copy2(ROOT/'index_v06.html',destination/'index.html')
    conf=make_conf(backend)
    (destination/'vercel.json').write_text(json.dumps(conf,ensure_ascii=False,indent=2)+'\n')
    (destination/'.gitignore').write_text('.vercel/\n')
    (destination/'.vercelignore').write_text('.git/\n.vercel/\n.env*\n.runtime/\nbackend/\ntests/\n*.sqlite*\n')
    return destination

if __name__=='__main__':
    import os
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);p.add_argument('--backend',default=os.getenv('API_ORIGIN'))
    p.add_argument('--root-config',action='store_true',help='저장소 루트에 vercel.json(자동 빌드용)을 쓴다')
    a=p.parse_args()
    if not a.backend:raise SystemExit('서버 주소가 필요합니다: --backend 또는 환경변수 API_ORIGIN')
    if a.root_config:
        if not re.fullmatch(r'https://[a-z0-9-]+\.(?:trycloudflare|onrender)\.com',a.backend):raise SystemExit('서버 주소 형식이 올바르지 않습니다.')
        (ROOT/'vercel.json').write_text(json.dumps(make_conf(a.backend,build=True),ensure_ascii=False,indent=2)+'\n');print('vercel.json 작성')
    else:print(package(a.destination,a.backend))
