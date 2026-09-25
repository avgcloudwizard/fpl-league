"""Cheap local schedule gate: no API requests on quiet quarter-hours."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]

def refresh_due(snapshot, now):
    if not snapshot or not snapshot.get('fixture_kickoffs'):
        return True
    updated = datetime.fromisoformat(snapshot['updated_at'].replace('Z', '+00:00'))
    if now - updated >= timedelta(hours=6):
        return True
    for value in snapshot['fixture_kickoffs']:
        kickoff = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if kickoff - timedelta(minutes=45) <= now <= kickoff + timedelta(hours=5):
            return True
    return False

if __name__ == '__main__':
    path = ROOT / 'data/league.json'
    snapshot = json.loads(path.read_text()) if path.exists() else None
    due = os.environ.get('FORCE_REFRESH') == 'true' or refresh_due(snapshot, datetime.now(timezone.utc))
    value = 'true' if due else 'false'
    print('Refresh due: ' + value)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('run=' + value + '\n')
