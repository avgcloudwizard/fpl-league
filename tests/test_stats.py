import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path
from scripts.update_fpl import (build_stats, captain_detail, normalize, write_json, main,
                               free_transfers, squad_detail, manager_mvp, price_watch, scoring_awards, projection, update_creators)

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
        self.assertEqual(ms[0]['projected_base'],2090) # Uses completed total, not provisional 999
        self.assertEqual(months[1]['rows'][0]['points'],60)
        self.assertIsNone(months[0]['rows'][0]['movement'])
        self.assertEqual(ms[0]['power'],50)
        self.assertEqual(ms[0]['best_gws'],[2])
        self.assertEqual(ms[0]['worst_gws'],[1])
        self.assertEqual(months[1]['rows'][0]['best_gws'],[2])
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
    def test_awards_base_points_thresholds_and_final_lineup(self):
        picks={'picks':[{'element':1,'multiplier':3,'is_captain':True},{'element':2,'multiplier':1},{'element':3,'multiplier':0}]}
        detail=squad_detail(picks,{1:4,2:12,3:20},{1:'Cap',2:'Haul',3:'Bench'})
        result=scoring_awards([score(1,24)],{'7:1':detail},7)
        self.assertEqual(result['captain_failures'],1)
        self.assertEqual(result['hauls'],1) # TC's 12 counted as base 4; unused bench excluded.
        self.assertEqual(result['captain_failure_details'][0]['player'],'Cap')
        detail=squad_detail(picks,{1:12,2:11,3:20},{1:'Cap',2:'Other',3:'Bench'})
        result=scoring_awards([score(1,47)],{'7:1':detail},7)
        self.assertEqual((result['captain_failures'],result['hauls']),(0,1))
        self.assertIsNone(scoring_awards([score(1,48)],{'7:1':detail},7)['hauls'])
        self.assertIsNone(scoring_awards([score(1,47),score(2,40)],{'7:1':detail},7)['captain_failures'])
    def test_projection_stability_bounds_and_final_season(self):
        values=[projection(500,60,28,str(i)) for i in range(20)]
        self.assertTrue(all(2<=abs(v[2])<=5 for v in values))
        self.assertTrue(any(v[2]<0 for v in values) and any(v[2]>0 for v in values))
        self.assertEqual(projection(500,60,28,'same'),projection(500,60,28,'same'))
        self.assertEqual(projection(2300,60,0,'done'),(2300,2300,0))
        self.assertEqual(projection(500,None,28,'none'),(None,None,None))
        self.assertEqual(values[0][0],round(500+60*28*(1+values[0][2]/100)))
    def test_best_gameweek_rank_is_global_and_lower_is_better(self):
        a=score(1,50);a['overall_gw_rank']=10000
        b=score(2,60);b['overall_gw_rank']=10000
        ms=[manager(1,[a,b])]
        build_stats(ms,events(),38)
        self.assertEqual(ms[0]['best_gw_rank'],10000)
        self.assertEqual(ms[0]['best_gw_rank_gws'],[1,2])
    def test_creator_ranks_transfers_movement_and_failed_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            write_json(root/'content-creators.json',{'season':2026,'checked_at':'2026-09-25','source':'reference',
                       'managers':[{'id':1,'name':'Creator A'},{'id':2,'name':'Creator B'}]})
            def public(path):
                entry=int(path.split('/')[1])
                if path.endswith('/history/'):
                    return {'current':[{'event':1,'points':40 if entry==1 else 60,'event_transfers':0,'event_transfers_cost':0,'total_points':40 if entry==1 else 60},
                                       {'event':2,'points':60 if entry==1 else 40,'event_transfers':1 if entry==1 else 0,'event_transfers_cost':0,'total_points':100}], 'chips':[]}
                return {'name':'Team '+str(entry),'summary_overall_points':100,'summary_overall_rank':1000+entry}
            with patch('scripts.update_fpl.ROOT',root),patch('scripts.update_fpl.fetch',side_effect=public):
                result=update_creators('2026',2,5,38)
                self.assertEqual([m['id'] for m in result['managers']],[2,1])
                self.assertEqual(result['managers'][0]['live_rank'],1002)
                self.assertEqual(result['managers'][0]['ft'],2)
                self.assertEqual(result['managers'][1]['latest_score'],60)
                self.assertEqual(result['managers'][1]['movement'],0)
                with self.assertRaises(ValueError):update_creators('2027',2,5,38)
            with patch('scripts.update_fpl.ROOT',root),patch('scripts.update_fpl.fetch',side_effect=RuntimeError('unavailable')):
                with self.assertRaises(RuntimeError):update_creators('2026',2,5,38)
    def test_normalization(self):
        self.assertEqual(normalize(8,[8,8]),50)
        self.assertEqual(normalize(9,[1,9]),100)
        self.assertEqual(normalize(1,[1,9]),0)
    def test_free_transfers_cap_chips_hits_and_late_join(self):
        def hist(moves):
            return [{'event':i,'event_transfers':n} for i,n in enumerate(moves,1)]
        self.assertEqual(free_transfers(hist([0,0,0,0,0,0,0]),{}),5)
        self.assertEqual(free_transfers(hist([0,0,2,0,2]),{4:'wildcard'}),1)
        self.assertEqual(free_transfers(hist([0,0,15,0]),{3:'freehit'}),3)
        self.assertEqual(free_transfers(hist([0,0,10,0]),{3:'wildcard'}),3)
        self.assertEqual(free_transfers(hist([0,0,1]),{3:'bboost'}),2)
        self.assertEqual(free_transfers([{'event':4,'event_transfers':15},{'event':5,'event_transfers':0}],{}),2)
        self.assertIsNone(free_transfers([{'event':1,'event_transfers':0},{'event':3,'event_transfers':0}],{}))
    def test_mvp_uses_final_scoring_not_bench_or_unowned_points(self):
        players={1:{'id':1,'web_name':'A','team':1,'code':1},2:{'id':2,'web_name':'B','team':1,'code':2}}
        picks={'picks':[{'element':1,'multiplier':3,'is_captain':True},{'element':2,'multiplier':0}]}
        detail=squad_detail(picks,{1:8,2:20},{1:'A',2:'B'})
        self.assertEqual(detail['player_points'],{'1':24})
        history=[score(1,24)]
        mvps,coverage=manager_mvp(history,{'7:1':detail},7,players,{1:'ABC'})
        self.assertEqual((mvps[0]['name'],mvps[0]['points'],coverage),('A',24,1))
        self.assertEqual(manager_mvp(history+[score(2,5)],{'7:1':detail},7,players,{1:'ABC'})[0],[])
        tied={'player_points':{'1':10,'2':10}}
        self.assertEqual(len(manager_mvp([score(1,20)],{'7:1':tied},7,players,{1:'ABC'})[0]),2)
        benchboost={'picks':[{'element':1,'multiplier':1},{'element':2,'multiplier':1}]}
        self.assertEqual(sum(squad_detail(benchboost,{1:8,2:20},{1:'A',2:'B'})['player_points'].values()),28)
    def test_official_price_signals_locks_and_missing_forecasts(self):
        base={'id':1,'web_name':'A','team':1,'code':1,'now_cost':50,'selected_by_percent':'5.1','cost_change_event':-1,
              'price_change_percent':'96','price_change_projections':[{'offset':0,'projected_percent':'98','likelihood':4}]}
        elements=[base,{**base,'id':2,'price_change_projections':[{'offset':0,'projected_percent':'-110','likelihood':-5}]},
                  {**base,'id':3,'price_change_locked_until':'2099-01-01T00:00:00Z'},
                  {**base,'id':4,'price_change_calibrating':True},
                  {**base,'id':5,'price_change_projections':[]},
                  {**base,'id':6,'price_change_projections':[{'offset':0,'projected_percent':'85','likelihood':3}]}]
        rows=price_watch({'teams':[{'id':1,'short_name':'ABC'}],'elements':elements})['players']
        self.assertEqual([r['direction'] for r in rows],[1,-1,0,0,0,0])
        self.assertEqual(rows[0]['gw_change'],-0.1)
        self.assertEqual(rows[2]['status'],'Price locked')
        self.assertIsNone(rows[3]['projected_progress'])
        self.assertEqual(rows[4]['status'],'Forecast unavailable')
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
