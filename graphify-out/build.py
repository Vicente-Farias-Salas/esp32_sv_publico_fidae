"""
graphify build script — Step 4 + 4.5 + 5 + 6
Build graph, cluster, analyze, generate HTML + report
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json, to_html

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding='utf-8'))
detection  = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))

# Build graph
G = build_from_json(extraction, root='.', directed=False)
print(f"Graph: {G.number_of_nodes()} nodos, {G.number_of_edges()} edges")

# Guard
if G.number_of_nodes() == 0:
    print("ERROR: Graph is empty")
    raise SystemExit(1)

# Community detection
communities = cluster(G)
cohesion = score_all(G, communities)
tokens = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}
gods = god_nodes(G)
surprises = surprising_connections(G, communities)

# Label communities
labels = {}
for cid, nodes in communities.items():
    sample_labels = [G.nodes[n].get('label', n) for n in list(nodes)[:3] if n in G.nodes]
    labels[cid] = sample_labels[0][:30] if sample_labels else f"Community {cid}"

# Export graph.json
to_json(G, communities, 'graphify-out/graph.json')
print(f"Communities: {len(communities)}")
print(f"Cohesion: {dict(cohesion)}")

# Generate report
questions = suggest_questions(G, communities, labels)
report = generate(G, communities, cohesion, labels, gods, surprises, detection, tokens, '.', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding='utf-8')
print("Report generado: graphify-out/GRAPH_REPORT.md")

# Save analysis
analysis = {
    'communities': {str(k): v for k, v in communities.items()},
    'cohesion': {str(k): v for k, v in cohesion.items()},
    'gods': gods,
    'surprises': surprises,
    'questions': questions,
}
Path('graphify-out/.graphify_analysis.json').write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding='utf-8')
Path('graphify-out/.graphify_labels.json').write_text(json.dumps({str(k): v for k, v in labels.items()}, ensure_ascii=False), encoding='utf-8')

# Generate HTML visualization
to_html(G, communities, 'graphify-out/graph.html')
print("HTML generado: graphify-out/graph.html")

# Print key sections
print("\n=== God Nodes ===")
for g in gods[:5] if isinstance(gods, list) else [gods]:
    print(f"  {g}")
print("\n=== Surprising Connections ===")
for s in (surprises[:3] if isinstance(surprises, list) else [surprises]):
    print(f"  {s}")
print("\n=== Suggested Questions ===")
for q in (questions[:3] if isinstance(questions, list) else []):
    print(f"  {q}")
