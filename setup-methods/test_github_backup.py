"""Offline backup tests: local bare Git remote, no GitHub login or GPU required."""
import copy,json,pathlib,subprocess,tempfile,unittest
from unittest.mock import patch
import github_backup as g

class ExportTests(unittest.TestCase):
 def test_allowlist_chunk_restore_and_checksum(self):
  with tempfile.TemporaryDirectory()as t:
   root=pathlib.Path(t);source=root/'source';source.mkdir();dest=root/'export';out=root/'restored'
   data=b'{"metric":1}\n'*13+b'partial';(source/'stress.jsonl').write_bytes(data);(source/'results.json').write_text('{}');(source/'answer_key.json').write_text('PRIVATE');(source/'hidden_tests.json').write_text('PRIVATE');(source/'token').write_text('PRIVATE');(source/'runtime.log').symlink_to(source/'token')
   (source/'prompts').mkdir();(source/'prompts/001-Q.md').write_text('# CORRECT');(source/'prompts/not-a-question.md').write_text('PRIVATE')
   g.export_public(source,dest,23)
   self.assertEqual({p.name for p in dest.iterdir()},{'logs','logs-manifest.json','results.json','prompts'})
   self.assertEqual([p.name for p in(dest/'prompts').iterdir()],['001-Q.md'])
   self.assertTrue(all(p.stat().st_size<=23 for p in(dest/'logs').iterdir()))
   g.restore_logs(dest,out);self.assertEqual((out/'stress.jsonl').read_bytes(),data)
   next((dest/'logs').iterdir()).write_bytes(b'corrupted')
   with self.assertRaisesRegex(RuntimeError,'Corrupt'):g.restore_logs(dest,out)
 def test_empty_log(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t);(p/'source').mkdir();(p/'source/runtime.log').touch();g.export_public(p/'source',p/'dest');g.restore_logs(p/'dest',p/'restored');self.assertEqual((p/'restored/runtime.log').read_bytes(),b'')
 def test_private_destination_required(self):
  c={'upload':{'repository':'owner/repo','checkout':'unused','timeout_seconds':10}}
  with patch('github_backup.command',return_value=type('R',(),{'stdout':'{"private":false,"permissions":{"push":true}}'})()):
   with self.assertRaisesRegex(RuntimeError,'private'):g.GitHubBackup(c).private_access()
  with patch('github_backup.command',return_value=type('R',(),{'stdout':'{"private":true,"permissions":{"push":false}}'})()):
   with self.assertRaisesRegex(RuntimeError,'push permission'):g.GitHubBackup(c).private_access()
 def test_no_interactive_git(self):
  with patch('github_backup.subprocess.run',return_value=type('R',(),{'returncode':0})())as run:
   g.command(['git','version']);self.assertEqual(run.call_args.kwargs['env']['GIT_TERMINAL_PROMPT'],'0');self.assertEqual(run.call_args.kwargs['env']['GH_PROMPT_DISABLED'],'1')

class GitTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name);self.remote=self.root/'remote.git';subprocess.run(['git','init','--bare',str(self.remote)],capture_output=True,check=True)
  self.config={'upload':{'repository':'owner/repo','checkout':str(self.root/'checkout'),'timeout_seconds':10,'log_chunk_bytes':30}}
  self.backup=g.GitHubBackup(self.config);self.backup.remote=str(self.remote)
  self.source=self.root/'source';self.source.mkdir();(self.source/'results.json').write_text('{"score":1}');(self.source/'stress.jsonl').write_text('measurement\n'*10)
  self.methods=self.root/'methods';self.methods.mkdir();(self.methods/'README.md').write_text('methods');(self.methods/'answer_key.json').write_text('PRIVATE')
  self.access=patch.object(self.backup,'private_access');self.access.start()
 def tearDown(self):self.access.stop();self.temp.cleanup()
 def publish(self):return self.backup.publish(self.source,'Q2_K',self.methods)
 def test_verified_push_and_idempotent_retry(self):
  first=self.publish();second=self.publish();self.assertEqual(first,second)
  head=subprocess.check_output(['git','--git-dir',str(self.remote),'rev-parse','main'],text=True).strip();self.assertEqual(first,head)
  names=subprocess.check_output(['git','--git-dir',str(self.remote),'ls-tree','-r','--name-only','main'],text=True)
  self.assertIn('runs/Q2_K/results.json',names);self.assertIn('logs-manifest.json',names);self.assertNotIn('answer_key',names)
  self.assertEqual(self.backup.git('rev-list','--count','HEAD').stdout.strip(),'1')
 def test_interrupted_push_reuses_local_commit(self):
  original=g.command
  def fail_push(args,**kwargs):
   if 'push'in args:raise RuntimeError('network lost')
   return original(args,**kwargs)
  with patch('github_backup.command',side_effect=fail_push):
   with self.assertRaisesRegex(RuntimeError,'network lost'):self.publish()
  commit=self.backup.git('rev-parse','HEAD').stdout.strip();self.assertEqual(self.publish(),commit)
  self.assertEqual(self.backup.git('rev-list','--count','HEAD').stdout.strip(),'1')
 def test_new_checkout_resumes_existing_remote(self):
  first=self.publish();c=copy.deepcopy(self.config);c['upload']['checkout']=str(self.root/'second-checkout');other=g.GitHubBackup(c);other.remote=str(self.remote)
  with patch.object(other,'private_access'):
   second=other.publish(self.source,'Q2_K',self.methods)
  self.assertEqual(first,second)
 def test_oversize_file_refused_before_commit(self):
  with(self.source/'results.json').open('wb')as f:f.truncate(90*1024*1024)
  with self.assertRaisesRegex(RuntimeError,'safe GitHub size'):self.publish()
  self.assertNotEqual(self.backup.git('rev-parse','--verify','HEAD',check=False).returncode,0)

if __name__=='__main__':unittest.main()
