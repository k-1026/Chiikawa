"""SQLite 문법으로 쓰인 저장소 코드를 Supabase(PostgreSQL)에서 그대로 쓰게 해 주는 얇은 어댑터.
Store.db() 가 돌려주는 연결 객체와 같은 사용법(execute/executemany/executescript, row['col'], row[0], lastrowid)을 지킨다.
- 질문 부호(?) 자리표시자를 %s 로 바꾸고, SQLite 전용 문장(PRAGMA, ALTER TABLE ADD COLUMN, CREATE TABLE)은 건너뛴다(스키마는 supabase/001_accounts.sql 로 만든다).
- BEGIN IMMEDIATE 는 트랜잭션 단위 advisory lock 으로 바꾼다.
- 고유값 중복 오류는 sqlite3.IntegrityError 로 바꿔 기존 except 구문이 그대로 동작한다."""
import atexit
import os
import re
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import psycopg  # noqa: E402
from psycopg import errors as pgerr  # noqa: E402
from psycopg_pool import ConnectionPool  # noqa: E402

LOCK_KEY = 60061125
# INSERT OR REPLACE 가 쓰이는 표: (기본키, 갱신할 열)
REPLACE = {
    'challenges': ('user_id', ['hash', 'expires', 'attempts', 'sent_at']),
    'workspaces': ('user_id', ['data', 'updated_at']),
}


class Row(dict):
    """row['col'] 와 row[0] 를 모두 지원하고 dict(row) 로 복사할 수 있다."""
    def __getitem__(self, k):
        return list(self.values())[k] if isinstance(k, int) else dict.__getitem__(self, k)


def _row_factory(cur):
    names = [d.name for d in cur.description] if cur.description else []
    return lambda values: Row(zip(names, values))


class _Empty:
    lastrowid = None
    rowcount = 0
    def fetchone(self): return None
    def fetchall(self): return []
    def __iter__(self): return iter(())


class _Cur:
    def __init__(self, cur, lastrowid=None):
        self.cur, self.lastrowid = cur, lastrowid
        self.rowcount = cur.rowcount
    def fetchone(self): return self.cur.fetchone() if self.cur.description else None
    def fetchall(self): return self.cur.fetchall() if self.cur.description else []
    def __iter__(self): return iter(self.fetchall())


def translate(sql: str):
    """SQLite 문장을 PostgreSQL 문장으로 바꾼다. 건너뛸 문장이면 None."""
    s = sql.strip().rstrip(';')
    u = s.upper()
    if u.startswith('PRAGMA') or u.startswith('CREATE TABLE') or u.startswith('CREATE INDEX') or re.match(r'ALTER TABLE \w+ ADD COLUMN', u):
        return None
    ignore = False
    if u.startswith('INSERT OR IGNORE INTO'):
        s = 'INSERT INTO' + s[len('INSERT OR IGNORE INTO'):]
        ignore = True
    upsert = None
    m = re.match(r'INSERT OR REPLACE INTO (\w+)', s, re.I)
    if m:
        t = m.group(1).lower()
        if t not in REPLACE:
            raise ValueError('unsupported REPLACE target: ' + t)
        key, cols = REPLACE[t]
        s = 'INSERT INTO' + s[len('INSERT OR REPLACE INTO'):]
        upsert = ' ON CONFLICT (%s) DO UPDATE SET %s' % (key, ', '.join('%s=EXCLUDED.%s' % (c, c) for c in cols))
    s = s.replace('%', '%%').replace('?', '%s')
    if ignore:
        s += ' ON CONFLICT DO NOTHING'
    if upsert:
        s += upsert
    return s


class PgDB:
    def __init__(self, con):
        self.con = con

    def _run(self, sql, many=None, params=()):
        u = sql.strip().upper()
        if u.startswith('BEGIN'):
            self.con.execute('SELECT pg_advisory_xact_lock(%s)', (LOCK_KEY,))
            return _Empty()
        t = translate(sql)
        if t is None:
            return _Empty()
        returning = t.upper().startswith('INSERT INTO USERS(')
        if returning and 'RETURNING' not in t.upper():
            t += ' RETURNING id'
        try:
            cur = self.con.cursor(row_factory=_row_factory)
            if many is not None:
                cur.executemany(t, many)
                return _Cur(cur)
            cur.execute(t, params)
            last = cur.fetchone()['id'] if returning else None
            return _Cur(cur, last)
        except (pgerr.UniqueViolation, pgerr.IntegrityError) as e:
            raise sqlite3.IntegrityError(str(e)) from None

    def execute(self, sql, params=()):
        return self._run(sql, params=params)

    def executemany(self, sql, seq):
        return self._run(sql, many=list(seq))

    def executescript(self, script):
        return _Empty()  # 스키마는 supabase/001_accounts.sql 로 미리 만든다


class PgStore:
    """psycopg 연결 풀. schema 는 기본 daesatu (테스트는 daesatu_test)."""
    def __init__(self, url, schema='daesatu', max_size=6):
        if not re.fullmatch(r'[a-z_][a-z0-9_]*', schema):
            raise ValueError('bad schema')
        self.schema = schema
        self.pool = ConnectionPool(url, min_size=1, max_size=max_size, open=True, timeout=20,
                                   kwargs={'sslmode': 'require', 'connect_timeout': 15, 'autocommit': False},
                                   configure=lambda c: (c.execute(f'SET search_path TO {schema}, extensions'), c.commit()))
        atexit.register(self.close)

    def close(self):
        try:
            self.pool.close()
        except Exception:
            pass

    @contextmanager
    def db(self):
        with self.pool.connection() as con:
            try:
                yield PgDB(con)
                con.commit()
            except BaseException:
                con.rollback()
                raise
