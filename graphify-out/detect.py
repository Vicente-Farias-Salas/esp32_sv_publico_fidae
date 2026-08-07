import json
from graphify.detect import detect
from pathlib import Path

result = detect(Path('.'))
Path('graphify-out/.graphify_detect.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')

print(f'Corpus: {result["total_files"]} archivos · ~{result.get("total_words", 0)} palabras')
for k, v in result.get('files', {}).items():
    if len(v) > 0:
        print(f'  {k}: {len(v)} archivos')
