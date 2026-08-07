"""
graphify build script — pasos 3A, 3C (AST + Merge)
Part A: Extracción estructural (AST) de archivos de código
Part B: Se omite si no hay backend LLM disponible
Part C: Merge AST + empty semantic
"""
import json
from pathlib import Path
from graphify.extract import collect_files, extract

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))

# Part A — AST extraction for code files (no LLM needed)
code_files = []
for f in detect.get('files', {}).get('code', []):
    if Path(f).is_dir():
        code_files.extend(collect_files(Path(f)))
    else:
        code_files.append(Path(f))

print(f"AST: {len(code_files)} archivos de código")
result = extract(code_files, cache_root=Path('.'))
Path('graphify-out/.graphify_ast.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"AST: {len(result['nodes'])} nodos, {len(result['edges'])} edges")

# Part B — Semantic extraction (skip if no backend)
doc_files = [f for cat in ('document', 'paper', 'image') for f in detect['files'].get(cat, [])]
if doc_files:
    from graphify.llm import detect_backend
    backend = detect_backend()
    if backend:
        print(f"Semantic: usando backend '{backend}' para {len(doc_files)} docs")
        sem = {
            'nodes': [], 'edges': [], 'hyperedges': [],
            'input_tokens': 0, 'output_tokens': 0
        }
        try:
            sem_result = extract_corpus_parallel(doc_files, backend=backend)
            sem = sem_result
        except Exception as e:
            print(f"Semantic: error ({e}), usando empty")
    else:
        print(f"Semantic: no backend disponible, usando empty (code-only AST)")
        sem = {'nodes': [], 'edges': [], 'hyperedges': [], 'input_tokens': 0, 'output_tokens': 0}
else:
    sem = {'nodes': [], 'edges': [], 'hyperedges': [], 'input_tokens': 0, 'output_tokens': 0}

Path('graphify-out/.graphify_semantic.json').write_text(json.dumps(sem, indent=2, ensure_ascii=False), encoding='utf-8')

# Part C — Merge
ast = json.loads(Path('graphify-out/.graphify_ast.json').read_text(encoding='utf-8'))
seen = {n['id'] for n in ast['nodes']}
merged_nodes = list(ast['nodes'])
for n in sem['nodes']:
    if n['id'] not in seen:
        merged_nodes.append(n)
        seen.add(n['id'])

merged = {
    'nodes': merged_nodes,
    'edges': ast['edges'] + sem.get('edges', []),
    'hyperedges': sem.get('hyperedges', []),
    'input_tokens': sem.get('input_tokens', 0),
    'output_tokens': sem.get('output_tokens', 0),
}
Path('graphify-out/.graphify_extract.json').write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"Merged: {len(merged_nodes)} nodos, {len(merged['edges'])} edges")
