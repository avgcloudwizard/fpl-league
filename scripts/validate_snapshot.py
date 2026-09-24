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
        if 'ft' in m:
            assert m['ft'] is None or 0 <= m['ft'] <= m['ft_cap']
            assert m['mvp_coverage'] <= m['completed_count']
            assert not m['mvp'] or m['mvp_coverage'] == m['completed_count']
            for key in ('best', 'worst'):
                assert all(any(r['gw'] == gw and r['net'] == m[key] for r in m['history']) for gw in m[key + '_gws'])
    for m in data['managers']:
        if 'awards_coverage' in m:
            assert m['awards_coverage'] <= m['completed_count']
            if m['captain_failures'] is not None:
                assert m['awards_coverage'] == m['completed_count']
                assert m['captain_failures'] == len(m['captain_failure_details'])
                assert all(r['points'] <= 4 for r in m['captain_failure_details'])
                assert m['hauls'] >= 0
        if m.get('projection_variance') is not None:
            remaining = data['total_gameweeks'] - data['completed_count']
            assert (2 <= abs(m['projection_variance']) <= 5) if remaining else m['projection_variance'] == 0
    if data.get('creators'):
        creators = data['creators']['managers']
        creator_ids = [m['id'] for m in creators]
        assert len(creator_ids) == len(set(creator_ids))
        assert all(m['rank'] >= 1 and m['total'] is not None for m in creators)
        assert all(m['ft'] is None or 0 <= m['ft'] <= m['ft_cap'] for m in creators)
    if 'prices' in data:
        assert all(p['direction'] in (-1, 0, 1) for p in data['prices']['players'])
    print(f"Validated league {league_id}: {len(ids)} managers, {len(data['gameweeks'])} completed GWs")

if __name__ == '__main__':
    validate(json.loads((ROOT / 'data/league.json').read_text()), json.loads((ROOT / 'config.json').read_text())['league_id'])
