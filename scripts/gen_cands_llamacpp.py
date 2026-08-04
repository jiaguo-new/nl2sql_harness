#!/usr/bin/env python3
"""Generate candidates via llama.cpp server API for blind-spot questions."""
import json, sqlite3, re, sys, time, urllib.request, concurrent.futures
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def extract_sql(text):
    text = text.strip()
    m = re.search(r"```sql\n(.*?)```", text, re.S)
    if m: return m.group(1).strip().rstrip(";")
    m = re.search(r"```\n(.*?)```", text, re.S)
    if m: return m.group(1).strip().rstrip(";")
    m = re.search(r"(SELECT .*?)(?:;|$)", text, re.S | re.I)
    if m: return m.group(1).strip()
    return text.split("\n")[0].strip().rstrip(";")

def gen_one(args):
    ex, base_url, n, temperature = args
    qid = ex.get("question_id")
    db_id = ex["db_id"]
    question = ex["question"]
    evidence = ex.get("evidence", "")
    dbroot = '/home/dameng/bird_dev/dev_databases'
    
    # get schema
    dbp = f'{dbroot}/{db_id}/{db_id}.sqlite'
    try:
        uri = f'file:{dbp}?mode=ro'
        with sqlite3.connect(uri, uri=True, timeout=5) as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
            schema_parts = []
            for t in tables[:15]:
                ddl = conn.execute(f"SELECT sql FROM sqlite_master WHERE name='{t}'").fetchone()
                if ddl: schema_parts.append(ddl[0])
            schema = "\n".join(schema_parts)
    except: schema = ""
    
    prompt = f"Generate a valid SQLite SELECT query.\n\nDatabase: {db_id}\n{schema}\n\n"
    if evidence: prompt += f"Evidence: {evidence}\n\n"
    prompt += f"Question: {question}\n\nOutput only the SQL query:"
    
    cands = []
    for i in range(n):
        payload = json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512, "temperature": temperature, "top_p": 0.95,
        }).encode()
        req = urllib.request.Request(f"{base_url}/v1/chat/completions", data=payload,
                                    headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read().decode())
            sql = extract_sql(resp["choices"][0]["message"]["content"])
            if sql and sql.strip():
                # execute
                try:
                    uri2 = f'file:{dbp}?mode=ro'
                    with sqlite3.connect(uri2, uri=True, timeout=5) as conn:
                        result = [list(row) for row in conn.execute(sql).fetchmany(5)]
                except: result = None
                cands.append({"sql": sql, "model": "coder32b-q4", "result": result})
        except Exception as e:
            pass
    
    # dedup
    seen = set()
    unique = []
    for c in cands:
        s = c["sql"].strip().lower()
        if s not in seen:
            seen.add(s); unique.append(c)
    
    return {"id": qid, "db_id": db_id, "question": question, "candidates": unique, "n_candidates": len(unique)}

def main():
    dev = json.load(open('/home/dameng/bird_dev/dev.json'))
    blind_ids = set(json.load(open('/tmp/blind228_qids.json')))
    todo = [d for d in dev if d.get("question_id") in blind_ids]
    print(f"todo: {len(todo)}", flush=True)
    
    base_url = "http://127.0.0.1:8092"
    out_path = ROOT / "runs" / "coder32b_q4_blind228_cands.jsonl"
    
    done = set()
    if out_path.exists():
        for l in out_path.open():
            if l.strip(): done.add(json.loads(l)["id"])
        print(f"resume: {len(done)}", flush=True)
    todo = [d for d in todo if d.get("question_id") not in done]
    
    t0 = time.time(); written = 0
    with out_path.open("a") as f, concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(gen_one, (ex, base_url, 4, 0.7)): ex.get("question_id") for ex in todo}
        for fut in concurrent.futures.as_completed(futs):
            try:
                rec = fut.result(timeout=300)
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                f.flush()
                written += 1
                if written % 10 == 0:
                    print(f"  [{written}/{len(todo)}] {time.time()-t0:.0f}s", flush=True)
            except Exception as e:
                qid = futs[fut]
                f.write(json.dumps({"id": qid, "candidates": [], "error": str(e)[:100]}, ensure_ascii=False) + "\n")
                f.flush()
                written += 1
    print(f"done: {written} -> {out_path}", flush=True)

if __name__ == "__main__":
    main()
