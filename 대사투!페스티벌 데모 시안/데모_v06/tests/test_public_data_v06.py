import datetime
import unittest

import public_data_v06 as PD
from plan_schema_v06 import normalize_plan, plan_model, previous_for_ai
from workflow_v06 import review_report

TODAY = datetime.date(2026, 11, 27)


def fake(url, params):
    if 'AsosDaly' in url:
        return {'response': {'header': {'resultCode': '00'}, 'body': {'items': {'item': [
            {'tm': 'a', 'maxTa': '35.5', 'sumRn': ''}, {'tm': 'b', 'maxTa': '32.0', 'sumRn': '4.5'}]}}}}
    if 'storeListInRadius' in url:
        return {'header': {'stdrYm': '202609'}, 'body': {'totalCount': 3, 'items': [
            {'indsLclsNm': '음식', 'indsMclsNm': '한식'}, {'indsLclsNm': '음식', 'indsMclsNm': '한식'}, {'indsLclsNm': '소매'}]}}
    return {'response': {'header': {'resultCode': '0000'}, 'body': {'items': {'item': [
        {'title': '같은 시기 행사', 'eventstartdate': '20260901', 'eventenddate': '20260911'},
        {'title': '먼 행사', 'eventstartdate': '20261224', 'eventenddate': '20270103'}]}}}}


class Collect(unittest.TestCase):
    def test_summarises_three_sources_for_the_same_dates(self):
        out, failed = PD.collect('2028년 8월 21일~24일', today=TODAY, fetch=fake)
        self.assertEqual(failed, [])
        self.assertEqual([r[0] for r in out['weather']['rows']], ['2024', '2025', '2026'])
        self.assertEqual(out['weather']['rows'][0][2:], ['33.8', '35.5', '1 / 2일', '1일 · 4.5mm'])
        self.assertEqual(out['stores']['rows'][0], ['음식', '2'])
        self.assertEqual(out['events']['rows'], [['같은 시기 행사', '9/1~9/11']])

    def test_one_failure_keeps_the_others_and_never_shows_the_key(self):
        def flaky(url, params):
            if 'AsosDaly' in url:
                raise PD.PublicDataError('HTTP 403')
            return fake(url, params)
        out, failed = PD.collect('2028년 8월 21일~24일', today=TODAY, fetch=flaky)
        self.assertNotIn('weather', out)
        self.assertIn('stores', out)
        self.assertEqual(failed, ['날씨(기상청): HTTP 403'])

    def test_no_dates_skips_weather_and_events(self):
        out, failed = PD.collect('2027년 10월 주말 3일(금~일)', today=TODAY, fetch=fake)
        self.assertEqual(sorted(k for k in out if k in PD.NAMES), ['stores'])
        self.assertTrue(failed)


class InPlan(unittest.TestCase):
    def setUp(self):
        self.data, _ = PD.collect('2028년 8월 21일~24일', today=TODAY, fetch=fake)

    def test_tables_and_sources_go_into_chapters_and_survive_saving(self):
        plan = normalize_plan({'period': '2028년 8월 21일~24일', 'public': self.data})
        self.assertEqual(plan['public']['weather'], self.data['weather'])
        by = {s['h']: str(s['blocks']) for s in plan_model(plan)['sections']}
        self.assertIn('같은 시기 대구 등록 행사', by['3. 축제 개요'])
        self.assertIn('축제장 주변 상권', by['6. 추진 체계 · 일정'])
        self.assertIn('기상청 지상(종관, ASOS)', by['8. 안전관리 계획'])
        self.assertNotIn('public', previous_for_ai(plan))

    def test_period_change_asks_to_reload(self):
        plan = {'period': '2028년 9월 1일~3일', 'public': self.data}
        w = {'conditions': {}, 'goods': [], 'messages': [], 'plan': plan}
        self.assertTrue(any('다시 불러와' in b for b in review_report(w)['blockers']))

    def test_malformed_saved_value_is_dropped(self):
        self.assertNotIn('public', normalize_plan({'public': {'weather': 'x'}}))


if __name__ == '__main__':
    unittest.main()
