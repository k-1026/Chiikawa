import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from plan_schema_v06 import TEMPLATE,KEYS,normalize_plan,plan_model
from auth_v06 import Store

class FixedPlanTests(unittest.TestCase):
    def test_missing_unknown_and_shuffled_model_fields(self):
        original={'unexpected_section':'remove','heat':'실내 냉방','concept':'가족 축제','festival_name':'새 컨셉'}
        result=normalize_plan(original)
        self.assertEqual(tuple(result),KEYS)
        self.assertNotIn('unexpected_section',result)
        self.assertEqual(result['concept'],'가족 축제');self.assertEqual(result['host'],'')
    def test_table_columns_cannot_be_changed_by_model(self):
        f=normalize_plan({'programs':[{'desc':'체험','extra':'strip','name':'새 프로그램'}], 'schedule':[['오후','가','나','다','strip']], 'budget_items':[{'amount':100,'item':'장비'}]})
        self.assertEqual(list(f['programs'][0]),['name','desc'])
        self.assertEqual(f['schedule'],[['오후','가','나','다']])
        self.assertEqual(f['budget_items'][0],{'item':'장비','basis':'','amount':'100'})
    def test_eight_sections_and_headers_stay_fixed(self):
        def skeleton(model):
            return [(s['h'],[(b['t'],b.get('hdr'),b['rows'][0] if b['t']=='table' and b['hdr']=='col' else b.get('text')) for b in s['blocks']]) for s in model['sections']]
        a=plan_model({});b=plan_model({'festival_name':'야간 축제','programs':[{'name':'야간 산책'}],'budget_items':[{'item':'무대','amount':'100'}],'secret_section':'no'})
        self.assertEqual(len(a['sections']),9);self.assertEqual(skeleton(a),skeleton(b))
        self.assertEqual([s['h'] for s in b['sections']],[s['title'] for s in TEMPLATE['sections']]+['9. 굿즈 운영 및 성과품 납품'])  # 9장은 선택한 시안으로 자동 생성
        self.assertIn('야간 축제',str(b));self.assertNotIn('secret_section',str(b))
    def test_existing_and_edited_plans_share_canonical_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(Path(folder)/'db.sqlite3')
            with store.db() as db:db.execute('INSERT INTO workspaces VALUES(1,?,0)',('{"messages":[],"conditions":{},"goods":[],"plan":{"concept":"기존 컨셉"}}',))
            w=store.workspace(1);self.assertEqual(tuple(w['plan']),KEYS);self.assertEqual(w['plan']['concept'],'기존 컨셉')
            w['plan']={'goal':'수정한 목표','custom':'strip'};saved=store.save_workspace(1,w)
            self.assertEqual(tuple(saved['plan']),KEYS);self.assertEqual(saved['plan']['goal'],'수정한 목표')

if __name__=='__main__':unittest.main()
