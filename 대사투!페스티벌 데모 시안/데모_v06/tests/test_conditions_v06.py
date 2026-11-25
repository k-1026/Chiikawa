import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from conditions_v06 import missing_conditions,require_conditions,LABELS
from auth_v06 import Error
COMPLETE={'year':'2027','host':'기획팀','concept':'참여형 체험','programs':'사투리 퀴즈','scale':'500명','theme':'지역문화','period':'2027년 8월 27~29일','place':'두류공원','budget_total':'산정 요청','target':'가족','goal':'지역문화 체험 확대'}
class ConditionsTests(unittest.TestCase):
 def test_all_eleven_conditions_required(self):
  self.assertEqual(missing_conditions(COMPLETE),[])
  for key in LABELS:
   for value in ['', '   ','미입력','미정',None]:
    with self.subTest(key=key,value=value):
     self.assertIn(key,missing_conditions({**COMPLETE,key:value}))
     with self.assertRaises(Error):require_conditions({**COMPLETE,key:value})
  require_conditions(COMPLETE)
 def test_year_and_non_text_rejected(self):
  self.assertIn('year',missing_conditions({**COMPLETE,'year':'내년'}))
  self.assertIn('programs',missing_conditions({**COMPLETE,'programs':[]}))
