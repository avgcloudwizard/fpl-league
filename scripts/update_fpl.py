#!/usr/bin/env python3
"""Public FPL -> one consistent JSON snapshot. Python standard library only."""
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://fantasy.premierleague.com/api/'

def fetch(path):
    for attempt in range(3):
        try:
            time.sleep(0.3)
            req = urllib.request.Request(BASE + path, headers={'User-Agent': 'FPL-Friends-Stats/1.0', 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n')
    os.replace(temp, path)

def average(values):
    return round(sum(values) / len(values), 2) if values else None

def ranks(items, key, field='rank'):
    """Competition ranking; equal keys share a rank."""
    ordered = sorted(items, key=key)
    last, rank = None, 0
    for i, item in enumerate(ordered, 1):
        value = key(item)
        if value != last:
            rank = i
        item[field] = rank
        last = value
    return ordered

def normalize(value, values):
    if not values or value is None:
        return 50
    low, high = min(values), max(values)
    return 50 if low == high else (value - low) / (high - low) * 100

def captain_detail(picks, live, players):
    squad = picks.get('picks', [])
    # Final multipliers reflect vice-captain fallback, triple captain and autosubs.
    captain = next((p for p in squad if p.get('multiplier', 0) > 1), None)
    if captain is None:
        captain = next((p for p in squad if p.get('is_captain')), None)
    if not captain:
        return {}
    element = captain['element']
    points = live.get(element)
    multiplier = captain.get('multiplier', 0)
    return {'captain': players.get(element, str(element)),
            'captain_points': points * multiplier if points is not None else None,
            'captain_multiplier': multiplier, 'chip': picks.get('active_chip')}

def build_stats(managers, events, total_events, start_event=1):
    completed_ids = [e['id'] for e in events]
    by_gw = []
    previous = {}
    tie_transfers = {m['id']: 0 for m in managers}
    for event in events:
        rows = []
        for m in managers:
            row = next((dict(r) for r in m['history'] if r['gw'] == event['id']), None)
            if row is None:
                continue
            if row.get('chip') not in ('wildcard', 'freehit'):
                tie_transfers[m['id']] += row['transfers']
            row.update(id=m['id'], name=m['name'], team=m['team'], tie_transfers=tie_transfers[m['id']])
            # League may start after GW1; reconstruct its own score from that deadline.
            row['league_total'] = sum(r['net'] for r in m['history'] if start_event <= r['gw'] <= event['id'])
            rows.append(row)
        ranks(rows, lambda r: (-r['league_total'], r['tie_transfers']), 'league_rank')
        ranks(rows, lambda r: -r['net'], 'gw_rank')
        for row in rows:
            row['movement'] = previous[row['id']] - row['league_rank'] if row['id'] in previous else None
        previous = {r['id']: r['league_rank'] for r in rows}
        by_gw.append({**event, 'rows': sorted(rows, key=lambda r: (r['gw_rank'], r['league_rank']))})
    last_id = completed_ids[-1] if completed_ids else None
    for m in managers:
        hist = m['history']
        scores = [r['net'] for r in hist]
        recent = scores[-5:]
        positions = [r for gw in by_gw for r in gw['rows'] if r['id'] == m['id']]
        caps = [r['captain_points'] for r in hist if r.get('captain_points') is not None]
        last = next((r for r in hist if r['gw'] == last_id), None)
        season_avg, recent_avg = average(scores), average(recent)
        # Official current total may include an unfinished GW. Do not project it twice.
        completed_total = hist[-1]['total'] if hist else 0
        expected = .65 * recent_avg + .35 * season_avg if scores else None
        projected = round(completed_total + expected * (total_events - len(completed_ids))) if expected is not None else None
        momentum = positions[-min(5, len(positions))]['league_rank'] - positions[-1]['league_rank'] if positions else 0
        m.update(average=season_avg, recent_average=recent_avg, recent=hist[-5:],
                 best=max(scores) if scores else None, worst=min(scores) if scores else None,
                 bench=sum(r['bench'] for r in hist), captain_points=sum(caps) if caps else None,
                 captain_coverage=len(caps), completed_count=len(hist),
                 hits=sum(r['hits'] for r in hist), transfers=sum(r['transfers'] for r in hist),
                 highest_position=min((r['league_rank'] for r in positions), default=None),
                 lowest_position=max((r['league_rank'] for r in positions), default=None),
                 wins=sum(r['gw_rank'] == 1 for r in positions),
                 biggest_rise=max([r['movement'] or 0 for r in positions] + [0]),
                 latest_score=last['net'] if last else None, momentum=momentum,
                 completed_total=completed_total, projected_total=projected)
    eligible = [m for m in managers if m['average'] is not None]
    for m in managers:
        if m not in eligible:
            m.update(power=None, form='Not enough data', projected_position=None)
            continue
        components = [(0.4, 'latest_score'), (0.3, 'recent_average'), (0.2, 'average'), (0.1, 'momentum')]
        power = sum(weight * normalize(m[key], [x[key] for x in eligible if x[key] is not None]) for weight, key in components)
        m['power'] = round(power)
        form = normalize(m['recent_average'], [x['recent_average'] for x in eligible])
        m['form'] = 'Excellent' if form >= 75 else 'Good' if form >= 50 else 'Steady' if form >= 25 else 'Cold streak'
    ranks(eligible, lambda m: -m['projected_total'], 'projected_position')
    monthly = []
    for month in sorted(set(e['month'] for e in events)):
        weeks = [gw for gw in by_gw if gw['month'] == month]
        before = next((gw for gw in reversed(by_gw) if gw['id'] < weeks[0]['id']), None)
        start_ranks = {r['id']: r['league_rank'] for r in before['rows']} if before else {}
        end_ranks = {r['id']: r['league_rank'] for r in weeks[-1]['rows']}
        rows = []
        for m in managers:
            scores = [r['net'] for gw in weeks for r in gw['rows'] if r['id'] == m['id']]
            if scores:
                rows.append({'id': m['id'], 'name': m['name'], 'team': m['team'], 'points': sum(scores),
                             'average': average(scores), 'best': max(scores), 'worst': min(scores),
                             'movement': start_ranks[m['id']] - end_ranks[m['id']] if m['id'] in start_ranks and m['id'] in end_ranks else None})
        monthly.append({'id': month, 'label': datetime.strptime(month, '%Y-%m').strftime('%B %Y'),
                        'gameweeks': [gw['id'] for gw in weeks], 'rows': ranks(rows, lambda r: -r['points'])})
    return by_gw, monthly

def main():
    config = json.loads((ROOT / 'config.json').read_text())
    league_id = int(config['league_id'])
    bootstrap = fetch('bootstrap-static/')
    players = {p['id']: p['web_name'] for p in bootstrap['elements']}
    season = bootstrap['events'][0]['deadline_time'][:4]
    standings, league, page = [], None, 1
    while True:
        response = fetch(f'leagues-classic/{league_id}/standings/?page_standings={page}')
        league = response['league']
        standings.extend(response['standings']['results'])
        if not response['standings']['has_next']:
            break
        page += 1
    start = league.get('start_event', 1)
    completed = [e for e in bootstrap['events'] if e['finished'] and e['data_checked']]
    events = [{'id': e['id'], 'deadline': e['deadline_time'],
               'month': datetime.fromisoformat(e['deadline_time'].replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/London')).strftime('%Y-%m')}
              for e in completed if e['id'] >= start]
    completed_ids = {e['id'] for e in completed}
    cache_path = ROOT / '.fpl-cache.json'
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    if cache.get('season') != season or cache.get('league_id') != league_id:
        cache = {'season': season, 'league_id': league_id, 'details': {}}
    details = cache['details']
    live_cache, warnings, managers = {}, [], []
    latest = max(completed_ids, default=0)
    for s in standings:
        entry = s['entry']
        print(f"Updating {s['entry_name']} ({entry})", flush=True)
        # History is required: fail the snapshot if it is unavailable, preserving old data.
        history = fetch(f'entry/{entry}/history/')
        chips = {c['event']: c['name'] for c in history.get('chips', [])}
        rows = []
        for h in history['current']:
            gw = h['event']
            if gw not in completed_ids:
                continue
            key = f'{entry}:{gw}'
            detail = details.get(key, {})
            if not detail or gw == latest or time.time() - detail.get('fetched_at', 0) > 7 * 86400:
                try:
                    if gw not in live_cache:
                        live_data = fetch(f'event/{gw}/live/')
                        live_cache[gw] = {p['id']: p['stats']['total_points'] for p in live_data['elements']}
                    picks = fetch(f'entry/{entry}/event/{gw}/picks/')
                    detail = captain_detail(picks, live_cache[gw], players)
                    detail['fetched_at'] = time.time()
                    details[key] = detail
                except Exception as exc:
                    warnings.append(f'Captain details unavailable for {s["entry_name"]}, GW{gw}; previous details retained if available.')
                    print(f'Optional detail failed: {type(exc).__name__}', file=sys.stderr)
            rows.append({'gw': gw, 'gross': h['points'], 'net': h['points'] - h['event_transfers_cost'],
                         'hits': h['event_transfers_cost'], 'transfers': h['event_transfers'],
                         'total': h['total_points'], 'bench': h['points_on_bench'],
                         'chip': chips.get(gw), **{k: v for k, v in detail.items() if k not in ('fetched_at', 'chip')}})
        rows.sort(key=lambda r: r['gw'])
        latest_history = history['current'][-1] if history['current'] else {}
        managers.append({'id': entry, 'name': s['player_name'], 'team': s['entry_name'],
                         'rank': s['rank'], 'total': s['total'], 'event_total': s['event_total'],
                         'movement': s['last_rank'] - s['rank'] if s.get('last_rank') else None,
                         'value': latest_history.get('value', 0) / 10 or None, 'history': rows})
    gameweeks, monthly = build_stats(managers, events, len(bootstrap['events']), start)
    active = next((e for e in bootstrap['events'] if e['is_current']), None)
    data = {'version': 1, 'league_id': league_id, 'name': league['name'],
            'season': f'{season}/{str(int(season)+1)[-2:]}',
            'updated_at': datetime.now(timezone.utc).isoformat(), 'refresh_hours': config['refresh_hours'],
            'latest_completed': latest or None, 'completed_count': len(completed),
            'total_gameweeks': len(bootstrap['events']),
            'current_gw': active['id'] if active else None,
            'in_progress': bool(active and active['id'] not in completed_ids),
            'warnings': warnings, 'managers': managers, 'gameweeks': gameweeks, 'months': monthly}
    write_json(ROOT / 'data/league.json', data)
    write_json(cache_path, cache)
    print(f"Saved {len(managers)} managers and {len(gameweeks)} completed gameweeks.")

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Update failed; previous successful dataset kept. {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(1)
