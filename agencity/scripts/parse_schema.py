#!/usr/bin/env python3
import json
import sys

data = json.load(sys.stdin)

# Get all table names from paths
tables = [p.strip('/') for p in data.get('paths', {}).keys() if p != '/']
print('=== Tables Found ===')
for t in sorted(set(tables)):
    if t and not t.startswith('rpc/'):
        print(f'  - {t}')
print()

# Get definitions (schemas)
print('=== Table Schemas ===')
for name, schema in data.get('definitions', {}).items():
    if 'properties' in schema:
        print(f'\n{name}:')
        for prop, details in schema['properties'].items():
            desc = details.get('description', '')
            dtype = details.get('type', details.get('format', 'unknown'))
            print(f'  {prop}: {dtype}' + (f' - {desc[:50]}' if desc else ''))
