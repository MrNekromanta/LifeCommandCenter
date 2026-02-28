import sys, json
sys.stdout.reconfigure(encoding='utf-8')
meta = json.load(open('c:/projects/AI/LifeCommandCenter/e2graphrag/production_cache/chunk_metadata.json'))
for i, m in enumerate(meta):
    if i < 3 or i > 168:
        print(f"leaf_{i}: source={m['source']} chunk_idx={m['chunk_index']}")
    elif i == 3:
        print("...")
