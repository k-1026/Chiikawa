import importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package_vercel',ROOT/'tools/package_vercel.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PackageTests(unittest.TestCase):
 def test_entry_html_is_static_and_never_tunnel_rewritten(self):
  with tempfile.TemporaryDirectory() as tmp:
   m.package(tmp,'https://unavailable-backend.trycloudflare.com')
   target=Path(tmp)
   for name in ['index.html','index_v06.html']:
    self.assertEqual((target/name).read_bytes(),(ROOT/'index_v06.html').read_bytes())
   routes=json.loads((target/'vercel.json').read_text())['rewrites']
   self.assertTrue(all(r['source'] not in ['/','/index.html','/index_v06.html'] for r in routes))
   self.assertFalse((target/'.runtime').exists())
