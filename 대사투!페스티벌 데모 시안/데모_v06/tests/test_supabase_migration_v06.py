import importlib.util,json,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('migration',ROOT/'tools/migrate_supabase_v06.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MigrationTests(unittest.TestCase):
 def test_readonly_snapshot_and_dry_run_never_print_rows(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'test.sqlite3'
   with sqlite3.connect(p) as db:
    db.execute('CREATE TABLE users(id INTEGER PRIMARY KEY,name TEXT,password TEXT)')
    db.execute('INSERT INTO users VALUES(1,?,?)',('비공개 이름','private-password-hash'))
   before=p.read_bytes();snap=m.snapshot(p)
   self.assertEqual(snap['users'][1][0][2],'private-password-hash')
   r=subprocess.run([sys.executable,str(ROOT/'tools/migrate_supabase_v06.py'),'--source',str(p)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout)['counts'],{'users':1})
   self.assertNotIn('private-password-hash',r.stdout);self.assertNotIn('비공개 이름',r.stdout)
   self.assertEqual(before,p.read_bytes())
 def test_schema_private_and_rls_for_every_table(self):
  s=(ROOT/'supabase/001_accounts.sql').read_text()
  self.assertIn('REVOKE ALL ON SCHEMA daesatu FROM PUBLIC, anon, authenticated',s)
  for t in m.TABLES:
   self.assertIn('ALTER TABLE daesatu."'+t+'" ENABLE ROW LEVEL SECURITY',s)
   self.assertIn('REVOKE ALL ON daesatu."'+t+'" FROM PUBLIC, anon, authenticated',s)
