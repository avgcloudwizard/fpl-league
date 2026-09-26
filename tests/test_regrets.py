import unittest
from scripts.regrets import untouched_score, original_lineup

class FrozenSquadTests(unittest.TestCase):
    def setUp(self):
        # 3-4-3, with GK / MID / DEF / DEF in bench order.
        self.roles = dict(enumerate([1,2,2,2,3,3,3,3,4,4,4,1,3,2,2], 1))
        self.lineup = [{'element':i,'position':i,'is_captain':i==9,'is_vice_captain':i==5} for i in range(1,16)]
        self.stats = {i:{'minutes':90,'total_points':2} for i in range(1,16)}

    def test_normal_no_chip_multiplier(self):
        self.assertEqual(untouched_score(self.lineup,self.stats,self.roles),24)

    def test_defender_absent_skips_first_bench_midfielder(self):
        self.stats[2]={'minutes':0,'total_points':0}
        self.stats[13]['total_points']=20
        self.stats[14]['total_points']=7
        self.assertEqual(untouched_score(self.lineup,self.stats,self.roles),29)

    def test_goalkeeper_and_vice_fallback(self):
        self.stats[1]={'minutes':0,'total_points':0}
        self.stats[9]={'minutes':0,'total_points':0}
        self.stats[12]['total_points']=6
        self.stats[5]['total_points']=8
        self.assertEqual(untouched_score(self.lineup,self.stats,self.roles),40)

    def test_blank_all_zero(self):
        self.stats={i:{'minutes':0,'total_points':0} for i in range(1,16)}
        self.assertEqual(untouched_score(self.lineup,self.stats,self.roles),0)

    def test_negative_captain_points(self):
        self.stats[9]['total_points']=-2
        self.assertEqual(untouched_score(self.lineup,self.stats,self.roles),16)

    def test_restore_original_autosub_order(self):
        self.lineup[1]['position'],self.lineup[13]['position']=14,2
        d={'lineup':self.lineup,'automatic_subs':[{'element_out':2,'element_in':14}]}
        restored=original_lineup(d)
        self.assertEqual([p['element'] for p in restored],list(range(1,16)))
        self.assertEqual(self.lineup[1]['position'],14)

    def test_missing_player_fails_instead_of_inventing_zero(self):
        del self.stats[12]
        with self.assertRaises(ValueError):untouched_score(self.lineup,self.stats,self.roles)

class RegretComparisonTests(unittest.TestCase):
    def test_captain_bonus_receipt_hits_and_bench_boost(self):
        from scripts.regrets import build_regrets
        base=FrozenSquadTests();base.setUp()
        elements={i:{'web_name':str(i),'element_type':base.roles[i]} for i in range(1,16)}
        elements[16]={'web_name':'Sold','element_type':4}
        lineup=[dict(p,multiplier=3 if p['is_captain'] else 1 if p['position']<=11 else 0) for p in base.lineup]
        details={'1:1':{'lineup':lineup,'automatic_subs':[]}}
        m={'id':1,'history':[{'gw':1,'net':40,'chip':'3xc','hits':4}]}
        stats={i:{'total_points':2,'minutes':90} for i in range(1,17)}
        stats[5]['total_points']=10
        def fetch(path):
            if path.endswith('/live/'):
                return {'elements':[{'id':i,'stats':s} for i,s in stats.items()]}
            return [{'event':1,'element_in':5,'element_out':16},{'event':1,'element_in':6,'element_out':16}]
        row=build_regrets([m],details,elements,{1},{},fetch)['rows'][0]
        self.assertEqual(row['captains'][0]['delta'],16) # (10-2) × two TC bonus copies
        self.assertEqual(row['receipts'][0]['delta'],4) # (10-2)+(2-2)-4, hit counted once
        self.assertEqual(row['receipts'][0]['weeks'],[1])
        self.assertEqual(row['bench'][0]['points'],2)
        m['history'][0]['chip']='bboost'
        row=build_regrets([m],details,elements,{1},{},fetch)['rows'][0]
        self.assertEqual(row['bench'],[])
        m['history'][0]['chip']='wildcard'
        row=build_regrets([m],details,elements,{1},{},fetch)['rows'][0]
        self.assertEqual(row['receipts'],[])
