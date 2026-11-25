"""세부지침안 문서 RAG 실습 (기본 RAG: 검색 1번 → 답변 1번)

- 벡터DB·RAG 프레임워크 없이 numpy 코사인 유사도로 검색한다.
- 임베딩·답변 생성은 google-genai SDK를 쓴다. (에이전트/멀티에이전트 구조 아님)
- 환경변수는 이 파일과 같은 폴더의 .env 에서 읽는다. (.env.example 참고)

사용법
  python rgh.py stats            # 색인 대상 파일·조각 통계 (API 호출 없음)
  python rgh.py index            # 조각 임베딩 후 rag_index/ 에 저장 (API 호출)
  python rgh.py ask "질문" [-k 5] # 검색 + 답변 (API 호출)
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 설정
# 환경변수(.env)로 바꿀 수 있고, 없으면 아래 기본값을 쓴다.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))      # 조각 최대 글자수
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 120))  # 앞 조각과 겹치는 글자수(줄 단위로 맞춤)
MIN_CHUNK_CHARS = 20                                 # 이보다 짧은 조각은 버린다
EMBED_BATCH = int(os.getenv("EMBED_BATCH", 10))      # 임베딩 API 1회 호출당 조각 수 (작게: 분당 토큰 한도 때문)
EMBED_PAUSE = float(os.getenv("EMBED_PAUSE", 3))     # 호출 사이 쉬는 시간(초)
TOP_K = 5                                            # 질문당 가져올 조각 수

# 색인 대상: 이 폴더 아래의 .md / .csv 만
DOCS_DIR = (HERE / os.getenv("DOCS_DIR", "../세부지침안")).resolve()
INDEX_DIR = HERE / "rag_index"
EXTENSIONS = {".md", ".csv"}

# 색인에서 뺄 파일 (이름에 이 글자가 들어 있으면 제외)
EXCLUDE_NAME_KEYWORDS = [
    "통합본", "묶음본",        # 개별 파일을 이어 붙인 문서 → 내용 중복
    "_양식.md",                # 빈 템플릿 (F·G·I·P 파트)
    "_품목시트_양식",          # D파트 템플릿
    "인수인계",                # 작업 메모
]
# 위 규칙 말고 따로 빼고 싶은 파일은 '세부지침안 기준 상대경로'로 여기에 추가
EXCLUDE_PATHS: list[str] = []


def nfc(s: str) -> str:
    """맥(macOS)은 한글 파일명을 분해형(NFD)으로 돌려주므로 조합형(NFC)으로 통일한다."""
    return unicodedata.normalize("NFC", s)


def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(HERE / ".env")
    except ImportError:
        pass  # stats 만 쓸 때는 python-dotenv 없이도 동작


# ---------------------------------------------------------------- 1) 파일 수집
def list_files() -> list[Path]:
    files = []
    for p in sorted(DOCS_DIR.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in EXTENSIONS:
            continue
        rel = nfc(p.relative_to(DOCS_DIR).as_posix())
        name = nfc(p.name)
        if any(k in name for k in EXCLUDE_NAME_KEYWORDS) or rel in EXCLUDE_PATHS:
            continue
        files.append(p)
    return files


def source_label(p: Path) -> str:
    """조각 출처를 '파트폴더/폴더명' 형태로 만든다.
    예) A파트v5/A05_….md → 'A파트v5'
        B파트v5/참고자료/….md → 'B파트v5/참고자료'
        D파트v1/D-03_품목별수치/D-03-01_아크릴키링/….md → 'D파트v1/D-03-01_아크릴키링'
        P파트/P세부지침안V11/….md → 'P파트/P세부지침안V11'
    """
    parts = [nfc(x) for x in p.relative_to(DOCS_DIR).parts[:-1]]
    if not parts:
        return "(루트)"
    top, parent = parts[0], parts[-1]
    return top if top == parent else f"{top}/{parent}"


# ---------------------------------------------------------------- 2) 조각내기
HEADING = re.compile(r"^#{1,6}\s+(.*)")


def _split_long_line(line: str) -> list[str]:
    """한 줄이 CHUNK_SIZE 보다 길면 글자 수로 잘라 겹치게 나눈다."""
    step = max(CHUNK_SIZE - CHUNK_OVERLAP, 1)
    return [line[i:i + CHUNK_SIZE] for i in range(0, len(line), step)]


def _overlap_tail(buf: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """다음 조각 앞에 붙일, 현재 조각의 뒤쪽 줄들 (합쳐서 CHUNK_OVERLAP 글자 이하)."""
    tail, total = [], 0
    for line, head in reversed(buf):
        if total + len(line) + 1 > CHUNK_OVERLAP:
            break
        tail.insert(0, (line, head))
        total += len(line) + 1
    while tail and not tail[0][0].strip():  # 앞쪽 빈 줄 제거
        tail.pop(0)
    return tail


def chunk_text(text: str) -> list[tuple[str, str]]:
    """문서를 줄 단위로 모아 (제목, 조각본문) 목록으로 만든다.
    표·목록이 줄 중간에서 끊기지 않게 줄 경계에서 자르고, 마크다운 제목을 따라간다."""
    chunks, buf, size, fresh = [], [], 0, False  # fresh: 겹침 말고 새로 들어온 줄이 있는가
    heading = ""

    def flush():
        body = "\n".join(l for l, _ in buf).strip()
        if fresh and len(body) >= MIN_CHUNK_CHARS:
            chunks.append((buf[0][1], body))

    for raw in text.splitlines():
        m = HEADING.match(raw)
        if m:
            heading = m.group(1).strip()
        pieces = _split_long_line(raw) if len(raw) > CHUNK_SIZE else [raw]
        for piece in pieces:
            if buf and size + len(piece) + 1 > CHUNK_SIZE:
                flush()
                buf = _overlap_tail(buf)
                size, fresh = sum(len(l) + 1 for l, _ in buf), False
            buf.append((piece, heading))
            size += len(piece) + 1
            fresh = fresh or bool(piece.strip())
    if buf:
        flush()
    return chunks


def build_chunks() -> list[dict]:
    chunks = []
    for p in list_files():
        text = nfc(p.read_text(encoding="utf-8"))
        src, fname = source_label(p), nfc(p.name)
        for i, (heading, body) in enumerate(chunk_text(text)):
            chunks.append({
                "id": len(chunks),
                "source": src,          # 파트폴더/폴더명
                "file": fname,          # 근거 파일명
                "heading": heading,     # 조각이 속한 제목
                "seq": i,               # 파일 안에서 몇 번째 조각인가
                "text": body,
            })
    return chunks


def embed_input(c: dict) -> str:
    """임베딩할 때는 본문 앞에 출처·파일·제목을 붙여 검색이 잘 되게 한다."""
    return f"[{c['source']} | {c['file']} | {c['heading']}]\n{c['text']}"


# ---------------------------------------------------------------- 3) 임베딩
def get_client():
    from google import genai
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit(".env 에 GEMINI_API_KEY 를 설정하세요.")
    return genai.Client(api_key=key)


def _normalize(vecs):
    import numpy as np
    arr = np.array(vecs, dtype="float32")
    arr /= np.linalg.norm(arr, axis=1, keepdims=True)  # 정규화 → 내적 = 코사인 유사도
    return arr


def embed_texts(client, texts: list[str], task_type: str, partial_path: Path | None = None):
    """texts 를 임베딩해 (N, dim) float32 배열로 돌려준다. 길이는 1로 정규화한다.

    무료 티어의 분당 한도(429)에 걸리면 기다렸다 다시 시도한다.
    partial_path 를 주면 지금까지 만든 벡터를 거기에 저장해서, 중간에 멈춰도 이어서 한다."""
    import numpy as np
    from google.genai import types

    model = os.getenv("EMBEDDING_MODEL")
    if not model:
        sys.exit(".env 에 EMBEDDING_MODEL 을 설정하세요.")
    dim = int(os.getenv("EMBEDDING_DIM", 768))

    vecs = []
    if partial_path and partial_path.exists():
        done = np.load(partial_path)
        if len(done) <= len(texts) and done.shape[1] == dim:
            vecs = list(done)
            print(f"  이전에 만든 {len(vecs)}개를 이어서 진행")

    for i in range(len(vecs), len(texts), EMBED_BATCH):
        batch = texts[i:i + EMBED_BATCH]
        for attempt in range(8):  # 한도 초과(429) 등은 기다렸다 재시도
            try:
                res = client.models.embed_content(
                    model=model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type, output_dimensionality=dim),
                )
                vecs.extend(e.values for e in res.embeddings)
                break
            except Exception as e:
                msg = str(e)
                # 하루 한도를 넘었거나 이 모델의 무료 한도가 0이면 기다려도 소용없다
                if "PerDay" in msg or "limit: 0" in msg:
                    if partial_path and vecs:
                        INDEX_DIR.mkdir(exist_ok=True)
                        np.save(partial_path, _normalize(vecs))
                    sys.exit(f"하루 한도 초과이거나 이 모델의 한도가 0입니다. 전체 메시지:\n{msg}")
                wait = 30 * (attempt + 1)
                print(f"  재시도 {attempt + 1}/8 ({wait}초 후): {msg[:300]}")
                time.sleep(wait)
        else:
            if partial_path and vecs:
                INDEX_DIR.mkdir(exist_ok=True)
                np.save(partial_path, _normalize(vecs))
            sys.exit("임베딩에 계속 실패했습니다. 다시 실행하면 저장된 곳부터 이어서 합니다.")
        print(f"  임베딩 {len(vecs)}/{len(texts)}")
        if partial_path and len(vecs) % (EMBED_BATCH * 5) == 0:
            INDEX_DIR.mkdir(exist_ok=True)
            np.save(partial_path, _normalize(vecs))
        time.sleep(EMBED_PAUSE)
    return _normalize(vecs)


# ---------------------------------------------------------------- 명령: stats
def cmd_stats(_args):
    files = list_files()
    chunks = build_chunks()
    total = sum(len(nfc(p.read_text(encoding="utf-8"))) for p in files)
    sizes = [len(c["text"]) for c in chunks]
    print(f"문서 폴더      : {DOCS_DIR}")
    print(f"색인 대상 파일 : {len(files)}개, {total:,}자")
    print(f"조각 설정      : 크기 {CHUNK_SIZE}자 / 겹침 {CHUNK_OVERLAP}자")
    print(f"조각 수        : {len(chunks)}개 "
          f"(평균 {sum(sizes) // max(len(sizes), 1)}자, 최소 {min(sizes)}자, 최대 {max(sizes)}자)")
    by_src: dict[str, int] = {}
    for c in chunks:
        by_src[c["source"]] = by_src.get(c["source"], 0) + 1
    print("출처별 조각 수 :")
    for s, n in sorted(by_src.items()):
        print(f"  {s}: {n}")


# ---------------------------------------------------------------- 명령: index
def cmd_index(_args):
    import numpy as np
    load_env()
    chunks = build_chunks()
    print(f"조각 {len(chunks)}개 임베딩 시작")
    INDEX_DIR.mkdir(exist_ok=True)
    partial = INDEX_DIR / "partial.npy"
    emb = embed_texts(get_client(), [embed_input(c) for c in chunks],
                      "RETRIEVAL_DOCUMENT", partial_path=partial)
    np.save(INDEX_DIR / "embeddings.npy", emb)
    partial.unlink(missing_ok=True)
    (INDEX_DIR / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장 완료: {INDEX_DIR} (벡터 {emb.shape})")


# ---------------------------------------------------------------- 검색 + 답변
def retrieve(client, question: str, k: int):
    import numpy as np
    emb = np.load(INDEX_DIR / "embeddings.npy")
    chunks = json.loads((INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
    q = embed_texts(client, [question], "RETRIEVAL_QUERY")[0]
    scores = emb @ q
    top = np.argsort(-scores)[:k]
    return [(chunks[i], float(scores[i])) for i in top]


SYSTEM_PROMPT = (
    "너는 '대구 사투리 축제' 세부지침 문서에 대한 질문에 답하는 도우미야.\n"
    "- 아래 [참고 조각]에 적힌 내용만 근거로 답해. 상식이나 추측으로 보태지 마.\n"
    "- 참고 조각에 답이 없으면 '제공된 문서에서 찾을 수 없습니다.'라고 답해.\n"
    "- 두 조각 이상을 비교해야 하면 각각의 내용을 구분해서 설명해.\n"
    "- 답 마지막 줄에 근거로 쓴 파일명을 '근거: 파일명' 형태로 적어."
)


def answer_question(question: str, k: int = TOP_K, client=None):
    """검색 1회 → 답변 1회. (답변 텍스트, [(조각, 점수), ...]) 반환."""
    from google.genai import types
    load_env()
    client = client or get_client()
    model = os.getenv("GEMINI_MODEL")
    if not model:
        raise RuntimeError(".env 에 GEMINI_MODEL 을 설정하세요.")
    if not (INDEX_DIR / "embeddings.npy").exists():
        raise RuntimeError("색인이 없습니다. 먼저 `python rgh.py index` 를 실행하세요.")
    hits = retrieve(client, question, k)
    context = "\n\n".join(
        f"[조각 {n}] 출처: {c['source']} / 파일: {c['file']} / 제목: {c['heading']}\n{c['text']}"
        for n, (c, _) in enumerate(hits, 1))
    prompt = f"[참고 조각]\n{context}\n\n[질문]\n{question}"
    res = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0))
    return res.text, hits


def cmd_ask(args):
    try:
        text, hits = answer_question(args.question, args.k)
    except RuntimeError as e:
        sys.exit(str(e))
    print("== 검색된 조각 ==")
    for c, s in hits:
        print(f"  {s:.3f}  {c['source']} | {c['file']} | {c['heading']}")
    print("\n== 답변 ==")
    print(text)


def cmd_serve(args):
    """안내페이지(index.html)를 띄우고, 채팅창 질문을 /api/ask 로 받아 RAG로 답한다."""
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    load_env()
    client = get_client()
    web_dir = (HERE / "../local 리서치/2027/안내페이지").resolve()

    class H(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(web_dir), **kw)

        def _json(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_POST(self):
            if self.path != "/api/ask":
                return self._json(404, {"error": "not found"})
            try:
                n = int(self.headers.get("Content-Length", 0))
                q = json.loads(self.rfile.read(n) or b"{}").get("question", "").strip()
                if not q:
                    return self._json(400, {"error": "질문이 비어 있습니다."})
                text, hits = answer_question(q, TOP_K, client)
                self._json(200, {"answer": text, "sources": [
                    {"file": c["file"], "source": c["source"], "heading": c["heading"],
                     "score": round(s, 3)} for c, s in hits]})
            except Exception as e:  # 한도 초과 등
                self._json(500, {"error": str(e)[:300]})

    srv = ThreadingHTTPServer(("127.0.0.1", args.port), H)
    print(f"http://localhost:{args.port}  (종료: Ctrl+C)")
    srv.serve_forever()


def main():
    ap = argparse.ArgumentParser(description="세부지침안 RAG 실습")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats", help="색인 대상·조각 통계 (API 호출 없음)").set_defaults(fn=cmd_stats)
    sub.add_parser("index", help="임베딩 후 rag_index/ 에 저장").set_defaults(fn=cmd_index)
    a = sub.add_parser("ask", help="질문하기")
    a.add_argument("question")
    a.add_argument("-k", type=int, default=TOP_K, help="가져올 조각 수")
    a.set_defaults(fn=cmd_ask)
    sv = sub.add_parser("serve", help="안내페이지 + 채팅 RAG 서버")
    sv.add_argument("--port", type=int, default=8000)
    sv.set_defaults(fn=cmd_serve)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
