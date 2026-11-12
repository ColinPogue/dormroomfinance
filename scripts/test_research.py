import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'automation'))
from research import load_research

class ResearchTest(unittest.TestCase):
    def test_source_gate(self):
        good={'keyword':'test','reviewed_by':'Editor','sources':[{'url':'https://example.com/terms','verified_on':'2026-11-12','claims':['A checked claim']}]}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'pack.json'
            path.write_text(json.dumps(good))
            self.assertEqual(load_research(path,'test',date(2026,11,12)),good)
            with self.assertRaises(ValueError): load_research(path,'other',date(2026,11,12))
            for field,value in [('url','http://example.com'),('url','https://user:pass@example.com'),('verified_on','2026-10-01'),('verified_on','2026-11-13'),('claims',[])]:
                bad=json.loads(json.dumps(good));bad['sources'][0][field]=value;path.write_text(json.dumps(bad))
                with self.subTest(field=field,value=value), self.assertRaises(ValueError): load_research(path,'test',date(2026,11,12))
            for field,value in [('reviewed_by',''),('sources',[])]:
                bad=json.loads(json.dumps(good));bad[field]=value;path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):load_research(path,'test',date(2026,11,12))

if __name__=='__main__':unittest.main()
