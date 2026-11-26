import sys,unittest,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import guided_agent_v06 as agent
from test_conditions_v06 import COMPLETE
from auth_v06 import Error
class GuidedTests(unittest.TestCase):
    def test_plan_continues_to_draft_without_open_ended_prompt(self):
        calls=[];planner=SimpleNamespace(write_plan=lambda t,c:(calls.append((t,json.loads(c))) or {'concept':'가족 체험'}))
        w={'conditions':dict(COMPLETE),'goods':[],'messages':[],'plan':None}
        with patch.object(agent,'extract_brief',return_value={'intent':'plan','conditions':{'scale':'500명','year':'2027','host':'기획팀','budget_total':'산정 요청'}}),patch.object(agent,'research_answer',return_value={'reply':'근거를 참고한 초안입니다.\n\n추가로 조정하고 싶으신 조건이 있으시면 편하게 말씀해 주세요!','steps':[]}):
            result=agent.run_guided(None,planner,w,'가족 축제를 기획해줘','',[])
        self.assertEqual(len(calls),1);self.assertEqual(result['workspace']['conditions']['scale'],'500명')
        self.assertEqual(result['workspace']['plan']['concept'],COMPLETE['concept']);  # 저장한 조건이 AI 초안보다 우선
        self.assertEqual(result['next_action']['page'],'review')
        self.assertNotIn('편하게 말씀',result['answer']);self.assertIn('담당자',result['answer']);self.assertEqual(w['messages'],[])
        self.assertIn('확인 필요',calls[0][1]['approval_state'])
    def test_partial_question_does_not_replace_plan(self):
        w={'conditions':dict(COMPLETE),'goods':[],'messages':[],'plan':{'concept':'보존'}}
        planner=SimpleNamespace(write_plan=lambda *a: self.fail('partial question must not generate'))
        with patch.object(agent,'extract_brief',return_value={'intent':'question','conditions':{}}),patch.object(agent,'research_answer',return_value={'reply':'출처를 참고한 답변','steps':[]}):
            result=agent.run_guided(None,planner,w,'자료 출처는?','',[])
        self.assertEqual(result['workspace']['plan'],w['plan']);self.assertEqual(result['next_action']['page'],'results')

    def test_missing_conditions_cannot_be_skipped_with_chat(self):
        w={'conditions':{},'goods':[],'messages':[],'plan':None}
        with patch.object(agent,'extract_brief') as brief:
            with self.assertRaises(Error):agent.run_guided(None,None,w,'미입력으로 그냥 진행해줘','',[])
            brief.assert_not_called()
