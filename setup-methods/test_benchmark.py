"""CPU-only tests. Docker cases use CPU containers, never the GPU."""
import copy,json,os,pathlib,tempfile,unittest
from unittest.mock import patch
import benchmark as b
from grading import same,math_grade,extract_code,policy,code_grade
from monitoring import energy_delta
C=json.loads((pathlib.Path(__file__).parent/'config.json').read_text())

def row(id='a',category='algorithmic_python',correct=None):
 return {'id':id,'quant':'Q2_K','category':category,'request':{'messages':[{'role':'user','content':'Exact question'}]},'inference_complete':True,'response':'FINAL_CODE:\n```python\ndef solve(data):\n    return data["x"]\n```','reasoning':'preserve me','grade':{'correct':correct,'status':'pending'if correct is None else'correct'if correct else'incorrect','strict_correct':correct},'inference_seconds':1}
def book(rows):return {'quant':'Q2_K','purpose':'test','run_id':'test','planned':len(rows),'questions':rows,'energy_segments':[]}
class GradingTests(unittest.TestCase):
 def test_exact_types(self):
  for value in [True,1.0,'1',None,[]]:self.assertFalse(same(value,1))
  self.assertFalse(same({'answer':[2,4]},{'answer':[1,2]}));self.assertFalse(same(None,[]))
 def test_math(self):
  self.assertTrue(math_grade('working\nFINAL_JSON: {"answer":3}',3)['strict_correct'])
  self.assertFalse(math_grade('FINAL_JSON: {"answer":3.0}',3)['correct'])
  self.assertFalse(math_grade('FINAL_JSON: {"answer":true}',1)['correct'])
  self.assertFalse(math_grade('FINAL_JSON: {"answer":3,"answer":4}',4)['correct'])
  self.assertFalse(math_grade('FINAL_JSON: {"answer":NaN}',None)['correct'])
 def test_solution_and_format_separate(self):
  g=math_grade('```json\n{"answer":[1,2]}\n```',[1,2]);self.assertTrue(g['correct']);self.assertFalse(g['strict_correct'])
  g=math_grade('FINAL_JSON: {"answer":3} trailing',3);self.assertTrue(g['correct']);self.assertFalse(g['strict_correct'])
  g=math_grade('FINAL_JSON: {"answer":3}',3,True);self.assertTrue(g['correct']);self.assertFalse(g['strict_correct'])
 def test_code_fence_and_literal(self):
  code='def solve(data):\n    s = """hello\n```\nworld"""\n    return s'
  got,strict=extract_code('FINAL_CODE:\n```python\n'+code+'\n```');self.assertEqual(got,code);self.assertTrue(strict)
  got,strict=extract_code('```python\ndef solve(data):\n    return 1\n```');self.assertFalse(strict);self.assertIn('return 1',got)
 def test_policy_never_executes(self):
  for code in ['import os\ndef solve(d): return 1','def solve(d):\n class C: pass\n return 1','def solve(d): return d.__class__','INF=10**18\ndef solve(d): return 1']:
   self.assertIsNotNone(policy(code))
  self.assertIsNone(policy('INF=100\ndef solve(d): return len(d)'))
 def test_infra_not_wrong(self):
  with patch('grading.subprocess.run',side_effect=OSError('docker unavailable')):
   g=code_grade('FINAL_CODE:\n```python\ndef solve(d): return 1\n```',[{'input':{},'expected':1}],C['sandbox']);self.assertIsNone(g['correct']);self.assertEqual(g['status'],'infrastructure_error')
class PersistenceTests(unittest.TestCase):
 def test_atomic_data_and_document_agreement(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t);data=book([row('yes',correct=True),row('no',correct=False)]);data['_math_keys']={'secret':'never upload'};b.persist(p,data)
   self.assertNotIn('_math_keys',b.load(p/'results.json'));s=b.load(p/'summary.json');self.assertEqual(s['score'],1);self.assertTrue(s['complete']);self.assertEqual((p/'prompts/001-yes.md').read_text().splitlines()[0],'# CORRECT');self.assertEqual((p/'prompts/002-no.md').read_text().splitlines()[0],'# INCORRECT')
 def test_pending_and_infra_excluded(self):
  x=row();data=book([x]);self.assertIsNone(b.summary(data)['score']);x['grade']={'status':'infrastructure_error','correct':None};self.assertEqual(b.summary(data)['incorrect'],0);self.assertFalse(b.summary(data)['complete'])
 def test_resume_preserves_interruption(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t);r=row();r['inference_complete']=False;data=book([r]);b.save(p/'recovery.json',{'inflight':{'id':'a','attempt_id':'interrupted','reasoning':'partial'}})
   with patch('benchmark.subprocess.check_output',return_value=''):b.recover(p,data)
   self.assertFalse(r['inference_complete']);self.assertEqual(r['interrupted_attempts'][0]['reasoning'],'partial')
 def test_resume_does_not_repeat_completed_grades(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t);data=book([row('already',correct=True),row('pending')]);fake=copy.deepcopy(C);tests=p/'tests.private';tests.write_text(json.dumps({'tests':{'pending':[{'input':{},'expected':0}]}}));fake['dataset']['hidden_tests']['path']=str(tests)
   with patch('benchmark.process_servers',return_value=[]),patch('benchmark.code_grade',return_value={'correct':True,'strict_correct':True,'status':'correct','passed':1,'total':1})as grade,patch.object(b.Progress,'start'),patch.object(b.Progress,'close'):
    b.grade_pending(p,data,fake);self.assertEqual(grade.call_count,1);b.grade_pending(p,data,fake);self.assertEqual(grade.call_count,1)
 def test_grading_refuses_live_model(self):
  with patch('benchmark.process_servers',return_value=[123]):
   with self.assertRaises(RuntimeError):b.grade_pending(pathlib.Path('.'),book([]),C)
 def test_single_profile_commands(self):
  commands=[]
  for q,n in [('Q8_0',30),('Q2_K',4)]:commands.append(b.Server(C,q,pathlib.Path('.'),None).command(n))
  for cmd in commands:cmd[cmd.index('-m')+1]='MODEL';cmd[cmd.index('--n-cpu-moe')+1]='PLACEMENT'
  self.assertEqual(commands[0],commands[1])

 def test_event_explicit_time(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t);b.event(p,'probe',time='recorded');self.assertEqual(json.loads((p/'diagnostics.jsonl').read_text())['time'],'recorded')
 def test_github_preflight_failure(self):
  with patch('github_backup.GitHubBackup.publish',side_effect=RuntimeError('authentication unavailable')):
   with self.assertRaisesRegex(RuntimeError,'before model load'):b.backup_preflight(C)
 def test_backup_export_is_allowlisted_and_consistent(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t);data=book([row('yes',correct=True)]);b.persist(p,data);(p/'answer_key.json').write_text('PRIVATE');(p/'hidden_tests.json').write_text('PRIVATE');seen=[]
   def upload(**kwargs):
    snap=pathlib.Path(kwargs['snapshot']);names=[str(f.relative_to(snap))for f in snap.rglob('*')if f.is_file()];seen.extend(names);self.assertNotIn('answer_key.json',names);self.assertNotIn('hidden_tests.json',names);self.assertEqual(json.loads((snap/'summary.json').read_text())['correct'],1);self.assertEqual((snap/'prompts/001-yes.md').read_text().splitlines()[0],'# CORRECT');return 'test-commit'
   with patch('benchmark.GitHubBackup.publish',side_effect=upload):b.Backup(C,p,'test').upload(force=True,wait=True)
   self.assertIn('results.json',seen);self.assertTrue(b.load(p/'upload.json')['success'])
 def test_counter_wrap(self):self.assertEqual(energy_delta(98,3,100),5)
@unittest.skipUnless(os.environ.get('RUN_DOCKER_TESTS')=='1','set RUN_DOCKER_TESTS=1 for real CPU sandbox tests')
class DockerTests(unittest.TestCase):
 def grade(self,code,cases,seconds=None):
  config=copy.deepcopy(C['sandbox'])
  if seconds:config.update(cpu_seconds=seconds,wall_seconds=seconds+3)
  return code_grade('FINAL_CODE:\n```python\n'+code+'\n```',cases,config)
 def test_pass(self):
  g=self.grade('def solve(d): return sum(d["a"])',[{'input':{'a':[]},'expected':0},{'input':{'a':[1,2]},'expected':3}]);self.assertTrue(g['correct']);self.assertEqual(g['passed'],2)
 def test_first_failure_and_all_tests(self):
  g=self.grade('def solve(d): return d["x"]',[{'input':{'x':1},'expected':0},{'input':{'x':2},'expected':2}]);self.assertFalse(g['correct']);self.assertEqual(g['passed'],1);self.assertEqual(g['first_failure']['index_0_based'],0)
 def test_input_mutation(self):
  g=self.grade('def solve(d):\n d["a"].append(1)\n return 0',[{'input':{'a':[]},'expected':0}]);self.assertEqual(g['first_failure']['status'],'input_mutation')
 def test_bool_not_int(self):self.assertFalse(self.grade('def solve(d): return True',[{'input':{},'expected':1}])['correct'])
 def test_timeout(self):
  g=self.grade('def solve(d):\n while True: pass',[{'input':{},'expected':0}],1);self.assertFalse(g['correct']);self.assertNotEqual(g['status'],'infrastructure_error')
if __name__=='__main__':unittest.main()
