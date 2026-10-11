import json, sys, pytest
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from test_harness import load
@pytest.fixture
def e(): return load('agent_escrow.py','AgentEscrow','jobs')
def test_accept_and_digests(e):
 _,c,q,b,U=e
 c.open_job('job-1','https://brief.example/x','https://deliver.example/x','https://policy.example/x','Ship a working report with the required sections.')
 b.extend(['brief body','deliverable body','acceptance body','brief body','deliverable body','acceptance body'])
 q.extend([json.dumps({'decision':'ACCEPT','score':92,'summary':'meets policy','missing':[]})]*2)
 c.review_delivery('job-1'); r=json.loads(c.get_job('0xowner','JOB-1'))
 assert r['state']=='ACCEPTED' and len(r['digests'])==3
def test_distinct_and_replay_guards(e):
 _,c,q,b,U=e
 with pytest.raises(U): c.open_job('x','https://same.example/a','https://same.example/b','https://third.example/c','long enough instructions here')
 c.open_job('JOB-2','https://a.example/a','https://b.example/b','https://c.example/c','long enough instructions here')
 b.extend(['x','y','z'])
 with pytest.raises(U): c.review_delivery('JOB-2')


