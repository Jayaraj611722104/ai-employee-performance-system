import os, re, json

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')
OUT_PATH    = os.path.join(os.path.dirname(__file__), 'schema.json')

def parse_schema(sql_text):
    tables = {}
    # split by CREATE TABLE blocks
    for block in re.split(r'(?i)\bCREATE\s+TABLE\b', sql_text):
        block = block.strip()
        if not block:
            continue
        # table name is first token before '('
        m = re.match(r'`?(\w+)`?\s*\(', block)
        if not m:
            continue
        table = m.group(1)
        body = block[block.find('(')+1:block.rfind(')')]
        cols = []
        for line in body.splitlines():
            ln = line.strip().rstrip(',')
            if not ln or ln.upper().startswith(('PRIMARY KEY','UNIQUE','KEY','CONSTRAINT','FOREIGN KEY','INDEX')):
                continue
            # column definition: `name` TYPE(...)
            cm = re.match(r'`?(\w+)`?\s+([A-Za-z0-9_()]+)', ln)
            if cm:
                cols.append({
                    'name': cm.group(1),
                    'type': cm.group(2)
                })
        tables[table] = {'columns': cols}
    return tables

def convert():
    if not os.path.exists(SCHEMA_PATH):
        print(f"schema.sql not found at {SCHEMA_PATH}")
        return
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        sql_text = f.read()
    tables = parse_schema(sql_text)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump({'tables': tables}, f, indent=2)
    print(f"✅ Converted schema.sql to {OUT_PATH}")

if __name__ == '__main__':
    convert()
