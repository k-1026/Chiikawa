"""굿즈 계획서는 PDF 기준 A4 5쪽 이상, 기획안 요약본은 최대 입력에서도 2쪽 이내여야 한다."""
import re, sys, tempfile, time, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import goods_v06 as G, goods_compose_v06 as C, plan_schema_v06 as P, plan_export_v06 as X
from auth_v06 import Store

def pages(data): return len(re.findall(rb'/Type\s*/Page[^s]', data))

class GoodsDocTests(unittest.TestCase):
    def test_every_item_plan_has_at_least_five_pages(self):
        tmp = tempfile.TemporaryDirectory(); st = Store(Path(tmp.name) / 't.sqlite'); G.ensure_table(st)
        ws = {'plan': {'festival_name': '테스트 축제', 'period': '2027-08-20 ~ 2027-08-22'}, 'conditions': {}}
        for item in G.ITEMS:
            did = 't' + item
            with st.db() as db:
                db.execute('INSERT INTO goods_designs(id,user_id,item,concept,prompt,image,created_at,selected,who,pose) VALUES(?,?,?,?,?,?,?,?,?,?)',
                           (did, 1, item, '우주 파티', 'x', C.compose(item, 'both', None, 0), int(time.time()), 1, 'both', ''))
            data, _ = G.export_plan(st, 1, did, 300, ws, 'pdf')
            self.assertGreaterEqual(pages(data), G.MIN_PAGES, item)
        tmp.cleanup()

    def test_summary_fits_two_pages_with_maximum_input(self):
        long = '대구 사투리를 소재로 한 가족 참여형 축제를 운영하며 지역 상권과 연계한다. ' * 6
        f = {}
        for s in P.TEMPLATE['sections']:
            for k in s['fields']:
                if k in P.TABLES:
                    spec = P.TABLES[k]
                    f[k] = ([{c: long[:90] for c in spec['keys']} for _ in range(8)] if spec['kind'] == 'object'
                            else [[long[:30]] * len(spec['keys']) for _ in range(5)] if spec['kind'] == 'array' else [long[:60]] * 5)
                else:
                    f[k] = long
        img = C.compose('sticker', 'both', None, 0)
        goods = [{'did': 'abcdef1234567890', 'item_name': n, 'who_txt': '대키미 + 외지몽', 'image_b64': img, 'spec': ''} for n in ('스티커', '키링', '마그넷', '에코백')]
        self.assertLessEqual(pages(X.to_pdf(P.plan_model(f, goods=goods, part='summary'))), 2)

if __name__ == '__main__':
    unittest.main()


class PoseTests(unittest.TestCase):
    def test_pose_library_and_yearly_rotation(self):
        lib = G.pose_library()
        self.assertEqual(len([p for p in lib if p['char'] == 'daekimi']), 12)
        self.assertEqual(len([p for p in lib if p['char'] == 'oejimong']), 12)
        a = G.choose_poses('both', 'keyring', 2027, 0, set())
        b = G.choose_poses('both', 'keyring', 2028, 0, set())
        self.assertNotEqual(a, b)                       # 해마다 다른 포즈
        for pid in list(a.values()) + list(b.values()):
            p = next(x for x in lib if x['id'] == pid)
            self.assertEqual(p['use'], 'general')      # 경계·삐짐·시무룩 같은 분위기는 추천에서 제외
        used = set(a.values())
        c = G.choose_poses('both', 'keyring', 2027, 0, used)
        self.assertFalse(set(c.values()) & used)       # 이미 쓴 포즈는 피함
        self.assertTrue(C.compose('keyring', 'both', None, 0, a))

    def test_recommendation_excludes_fixed_items(self):
        seen = []
        for _ in range(2):
            out = G.recommend('우주 사투리 가족 청년', {'plan': {}, 'conditions': {}}, seen, [])
            ks = [x['item'] for x in out['recommendations']]
            self.assertFalse(set(ks) & set(G.FIXED))
            self.assertEqual(len(ks), len(set(ks)))
            self.assertFalse(set(ks) & set(seen))
            seen += ks


class BackgroundCacheTests(unittest.TestCase):
    def setUp(self):
        import base64, io
        from PIL import Image
        buf = io.BytesIO(); Image.new('RGB', (64, 64), (240, 230, 220)).save(buf, 'JPEG')
        self.jpeg = base64.b64encode(buf.getvalue()).decode()
        self.tmp = tempfile.TemporaryDirectory(); self.st = Store(Path(self.tmp.name) / 't.sqlite')
        self.calls = 0; self.orig = G.generate_image
        def fake(prompt):
            self.calls += 1
            return self.jpeg
        G.generate_image = fake

    def tearDown(self):
        G.generate_image = self.orig; self.tmp.cleanup()

    def test_same_product_photo_is_reused_instead_of_regenerated(self):
        G.create(self.st, 1, 'notebook', '첫 컨셉', 2, 'both', 2027, 'auto')
        first = self.calls
        self.assertEqual(first, 2)                       # 변형 2개만 새로 만든다
        G.create(self.st, 1, 'notebook', '다른 컨셉', 2, 'both', 2027, 'auto')
        G.create(self.st, 2, 'notebook', '또 다른 컨셉', 2, 'both', 2028, 'auto')
        self.assertEqual(self.calls, first)             # 제품 사진은 컨셉·사용자와 상관없이 재사용 → 한도를 쓰지 않는다

    def test_optional_background_failure_still_makes_design_but_product_photo_failure_does_not(self):
        def boom(prompt): raise G.GoodsError('한도')
        G.generate_image = boom
        out = G.create(self.st, 1, 'pinbutton', '새 컨셉', 1, 'both', 2027, 'auto')
        self.assertTrue(out[0]['bg_failed'])             # 배경만 못 만들면 기본 배경으로 시안은 만든다
        with self.assertRaises(G.GoodsError):
            G.create(self.st, 1, 'pouch', '새 컨셉', 1, 'both', 2027, 'auto')   # 제품 사진이 없으면 만들 수 없다
