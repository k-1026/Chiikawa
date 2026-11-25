"""지침 문서 검색을 컴퓨터의 rag_index 파일 대신 Supabase(pgvector)에서 한다.
rgh.retrieve(client, question, k) 와 같은 값 [(chunk dict, score)] 을 돌려주므로 기존 도구 코드를 바꾸지 않고 끼워 넣는다."""
def install(store):
    """store.pg 가 있을 때만 rgh.retrieve 를 DB 검색으로 바꾼다. 바꿨으면 True."""
    if not getattr(store, 'pg', None):
        return False
    import rgh  # docs/rgh.py (embed_texts 재사용)

    def retrieve(client, question, k):
        q = rgh.embed_texts(client, [question], 'RETRIEVAL_QUERY')[0]
        vec = '[' + ','.join('%.7g' % float(x) for x in q) + ']'
        with store.db() as db:
            rows = db.execute(
                'SELECT id,source,file,heading,seq,text,1-(embedding <=> %s::extensions.vector) AS score '
                'FROM knowledge_chunks ORDER BY embedding <=> %s::extensions.vector LIMIT %s'.replace('%s', '?'),
                (vec, vec, int(k))).fetchall()
        return [({'id': r['id'], 'source': r['source'], 'file': r['file'], 'heading': r['heading'], 'seq': r['seq'], 'text': r['text']}, float(r['score'])) for r in rows]

    rgh.retrieve = retrieve
    return True
