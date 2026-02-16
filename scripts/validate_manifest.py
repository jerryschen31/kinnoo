#!/usr/bin/env python3
"""Validate FEATURES.txt, TASKS.txt, and TESTS.txt YAML manifests.

Checks performed:
- Unique IDs for features, tasks, tests
- Each feature.tasks item exists in TASKS.txt
- Each task.tests item exists in TESTS.txt
- Each test.covers entry references an existing feature and AC id

Usage: python3 scripts/validate_manifest.py
Requires: PyYAML (`pip install pyyaml`) or will instruct how to install.
"""
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    print("PyYAML is required. Install with: pip install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]

def load_yaml(path: Path):
    if not path.exists():
        return {}
    text = path.read_text()
    try:
        return yaml.safe_load(text) or {}
    except Exception as e:
        print(f"Failed to parse {path}: {e}")
        sys.exit(2)

def main():
    features = load_yaml(ROOT / 'FEATURES.txt').get('features', [])
    tasks = load_yaml(ROOT / 'TASKS.txt').get('tasks', [])
    tests = load_yaml(ROOT / 'TESTS.txt').get('tests', [])

    features_by_id = {f['id']: f for f in features if 'id' in f}
    tasks_by_id = {t['id']: t for t in tasks if 'id' in t}
    tests_by_id = {tt['id']: tt for tt in tests if 'id' in tt}

    errors = []

    # Unique ID checks
    if len(features_by_id) != len(features):
        errors.append('Duplicate feature IDs found')
    if len(tasks_by_id) != len(tasks):
        errors.append('Duplicate task IDs found')
    if len(tests_by_id) != len(tests):
        errors.append('Duplicate test IDs found')

    # Feature -> tasks
    for fid, f in features_by_id.items():
        for tid in f.get('tasks', []) or []:
            if tid not in tasks_by_id:
                errors.append(f'Feature {fid} references unknown task {tid}')
        # build AC map
        ac_ids = {ac['id'] for ac in f.get('acceptance_criteria', []) or [] if 'id' in ac}
        # tests_map references
        for ac, tlist in (f.get('tests_map') or {}).items():
            if ac not in ac_ids:
                errors.append(f'Feature {fid} tests_map references unknown AC {ac}')
            for tid in tlist:
                if tid not in tests_by_id:
                    errors.append(f'Feature {fid} tests_map references unknown test {tid} for AC {ac}')

    # Task -> tests
    for tid, t in tasks_by_id.items():
        for testid in t.get('tests', []) or []:
            if testid not in tests_by_id:
                errors.append(f'Task {tid} references unknown test {testid}')

    # Test covers -> feature:AC
    for testid, tt in tests_by_id.items():
        for cover in tt.get('covers', []) or []:
            feat = cover.get('feature')
            ac = cover.get('ac')
            if feat not in features_by_id:
                errors.append(f'Test {testid} covers unknown feature {feat}')
            else:
                # verify AC exists in feature
                ac_list = {a['id'] for a in features_by_id[feat].get('acceptance_criteria', []) or [] if 'id' in a}
                if ac not in ac_list:
                    errors.append(f'Test {testid} covers unknown AC {ac} for feature {feat}')

    if errors:
        print('\nValidation failed:')
        for e in errors:
            print('- ' + e)
        sys.exit(1)

    print('Validation passed: manifests are consistent')

if __name__ == '__main__':
    main()
