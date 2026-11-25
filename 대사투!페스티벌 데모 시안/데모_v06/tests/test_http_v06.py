import http.cookiejar
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request,build_opener,HTTPCookieProcessor
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import server_v06 as server
from auth_v06 import Store,totp
from test_conditions_v06 import COMPLETE

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();server.STORE=Store(Path(cls.tmp.name)/'db.sqlite3')
        cls.srv=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.srv.daemon_threads=True
        cls.base='http://127.0.0.1:'+str(cls.srv.server_port)
        cls.thread=threading.Thread(target=cls.srv.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.srv.shutdown();cls.srv.server_close();cls.tmp.cleanup()
    def setUp(self):
        self.opener=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()));self.csrf=None
        # Each test represents a fresh client; do not accumulate sign-in limits across tests.
        with server.STORE.db() as db:db.execute("DELETE FROM rates WHERE key LIKE 'login:%'")
    def call(self,path,b=None,extra=None):
        h={'Origin':self.base}
        if b is not None:h|={'Content-Type':'application/json','X-CSRF-Token':self.csrf or ''}
        h.update(extra or {})
        r=Request(self.base+path,data=None if b is None else json.dumps(b).encode(),headers=h)
        try:
            with self.opener.open(r) as res:return res.status,res.read(),res.headers
        except HTTPError as e:
            try:return e.code,e.read(),e.headers
            finally:e.close()
    def session(self):
        code,body,h=self.call('/api/me');d=json.loads(body);self.csrf=d['csrf'];return d,h
    def test_explicit_public_origin_cookie_and_csrf(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            conf=Path(directory)/'origin.json';conf.write_text('{"origin":"https://festival-check.trycloudflare.com"}')
            with patch.object(server,'PUBLIC_ORIGIN_FILE',conf):
                host='festival-check.trycloudflare.com';origin='https://'+host
                status,raw,h=self.call('/api/me',extra={'Host':host,'Origin':origin})
                self.assertEqual(status,200);self.assertIn('; Secure',h['Set-Cookie']);self.csrf=json.loads(raw)['csrf']
                public_headers={'Host':host,'Origin':origin,'Cookie':h['Set-Cookie'].split(';')[0]}
                self.assertEqual(self.call('/api/login',{},public_headers)[0],401)
                self.assertEqual(self.call('/api/owner/setup',{},public_headers)[0],403)
                self.assertEqual(self.call('/api/status',extra={'Host':'evil.trycloudflare.com'})[0],403)
                self.assertEqual(self.call('/api/register',{}, {'Host':host,'Origin':'http://'+host})[0],403)
                self.assertEqual(self.call('/api/register',{}, {'Host':host,'Origin':'https://evil.example'})[0],403)
                self.assertEqual(self.call('/api/admin/users',extra={'Host':host,'Origin':origin})[0],401)
                for path in ['/.runtime/public_origin.json','/.runtime/accounts.sqlite3','/.env']:
                    self.assertEqual(self.call(path,extra={'Host':host,'Origin':origin})[0],404)
            conf.write_text('{"origin":"https://attacker.example"}')
            with patch.object(server,'PUBLIC_ORIGIN_FILE',conf):self.assertEqual(server.public_origin(),'')

    def test_vercel_bridge_accepts_only_configured_web_origin(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            conf=Path(directory)/'origin.json'
            conf.write_text(json.dumps({'origin':'https://festival-check.trycloudflare.com','web_origins':['https://daesatu-festival-v05.vercel.app']}))
            with patch.object(server,'PUBLIC_ORIGIN_FILE',conf):
                host='festival-check.trycloudflare.com'
                status,raw,h=self.call('/api/me',extra={'Host':host})
                self.assertEqual(status,200)
                self.csrf=json.loads(raw)['csrf']
                headers={'Host':host,'Origin':'https://daesatu-festival-v05.vercel.app','Cookie':h['Set-Cookie'].split(';')[0]}
                self.assertEqual(self.call('/api/login',{},headers)[0],401)
                self.assertEqual(self.call('/api/login',{},dict(headers,Origin='https://evil.vercel.app'))[0],403)
                status,raw,h=self.call('/api/me',extra={'Host':'daesatu-festival-v05.vercel.app'})
                self.assertEqual(status,200);self.assertIn('; Secure',h['Set-Cookie'])

    def test_ai_disabled_does_not_disable_manual_workspace(self):
        from unittest.mock import patch
        import os
        user=server.STORE.provision_manager('수동기획담당','Manual-private-2026!')
        self.session();_,raw,_=self.call('/api/login',{'employee_id':user['name'],'password':'Manual-private-2026!'})
        self.csrf=json.loads(raw)['csrf']
        with patch.dict(os.environ,{'AI_ENABLED':'0'}),patch.object(server,'ai_modules') as ai:
            _,raw,_=self.call('/api/status');self.assertFalse(json.loads(raw)['features']['ai'])
            for path in ['/api/chat','/api/chat/edit','/api/plan']:
                self.assertEqual(self.call(path,{'question':'기획해줘'})[0],503)
            code,raw,_=self.call('/api/workspace',{'plan':{'festival_name':'직접 작성한 축제'},'conditions':COMPLETE})
            self.assertEqual(code,200);self.assertEqual(json.loads(raw)['plan']['festival_name'],'직접 작성한 축제')
            self.assertEqual(self.call('/api/review')[0],200)
            self.assertEqual(self.call('/reference_v06.html')[0],200)
            ai.assert_not_called()

    def test_anonymous_private_paths_denied(self):
        self.session()
        for p in ['/api/workspace','/api/admin/users','/reference_v06.html']:
            self.assertIn(self.call(p)[0],[401,403])
        for p in ['/backend/auth_v06.py','/.runtime/accounts.sqlite3','/.env','/assets_v06/../backend/auth_v06.py','/%2e%2e/backend/config.py']:
            self.assertEqual(self.call(p)[0],404,p)
    def test_preprovisioned_managers_without_org_and_owner_permissions_denied(self):
        passwords='Manager-test-2026!';people=[]
        for i,name in enumerate(['원현희','양유현','오민주']):
            u=server.STORE.provision_manager(name,passwords);people.append(u)
            self.session()
            status,raw,_=self.call('/api/login',{'org_id':'','employee_id':name,'password':passwords})
            self.assertEqual(status,200);d=json.loads(raw);self.csrf=d['csrf']
            self.assertEqual(d['user']['role'],'manager');self.assertEqual(d['user']['org_name'],'일반 관리자');self.assertNotIn('owner_challenge',d)
            self.assertEqual(self.call('/api/workspace')[0],200)
            self.assertEqual(self.call('/reference_v06.html')[0],200)
            for endpoint in ['/api/admin/users','/api/admin/audit','/api/owner/enrollment']:
                self.assertEqual(self.call(endpoint)[0],403)
            self.assertEqual(self.call('/api/owner/login-confirm',{'code':'000000'})[0],401)
            self.call('/api/conditions',{'conditions':{'concept':name+'의 기획'}})
            self.call('/api/workspace',{'plan':{'concept':name+'의 초안'}})
            self.call('/api/logout',{})
        for u in people:
            self.assertEqual(server.STORE.workspace(u['id'])['conditions']['concept'],u['name']+'의 기획')
            self.assertEqual(server.STORE.workspace(u['id'])['plan']['concept'],u['name']+'의 초안')
            self.assertNotIn(passwords,u['password'])
        self.session()
        self.assertEqual(self.call('/api/login',{'employee_id':'원현희','password':'wrong'})[0],401)

    def test_attachment_chat_followup_plan_and_fresh_entry(self):
        import base64
        from unittest.mock import patch
        from types import SimpleNamespace
        password='Attachment-test-2026!'
        user=server.STORE.provision_manager('자료담당',password)
        self.session();status,raw,_=self.call('/api/login',{'employee_id':'자료담당','password':password});self.assertEqual(status,200);self.csrf=json.loads(raw)['csrf']
        self.call('/api/conditions',{'conditions':COMPLETE})
        data=base64.b64encode('행사명: 보랏빛 산책 / 우천 시 실내 전환'.encode()).decode()
        status,raw,_=self.call('/api/attachments',{'name':'계획.txt','data':data});self.assertEqual(status,200);file=json.loads(raw)['attachment'];self.assertNotIn('text',file)
        seen=[]
        def reply(orch,content):seen.append(content);return {'reply':'첨부를 읽은 답변','steps':[]}
        plans=[];planner=SimpleNamespace(write_plan=lambda t,c:(plans.append(c) or {'concept':'첨부 기반 초안'}))
        with patch.object(server,'ai_modules',return_value=(None,planner,None)),patch.object(server,'answer_with_files',side_effect=reply):
            status,raw,_=self.call('/api/chat',{'question':'','attachment_ids':[file['id']]});self.assertEqual(status,200)
            w=json.loads(raw)['workspace'];self.assertEqual(w['messages'][0]['attachments'][0]['id'],file['id'])
            self.assertEqual(self.call('/api/chat',{'question':'우천 시는?'})[0],200)
            self.assertEqual(self.call('/api/plan',{})[0],200)
        self.assertTrue(all('보랏빛 산책' in c for c in seen));self.assertIn('보랏빛 산책',plans[0])
        self.assertEqual(self.call('/api/chat',{'question':'남의 파일','attachment_ids':['not-owned']})[0],400)
        self.assertEqual(self.call('/app_v06.js')[0],200);self.assertEqual(self.call('/api/workspace')[0],200)
        self.assertEqual(self.call('/index_v06.html')[0],200)
        self.assertEqual(self.call('/api/workspace')[0],200)
        status,raw,_=self.call('/api/me');self.assertEqual(json.loads(raw)['user']['role'],'manager')

    def test_edit_chat_preserves_archive_and_rebuilds_from_edited_turn(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        u=server.STORE.provision_manager('수정담당','Edit-test-2026!')
        self.session();_,raw,_=self.call('/api/login',{'employee_id':u['name'],'password':'Edit-test-2026!'});self.csrf=json.loads(raw)['csrf']
        server.STORE.save_workspace(u['id'],{'messages':[{'role':'user','content':'이전 요청'},{'role':'assistant','content':'이전 답변'}],'conditions':{**COMPLETE,'scale':'1000명'},'condition_inputs':COMPLETE,'plan':{'festival_name':'이전 초안'},'goods':[]})
        def run(orch,planner,w,question,context,attachments):
            self.assertEqual(w['messages'],[]);self.assertEqual(w['conditions'],COMPLETE);self.assertIsNone(w['plan'])
            w['messages']=[{'role':'user','content':question},{'role':'assistant','content':'수정 후 답변'}];w['plan']={'festival_name':'새 초안'}
            return {'workspace':w,'answer':'수정 후 답변','steps':[],'next_action':{'page':'review'}}
        with patch.object(server,'ai_modules',return_value=(None,None,None)),patch.object(server,'run_guided',side_effect=run):
            code,raw,_=self.call('/api/chat/edit',{'message_index':0,'question':'500명으로 바꿔줘'})
            self.assertEqual(code,200);w=json.loads(raw)['workspace'];self.assertEqual(w['archives'][0]['messages'][0]['content'],'이전 요청');self.assertEqual(w['messages'][0]['content'],'500명으로 바꿔줘')
            self.assertEqual(self.call('/api/chat/edit',{'message_index':1,'question':'assistant 수정 시도'})[0],400)
        before=server.STORE.workspace(u['id'])
        with patch.object(server,'ai_modules',side_effect=RuntimeError('provider unavailable')):
            self.assertEqual(self.call('/api/chat/edit',{'message_index':0,'question':'실패할 수정'})[0],503)
        self.assertEqual(server.STORE.workspace(u['id']),before)

    def test_export_endpoint_uses_v06_shaded_document(self):
        import io,zipfile
        u=server.STORE.provision_manager('문서담당','Document-test-2026!')
        self.session();_,raw,_=self.call('/api/login',{'employee_id':u['name'],'password':'Document-test-2026!'});self.csrf=json.loads(raw)['csrf']
        code,raw,h=self.call('/api/export?fmt=docx',{'fields':{'festival_name':'단어 보호 테스트','concept':'지역문화체험'}})
        self.assertEqual(code,200);xml=zipfile.ZipFile(io.BytesIO(raw)).read('word/document.xml').decode()
        self.assertIn('EEE8F7',xml);self.assertIn('w:cantSplit',xml);self.assertIn('w:wordWrap',xml)

    def test_all_conditions_gate_blocks_chat_plan_and_edit_before_any_ai(self):
        from unittest.mock import patch
        u=server.STORE.provision_manager('필수조건담당','Conditions-test-2026!')
        self.session();_,raw,_=self.call('/api/login',{'employee_id':u['name'],'password':'Conditions-test-2026!'});self.csrf=json.loads(raw)['csrf']
        with patch.object(server,'ai_modules') as ai:
            for values in [{},{**COMPLETE,'theme':''},{**COMPLETE,'place':'미정'},{**COMPLETE,'goal':'   '}]:
                self.call('/api/conditions',{'conditions':values})
                for endpoint in ['/api/chat','/api/plan','/api/chat/edit']:
                    code,raw,_=self.call(endpoint,{'question':'조건 없이 진행해줘','message_index':0})
                    self.assertEqual(code,409);self.assertIn('모든 필수 조건',json.loads(raw)['error'])
            ai.assert_not_called()

    def test_tutorial_and_range_requests(self):
        code,raw,h=self.call('/assets_v06/tutorial-60s.mp4',extra={'Range':'bytes=0-31'})
        self.assertEqual(code,206);self.assertEqual(len(raw),32);self.assertIn(b'ftyp',raw);self.assertEqual(h['Accept-Ranges'],'bytes')
        self.assertTrue(h['Content-Range'].startswith('bytes 0-31/'))
        self.assertEqual(self.call('/assets_v06/tutorial-60s.mp4',extra={'Range':'bytes=999999999-'})[0],416)
        self.assertEqual(self.call('/assets_v06/tutorial-ko.vtt')[0],200)
        self.assertEqual(self.call('/journey_v06.js')[0],200)

    def test_admin_remembered_browser_and_logout(self):
        from auth_v06 import now,digest
        u=server.STORE.provision_manager('로그인유지담당','Remember-test-2026!')
        self.session();code,raw,h=self.call('/api/login',{'employee_id':u['name'],'password':'Remember-test-2026!'})
        self.assertEqual(code,200);self.csrf=json.loads(raw)['csrf']
        self.assertIn('Max-Age=2592000',h['Set-Cookie'])
        for path in ['/api/entry','/index_v06.html','/']:
            self.assertEqual(self.call(path)[0],200)
            self.assertEqual(self.call('/api/workspace')[0],200)
        other=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        with other.open(self.base+'/api/me') as r:self.assertIsNone(json.loads(r.read())['user'])
        self.assertEqual(self.call('/api/admin/users')[0],403)
        _,_,h=self.call('/api/logout',{});self.assertIn('Max-Age=0',h['Set-Cookie'])
        self.assertEqual(self.call('/api/workspace')[0],401)

    def test_user_fresh_entry_and_review_revision(self):
        u=server.STORE.register({'org_id':'dgfca','employee_id':'JOURNEY1','name':'김기획','password':'Journey-private-2026!','method':'phone','contact':'01012345678','consent':True})
        with server.STORE.db() as db:db.execute("UPDATE users SET verified=1,status='approved' WHERE id=?",(u['id'],))
        self.session();_,raw,_=self.call('/api/login',{'org_id':'dgfca','employee_id':'JOURNEY1','password':'Journey-private-2026!'})
        self.csrf=json.loads(raw)['csrf']
        self.call('/api/workspace',{'plan':{'festival_name':'여름축제','budget_total':'미정'},'conditions':{'theme':'사투리'}})
        code,raw,_=self.call('/api/review');self.assertEqual(code,200);report=json.loads(raw)
        self.assertFalse(report['complete']);self.assertTrue(report['missing']);self.assertFalse(report['evidence'])
        code,_,_=self.call('/api/review',{'responsible':'김기획','checks':{'missing':True,'evidence':True,'budget':True,'responsibility':True},'note':'미정은 추가 조사 예정'})
        self.assertEqual(code,200);self.assertTrue(json.loads(self.call('/api/review')[1])['complete'])
        self.call('/api/workspace',{'goods':[{'id':'test','name':'손수건'}]})
        self.assertFalse(json.loads(self.call('/api/review')[1])['complete'])
        code,raw,_=self.call('/api/entry');self.assertEqual(code,200);self.assertIsNone(json.loads(raw)['user']);self.assertEqual(self.call('/api/workspace')[0],401)

    def test_no_csrf_or_foreign_origin_denied(self):
        self.assertEqual(self.call('/api/register',{})[0],403)
        self.session()
        self.assertEqual(self.call('/api/register',{}, {'Origin':'https://attacker.example'})[0],403)
    def test_cookie_security(self):
        d,h=self.session();cookie=h['Set-Cookie']
        self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie);self.assertIn('no-store',h['Cache-Control'])
        self.assertIsNone(d['user'])
    def test_pending_registration_cannot_chat(self):
        self.session();b={'org_id':'dgfca','employee_id':'P001','name':'김민지','password':'Private-1234-pass!','method':'phone','contact':'01012345678','consent':True}
        status,raw,_=self.call('/api/register',b);self.assertEqual(status,200)
        d=json.loads(raw);self.csrf=d['csrf'];self.assertEqual(d['user']['status'],'pending')
        for p in ['/api/chat','/api/plan','/api/export?fmt=pdf','/api/workspace']:
            self.assertEqual(self.call(p,{'question':'테스트'})[0],403,p)
        self.assertEqual(self.call('/reference_v06.html')[0],403)
    def test_chat_context_and_saved_messages(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        self.session()
        uid=server.STORE.register({'org_id':'dgfca','employee_id':'CTX1','name':'박수진','password':'Context-private-2026!','method':'phone','contact':'01012345678','consent':True})['id']
        with server.STORE.db() as db:db.execute("UPDATE users SET verified=1,status='approved' WHERE id=?",(uid,))
        status,raw,_=self.call('/api/login',{'org_id':'dgfca','employee_id':'CTX1','password':'Context-private-2026!'})
        self.assertEqual(status,200);self.csrf=json.loads(raw)['csrf']
        self.call('/api/conditions',{'conditions':{**COMPLETE,'budget_total':'4억'}})
        seen=[]
        fake=SimpleNamespace(handle_message=lambda q:(seen.append(q) or {'reply':'기획 답변','steps':[]}))
        with patch.object(server,'ai_modules',return_value=(fake,None,None)):
            self.assertEqual(self.call('/api/chat',{'question':'여름 축제를 열고 싶어요'})[0],200)
            self.assertEqual(self.call('/api/chat',{'question':'실내도 포함해줘'})[0],200)
        self.assertIn('4억',seen[-1]);self.assertIn('여름 축제',seen[-1]);self.assertIn('실내도 포함해줘',seen[-1])
        self.call('/api/workspace',{'conditions':{'예산':'3억'},'messages':[]})
        self.assertEqual(len(server.STORE.workspace(uid)['messages']),4)
        other=server.STORE.register({'org_id':'dgfca','employee_id':'CTX2','name':'이수진','password':'Context-private-2026!','method':'phone','contact':'01012345678','consent':True})
        self.assertEqual(server.STORE.workspace(other['id'])['messages'],[])
        self.call('/api/workspace',{'reset':True})
        self.assertEqual(server.STORE.workspace(uid)['messages'],[])

    def test_owner_bootstrap_and_admin_audited(self):
        self.session();token=server.STORE.bootstrap.read_text().strip()
        status,raw,_=self.call('/api/owner/setup',{'token':token,'name':'김승희','password':'Owner-private-2026!'})
        self.assertEqual(status,200);d=json.loads(raw);self.csrf=d['csrf']
        self.assertEqual(self.call('/api/admin/users')[0],403)
        code=totp(d['totp_secret']);status,confirmed,_=self.call('/api/owner/confirm',{'code':code});self.assertEqual(status,200);self.csrf=json.loads(confirmed)['csrf']
        self.assertEqual(self.call('/api/admin/users')[0],200)
        status,raw,_=self.call('/api/workspace');self.assertEqual(status,200)
        self.assertEqual(json.loads(raw)['messages'],[])
        uid=d['user']['id'];self.assertEqual(self.call('/api/admin/users/'+str(uid)+'/workspace')[0],200)
        status,raw,_=self.call('/api/admin/audit');self.assertIn('admin_workspace_view',raw.decode())
        self.assertNotIn(d['totp_secret'],raw.decode())
        self.assertEqual(self.call('/api/admin/orgs/dgfca',{'domains':['example.go.kr']})[0],200)
        self.call('/api/logout',{})
        self.assertEqual(self.call('/api/admin/users')[0],401)

    def test_zz_local_owner_staged_login(self):
        from auth_v06 import now
        self.session()
        owner=server.STORE.provision_local_owner('김승희','Local-12345')
        body={'org_id':'','employee_id':'김승희','password':'Local-12345'}
        status,raw,_=self.call('/api/login',body|{'password':'wrong'})
        self.assertEqual(status,401);self.assertNotIn('owner_challenge',json.loads(raw))
        status,raw,_=self.call('/api/login',body);self.assertEqual(status,200)
        d=json.loads(raw);self.csrf=d['csrf'];self.assertTrue(d['owner_challenge']);self.assertIsNone(d['user'])
        self.assertIsNone(self.session()[0]['user'])
        for path in ['/api/admin/users','/api/workspace','/api/owner/enrollment','/reference_v06.html']:
            self.assertIn(self.call(path)[0],[401,403])
        status,raw,_=self.call('/api/owner/login-confirm',{'code':totp(owner['totp_secret'],now()+30)})
        self.assertEqual(status,200);self.csrf=json.loads(raw)['csrf']
        self.assertEqual(self.call('/api/admin/users')[0],200)
        self.call('/api/logout',{})
        self.assertEqual(self.call('/api/admin/users')[0],401)

if __name__=='__main__':unittest.main()
