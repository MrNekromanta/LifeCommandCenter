"""Test fuzzy search improvements: CamelCase + trigram."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'c:\projects\AI\LifeCommandCenter\rag-mcp')
from graph_store import GraphStore, _camel_split

# Test _camel_split
tests = [
    ('BiznesValidator', ['biznes', 'validator']),
    ('Wiki RAG Baremetal', ['wiki', 'rag', 'baremetal']),
    ('n8n', ['n8n']),
    ('ADHD coaching', ['adhd', 'coaching']),
    ('Crypto Phantom Rebalancing', ['crypto', 'phantom', 'rebalancing']),
]
print('=== CAMEL SPLIT ===')
for inp, expected in tests:
    result = _camel_split(inp)
    ok = '✅' if result == expected else '❌'
    print(f'  {ok} {inp:35s} -> {result}')

# Load store
store = GraphStore(r'c:\projects\AI\LifeCommandCenter\e2graphrag\production_cache')

# Test Problem 1: CamelCase search
print('\n=== PROBLEM 1: CamelCase search ===')
cases = [
    ('biznes validator', 'BiznesValidator'),
    ('crypto rebalancing', 'Crypto Phantom Rebalancing'),
    ('adhd', 'ADHD coaching'),
]
for query, expected_top in cases:
    results = store.search_entities(query, limit=3)
    top = results[0] if results else {'entity': 'NONE', 'score': 0}
    ok = '✅' if top['entity'] == expected_top else '⚠️'
    print(f'  {ok} "{query}" -> {top["entity"]} (score={top["score"]})')
    if results[1:]:
        print(f'      also: {[(r["entity"], r["score"]) for r in results[1:3]]}')

# Test Problem 3: Trigram fallback
print('\n=== PROBLEM 3: Trigram fallback ===')
fuzzy_cases = ['kubernetes', 'postgress', 'trelllo', 'grafanna', 'supabasee']
for query in fuzzy_cases:
    results = store.search_entities(query, limit=3)
    matches = [(r['entity'], r['score']) for r in results[:3]]
    has_match = '✅' if matches else '❌'
    print(f'  {has_match} "{query}" -> {matches}')

# Regression: old tests still pass
print('\n=== REGRESSION ===')
r = store.search_entities('trello', limit=1)
print(f'  trello -> {r[0]["entity"]} score={r[0]["score"]}')
r = store.search_entities('LifeCommandCenter', limit=1)
print(f'  LCC -> {r[0]["entity"]} score={r[0]["score"]}')
r = store.search_entities('BiznesValidator', limit=1)
print(f'  BV exact -> {r[0]["entity"]} score={r[0]["score"]}')

print('\n✅ ALL DONE')
