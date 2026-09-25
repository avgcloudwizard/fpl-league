"""Small transparent form/chip projection and prize arithmetic; no external dependencies."""
from datetime import datetime
from zoneinfo import ZoneInfo

CHIP_BONUS = {'wildcard': 8, 'freehit': 8, 'bboost': 12, '3xc': 8}
BASELINE = 50
WINNER_RANGE = (2450, 2530)

def remaining_chips(used, definitions, last_gw):
    available = []
    for chip in definitions:
        start, stop = chip['start_event'], chip['stop_event']
        if stop <= last_gw or chip['name'] not in CHIP_BONUS:
            continue
        if any(c['name'] == chip['name'] and start <= c['gw'] <= stop for c in used):
            continue
        available.append({'name': chip['name'], 'start': start, 'expires': stop})
    return available

def forecast(manager, total_gws, latest, definitions):
    history = manager['history']
    if not history:
        return {'projected_total': None, 'projection_raw': None, 'chips_remaining': []}
    scores = [r['net'] for r in history]
    season = sum(scores) / len(scores)
    recent = sum(scores[-5:]) / len(scores[-5:])
    form = .65 * recent + .35 * season
    # Early chip-heavy GWs are shrunk towards a conservative ordinary-GW baseline.
    trust = len(scores) / (len(scores) + 10)
    expected = max(0, BASELINE + trust * (form - BASELINE))
    remaining = max(0, total_gws - latest)
    chips = remaining_chips(manager.get('chips', []), definitions, latest)
    bonus = 0
    for stop in sorted({c['expires'] for c in chips}):
        window = [c for c in chips if c['expires'] == stop]
        start = min(c['start'] for c in window)
        choices = sorted((CHIP_BONUS[c['name']] for c in window), reverse=True)
        slots = max(0, stop - max(latest, start - 1))
        bonus += sum(choices[:slots])  # One chip per GW; expired opportunities cannot roll over.
    actual = history[-1]['total']
    raw = actual + expected * remaining + (bonus if remaining else 0)
    projected = actual if not remaining else max(actual, round(raw))
    return {'projected_total': projected, 'projection_raw': round(raw),
            'projection_expected_gw': round(expected, 2), 'projection_chip_bonus': bonus,
            'chips_remaining': chips}

def calibrate_projections(managers, remaining):
    """Set a shared season scoring scale while preserving form/chip point gaps."""
    eligible = [m for m in managers if m.get('projected_total') is not None]
    if not eligible or remaining <= 0:
        return  # Final actual scores, including genuine ties, are never invented.
    ordered = sorted(eligible, key=lambda m: (-m['projected_total'], m['rank'], m['id']))
    leader = ordered[0]['projected_total']
    target = max(WINNER_RANGE[0], min(WINNER_RANGE[1], leader))
    previous = None
    for m in ordered:
        value = target - (leader - m['projected_total'])
        m['projected_total'] = min(value, previous - 1) if previous is not None else value
        previous = m['projected_total']
    # Never project below points already earned, even late in an exceptional season.
    floor = None
    for m in reversed(ordered):
        actual = m['history'][-1]['total']
        m['projected_total'] = max(m['projected_total'], actual, floor + 1 if floor is not None else actual)
        floor = m['projected_total']

def month_key(event):
    return datetime.fromisoformat(event['deadline_time'].replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/London')).strftime('%Y-%m')

def award_months(months, events):
    for month in months:
        scheduled = [e for e in events if month_key(e) == month['id']]
        month['complete'] = bool(scheduled) and all(e['finished'] and e['data_checked'] for e in scheduled)

def prize_tracker(managers, months, events, config):
    slots = config['season_prizes']
    monthly_amount = config['monthly_prize']
    prize_months = sorted({month_key(e) for e in events})[:config['monthly_count']]
    earned = {m['id']: 0 for m in managers}
    wins = {m['id']: [] for m in managers}
    awards = []
    for month in months:
        if not month.get('complete') or month['id'] not in prize_months:
            continue
        winners = [r for r in month['rows'] if r['rank'] == 1]
        if not winners:
            continue
        share = monthly_amount / len(winners)
        awards.append({'month': month['id'], 'label': month['label'], 'winner_ids': [r['id'] for r in winners], 'each': share})
        for winner in winners:
            earned[winner['id']] += share
            wins[winner['id']].append(month['id'])
    ordered = sorted(managers, key=lambda m: m['rank'])
    season_awards, index = {}, 0
    while index < len(ordered):
        group = [m for m in ordered if m['rank'] == ordered[index]['rank']]
        share = sum(slots[index:index + len(group)]) / len(group)
        for m in group:
            season_awards[m['id']] = share
        index += len(group)
    season_complete = bool(events) and all(e['finished'] and e['data_checked'] for e in events)
    rows = []
    for m in managers:
        season_prize = season_awards[m['id']]
        secured = earned[m['id']] + (season_prize if season_complete else 0)
        rows.append({'id': m['id'], 'monthly_wins': len(wins[m['id']]), 'months_won': wins[m['id']],
                     'monthly_earned': earned[m['id']], 'earned': secured,
                     'net': secured - config['buy_in'], 'season_prize': season_prize,
                     'if_ended_net': earned[m['id']] + season_prize - config['buy_in']})
    allocated = sum(r['earned'] for r in rows)
    return {**config, 'season_complete': season_complete, 'awards': awards, 'rows': rows,
            'allocated': allocated, 'remaining_pool': config['total_pool'] - allocated}
