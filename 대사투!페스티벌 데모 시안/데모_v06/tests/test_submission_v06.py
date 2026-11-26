import base64
import io
import unittest
import zipfile

from plan_schema_v06 import TEMPLATE, apply_fixed, normalize_plan, plan_model
from workflow_v06 import CHECKS, review_report, signature


def full_fields():
    fields = {}
    for key in [k for s in TEMPLATE['sections'] for k in s['fields']]:
        spec = TEMPLATE['tables'].get(key)
        if not spec:
            fields[key] = '값 ' + key
        elif spec['kind'] == 'array':
            fields[key] = [['낮', '가', '나', '다']]
        else:
            fields[key] = [{c: '값' for c in spec['keys']}]
    fields['missing'] = ['검토용 메모']
    return fields


def text_of(model):
    return str([model['title'], model.get('subtitle'), model['warn'], [
        [b for b in s['blocks'] if b.get('t') != 'img'] for s in model['sections']]])


def goods():
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (64, 64), (200, 180, 240)).save(buf, 'JPEG')
    return [{'item_name': '키링', 'did': 'abcdef123456', 'who_txt': '대키미', 'image_b64': base64.b64encode(buf.getvalue()).decode()}]


class FixedContent(unittest.TestCase):
    def test_blank_values_are_filled_without_overwriting(self):
        out = apply_fixed(normalize_plan({'place': '', 'heat': '담당자가 적은 대응'}))
        self.assertIn('두류공원', out['place'])
        self.assertEqual(out['heat'], '담당자가 적은 대응')
        self.assertEqual(out['host'], '')  # 근거 없는 값은 채우지 않는다

    def test_generated_plan_uses_fixed_layout(self):
        self.assertIn('메인 출입로', apply_fixed({'layout': 'AI가 지어낸 배치'}, generated=True)['layout'])
        self.assertEqual(apply_fixed({'layout': '담당자 수정'})['layout'], '담당자 수정')

    def test_body_has_map_and_zone_tables(self):
        section = next(s for s in plan_model(full_fields())['sections'] if s['h'].startswith('3.'))
        self.assertTrue(any(b.get('t') == 'img' and b.get('wide') for b in section['blocks']))
        self.assertIn('10미 포장마차', str(section['blocks']))
        self.assertIn('의료실', str(section['blocks']))


class Submission(unittest.TestCase):
    def workspace(self, fields):
        w = {'conditions': {}, 'goods': [], 'messages': [], 'plan': fields}
        w['review'] = {'signature': signature(w), 'checks': {k: True for k in CHECKS}, 'responsible': '담당', 'at': 1, 'goods_ids': ['g1']}
        return w

    def test_complete_and_reviewed_is_submittable(self):
        self.assertTrue(review_report(self.workspace(full_fields()), ['g1'])['submittable'])

    def test_blank_field_blocks(self):
        fields = full_fields()
        fields['host'] = '미정'
        report = review_report(self.workspace(fields), ['g1'])
        self.assertFalse(report['submittable'])
        self.assertIn('host', report['blank_keys'])

    def test_one_empty_table_cell_blocks(self):
        fields = full_fields()
        fields['schedule'] = [['낮', '미입력', '나', '다']]
        self.assertIn('schedule', review_report(self.workspace(fields), ['g1'])['blank_keys'])

    def test_edit_or_goods_change_needs_new_review(self):
        w = self.workspace(full_fields())
        self.assertFalse(review_report(w, ['g2'])['submittable'])
        w['plan']['host'] = '다른 기관'
        self.assertFalse(review_report(w, ['g1'])['submittable'])

    def test_final_copy_has_no_draft_wording(self):
        for part in ('full', 'summary'):
            model = plan_model(full_fields(), goods=goods(), part=part, final={'responsible': '담당', 'date': '2026-11-27'})
            text = text_of(model)
            for word in ('검토용', '초안', '점촌', '입력 필요', '추가로 확인할 사항', '자체 점검 상태', '점검 항목', '쪽 이상'):
                self.assertNotIn(word, text, (part, word))
            self.assertIn('제출본', model['subtitle'])
        self.assertIn('초안', plan_model(full_fields())['subtitle'])


class Saving(unittest.TestCase):
    def test_saved_review_keeps_reviewed_goods(self):
        import tempfile
        from pathlib import Path
        from auth_v06 import Store
        store = Store(Path(tempfile.mkdtemp()) / 'db.sqlite3')
        user = store.provision_manager('시험담당', 'Test-only-pass-2026!')
        w = {'conditions': {}, 'goods': [], 'messages': [], 'plan': normalize_plan(full_fields())}
        w['review'] = {'signature': signature(w), 'checks': {k: True for k in CHECKS}, 'responsible': '담당', 'at': 1, 'goods_ids': ['g1']}
        store.save_workspace(user['id'], w)
        self.assertTrue(review_report(store.workspace(user['id']), ['g1'])['submittable'])


class Files(unittest.TestCase):
    def test_hwpx_and_docx_contain_map_and_goods_pictures(self):
        import plan_export_v06 as X
        model = plan_model(full_fields(), goods=goods())
        for maker, folder in ((X.to_hwpx, 'BinData/'), (X.to_docx, 'word/media/')):
            names = zipfile.ZipFile(io.BytesIO(maker(model))).namelist()
            self.assertEqual(len([n for n in names if n.startswith(folder)]), 2, (folder, names))


if __name__ == '__main__':
    unittest.main()
