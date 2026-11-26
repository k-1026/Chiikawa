import base64
import io
import unittest
import zipfile

from plan_schema_v06 import TEMPLATE, NARRATIVE_CHAPTERS, apply_conditions, apply_fixed, normalize_plan, plan_model, previous_for_ai
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
    fields['narr'] = {k: '▶ 요약\n□ 제목\n○ 항목: 설명\n- 세부' for k, _ in NARRATIVE_CHAPTERS}
    return fields


def text_of(model):
    return str([model['title'], model.get('subtitle'), model['warn'], [
        [b for b in s['blocks'] if b.get('t') != 'img'] for s in model['sections']]])


def goods():
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (64, 64), (200, 180, 240)).save(buf, 'JPEG')
    return [{'item': 'keyring', 'item_name': '키링', 'did': 'abcdef123456', 'who_txt': '대키미', 'image_b64': base64.b64encode(buf.getvalue()).decode()}]


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
        section = next(s for s in plan_model(full_fields())['sections'] if s['h'].startswith('5.'))
        self.assertTrue(any(b.get('t') == 'img' and b.get('wide') for b in section['blocks']))
        self.assertIn('10미 포장마차', str(section['blocks']))
        self.assertIn('의료실', str(section['blocks']))


class Conditions(unittest.TestCase):
    CONDITIONS = {'year': '2028', 'period': '8월 21일~24일', 'host': '대구광역시', 'place': '두류 야외음악당', 'concept': '지역 상권 연계',
                  'goal': '축제의 입지', 'scale': '중규모 · 1,000명 내외', 'budget_total': '산정 요청', 'programs': '사투리 퀴즈'}

    def test_saved_conditions_beat_the_ai_draft(self):
        out = apply_conditions({'period': '2027-08-20 ~ 08-22', 'host': '', 'concept': '문화 축제', 'budget_total': '', 'programs': [{'name': '토론 대회', 'desc': '가'}]}, self.CONDITIONS)
        self.assertEqual(out['period'], '2028년 8월 21일~24일')
        self.assertEqual(out['host'], '대구광역시')
        self.assertEqual(out['concept'], '지역 상권 연계')
        self.assertEqual(out['visitors'], '1,000명 내외')
        self.assertEqual(out['budget_total'], '')   # '산정 요청'은 금액이 아니다
        self.assertEqual([r['name'] for r in out['programs']], ['사투리 퀴즈', '토론 대회'])

    def test_program_written_with_extra_words_is_not_added_twice(self):
        out = apply_conditions({'programs': [{'name': '사투리 골든벨 퀴즈쇼', 'desc': '가'}]}, self.CONDITIONS)
        self.assertEqual([r['name'] for r in out['programs']], ['사투리 골든벨 퀴즈쇼'])

    def test_old_condition_values_are_not_sent_back_to_ai(self):
        self.assertEqual(previous_for_ai({'concept': '예전', 'period': '예전', 'narr': {}, 'goal': 'x', 'effects': '유지'}), {'effects': '유지'})


class Schedule(unittest.TestCase):
    def test_day_columns_follow_the_festival_period(self):
        from plan_schema_v06 import schedule_headers
        self.assertEqual(schedule_headers('2028년 8월 21일~24일'), ['8/21(월)', '8/22(화)', '8/23(수)', '8/24(목)'])
        self.assertEqual(schedule_headers('2027-08-20(금) ~ 2027-08-22(일)'), ['8/20(금)', '8/21(토)', '8/22(일)'])
        self.assertEqual(schedule_headers('8월 30일~9월 1일'), ['8/30', '8/31', '9/1'])
        self.assertEqual(schedule_headers('2027년 10월 주말 3일(금~일)'), ['1일차', '2일차', '3일차'])
        self.assertEqual(schedule_headers(''), ['1일차', '2일차', '3일차'])

    def test_four_day_festival_gets_four_columns_and_the_new_one_blocks(self):
        fields = full_fields()
        fields['period'] = '2028년 8월 21일~24일'
        out = normalize_plan(fields)
        self.assertEqual(len(out['schedule'][0]), 5)
        self.assertEqual(out['schedule'][0][4], '')
        w = {'conditions': {}, 'goods': [], 'messages': [], 'plan': fields}
        self.assertIn('schedule', review_report(w)['blank_keys'])
        header = next(b['rows'][0] for s in plan_model(fields)['sections'] for b in s['blocks'] if b['t'] == 'table' and b['rows'][0][0].startswith('구분 · 시간대'))
        self.assertEqual(header[1:], ['8/21(월)', '8/22(화)', '8/23(수)', '8/24(목)'])


class Narrative(unittest.TestCase):
    def test_chapters_are_grouped_and_short_ones_are_expanded_once(self):
        import json
        import narrative_v06 as N
        calls = []

        def fake(prompt, system):
            calls.append(prompt)
            keys = [k for k, _ in NARRATIVE_CHAPTERS if '- %s (' % k in prompt]
            size = 5000 if '## 보강할 장' in prompt else 30
            return json.dumps({k: '▶ ' + '가' * size for k in keys}, ensure_ascii=False)

        out = N.write(full_fields(), {}, [], ['overview', 'programs'], call=fake)
        self.assertEqual(sorted(out), ['overview', 'programs'])
        self.assertEqual(len(calls), 4)   # 묶음 2개 × (작성 + 보강 1회)
        self.assertGreater(len(out['programs']), 4000)

    def test_empty_chapter_blocks_submission_and_text_is_rendered(self):
        fields = full_fields()
        del fields['narr']['safety']
        w = {'conditions': {}, 'goods': [], 'messages': [], 'plan': fields}
        self.assertTrue(any('8. 안전관리 계획' in b for b in review_report(w)['blockers']))
        model = plan_model(full_fields())
        kinds = {b['t'] for s in model['sections'] for b in s['blocks']}
        self.assertTrue({'cover', 'lead', 'li'} <= kinds)

    def test_goods_appendix_follows_selected_design(self):
        model = plan_model(full_fields(), goods=goods(), final={'responsible': '담당', 'date': '2026-11-27'})
        appendix = [s for s in model['sections'] if s.get('appendix')]
        self.assertIn('별첨 1. 키링 제작 계획서', appendix[0]['h'])
        self.assertIn('디자인 적용 방법', str(appendix))
        self.assertIn('다이컷', str(appendix))


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
            for word in ('검토용', '초안', '점촌', '입력 필요', '추가로 확인할 사항', '자체 점검', '쪽 이상'):
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


class PageCount(unittest.TestCase):
    def test_body_with_written_chapters_fits_target_and_has_no_blank_page(self):
        import plan_export_v06 as X
        import plan_form_v06 as F
        fields = full_fields()
        para = '○ 운영 방법: 현장 담당자가 진행 순서를 안내하고 참여자의 이해를 확인하며 필요한 조치를 기록한다. 변경 사항은 안내 부스와 온라인에 함께 알린다.'
        sizes = {'programs': 22, 'safety': 13, 'space': 8, 'promotion': 8, 'organization': 8, 'purpose': 8, 'background': 7}
        fields['narr'] = {k: '▶ 요약 문장\n□ 제목\n' + '\n'.join([para] * sizes.get(k, 6)) for k, _ in NARRATIVE_CHAPTERS}
        _, pages = F.fit_density(plan_model(fields, goods=goods()), X._print_pdf)
        self.assertTrue(20 <= pages <= 24, pages)


class Files(unittest.TestCase):
    def test_hwpx_and_docx_contain_map_and_goods_pictures(self):
        import plan_export_v06 as X
        model = plan_model(full_fields(), goods=goods())
        for maker, folder in ((X.to_hwpx, 'BinData/'), (X.to_docx, 'word/media/')):
            names = zipfile.ZipFile(io.BytesIO(maker(model))).namelist()
            self.assertGreaterEqual(len([n for n in names if n.startswith(folder)]), 2, (folder, names))  # 지도 + 굿즈 시안


if __name__ == '__main__':
    unittest.main()
