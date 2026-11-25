import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from auth_v06 import Store,Error,totp,now,password_ok

class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/'db.sqlite3')
        token=self.store.bootstrap.read_text().strip()
        self.owner=self.store.setup_owner({'token':token,'name':'김승희','password':'Owner-private-2026!'})
        self.owner=self.store.confirm_owner(self.owner,totp(self.owner['totp_secret']))
    def tearDown(self):self.temp.cleanup()
    def registration(self,**kw):
        b={'org_id':'dgfca','employee_id':'D001','name':'김민지','password':'Private-pass-2026!','method':'phone','contact':'010-1234-5678','consent':True};b.update(kw)
        return self.store.register(b)
    def verify(self,u):
        sent=[]
        with patch.dict(os.environ,{'TWILIO_ACCOUNT_SID':'test','TWILIO_AUTH_TOKEN':'test','TWILIO_FROM':'test'}),patch.object(self.store,'deliver',side_effect=lambda m,c,code:sent.append(code)):
            self.store.send_code(u)
        return self.store.verify(u,sent[0])
    def test_manager_custom_display_label_does_not_grant_owner_rights(self):
        u=self.store.provision_manager('차경훈','Fixture-Teacher-2026!',role_label='강사님 최고✨')
        public=self.store.public(u);self.assertEqual(public['org_name'],'강사님 최고✨');self.assertEqual(public['role'],'manager')
        logged=self.store.direct_password({'employee_id':'차경훈','password':'Fixture-Teacher-2026!'},'fixture')
        self.assertEqual(logged['id'],u['id']);self.store.require_access(logged)
        with self.assertRaises(Error):self.store.require_owner(logged)
        self.assertNotIn('Fixture-Teacher-2026!',json.dumps(public))

    def test_remember_only_fully_authenticated_admins_and_expiry(self):
        from auth_v06 import digest
        for scope,remember in [('owner_challenge',False),('owner_enroll',False),('owner_mfa',True)]:
            token,_=self.store.new_session(self.owner['id'],scope=scope);session=self.store.session(token)
            self.assertEqual(self.store.remembered(session,self.owner),remember)
            self.assertGreaterEqual(session['expires']-now(),(30*86400 if remember else 8*3600)-2)
        self.store.renew_session(token)
        with self.store.db() as db:db.execute('UPDATE sessions SET expires=? WHERE token=?',(now()-1,digest(token)))
        self.assertIsNone(self.store.session(token))
        self.assertFalse(self.store.remembered({'scope':'owner_mfa'},{**self.owner,'status':'suspended'}))

    def test_local_owner_password_stage_requires_exact_credentials(self):
        u=self.store.provision_local_owner('김승희','Local-12345')
        self.assertTrue(password_ok('Local-12345',u['password']))
        self.assertNotIn('Local-12345',u['password'])
        for b in [{'employee_id':'김승희','password':'wrong'}, {'employee_id':'OWNER','password':'Local-12345'}]:
            with self.assertRaises(Error):self.store.owner_password(b,'local')
        self.assertEqual(self.store.owner_password({'employee_id':'김승희','password':'Local-12345'},'local')['id'],u['id'])
        removed={'chimac','dimf','suseong_foundation','buk_foundation','dalseo_foundation'}
        with self.store.db() as db:db.execute("INSERT OR IGNORE INTO orgs(id,name) VALUES('chimac','old choice')")
        self.assertFalse(removed & {x['id'] for x in self.store.status()['orgs']})
        with self.assertRaises(Error):self.registration(org_id='chimac')

    def test_owner_bootstrap_private_and_one_use(self):
        self.assertFalse(self.store.bootstrap.exists());self.assertEqual(self.owner['role'],'owner')
        with self.assertRaises(Error):self.store.setup_owner({'token':'wrong'})
        self.assertEqual(os.stat(self.store.path).st_mode&0o777,0o600)
    def test_pending_owner_requires_bootstrap_and_sessions_revoked(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory)/'test.sqlite3');token=store.bootstrap.read_text().strip()
            b={'token':token,'name':'김승희','password':'Owner-private-2026!'}
            u=store.setup_owner(b);raw,_=store.new_session(u['id'],scope='owner_enroll')
            with self.assertRaises(Error):store.login({'org_id':'owner','employee_id':'OWNER','password':b['password']},'pending-owner')
            self.assertTrue(store.bootstrap.exists())
            self.assertEqual(store.setup_owner(b)['id'],u['id'])
            store.confirm_owner(u,totp(u['totp_secret']))
            self.assertIsNone(store.session(raw));self.assertFalse(store.bootstrap.exists())
            with self.assertRaises(Error):store.confirm_owner(u,totp(u['totp_secret']))

    def test_owner_requires_totp_and_replay_denied(self):
        b={'org_id':'owner','employee_id':'OWNER','password':'Owner-private-2026!'}
        with self.assertRaises(Error):self.store.login(b,'ownerip')
        b['totp']=totp(self.owner['totp_secret'])
        with self.assertRaises(Error):self.store.login(b,'ownerip') # enrollment code cannot be reused
    def test_gate_needs_verification_and_approval(self):
        u=self.registration()
        with self.assertRaises(Error):self.store.require_access(u)
        with self.assertRaises(Error):self.store.decide(self.owner,u['id'],{'status':'approved','affiliation_note':'재직 확인'})
        u=self.verify(u)
        with self.assertRaises(Error):self.store.require_access(u)
        with self.assertRaises(Error):self.store.decide(self.owner,u['id'],{'status':'approved'})
        self.store.decide(self.owner,u['id'],{'status':'approved','affiliation_note':'기관 담당자 명단으로 소속 확인'})
        self.store.require_access(self.store.user(u['id']))
    def test_suspension_immediate(self):
        u=self.verify(self.registration());self.store.decide(self.owner,u['id'],{'status':'approved','affiliation_note':'명단 확인'})
        raw,_=self.store.new_session(u['id']);self.store.decide(self.owner,u['id'],{'status':'suspended','reason':'담당자 요청'})
        with self.assertRaises(Error):self.store.require_access(self.store.user(self.store.session(raw)['user_id']))
    def test_session_rotation_and_hash(self):
        raw,csrf=self.store.new_session(self.owner['id']);new,_=self.store.new_session(self.owner['id'],raw)
        self.assertIsNone(self.store.session(raw));self.assertTrue(self.store.session(new));self.assertNotEqual(raw,csrf)
        with self.store.db() as db:stored=db.execute('SELECT token FROM sessions').fetchone()[0]
        self.assertNotEqual(new,stored)
    def test_duplicate_validation_and_no_role_escalation(self):
        u=self.registration(role='owner',status='approved',verified=True)
        self.assertEqual(u['role'],'user');self.assertFalse(u['verified']);self.assertEqual(u['status'],'pending')
        with self.assertRaises(Error):self.registration(employee_id='d001')
        for b in [{'name':'test'},{'employee_id':' '},{'consent':False},{'password':'123456789012'}]:
            with self.assertRaises(Error):self.registration(employee_id='X002',**{k:v for k,v in b.items() if k!='employee_id'}) if 'employee_id' not in b else self.registration(**b)
    def test_contact_domain_strict(self):
        with self.assertRaises(Error):self.registration(method='email',contact='user@agency.example')
        with self.store.db() as db:db.execute("UPDATE orgs SET domains='[\"agency.example\"]' WHERE id='dgfca'")
        with self.assertRaises(Error):self.registration(method='email',contact='user@agency.example.attacker.com')
        self.assertEqual(self.registration(method='email',contact='USER@AGENCY.EXAMPLE')['contact'],'user@agency.example')
    def test_provider_unconfigured_never_returns_code(self):
        u=self.registration()
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(Error) as c:self.store.send_code(u)
        self.assertEqual(c.exception.status,503);self.assertFalse(self.store.user(u['id'])['verified'])
    def test_wrong_code_attempts_and_expiry(self):
        u=self.registration();sent=[]
        with patch.dict(os.environ,{'TWILIO_ACCOUNT_SID':'t','TWILIO_AUTH_TOKEN':'t','TWILIO_FROM':'t'}),patch.object(self.store,'deliver',side_effect=lambda m,c,v:sent.append(v)):
            self.store.send_code(u)
        wrong='111111' if sent[0]!='111111' else '222222'
        for _ in range(5):
            with self.assertRaises(Error):self.store.verify(u,wrong)
        with self.assertRaises(Error):self.store.verify(u,sent[0])
        with self.store.db() as db:
            row=db.execute('SELECT * FROM challenges').fetchone();self.assertNotIn(sent[0],row['hash']);db.execute('UPDATE challenges SET attempts=0,expires=?',(now()-1,))
        with self.assertRaises(Error):self.store.verify(u,sent[0])
    def test_delivery_failure_clears_challenge(self):
        u=self.registration()
        with patch.dict(os.environ,{'TWILIO_ACCOUNT_SID':'t','TWILIO_AUTH_TOKEN':'t','TWILIO_FROM':'t'}),patch.object(self.store,'deliver',side_effect=RuntimeError('secret')):
            with self.assertRaises(Error) as e:self.store.send_code(u)
        self.assertNotIn('secret',str(e.exception))
        with self.store.db() as db:self.assertIsNone(db.execute('SELECT * FROM challenges').fetchone())
    def test_owner_only_approval_and_workspaces_separate(self):
        a=self.registration();b=self.registration(employee_id='D002')
        with self.assertRaises(Error):self.store.decide(a,b['id'],{'status':'approved'})
        self.store.save_workspace(a['id'],{'messages':[{'role':'assistant','content':'기관 A 업무'}],'conditions':{},'plan':None,'goods':[]})
        self.assertEqual(self.store.workspace(b['id'])['messages'],[])
        self.assertEqual(self.store.workspace(a['id'])['messages'][0]['content'],'기관 A 업무')
    def test_public_does_not_expose_credentials(self):
        p=self.store.public(self.owner)
        for k in ['password','totp_secret','totp_last']:self.assertNotIn(k,p)
    def test_revoked_sessions_and_throttle(self):
        raw,_=self.store.new_session();self.store.logout(raw);self.assertIsNone(self.store.session(raw))
        self.store.limit('test',1,60)
        with self.assertRaises(Error):self.store.limit('test',1,60)

if __name__=='__main__':unittest.main()
