import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from workflow_v06 import review_report,signature

class WorkflowTests(unittest.TestCase):
    def test_unresolved_and_sources_are_honest(self):
        w={'conditions':{},'plan':{'festival_name':'사투리축제','budget_total':'미정','missing':['우천 대책 확인']},'goods':[], 'messages':[{'role':'assistant','content':'출처 https://example.org/report.'},{'role':'user','content':'참고','attachments':[{'name':'계획.pdf','id':'a'}]}]}
        r=review_report(w)
        self.assertFalse(r['complete']);self.assertIn('총 사업비',r['missing']);self.assertTrue(any('계획.pdf' in e['label'] for e in r['evidence']))
        w['review']={'signature':signature(w),'checks':dict.fromkeys(['missing','evidence','budget','responsibility'],True),'responsible':'담당자','at':1}
        self.assertTrue(review_report(w)['complete'])
        w['plan']['place']='두류공원';self.assertFalse(review_report(w)['complete'])
    def test_empty_plan_never_reviewed(self):
        self.assertFalse(review_report({'plan':None})['complete'])
