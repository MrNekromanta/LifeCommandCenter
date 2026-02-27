import os, re, json, sys
from pathlib import Path
from collections import defaultdict

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

audit_dir = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\audit")
files = sorted(audit_dir.glob("*.md"))

# Entity dictionary - categorized
entities = {
    "projects": {},      # name -> {aliases, description, status}
    "tools": {},         # name -> {type, aliases}
    "concepts": set(),   # domain concepts
    "people": set(),     # people mentioned
    "organizations": set(),
    "locations": set(),
}

# Relationship graph
relations = []

for f in files:
    text = f.read_text(encoding="utf-8")
    basename = f.stem
    
    # 1. Extract relationship lines: Entity -[REL]-> Entity // comment
    for m in re.finditer(r'(\w[\w_]*)\s*-\[(\w+)\]->\s*(\w[\w_]*)\s*(?://\s*(.+))?', text):
        src, rel, tgt, comment = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        relations.append({
            "source": src, "relation": rel, "target": tgt, 
            "comment": comment.strip(), "file": basename
        })
    
    # 2. Extract from cross-project entity tables
    # Pattern: | EntityName | Type | Projects | Role |
    in_entity_table = False
    for line in text.split('\n'):
        if '| Encja |' in line or '| Narzędzie |' in line:
            in_entity_table = True
            continue
        if in_entity_table:
            if line.strip().startswith('|---'):
                continue
            if not line.strip().startswith('|'):
                in_entity_table = False
                continue
            cols = [c.strip() for c in line.split('|')[1:-1]]
            if len(cols) >= 3:
                name = cols[0]
                etype = cols[1] if len(cols) > 1 else ""
                projects = cols[2] if len(cols) > 2 else ""
                role = cols[3] if len(cols) > 3 else ""
                if name and name != '---':
                    entities["tools"][name] = {
                        "type": etype,
                        "projects": [p.strip() for p in re.split(r'[,;]', projects) if p.strip()],
                        "role": role,
                        "source": basename
                    }
    
    # 3. Extract Stack items from project sections
    # Pattern: - **ToolName** — description | Status: status
    for m in re.finditer(r'- \*\*([^*]{2,40})\*\*\s*[—–-]\s*([^|\n]{5,100})', text):
        name = m.group(1).strip()
        desc = m.group(2).strip()
        # Filter noise: skip sentences, keep tool names
        if ' ' in name and len(name.split()) > 4:
            continue
        if name not in entities["tools"]:
            entities["tools"][name] = {"type": "technology", "projects": [], "role": desc, "source": basename}

# Deduplicate projects from relations
project_names = set()
for r in relations:
    project_names.add(r["source"])
    project_names.add(r["target"])

# Output
print(f"=== STATISTICS ===")
print(f"Files processed: {len(files)}")
print(f"Tools/Technologies: {len(entities['tools'])}")
print(f"Projects (from relations): {len(project_names)}")
print(f"Relations: {len(relations)}")
print()

print(f"=== PROJECTS ({len(project_names)}) ===")
for p in sorted(project_names):
    print(f"  {p}")

print()
print(f"=== TOOLS/TECHNOLOGIES ({len(entities['tools'])}) ===")
for name in sorted(entities["tools"].keys()):
    info = entities["tools"][name]
    projs = ", ".join(info["projects"][:3]) if info["projects"] else info.get("source", "")
    print(f"  {name} [{info['type']}] -> {projs}")

print()
print(f"=== RELATIONS ({len(relations)}) ===")
for r in relations:
    cmt = f" // {r['comment']}" if r['comment'] else ""
    print(f"  {r['source']} -[{r['relation']}]-> {r['target']}{cmt}")
