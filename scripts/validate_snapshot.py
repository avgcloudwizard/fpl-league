"""Refuse to publish a malformed or wrong-league snapshot."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def validate(data, league_id):
    assert data['league_id'] == league_id, 'Snapshot belongs to a different league'
    assert data['updated_at'] and data['version'] == 1
    ids = [m['id'] for m in data['managers']]
    assert len(ids) == len(set(ids)), 'Duplicate entries'
    assert all(0 <= m['power'] <= 100 for m in data['managers'] if m['power'] is not None)
    for gw in data['gameweeks']:
        assert gw['id'] <= data['latest_completed']
        for r in gw['rows']:
            assert r['net'] == r['gross'] - r['hits'], 'Hits applied incorrectly'
            assert r['id'] in ids
    for m in data['managers']:
        assert m['completed_count'] == len(m['history'])
        assert m['captain_coverage'] <= m['completed_count']
    print(f"Validated league {league_id}: {len(ids)} managers, {len(data['gameweeks'])} completed GWs")

if __name__ == '__main__':
    validate(json.loads((ROOT / 'data/league.json').read_text()), json.loads((ROOT / 'config.json').read_text())['league_id'])
