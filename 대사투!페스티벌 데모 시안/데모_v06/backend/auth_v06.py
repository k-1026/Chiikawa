"""Institution accounts, verified contact, human approval, owner TOTP, and audit storage."""
from plan_schema_v06 import normalize_plan
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import sqlite3
import struct
import time
import unicodedata
from contextlib import contextmanager
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

ORGS = [('daegu','대구광역시청 콘텐츠산업과'),('dgfca','대구문화예술진흥원')]
for k,n in [('jung','중구'),('dong','동구'),('seo','서구'),('nam','남구'),('buk','북구'),('suseong','수성구'),('dalseo','달서구'),('dalseong','달성군'),('gunwi','군위군')]:
    ORGS.append(('district_'+k,n+'청 문화관광 담당 부서'))
# Removed institution choices are excluded from new registration.
# ORGS += [('suseong_foundation','수성문화재단'),('buk_foundation','행복북구문화재단'),('dalseo_foundation','달서문화재단'),('dimf','대구국제뮤지컬페스티벌(DIMF)'),('chimac','한국치맥산업협회')]

class Error(Exception):
    def __init__(self,message,status=400): self.status=status; super().__init__(message)

def now(): return int(time.time())
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def password_hash(password,salt=None,min_length=12):
    if not isinstance(password,str) or not min_length<=len(password)<=128: raise Error(f'비밀번호는 {min_length}~128자로 입력해 주세요.')
    if password.lower() in {'password1234','123456789012','qwerty123456','aaaaaaaaaaaa'} or len(set(password))<4: raise Error('쉽게 추측할 수 없는 비밀번호를 사용해 주세요.')
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1,dklen=32).hex()

def password_ok(password,stored):
    try:
        salt,value=stored.split(':'); raw=hashlib.scrypt(str(password)[:128].encode(),salt=salt.encode(),n=16384,r=8,p=1,dklen=32).hex()
        return hmac.compare_digest(raw,value) and len(str(password))<=128
    except (ValueError,TypeError): return False

def totp(secret,at=None):
    key=base64.b32decode(secret+'='*((-len(secret))%8)); msg=struct.pack('>Q',(now() if at is None else at)//30)
    value=hmac.new(key,msg,hashlib.sha1).digest(); offset=value[-1]&15
    return str((struct.unpack('>I',value[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)

def totp_counter(secret,code,last=-1):
    if not re.fullmatch(r'\d{6}',str(code)): return None
    for d in [-1,0,1]:
        t=now()+d*30; c=t//30
        if c>last and hmac.compare_digest(totp(secret,t),str(code)): return c
    return None

class Store:
    def __init__(self,path,url=None,schema='daesatu'):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        os.chmod(self.path.parent,0o700)
        self.pg=None
        test_schema=os.getenv('DAESATU_TEST_SCHEMA')  # 테스트 전용: 실제 데이터 스키마(daesatu)는 절대 비우지 않는다
        if test_schema and not url:url,schema=os.getenv('DATABASE_URL'),test_schema
        if url:
            from pg_store_v06 import PgStore
            self.pg=PgStore(url,schema)
            if test_schema:
                if schema!='daesatu_test':raise RuntimeError('테스트 스키마 이름이 올바르지 않습니다.')
                with self.pg.db() as c:c.con.execute('TRUNCATE orgs,users,sessions,challenges,workspaces,audit,rates,attachments RESTART IDENTITY')
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS orgs(id TEXT PRIMARY KEY,name TEXT NOT NULL,domains TEXT NOT NULL DEFAULT '[]');
            CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,org_id TEXT NOT NULL,employee_id TEXT NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'user',status TEXT NOT NULL DEFAULT 'pending',method TEXT NOT NULL,contact TEXT NOT NULL,verified INTEGER NOT NULL DEFAULT 0,reason TEXT NOT NULL DEFAULT '',affiliation_note TEXT NOT NULL DEFAULT '',totp_secret TEXT,totp_last INTEGER NOT NULL DEFAULT -1,consent_at INTEGER NOT NULL,created_at INTEGER NOT NULL,UNIQUE(org_id,employee_id));
            CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER,csrf TEXT NOT NULL,expires INTEGER NOT NULL,scope TEXT NOT NULL DEFAULT 'normal');
            CREATE TABLE IF NOT EXISTS challenges(user_id INTEGER PRIMARY KEY,hash TEXT NOT NULL,expires INTEGER NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,sent_at INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS workspaces(user_id INTEGER PRIMARY KEY,data TEXT NOT NULL,updated_at INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor INTEGER,action TEXT NOT NULL,target INTEGER,detail TEXT NOT NULL,created_at INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS rates(key TEXT NOT NULL,created_at INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS rates_key ON rates(key,created_at);
            ''')
            if 'scope' not in [r[1] for r in db.execute('PRAGMA table_info(sessions)')]:
                db.execute("ALTER TABLE sessions ADD COLUMN scope TEXT NOT NULL DEFAULT 'normal'")
            if 'role_label' not in [r[1] for r in db.execute('PRAGMA table_info(users)')]:
                db.execute("ALTER TABLE users ADD COLUMN role_label TEXT NOT NULL DEFAULT ''")
            if 'direct_login' not in [r[1] for r in db.execute('PRAGMA table_info(users)')]:
                db.execute('ALTER TABLE users ADD COLUMN direct_login INTEGER NOT NULL DEFAULT 0')
            db.executemany('INSERT OR IGNORE INTO orgs(id,name) VALUES(?,?)',ORGS)
        if not self.pg and self.path.exists():os.chmod(self.path,0o600)
        self.bootstrap=self.path.parent/'owner_setup_token.txt'
        with self.db() as db: has_owner=db.execute("SELECT 1 FROM users WHERE role='owner'").fetchone()
        if not has_owner and not self.bootstrap.exists():
            with self.bootstrap.open('x') as f: f.write(secrets.token_urlsafe(32)+'\n')
            os.chmod(self.bootstrap,0o600)

    @contextmanager
    def db(self):
        if self.pg:
            with self.pg.db() as con:yield con
            return
        con=sqlite3.connect(self.path,timeout=20);con.row_factory=sqlite3.Row
        try:
            yield con;con.commit()
        except: con.rollback();raise
        finally: con.close()

    def event(self,actor,action,target=None,detail=''):
        with self.db() as db: db.execute('INSERT INTO audit(actor,action,target,detail,created_at) VALUES(?,?,?,?,?)',(actor,action,target,str(detail)[:1000],now()))

    def limit(self,key,n,seconds):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            count=db.execute('SELECT count(*) FROM rates WHERE key=? AND created_at>?',(key,now()-seconds)).fetchone()[0]
            if count>=n: raise Error('요청이 많아요. 잠시 후 다시 시도해 주세요.',429)
            db.execute('INSERT INTO rates VALUES(?,?)',(key,now()));db.execute('DELETE FROM rates WHERE created_at<?',(now()-86400,))

    def status(self):
        with self.db() as db:
            owner=db.execute("SELECT 1 FROM users WHERE role='owner'").fetchone()
            orgs=[dict(r) for r in db.execute('SELECT * FROM orgs')]
        orgs=[r for r in orgs if r['id'] in dict(ORGS)]
        for r in orgs:r['domains']=json.loads(r['domains'])
        return {'setup_required':not bool(owner),'providers':{'email':bool(os.getenv('SMTP_HOST') and os.getenv('SMTP_FROM')),'phone':all(os.getenv(k) for k in ['TWILIO_ACCOUNT_SID','TWILIO_AUTH_TOKEN','TWILIO_FROM'])},'orgs':orgs}

    def user(self,uid):
        with self.db() as db: row=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
        return dict(row) if row else None

    def public(self,u):
        if not u:return None
        org_name=(u.get('role_label') if u['role']=='manager' else '') or {'owner':'최고 관리자','manager':'일반 관리자'}.get(u['role'],dict(ORGS).get(u['org_id'],u['org_id']))
        return {k:u[k] for k in ['id','org_id','employee_id','name','role','status','method','contact','verified','reason','created_at','affiliation_note']}|{'org_name':org_name}

    def session(self,raw):
        if not raw:return None
        with self.db() as db: r=db.execute('SELECT * FROM sessions WHERE token=? AND expires>?',(digest(raw),now())).fetchone()
        return dict(r) if r else None

    def new_session(self,uid=None,old=None,scope='normal'):
        token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
        person=self.user(uid) if uid else None
        duration=30*86400 if self.remembered({'scope':scope},person) else 8*3600
        with self.db() as db:
            if old:db.execute('DELETE FROM sessions WHERE token=?',(digest(old),))
            db.execute('DELETE FROM sessions WHERE expires<?',(now(),))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(digest(token),uid,csrf,now()+duration,scope))
        return token,csrf

    def remembered(self,session,user):
        return bool(session and user and user['verified'] and user['status']=='approved' and ((user['role']=='manager' and session['scope']=='normal') or (user['role']=='owner' and session['scope']=='owner_mfa')))

    def renew_session(self,raw):
        with self.db() as db:db.execute('UPDATE sessions SET expires=? WHERE token=?',(now()+30*86400,digest(raw)))

    def logout(self,raw):
        with self.db() as db:db.execute('DELETE FROM sessions WHERE token=?',(digest(raw),))

    def register(self,b):
        org=str(b.get('org_id','')); eid=unicodedata.normalize('NFKC',str(b.get('employee_id','')).strip()).upper(); name=unicodedata.normalize('NFC',str(b.get('name','')).strip())
        method=b.get('method'); contact=str(b.get('contact','')).strip()
        if org not in dict(ORGS): raise Error('소속 기관을 선택해 주세요.')
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9_-]{1,39}',eid):raise Error('사원번호는 영문·숫자·밑줄·하이픈 2~40자로 입력해 주세요.')
        if not re.fullmatch(r'[가-힣A-Za-zÀ-ž·. -]{2,50}',name) or name.casefold() in {'테스트','홍길동','관리자','test','admin','익명','아무개'}: raise Error('실제 사원 이름을 입력해 주세요.')
        if b.get('consent') is not True: raise Error('운영자 열람 및 개인정보 처리 안내를 확인해 주세요.')
        if method=='email':
            contact=contact.lower()
            if not re.fullmatch(r'[^\s@]{1,64}@(?:[a-z0-9-]+\.)+[a-z]{2,63}',contact):raise Error('올바른 기관 이메일 주소를 입력해 주세요.')
            with self.db() as db:domains=json.loads(db.execute('SELECT domains FROM orgs WHERE id=?',(org,)).fetchone()[0])
            if not domains:raise Error('기관 이메일 도메인 확인이 필요합니다. 운영자에게 문의해 주세요.')
            if contact.rsplit('@',1)[1] not in domains:raise Error('선택한 기관에서 승인한 이메일 도메인이 아닙니다.')
        elif method=='phone':
            contact=re.sub(r'[\s()-]','',contact)
            if contact.startswith('010'):contact='+82'+contact[1:]
            if not re.fullmatch(r'\+8210\d{8}',contact):raise Error('본인 휴대폰 번호(010 또는 +8210)를 입력해 주세요.')
        else:raise Error('이메일 또는 휴대폰 인증을 선택해 주세요.')
        hashed=password_hash(b.get('password'))
        if str(b.get('password')).casefold() in {eid.casefold(),contact.casefold(),name.casefold()}:raise Error('사원정보와 다른 비밀번호를 사용해 주세요.')
        try:
            with self.db() as db:
                cur=db.execute('INSERT INTO users(org_id,employee_id,name,password,method,contact,consent_at,created_at) VALUES(?,?,?,?,?,?,?,?)',(org,eid,name,hashed,method,contact,now(),now()));uid=cur.lastrowid
        except sqlite3.IntegrityError: raise Error('이미 등록된 기관·사원번호입니다. 로그인해 주세요.',409)
        self.event(uid,'registration',uid,'운영자 열람·처리 안내 동의');return self.user(uid)

    def login(self,b,ip):
        self.limit('login:'+ip,12,900)
        with self.db() as db:u=db.execute('SELECT * FROM users WHERE org_id=? AND employee_id=?',(b.get('org_id'),str(b.get('employee_id','')).strip().upper())).fetchone()
        good=password_ok(b.get('password',''),u['password'] if u else '0'*32+':'+'0'*64)
        if not u or not good:
            self.event(None,'login_failed')
            raise Error('기관·사원번호 또는 비밀번호를 확인해 주세요.',401)
        u=dict(u)
        if u['role']=='owner' and not u['verified']:
            raise Error('최고관리자 초기 설정 코드로 인증 앱 등록을 먼저 완료해 주세요.',403)
        if u['role']=='owner' and u['verified']:
            return self.confirm_owner_login(u,b.get('totp',''))
        self.event(u['id'],'login');return u

    def provision_local_owner(self,name,password):
        """Explicit local operator provisioning; never exposed by an HTTP endpoint."""
        hashed=password_hash(password,min_length=10)
        secret=base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute("SELECT * FROM users WHERE role='owner'").fetchone()
            if existing:
                if existing['name']!=name:raise Error('다른 운영자 계정이 이미 있습니다.',409)
                db.execute("UPDATE users SET employee_id=?,password=?,direct_login=1 WHERE id=?",(name,hashed,existing['id']))
                db.execute('DELETE FROM sessions WHERE user_id=?',(existing['id'],));uid=existing['id']
            else:
                uid=db.execute("INSERT INTO users(org_id,employee_id,name,password,role,status,method,contact,totp_secret,consent_at,created_at,direct_login) VALUES('owner',?,?,?,'owner','pending','totp','',?,?,?,1)",(name,name,hashed,secret,now(),now())).lastrowid
        self.event(uid,'owner_local_login_configured');return self.user(uid)

    def provision_manager(self,name,password,role_label=''):
        """Local-only provisioning explicitly authorized by the service owner."""
        name=unicodedata.normalize('NFC',str(name).strip())
        if not re.fullmatch(r'[가-힣]{2,10}',name):raise Error('관리자 이름을 확인해 주세요.')
        role_label=str(role_label).strip()
        if role_label and (len(role_label)>30 or re.search(r'[\x00-\x1f\x7f]',role_label)):raise Error('권한 표시 이름을 확인해 주세요.')
        hashed=password_hash(password,min_length=8)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM users WHERE employee_id=? AND direct_login=1 AND role!='manager'",(name,)).fetchone():raise Error('다른 권한의 로그인 이름과 중복됩니다.',409)
            row=db.execute("SELECT id FROM users WHERE org_id='manager' AND employee_id=?",(name,)).fetchone()
            if row:
                uid=row['id'];db.execute("UPDATE users SET name=?,password=?,role='manager',status='approved',verified=1,direct_login=1,reason='' WHERE id=?",(name,hashed,uid));db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
            else:
                uid=db.execute("INSERT INTO users(org_id,employee_id,name,password,role,status,method,contact,verified,consent_at,created_at,direct_login) VALUES('manager',?,?,?,'manager','approved','provisioned','',1,?,?,1)",(name,name,hashed,now(),now())).lastrowid
        with self.db() as db:db.execute('UPDATE users SET role_label=? WHERE id=?',(role_label,uid))
        self.event(uid,'manager_provisioned',uid,'최고 관리자의 명시적 요청으로 사전 등록');return self.user(uid)

    def owner_password(self,b,ip):
        return self.direct_password(b,ip)

    def direct_password(self,b,ip):
        self.limit('login:'+ip,12,900)
        eid=unicodedata.normalize('NFC',str(b.get('employee_id','')).strip())
        with self.db() as db:
            row=db.execute("SELECT * FROM users WHERE role IN ('owner','manager') AND direct_login=1 AND employee_id=?",(eid,)).fetchone()
        good=password_ok(b.get('password',''),row['password'] if row else '0'*32+':'+'0'*64)
        if not row or not good:
            self.event(None,'login_failed');raise Error('기관·사원번호 또는 비밀번호를 확인해 주세요.',401)
        u=dict(row)
        if u['verified'] and u['status']!='approved':raise Error('이용할 수 없는 계정입니다.',403)
        return u

    def confirm_owner_login(self,u,code):
        if not u or u['role']!='owner' or not u['verified']:raise Error('다시 로그인해 주세요.',401)
        self.limit('totp:'+str(u['id']),6,300)
        counter=totp_counter(u['totp_secret'],code,u['totp_last'])
        if counter is None:raise Error('인증 앱의 새로운 6자리 코드를 입력해 주세요.',401)
        with self.db() as db:
            cur=db.execute('UPDATE users SET totp_last=? WHERE id=? AND totp_last<?',(counter,u['id'],counter))
            if not cur.rowcount:raise Error('이미 사용한 인증 코드입니다.',401)
        self.event(u['id'],'login');return self.user(u['id'])

    def setup_owner(self,b):
        self.limit('owner-setup',10,900)
        token=str(b.get('token',''))
        if not self.bootstrap.exists() or not hmac.compare_digest(token,self.bootstrap.read_text().strip()):raise Error('초기 설정 코드가 올바르지 않습니다.',403)
        name=str(b.get('name','')).strip()
        if not 2<=len(name)<=50:raise Error('운영자 이름을 입력해 주세요.')
        pw=password_hash(b.get('password'));secret=base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute("SELECT * FROM users WHERE role='owner'").fetchone()
            if existing:
                if existing['verified'] or not password_ok(b.get('password',''),existing['password']):
                    raise Error('최고관리자가 이미 등록되어 있거나 초기 설정 정보가 일치하지 않습니다.',409)
                return dict(existing)
            uid=db.execute("INSERT INTO users(org_id,employee_id,name,password,role,status,method,contact,totp_secret,consent_at,created_at) VALUES('owner','OWNER',?,?,'owner','pending','totp','',?,?,?)",(name,pw,secret,now(),now())).lastrowid
        self.event(uid,'owner_setup');return self.user(uid)

    def owner_enrollment(self,u):
        if u['role']!='owner' or u['verified']:raise Error('초기 보안 설정 대상이 아닙니다.',403)
        return {'totp_secret':u['totp_secret'],'otpauth_uri':'otpauth://totp/'+quote('Daesatu:OWNER')+'?secret='+u['totp_secret']+'&issuer=Daesatu&algorithm=SHA1&digits=6&period=30'}

    def confirm_owner(self,u,code):
        self.limit('totp:'+str(u['id']),6,300)
        self.owner_enrollment(u);counter=totp_counter(u['totp_secret'],code)
        if counter is None:raise Error('인증 앱의 6자리 코드를 확인해 주세요.')
        with self.db() as db:
            cur=db.execute("UPDATE users SET verified=1,status='approved',totp_last=? WHERE id=? AND verified=0",(counter,u['id']))
            if not cur.rowcount:raise Error('이미 완료된 초기 설정입니다.',409)
            db.execute('DELETE FROM sessions WHERE user_id=?',(u['id'],))
        if self.bootstrap.exists():self.bootstrap.unlink()
        self.event(u['id'],'owner_totp_enabled');return self.user(u['id'])

    def send_code(self,u):
        if u['verified']:raise Error('이미 인증을 완료했습니다.')
        if u['role']=='owner':raise Error('인증 앱으로 보안 설정을 완료해 주세요.')
        if not self.status()['providers'][u['method']]:raise Error('인증 발송 서비스가 아직 연결되지 않았습니다. 운영자에게 문의해 주세요.',503)
        self.limit('send:'+str(u['id']),5,3600)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT sent_at FROM challenges WHERE user_id=?',(u['id'],)).fetchone()
            if old and old[0]>now()-60:raise Error('인증번호는 60초 후 다시 요청할 수 있습니다.',429)
            code=str(secrets.randbelow(1000000)).zfill(6);salt=secrets.token_hex(16)
            db.execute('INSERT OR REPLACE INTO challenges VALUES(?,?,?,?,?)',(u['id'],salt+':'+digest(salt+code),now()+600,0,now()))
        try:self.deliver(u['method'],u['contact'],code)
        except Exception:
            with self.db() as db:db.execute('DELETE FROM challenges WHERE user_id=?',(u['id'],))
            self.event(u['id'],'verification_delivery_failed');raise Error('인증번호 발송에 실패했습니다. 잠시 후 다시 시도해 주세요.',503)
        self.event(u['id'],'verification_sent');return {'sent':True,'expires_in':600}

    def deliver(self,method,contact,code):
        text='[대사투! 페스티벌] 인증번호 '+code+' (10분 유효). 본인이 요청하지 않았다면 무시하세요.'
        if method=='email':
            msg=EmailMessage();msg['Subject']='대사투! 페스티벌 기관 이메일 인증';msg['From']=os.environ['SMTP_FROM'];msg['To']=contact;msg.set_content(text)
            host=os.environ['SMTP_HOST'];port=int(os.getenv('SMTP_PORT','587'))
            import ssl
            with smtplib.SMTP_SSL(host,port,timeout=15,context=ssl.create_default_context()) if port==465 else smtplib.SMTP(host,port,timeout=15) as smtp:
                if port!=465:smtp.starttls(context=ssl.create_default_context())
                if os.getenv('SMTP_USER'):smtp.login(os.environ['SMTP_USER'],os.environ.get('SMTP_PASSWORD',''))
                smtp.send_message(msg)
        else:
            sid=os.environ['TWILIO_ACCOUNT_SID'];auth=base64.b64encode((sid+':'+os.environ['TWILIO_AUTH_TOKEN']).encode()).decode()
            req=Request('https://api.twilio.com/2010-04-01/Accounts/'+quote(sid,safe='')+'/Messages.json',data=urlencode({'To':contact,'From':os.environ['TWILIO_FROM'],'Body':text}).encode(),headers={'Authorization':'Basic '+auth})
            with urlopen(req,timeout=15) as response:response.read(1000)

    def verify(self,u,code):
        self.limit('verify:'+str(u['id']),10,600)
        ok=False
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE');c=db.execute('SELECT * FROM challenges WHERE user_id=?',(u['id'],)).fetchone()
            if not c or c['expires']<now() or c['attempts']>=5:raise Error('인증번호가 만료되었거나 시도 횟수를 초과했습니다. 다시 발송해 주세요.')
            salt,hashvalue=c['hash'].split(':');ok=bool(re.fullmatch(r'\d{6}',str(code))) and hmac.compare_digest(digest(salt+str(code)),hashvalue)
            db.execute('UPDATE challenges SET attempts=attempts+1 WHERE user_id=?',(u['id'],))
            if ok:
                db.execute('UPDATE users SET verified=1 WHERE id=?',(u['id'],));db.execute('DELETE FROM challenges WHERE user_id=?',(u['id'],))
        if not ok:raise Error('인증번호가 일치하지 않습니다.')
        self.event(u['id'],'contact_verified');return self.user(u['id'])

    def require_access(self,u):
        if not u:raise Error('로그인이 필요합니다.',401)
        if not u['verified'] or u['status']!='approved':raise Error('연락처 인증과 소속 확인·승인이 필요합니다.',403)
        return u

    def require_owner(self,u):
        self.require_access(u)
        if u['role']!='owner':raise Error('최고관리자 권한이 필요합니다.',403)

    def decide(self,owner,target,b):
        self.require_owner(owner);u=self.user(target)
        if not u or u['role']=='owner':raise Error('변경할 수 없는 계정입니다.',404)
        status=b.get('status');reason=str(b.get('reason','')).strip()[:1000];note=str(b.get('affiliation_note','')).strip()[:1000]
        if status not in ['approved','rejected','suspended']:raise Error('올바른 승인 상태를 선택해 주세요.')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE');fresh=db.execute('SELECT verified FROM users WHERE id=?',(target,)).fetchone()
            if status=='approved' and (not fresh[0] or not note):raise Error('연락처 인증 완료 및 소속 확인 기록이 있어야 승인할 수 있습니다.')
            if status in ['rejected','suspended'] and not reason:raise Error('반려·정지 사유를 입력해 주세요.')
            db.execute('UPDATE users SET status=?,reason=?,affiliation_note=? WHERE id=?',(status,reason,note or u['affiliation_note'],target))
        self.event(owner['id'],'user_'+status,target,note or reason)

    def workspace(self,uid):
        with self.db() as db:r=db.execute('SELECT data FROM workspaces WHERE user_id=?',(uid,)).fetchone()
        w=json.loads(r[0]) if r else {'messages':[],'conditions':{},'plan':None,'goods':[]}
        if isinstance(w.get('plan'),dict):w['plan']=normalize_plan(w['plan'])
        return w

    def save_workspace(self,uid,w):
        if not isinstance(w,dict):raise Error('잘못된 작업 데이터입니다.')
        data={k:w.get(k,v) for k,v in {'messages':[],'conditions':{},'plan':None,'goods':[],'review':None,'agent':None,'archives':[],'condition_inputs':{}}.items()}
        if not isinstance(data['messages'],list) or not isinstance(data['conditions'],dict) or not isinstance(data['goods'],list) or not isinstance(data['plan'],(dict,type(None))):raise Error('작업 데이터 형식이 올바르지 않습니다.')
        data['messages']=[{'role':m['role'],'content':m['content'][:30000],**({'attachments':[{'id':str(a.get('id',''))[:100],'name':str(a.get('name',''))[:180],'size':a.get('size',0),'format':str(a.get('format',''))[:12],'truncated':bool(a.get('truncated'))} for a in m.get('attachments',[])[:5] if isinstance(a,dict)]} if isinstance(m.get('attachments'),list) and m['attachments'] else {})} for m in data['messages'][-200:] if isinstance(m,dict) and m.get('role') in ['user','assistant'] and isinstance(m.get('content'),str)]
        if data['plan'] is not None:data['plan']=normalize_plan(data['plan'])
        data['archives']=[{'at':v.get('at'),'messages':v.get('messages',[])[:200],'plan':v.get('plan')} for v in data['archives'][-3:] if isinstance(v,dict)] if isinstance(data['archives'],list) else []
        data['condition_inputs']=data['condition_inputs'] if isinstance(data['condition_inputs'],dict) else {}
        a=data.get('agent')
        if a is not None:
            if not isinstance(a,dict):raise Error('에이전트 진행 형식이 올바르지 않습니다.')
            data['agent']={'questions':[{'key':str(q.get('key',''))[:50],'text':str(q.get('text',''))[:300]} for q in a.get('questions',[])[:4] if isinstance(q,dict)],'stages':[{'label':str(t.get('label',''))[:100],'status':'done'} for t in a.get('stages',[])[:8] if isinstance(t,dict)],'next':{k:str(a.get('next',{}).get(k,''))[:300] for k in ('page','label','description')}}
        r=data.get('review')
        if r is not None:
            if not isinstance(r,dict):raise Error('검토 기록 형식이 올바르지 않습니다.')
            data['review']={'signature':str(r.get('signature',''))[:64],'checks':{k:r.get('checks',{}).get(k) is True for k in ('missing','evidence','budget','responsibility')},'responsible':str(r.get('responsible',''))[:100],'note':str(r.get('note',''))[:2000],'at':r.get('at') if isinstance(r.get('at'),int) else None}
        raw=json.dumps(data,ensure_ascii=False)
        if len(raw)>1000000:raise Error('기획 데이터가 너무 큽니다.',413)
        with self.db() as db:db.execute('INSERT OR REPLACE INTO workspaces VALUES(?,?,?)',(uid,raw,now()))
        return data
