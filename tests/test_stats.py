import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path
from scripts.update_fpl import build_stats, captain_detail, normalize, write_json, main

def manager(entry, history):
    return {'id': entry, 'name': str(entry), 'team': 'Team '+str(entry), 'history': history, 'rank':entry, 'total':999}

def score(gw, points, hits=0, total=None, chip=None, transfers=0):
    return {'gw':gw,'net':points-hits,'gross':points,'hits':hits,'total':total if total is not None else points-hits,'transfers':transfers,'bench':0,'chip':chip}

def events():
    return [{'id':1,'month':'2026-08'},{'id':2,'month':'2026-09'}]

class ScoringTests(unittest.TestCase):
    def test_hits_ties_months_and_unfinished_projection(self):
        ms=[manager(1,[score(1,50),score(2,64,4,110)]),manager(2,[score(1,50),score(2,60,0,110)])]
        gws,months=build_stats(ms,events(),38)
        self.assertEqual([r['gw_rank'] for r in gws[1]['rows']],[1,1])
        self.assertEqual(ms[0]['wins'],2)
        self.assertEqual(ms[0]['average'],55)
        self.assertEqual(ms[0]['hits'],4)
        self.assertEqual(ms[0]['projected_total'],2090) # Uses completed total, not provisional 999
        self.assertEqual(months[1]['rows'][0]['points'],60)
        self.assertIsNone(months[0]['rows'][0]['movement'])
        self.assertEqual(ms[0]['power'],50)
    def test_tie_break_ignores_chip_transfers(self):
        ms=[manager(1,[score(1,50,transfers=5,chip='wildcard')]),manager(2,[score(1,50,transfers=1)])]
        gws,_=build_stats(ms,events()[:1],38)
        self.assertEqual(gws[0]['rows'][0]['league_rank'],1)
        self.assertEqual(gws[0]['rows'][1]['league_rank'],2)
    def test_final_captain_and_vice_multiplier(self):
        players={1:'Captain',2:'Vice'}
        picks={'picks':[{'element':1,'multiplier':0,'is_captain':True},{'element':2,'multiplier':3,'is_vice_captain':True}]}
        detail=captain_detail(picks,{1:0,2:8},players)
        self.assertEqual(detail['captain'],'Vice')
        self.assertEqual(detail['captain_points'],24)
        self.assertIsNone(captain_detail(picks,{},players)['captain_points'])
    def test_empty_missing_and_blank_gameweeks(self):
        ms=[manager(1,[])]
        build_stats(ms,[],38)
        self.assertIsNone(ms[0]['power'])
        self.assertIsNone(ms[0]['projected_total'])
        ms=[manager(1,[score(1,0),score(2,0,4,-4)]),manager(2,[score(2,20,total=20)])]
        gws,_=build_stats(ms,events(),38)
        self.assertEqual(ms[0]['worst'],-4)
        self.assertIsNone(next(r for r in gws[1]['rows'] if r['id']==2)['movement'])
        self.assertIsNone(ms[0]['captain_points'])
        self.assertEqual(ms[1]['completed_count'],1)
    def test_normalization(self):
        self.assertEqual(normalize(8,[8,8]),50)
        self.assertEqual(normalize(9,[1,9]),100)
        self.assertEqual(normalize(1,[1,9]),0)
    def test_failed_fetch_keeps_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            write_json(root/'config.json',{'league_id':795551})
            write_json(root/'data/league.json',{'saved':'previous success'})
            before=(root/'data/league.json').read_bytes()
            with patch('scripts.update_fpl.ROOT',root),patch('scripts.update_fpl.fetch',side_effect=RuntimeError('FPL unavailable')):
                with self.assertRaises(RuntimeError):main()
            self.assertEqual((root/'data/league.json').read_bytes(),before)

if __name__=='__main__':unittest.main()
