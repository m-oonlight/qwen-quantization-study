"""Allowlisted, private-repository snapshots; no generated-code execution or secrets."""
import fcntl,hashlib,json,os,pathlib,re,shutil,subprocess,tempfile,time

PUBLIC={'results.json','summary.json','configuration.json','energy.json','stress.jsonl','diagnostics.jsonl','runtime.log','recovery.json','upload.json'}
LOGS={'stress.jsonl','diagnostics.jsonl','runtime.log'}
METHODS={'benchmark.py','grading.py','monitoring.py','github_backup.py','config.json','test_benchmark.py','test_github_backup.py','enable-cpu-energy.sh','README.md','BACKUP-SETUP.md','model-metadata-check.txt','test-results.txt','validation.json','system-check.txt','model-inventory.json','files.sha256.json','connection-check.json'}

def write_json(path,data):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');os.replace(temp,path)

def export_public(source,dest,chunk_bytes=8*1024*1024):
 """Export only public artifacts. Chunks concatenate byte-for-byte to original logs."""
 source=pathlib.Path(source);dest=pathlib.Path(dest);dest.mkdir(parents=True,exist_ok=True);manifest={}
 if not source.is_dir():raise RuntimeError('Missing snapshot source: '+str(source))
 for p in sorted(source.iterdir()):
  if p.is_symlink()or not p.is_file()or p.name not in PUBLIC:continue
  if p.name not in LOGS:
   shutil.copy2(p,dest/p.name);continue
  # Bound the snapshot at the observed EOF; concurrent appends wait for next backup.
  remaining=p.stat().st_size;size=remaining;total=hashlib.sha256();parts=[];idx=0
  with p.open('rb')as f:
   while remaining:
    data=f.read(min(chunk_bytes,remaining))
    if not data:raise RuntimeError('Log shrank during snapshot: '+p.name)
    remaining-=len(data);total.update(data);name=f'logs/{p.name}.part-{idx:06d}';idx+=1
    target=dest/name;target.parent.mkdir(exist_ok=True);target.write_bytes(data)
    parts.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
  manifest[p.name]={'bytes':size,'sha256':total.hexdigest(),'parts':parts}
 prompts=source/'prompts'
 if prompts.is_dir()and not prompts.is_symlink():
  for p in sorted(prompts.iterdir()):
   if p.is_file()and not p.is_symlink()and re.fullmatch(r'\d{3}-[A-Za-z0-9_-]+\.md',p.name):
    (dest/'prompts').mkdir(exist_ok=True);shutil.copy2(p,dest/'prompts'/p.name)
 if manifest:write_json(dest/'logs-manifest.json',{'format':'Concatenate parts in listed order to restore each exact original log; chunks may split JSON lines.','logs':manifest})

def restore_logs(folder,destination):
 folder=pathlib.Path(folder);destination=pathlib.Path(destination);destination.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((folder/'logs-manifest.json').read_text())
 for name,entry in manifest['logs'].items():
  if name not in LOGS:raise RuntimeError('Unexpected log name')
  h=hashlib.sha256();size=0;target=destination/(name+'.tmp')
  with target.open('wb')as out:
   for part in entry['parts']:
    rel=pathlib.PurePosixPath(part['path'])
    if len(rel.parts)!=2 or rel.parts[0]!='logs'or '..'in rel.parts:raise RuntimeError('Invalid chunk path')
    data=(folder/str(rel)).read_bytes()
    if len(data)!=part['bytes']or hashlib.sha256(data).hexdigest()!=part['sha256']:raise RuntimeError('Corrupt log chunk')
    out.write(data);h.update(data);size+=len(data)
  if h.hexdigest()!=entry['sha256']or size!=entry['bytes']:raise RuntimeError('Log checksum mismatch')
  os.replace(target,destination/name)

def command(args,cwd=None,timeout=120,check=True):
 env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GH_PROMPT_DISABLED='1')
 r=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
 if check and r.returncode:raise RuntimeError('Backup command failed ('+' '.join(args[:3])+'): '+r.stderr[-1800:])
 return r

class GitHubBackup:
 def __init__(self,config):
  self.c=config['upload'];self.repo=self.c['repository'];self.folder=pathlib.Path(self.c['checkout']).resolve();self.timeout=self.c['timeout_seconds']
  if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',self.repo):raise RuntimeError('Invalid GitHub owner/repository')
  self.remote='https://github.com/'+self.repo+'.git'
 def git(self,*args,check=True):
  return command(['git','-c','credential.helper=','-c','credential.helper=!gh auth git-credential',*args],cwd=self.folder,timeout=self.timeout,check=check)
 def private_access(self):
  r=command(['gh','api','repos/'+self.repo],timeout=min(30,self.timeout));data=json.loads(r.stdout)
  if data.get('private')is not True:raise RuntimeError('Refusing backup: destination repository must be private')
  if not data.get('permissions',{}).get('push'):raise RuntimeError('No push permission on private backup repository')
 def prepare(self):
  self.folder.mkdir(parents=True,exist_ok=True)
  if not(self.folder/'.git').exists():
   if any(self.folder.iterdir()):raise RuntimeError('Backup checkout must be empty before initialization')
   self.git('init','-b','main');self.git('remote','add','origin',self.remote)
   self.git('config','user.name','Qwen benchmark runner');self.git('config','user.email','qwen-benchmark@users.noreply.github.com')
  if self.git('remote','get-url','origin').stdout.strip()!=self.remote:raise RuntimeError('Backup remote changed; refusing upload')
  self.git('fetch','origin','main',check=False)
  remote=self.git('rev-parse','--verify','refs/remotes/origin/main',check=False)
  local=self.git('rev-parse','--verify','HEAD',check=False)
  if remote.returncode==0:
   if local.returncode!=0:self.git('checkout','-B','main','origin/main')
   elif self.git('merge-base','--is-ancestor','origin/main','HEAD',check=False).returncode:
    self.git('merge','--ff-only','origin/main')
 def _commit_push(self,message):
  # Allow only our explicit directory structure and plain files; never git-add the source tree.
  allowed=[p for p in ['README.md','setup-methods','runs','comparison.json']if(self.folder/p).exists()]
  if not allowed:raise RuntimeError('Empty backup snapshot')
  paths=self.git('ls-files','--others','--exclude-standard').stdout.splitlines()+self.git('ls-files').stdout.splitlines()
  for rel in set(paths):
   p=self.folder/rel
   if p.is_symlink():raise RuntimeError('Refusing symlink in backup checkout')
   if p.is_file()and p.stat().st_size>=90*1024*1024:raise RuntimeError('File exceeds safe GitHub size: '+rel)
  self.git('add','--',*allowed)
  if self.git('diff','--cached','--quiet',check=False).returncode:self.git('commit','-m',message)
  # No force push: an interrupted push retries existing local commits next time.
  self.git('push','--porcelain','origin','HEAD:refs/heads/main')
  local=self.git('rev-parse','HEAD').stdout.strip();remote=self.git('ls-remote','origin','refs/heads/main').stdout.split()
  if not remote or remote[0]!=local:raise RuntimeError('Remote commit verification failed')
  return local
 def publish(self,snapshot=None,destination=None,methods=None,message='Benchmark checkpoint'):
  # Process lock covers all model, methods and preflight uploads from this machine.
  self.folder.parent.mkdir(parents=True,exist_ok=True)
  with self.folder.with_suffix('.lock').open('a')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);self.private_access();self.prepare()
   if not(self.folder/'README.md').exists():(self.folder/'README.md').write_text('# Qwen quantization study\n\nPrivate research results and fixed benchmark methods.\n\nOne pass of 250 questions per quantization, Q8 through Q2. Pilot/smoke folders are excluded from the study. Each model summary and prompt grade is derived from its canonical results.json.\n\nLarge stress/runtime logs are stored as ordered byte chunks with SHA-256 manifests. See setup-methods/BACKUP-SETUP.md for restoration. No model weights, answer keys, hidden tests, account credentials or tokens are included.\n')
   if methods:
    target=self.folder/'setup-methods';target.mkdir(exist_ok=True)
    for p in pathlib.Path(methods).iterdir():
     if p.name in METHODS and p.is_file()and not p.is_symlink():shutil.copy2(p,target/p.name)
   comparison=pathlib.Path(self.c.get('comparison_file',str(self.folder.parent/'runs/comparison.json')))
   if comparison.is_file():
    data=json.loads(comparison.read_text());write_json(self.folder/'comparison.json',data)
   if snapshot:
    if not re.fullmatch(r'[A-Za-z0-9_-]+',destination or''):raise RuntimeError('Invalid run destination')
    target=self.folder/'runs'/destination
    if target.exists():shutil.rmtree(target)
    export_public(snapshot,target,self.c.get('log_chunk_bytes',8*1024*1024))
   return self._commit_push(message)

def preflight(config,methods):
 if not config['upload']['enabled']:raise RuntimeError('Backups are disabled; enable GitHub before a full run.')
 try:
  write_json(pathlib.Path(methods)/'connection-check.json',{'time_unix':time.time(),'study_id':config['study_id'],'purpose':'private repository write verification before model load; no exam data'})
  return GitHubBackup(config).publish(methods=methods,message='Verify unattended backup access before benchmark')
 except Exception as e:raise RuntimeError('GitHub backup preflight failed before model load: '+str(e))from e

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--restore-logs',type=pathlib.Path);p.add_argument('--destination',type=pathlib.Path);a=p.parse_args()
 if not a.restore_logs or not a.destination:p.error('Use --restore-logs RUN_FOLDER --destination LOCAL_OUTPUT_FOLDER')
 restore_logs(a.restore_logs,a.destination)
