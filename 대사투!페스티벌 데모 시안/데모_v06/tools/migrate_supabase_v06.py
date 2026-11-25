"""Copy an existing private SQLite snapshot into Supabase Postgres atomically.

Dry-run prints counts only. DATABASE_URL is read from the environment, never argv.
Do not place the database, connection URL, or exported rows in the public package.
"""
import argparse
import json
import os
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TABLES=('orgs','users','sessions','challenges','workspaces','audit','rates','attachments')

def snapshot(path):
    con=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    try:
        con.execute('BEGIN')
        found={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        result={}
        for table in TABLES:
            if table not in found:continue
            cur=con.execute('SELECT * FROM "'+table+'"')
            result[table]=([d[0] for d in cur.description],cur.fetchall())
        return result
    finally:con.close()

def migrate(path):
    import psycopg
    from psycopg import sql
    url=os.environ.get('DATABASE_URL','')
    if not url:raise ValueError('DATABASE_URL is required in the process environment')
    data=snapshot(path)
    # A single transaction rolls back schema and all rows on any failure.
    with psycopg.connect(url,sslmode='require',connect_timeout=15) as con:
        con.execute((ROOT/'supabase/001_accounts.sql').read_text())
        con.execute('SELECT pg_advisory_xact_lock(60061124)')
        for table in data:
            n=con.execute(sql.SQL('SELECT count(*) FROM daesatu.{}').format(sql.Identifier(table))).fetchone()[0]
            if n:raise ValueError('Destination is not empty; refusing to overwrite '+table)
        counts={}
        for table,(columns,rows) in data.items():
            if rows:
                stmt=sql.SQL('INSERT INTO daesatu.{} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,columns)),sql.SQL(',').join(sql.Placeholder() for _ in columns))
                with con.cursor() as cur:cur.executemany(stmt,rows)
            actual=con.execute(sql.SQL('SELECT count(*) FROM daesatu.{}').format(sql.Identifier(table))).fetchone()[0]
            if actual!=len(rows):raise ValueError('Row count mismatch: '+table)
            counts[table]=actual
        for table in ('users','audit'):
            con.execute(sql.SQL("SELECT setval(pg_get_serial_sequence(%s,'id'),COALESCE((SELECT max(id) FROM daesatu.{}),1),EXISTS(SELECT 1 FROM daesatu.{}))").format(sql.Identifier(table),sql.Identifier(table)),('daesatu.'+table,))
    return counts

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'.runtime/accounts.sqlite3');p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    try:
        counts=migrate(a.source) if a.apply else {t:len(rows) for t,(_,rows) in snapshot(a.source).items()}
        print(json.dumps({'mode':'migrated' if a.apply else 'dry-run','counts':counts}))
    except Exception as e:
        # Driver errors may embed connection strings; never print their contents.
        raise SystemExit('Migration did not complete ('+type(e).__name__+'). No secrets were printed.')
