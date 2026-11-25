"""Package only public assets. Runtime DB, source, and API secrets stay local."""
import argparse
import json
import re
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLIC_FILES=('index_v06.html','app_v06.js','journey_v06.js','style_v06.css','plan_template_v06.json')

def package(destination,backend):
    if not re.fullmatch(r'https://[a-z0-9-]+\.trycloudflare\.com',backend):
        raise ValueError('Expected exact HTTPS tunnel origin')
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    for name in PUBLIC_FILES:shutil.copy2(ROOT/name,destination/name)
    shutil.copytree(ROOT/'assets_v06',destination/'assets_v06',dirs_exist_ok=True)
    shutil.copy2(ROOT/'index_v06.html',destination/'index.html')
    routes = [{'source':'/api/:path*','destination':backend+'/api/:path*'},
               {'source':'/reference_v06.html','destination':backend+'/reference_v06.html'}]
    conf={'$schema':'https://openapi.vercel.sh/vercel.json','framework':None,'buildCommand':None,'outputDirectory':'.',
          'rewrites':routes,'headers':[{'source':'/(.*)','headers':[
              {'key':'Cache-Control','value':'no-store'},
              {'key':'X-Content-Type-Options','value':'nosniff'},
              {'key':'Referrer-Policy','value':'same-origin'},
              {'key':'X-Robots-Tag','value':'noindex, nofollow, noarchive'}]}]}
    (destination/'vercel.json').write_text(json.dumps(conf,ensure_ascii=False,indent=2)+'\n')
    (destination/'.gitignore').write_text('.vercel/\n')
    (destination/'.vercelignore').write_text('.git/\n.vercel/\n.env*\n.runtime/\nbackend/\ntests/\n*.sqlite*\n')
    return destination

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);p.add_argument('--backend',required=True)
    a=p.parse_args();print(package(a.destination,a.backend))
