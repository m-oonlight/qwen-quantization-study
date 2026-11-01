#!/usr/bin/env python3
"""One entry point for one quantization at a time. No full-run auto chaining."""
import argparse,copy,datetime,fcntl,hashlib,html,json,os,pathlib,re,shutil,signal,socket,subprocess,sys,tempfile,threading,time,urllib.request,uuid
from grading import math_grade,code_grade
from monitoring import Monitor
from github_backup import GitHubBackup,preflight as github_preflight
HERE=pathlib.Path(__file__).resolve().parent
PUBLIC={'results.json','summary.json','configuration.json','energy.json','stress.jsonl','diagnostics.jsonl','runtime.log','recovery.json','upload.json'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb')as f:
  for b in iter(lambda:f.read(16*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(path,obj):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp')
 with tmp.open('w')as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path);fd=os.open(path.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
def load(path,default=None):
 try:return json.loads(pathlib.Path(path).read_text())
 except FileNotFoundError:return copy.deepcopy(default)
def event(folder,kind,**data):
 with(folder/'diagnostics.jsonl').open('a')as f:f.write(json.dumps({'time':now(),'kind':kind,**data})+'\n');f.flush();os.fsync(f.fileno())
def request_json(base,path,payload=None,timeout=30):
 req=urllib.request.Request(base+path,data=json.dumps(payload).encode()if payload is not None else None,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout)as r:return json.load(r)
def alias(q):
 m={'Q8':'Q8_0','Q6':'Q6_K','Q5':'Q5_K_M','Q4':'Q4_K_M','Q3':'Q3_K_M','Q2':'Q2_K'};return m.get(q.upper(),q.upper())
def process_servers():
 out=[]
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   args=p.joinpath('cmdline').read_bytes().split(b'\0')
   if args and pathlib.Path(os.fsdecode(args[0])).name=='llama-server':out.append(int(p.name))
  except(OSError,ValueError):pass
 return out

def document(folder,row,index):
 g=row.get('grade',{});status='PENDING'if g.get('correct')is None and g.get('status')!='infrastructure_error'else'INFRASTRUCTURE ERROR'if g.get('status')=='infrastructure_error'else'CORRECT'if g.get('correct')else'INCORRECT'
 content=f"# {status}\n\nQuestion: {row['id']} | Quantization: {row['quant']} | Status: {g.get('status','pending')}\n\n"
 content+=f"Solution correct: {g.get('correct')} | Strict response correct: {g.get('strict_correct')}\n\n"
 if'passed'in g:content+=f"Hidden tests passed: {g['passed']}/{g['total']} | First failure (index only): {json.dumps(g.get('first_failure'))}\n\n"
 content+=f"Inference seconds: {row.get('inference_seconds')} | Decode tokens/s: {row.get('decode_tokens_per_second')} | Thinking budget exhausted: {row.get('thinking_budget_exhausted')} | Output cap reached: {row.get('output_truncated')}\n\n"
 content+='## Exact prompt\n\n'+row['request']['messages'][0]['content']+'\n\n## Entire emitted thinking\n\n'+row.get('reasoning','')+'\n\n## Entire final response\n\n'+row.get('response','')+'\n'
 target=folder/'prompts'/f"{index+1:03d}-{row['id']}.md";target.parent.mkdir(exist_ok=True);tmp=target.with_suffix('.tmp');tmp.write_text(content);os.replace(tmp,target)
def summary(book):
 rows=book['questions'];done=[r for r in rows if r.get('inference_complete')];correct=sum(r.get('grade',{}).get('correct')is True for r in rows);wrong=sum(r.get('grade',{}).get('correct')is False for r in rows);infra=sum(r.get('grade',{}).get('status')=='infrastructure_error'for r in rows);pending=len(rows)-correct-wrong-infra
 complete=len(done)==book['planned']and pending==0 and infra==0
 return {'quant':book['quant'],'purpose':book['purpose'],'planned':book['planned'],'inference_completed':len(done),'correct':correct,'incorrect':wrong,'pending':pending,'infrastructure_errors':infra,'strict_correct':sum(r.get('grade',{}).get('strict_correct')is True for r in rows),'output_truncated':sum(r.get('output_truncated')is True for r in rows),'coding_pending':sum(r['category']=='algorithmic_python'and r.get('grade',{}).get('correct')is None for r in rows),'thinking_budget_exhausted':sum(r.get('thinking_budget_exhausted')is True for r in rows),'thinking_cutoff_unknown':sum(r.get('thinking_budget_exhausted')is None for r in done),'complete':complete,'score_out_of':book['planned'],'score':correct if complete else None,'accuracy_among_graded':correct/(correct+wrong)if correct+wrong else None,'inference_seconds':sum(r.get('inference_seconds',0)for r in rows),'updated':now()}
def persist(folder,book):
 save(folder/'results.json',{k:v for k,v in book.items()if not k.startswith('_')})
 for i,r in enumerate(book['questions']):document(folder,r,i)
 s=summary(book);save(folder/'summary.json',s)
 energies=[r['energy']for r in book['questions']if r.get('energy')]
 def sumkey(section,key):
  values=[e[section].get(key)for e in energies]
  return sum(values)if values and all(v is not None for v in values)else None
 energy={'per_prompt':{r['id']:r.get('energy')for r in book['questions']},'inference_totals':{section:{key:sumkey(section,key)for key in ['gpu_kwh','cpu_kwh','combined_kwh']}for section in ['raw','above_idle_signed']},'execution_segments':book.get('energy_segments',[]),'scope':'CPU package plus GPU device only; above-idle is a signed baseline subtraction, not wall electricity.'};save(folder/'energy.json',energy);return s

class Progress:
 def __init__(self,folder,book):self.folder=folder;self.book=book;self.tps=0;self.current_start=None;self.generated=0;self.stop=threading.Event();self.thread=None
 def draw(self,final=False):
  s=summary(self.book);n=s['inference_completed'];
  if self.current_start:
   try:
    with (self.folder/'runtime.log').open('rb')as f:f.seek(max(0,f.seek(0,2)-8192));tail=f.read().decode(errors='replace')
    found=list(re.finditer(r'n_gen =\s*(\d+), tg =\s*([\d.]+) t/s',tail))
    if found:self.tps=float(found[-1][2])
   except OSError:pass
  graded=s['correct']+s['incorrect'];seconds=s['inference_seconds'];mean=seconds/n if n else None;elapsed=time.monotonic()-self.current_start if self.current_start else 0;eta=max(0,(self.book['planned']-n)*(mean or 500)-elapsed);bar='━'*int(24*n/self.book['planned'])+'─'*(24-int(24*n/self.book['planned']));color=sys.stdout.isatty();green='\033[32m'if color else'';red='\033[31m'if color else'';reset='\033[0m'if color else''
  upload=load(self.folder/'upload.json',{});backup_warning=' BACKUP FAILED'if upload.get('success')is False else''
  line=f"{bar} {n}/{self.book['planned']}  {self.tps:.1f} tok/s  ETA {int(eta//3600):02d}:{int(eta%3600//60):02d}  {green}PASS {s['correct']}{reset} {red}FAIL {s['incorrect']}{reset} PENDING {s['pending']} (coding {s['coding_pending']}) INFRA {s['infrastructure_errors']}{backup_warning}"
  print('\r'+line+' '*8,end='\n'if final else'',flush=True)
 def start(self):
  def loop():
   while not self.stop.wait(1):self.draw()
  self.thread=threading.Thread(target=loop,daemon=True);self.thread.start()
 def close(self):
  self.stop.set()
  if self.thread:self.thread.join();self.thread=None
  self.draw(True)

class Backup:
 def __init__(self,config,folder,destination):self.config=config;self.folder=folder;self.destination=destination;self.last=0;self.lock=threading.Lock();self.thread=None;self.timer_stop=threading.Event();self.timer=None
 def upload(self,force=False,wait=False):
  if not self.config['upload']['enabled']:return
  if not force and time.monotonic()-self.last<self.config['upload']['interval_seconds']:return
  if not self.lock.acquire(blocking=wait):return
  self.last=time.monotonic()
  def run():
   try:
    with tempfile.TemporaryDirectory(prefix='qbench-backup-')as temp:
     snap=pathlib.Path(temp)
     for p in self.folder.iterdir():
      rel=p.relative_to(self.folder)
      if p.is_file()and(p.name in PUBLIC or rel.parts[0]=='prompts'and p.suffix=='.md'):
       dest=snap/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
     snapshot_book=load(self.folder/'results.json')
     if snapshot_book:
      save(snap/'results.json',snapshot_book);save(snap/'summary.json',summary(snapshot_book))
      for i,row in enumerate(snapshot_book['questions']):document(snap,row,i)
     save(snap/'upload.json',{'time':now(),'provider':'github','repository':self.config['upload']['repository'],'destination':self.destination,'success':True,'verification':'Presence on the remote branch confirms snapshot publication. The containing Git commit identifies this snapshot; the local upload.json additionally records its verified SHA.'})
     commit=GitHubBackup(self.config).publish(snapshot=snap,destination=self.destination,methods=HERE/'setup-methods',message='Checkpoint '+self.destination)
     ok=True;record={'time':now(),'destination':self.destination,'success':True,'repository':self.config['upload']['repository'],'commit':commit,'mode':'private GitHub; allowlisted canonical snapshot; chunked logs'};save(self.folder/'upload.json',record)
     if not ok:event(self.folder,'backup_failed',**record)
   except Exception as e:
    record={'time':now(),'destination':self.destination,'success':False,'error':repr(e)};save(self.folder/'upload.json',record);event(self.folder,'backup_failed',**record)
   finally:self.lock.release()
  if wait:run()
  else:self.thread=threading.Thread(target=run,daemon=True);self.thread.start()
 def start_periodic(self):
  def loop():
   while not self.timer_stop.wait(self.config['upload']['interval_seconds']):self.upload(force=True)
  self.timer=threading.Thread(target=loop,daemon=True);self.timer.start()
 def stop_periodic(self):
  self.timer_stop.set()
  if self.timer:self.timer.join(timeout=2)
 def join(self):
  if self.thread:self.thread.join(timeout=self.config['upload']['timeout_seconds']+5)

class Server:
 def __init__(self,config,quant,folder,monitor):self.config=config;self.quant=quant;self.folder=folder;self.monitor=monitor;self.proc=None;self.log=None;self.base=f"http://{config['server']['host']}:{config['server']['port']}"
 def command(self,layers):
  c=self.config;s=c['server'];g=c['generation']
  return[c['runtime']['binary'],'--jinja','--reasoning','on','--reasoning-budget',str(g['reasoning_budget_tokens']),'-m',c['models'][self.quant]['path'],'--gpu-layers','all','--n-cpu-moe',str(layers),'--fit','off','--override-tensor','token_embd.weight=CUDA0','-c',str(s['context']),'-n',str(g['max_tokens']),'-b',str(s['batch']),'-ub',str(s['ubatch']),'-ctk',s['cache_k'],'-ctv',s['cache_v'],'--parallel',str(s['parallel']),'--threads',str(s['threads']),'--threads-batch',str(s['threads_batch']),'--flash-attn',s['flash_attention'],'--cache-ram',str(s['cache_ram']),'--host',s['host'],'--port',str(s['port']),'-lv',str(s['log_verbosity'])]
 def start(self,layers,phase='loading'):
  with socket.socket()as sock:
   if sock.connect_ex((self.config['server']['host'],self.config['server']['port']))==0:raise RuntimeError('Server port occupied; refusing to stop an unrelated process.')
  self.monitor.guard=None;cmd=self.command(layers);self.log=(self.folder/'runtime.log').open('a');self.log.write('\nSTART '+json.dumps({'time':now(),'command':cmd})+'\n');self.log.flush();self.proc=subprocess.Popen(cmd,stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True);self.monitor.set_phase(phase,self.proc.pid);save(self.folder/'recovery.json',{'server_pid':self.proc.pid,'server_start_ticks':pathlib.Path(f'/proc/{self.proc.pid}/stat').read_text().split()[21],'command':cmd,'time':now()})
  deadline=time.monotonic()+self.config['monitor']['load_timeout_seconds']
  while time.monotonic()<deadline:
   if self.proc.poll()is not None:raise RuntimeError('Model load failed; see runtime.log')
   if self.monitor.guard:raise RuntimeError('Memory guard during load: '+str(self.monitor.guard))
   try:
    props=request_json(self.base,'/props',timeout=2)
    if props.get('default_generation_settings',{}).get('n_ctx')==self.config['server']['context']:return props
   except Exception:pass
   time.sleep(.5)
  raise RuntimeError('Model load timeout')
 def close(self):
  if self.proc:
   if self.proc.poll()is None:
    os.killpg(self.proc.pid,signal.SIGTERM)
    try:self.proc.wait(timeout=20)
    except subprocess.TimeoutExpired:os.killpg(self.proc.pid,signal.SIGKILL);self.proc.wait()
   event(self.folder,'server_shutdown',pid=self.proc.pid,returncode=self.proc.returncode)
   self.proc=None;self.monitor.set_phase('between_phases',None)
  if self.log:self.log.close();self.log=None
 def qualify(self):
  c=self.config;lo=c['placement']['min_cpu_moe'];hi=c['placement']['max_cpu_moe'];best=None;trials=[]
  while lo<=hi:
   layers=(lo+hi)//2;record={'cpu_moe_layers':layers,'time':now()}
   try:
    self.start(layers,'qualification');params=copy.deepcopy(c['generation']);params.update(max_tokens=c['placement']['probe_max_tokens'],reasoning_budget_tokens=0,stream=False,messages=[{'role':'user','content':'Inert memory allocation probe. '*c['placement']['probe_repetitions']+'Reply OK.'}]);request_json(self.base,'/v1/chat/completions',params,timeout=120);r=self.monitor.sample();free=r['gpu']['memory.total']-r['gpu']['memory.used'];swap=r['model_process_memory_kib'].get('Swap',0);record.update(free_vram_mib=free,process_swap_kib=swap,passed=not self.monitor.guard and free>=c['placement']['minimum_free_vram_mib']and swap==0)
   except Exception as e:record.update(passed=False,error=repr(e))
   finally:self.close()
   trials.append(record);event(self.folder,'placement_probe',**record)
   if record['passed']:best=layers;hi=layers-1
   else:lo=layers+1
  if best is None:raise RuntimeError('No placement qualified; inspect runtime.log and diagnostics.jsonl')
  return best,trials

def recover(folder,book):
 rec=load(folder/'recovery.json',{});pid=rec.get('server_pid')
 if pid:
  try:
   proc=pathlib.Path('/proc')/str(pid);ticks=proc.joinpath('stat').read_text().split()[21];cmd=proc.joinpath('cmdline').read_bytes().decode().split('\0')
   if ticks==rec.get('server_start_ticks')and cmd and pathlib.Path(cmd[0]).name=='llama-server':
    os.killpg(pid,signal.SIGTERM)
    for _ in range(100):
     if not proc.exists():break
     time.sleep(.1)
    if proc.exists():os.killpg(pid,signal.SIGKILL)
    event(folder,'orphan_server_shutdown',pid=pid)
  except(ProcessLookupError,FileNotFoundError):pass
 if rec.get('inflight'):
  partial=rec['inflight'];row=next(r for r in book['questions']if r['id']==partial['id'])
  if not row.get('inference_complete'):
   row.setdefault('interrupted_attempts',[]).append(partial);event(folder,'incomplete_generation_preserved_for_explicit_restart',id=row['id'],attempt_id=partial['attempt_id']);save(folder/'results.json',book)
 save(folder/'recovery.json',{'time':now(),'recovered':True})
 # Remove only orphaned containers from this exact run, not unrelated containers.
 try:
  ids=subprocess.check_output(['docker','ps','-aq','--filter','label=qbench.owner='+book['run_id']],text=True,timeout=10).split()
  for cid in ids:subprocess.run(['docker','rm','-f',cid],capture_output=True,timeout=10)
 except(OSError,subprocess.SubprocessError):pass

def infer(row,c,server,monitor,progress,folder,book):
 params=copy.deepcopy(c['generation']);params['messages']=[{'role':'user','content':row['request']['messages'][0]['content']}];row['request']=params
 attempt={'id':row['id'],'attempt_id':uuid.uuid4().hex,'started':now(),'request':params,'reasoning':'','response':''};rec={'server_pid':server.proc.pid,'server_start_ticks':pathlib.Path(f'/proc/{server.proc.pid}/stat').read_text().split()[21],'inflight':attempt};save(folder/'recovery.json',rec)
 start=time.monotonic();progress.current_start=start;progress.generated=0;monitor.begin_question(row['id']);last_save=start;usage={};timings={};finish=None;done=False;first=None;reason=[];content=[];logpath=folder/'runtime.log';offset=logpath.stat().st_size
 req=urllib.request.Request(server.base+'/v1/chat/completions',data=json.dumps(params).encode(),headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=c['monitor']['socket_timeout_seconds'])as response:
   for raw in response:
    if monitor.guard:raise RuntimeError('Memory guard: '+str(monitor.guard))
    if not raw.startswith(b'data:'):continue
    data=raw[5:].strip()
    if data==b'[DONE]':done=True;break
    chunk=json.loads(data)
    if chunk.get('error'):raise RuntimeError(str(chunk['error']))
    usage=chunk.get('usage')or usage;timings=chunk.get('timings')or timings
    for choice in chunk.get('choices',[]):
     finish=choice.get('finish_reason')or finish;delta=choice.get('delta',{});got=False
     for field,bucket in [('reasoning_content',reason),('content',content)]:
      value=delta.get(field)
      if value:
       got=True;bucket.append(value)
       if first is None:first=time.monotonic()-start
     if got:progress.generated+=1
    elapsed=time.monotonic()-start
    progress.tps=timings.get('predicted_per_second')or(progress.generated/max(.001,elapsed-(first or 0)))
    if time.monotonic()-last_save>=c['monitor']['checkpoint_seconds']:
     attempt.update(reasoning=''.join(reason),response=''.join(content),seconds_observed=elapsed,usage=usage,timings=timings,checkpoint=now());save(folder/'recovery.json',rec);last_save=time.monotonic()
  if not done or finish is None:raise RuntimeError('Incomplete streamed response')
  elapsed=time.monotonic()-start
  with logpath.open('rb')as f:f.seek(offset);logs=f.read().decode(errors='replace')
  forced='budget exhausted'in logs or'budget=0, forcing'in logs
  natural='deactivated (natural end)'in logs
  row.update(inference_complete=True,attempt_id=attempt['attempt_id'],started=attempt['started'],finished=now(),reasoning=''.join(reason),response=''.join(content),inference_seconds=elapsed,first_token_seconds=first,usage=usage,timings=timings,decode_tokens_per_second=timings.get('predicted_per_second')or usage.get('completion_tokens',0)/max(.001,elapsed-(first or 0)),finish_reason=finish,output_truncated=finish=='length',thinking_budget_exhausted=True if forced else False if natural else None,thinking_cutoff_evidence='engine_budget_trace'if forced or natural else'not_reported_by_engine',energy=monitor.end_question())
  if row['category']=='algorithmic_python':row['grade']={'status':'pending','correct':None,'strict_correct':None,'reason':'coding deferred until inference server exits'}
  else:row['grade']=math_grade(row['response'],book['_math_keys'][row['id']]['answer'],row['output_truncated'])
  save(folder/'results.json',{k:v for k,v in book.items()if not k.startswith('_')});document(folder,row,book['questions'].index(row));save(folder/'recovery.json',{'server_pid':server.proc.pid,'server_start_ticks':rec['server_start_ticks'],'completed_id':row['id']});progress.tps=row['decode_tokens_per_second']
 except BaseException as e:
  attempt.update(reasoning=''.join(reason),response=''.join(content),seconds_observed=time.monotonic()-start,error=repr(e),checkpoint=now())
  if monitor.question_start:attempt['energy']=monitor.end_question()
  save(folder/'recovery.json',rec);event(folder,'inference_interrupted',id=row['id'],error=repr(e));raise
 finally:progress.current_start=None

def system_info():
 commands={'kernel':['uname','-a'],'cpu':['lscpu'],'gpu':['nvidia-smi','-q'],'docker':['docker','--version'],'python':[sys.executable,'--version'],'storage':['lsblk','-o','NAME,MODEL,SIZE,TYPE,MOUNTPOINTS']}
 out={}
 for name,cmd in commands.items():
  try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=10);out[name]=r.stdout+r.stderr
  except Exception as e:out[name]=repr(e)
 for name,path in [('os_release','/etc/os-release'),('swappiness','/proc/sys/vm/swappiness'),('cpu_governor','/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')]:
  try:out[name]=pathlib.Path(path).read_text().strip()
  except OSError:out[name]=None
 return out

def grade_pending(folder,book,c,force=False):
 if process_servers():raise RuntimeError('Refusing coding grading while any llama-server process is running. Stop it, then rerun with --grade-only.')
 tests=load(c['dataset']['hidden_tests']['path'])['tests'];progress=Progress(folder,book);progress.start()
 try:
  for i,row in enumerate(book['questions']):
   if row['category']!='algorithmic_python'or not row.get('inference_complete'):continue
   if not force and row.get('grade',{}).get('correct')is not None:continue
   if force and row.get('grade'):row.setdefault('previous_grades',[]).append(row['grade'])
   row['grade']=code_grade(row['response'],tests[row['id']],c['sandbox'],row.get('output_truncated',False),book['run_id']);row['graded_at']=now();persist(folder,book)
   if row['grade']['correct']is None:event(folder,'coding_infrastructure_error',id=row['id'],grade=row['grade']);raise RuntimeError('Coding infrastructure failure preserved; rerun --grade-only to continue.')
 finally:progress.close()

def finalize_energy(folder,book):
 energy=load(folder/'energy.json',{});raw={'gpu_j':0.,'cpu_j':0.};net={'gpu_j':0.,'cpu_j':0.};seconds=0.;net_seconds=0.;questions={};phases={};baselines={x.get('segment_id'):x for x in load(folder/'configuration.json',{}).get('idle_baselines',[])}
 if not(folder/'stress.jsonl').exists():return
 for line in(folder/'stress.jsonl').open():
  try:r=json.loads(line)
  except ValueError:continue
  if 'interval_gpu_j'not in r:continue
  dt=r.get('interval_seconds',0);seconds+=dt;g=r.get('interval_gpu_j');c=r.get('interval_cpu_j')
  if g is None or c is None:continue
  raw['gpu_j']+=g;raw['cpu_j']+=c
  phase=phases.setdefault(r.get('interval_phase','unknown'),{'gpu_j':0.,'cpu_j':0.,'seconds':0.});phase['gpu_j']+=g;phase['cpu_j']+=c;phase['seconds']+=dt
  ref=r.get('idle_reference')or baselines.get(r.get('segment_id'))
  if ref and ref.get('cpu_watts')is not None:net['gpu_j']+=g-ref['gpu_watts']*dt;net['cpu_j']+=c-ref['cpu_watts']*dt;net_seconds+=dt
  if r.get('interval_question'):
   q=questions.setdefault(r['interval_question'],{'gpu_j':0.,'cpu_j':0.,'seconds':0.});q['gpu_j']+=g;q['cpu_j']+=c;q['seconds']+=dt
 def kwh(v):return {'gpu_kwh':v['gpu_j']/3600000,'cpu_kwh':v['cpu_j']/3600000,'combined_kwh':(v['gpu_j']+v['cpu_j'])/3600000}
 energy.update(whole_run_observed_raw=kwh(raw),whole_run_above_idle_signed=kwh(net),observed_seconds=seconds,above_idle_coverage_seconds=net_seconds,by_phase={k:{**kwh(v),'seconds':v['seconds']}for k,v in phases.items()},per_question_all_attempts_observed={k:{**kwh(v),'seconds':v['seconds']}for k,v in questions.items()},measurement='Fsynced one-second telemetry integrated once, including interrupted attempts. CPU package plus GPU device only. No measurements during a powered-off gap.');save(folder/'energy.json',energy)

def comparison(config):
 rows=[]
 for q in config['order']:
  canonical=load(pathlib.Path(config['run_root'])/q/'results.json');s=summary(canonical)if canonical else None
  if s and s.get('complete'):rows.append(s)
 if len(rows)==len(config['order']):
  print('\nQuantization  Score      Strict   Inference hours')
  for r in rows:print(f"{r['quant']:12s}  {r['correct']:3d}/{r['planned']}    {r['strict_correct']:3d}      {r['inference_seconds']/3600:.2f}")
  save(pathlib.Path(config['run_root'])/'comparison.json',rows)

def backup_preflight(c):return github_preflight(c,HERE/'setup-methods')

def run(args):
 c=load(args.config);quant=alias(args.model)
 if quant not in c['models']:raise RuntimeError('Choose Q8, Q6, Q5, Q4, Q3 or Q2.')
 if args.smoke:
  c['generation']['reasoning_budget_tokens']=c['smoke']['thinking_tokens'];c['generation']['max_tokens']=c['smoke']['output_tokens'];c['monitor']['idle_seconds']=c['smoke']['idle_seconds']
 
 if not args.smoke and not args.grade_only:
  for earlier in c['order'][:c['order'].index(quant)]:
   if not load(pathlib.Path(c['run_root'])/earlier/'summary.json',{}).get('complete')or not load(pathlib.Path(c['run_root'])/earlier/'upload.json',{}).get('success'):raise RuntimeError('Finish '+earlier+' first; full-study order is Q8, Q6, Q5, Q4, Q3, Q2.')
 purpose='smoke (excluded from full study)'if args.smoke else'full single-pass study';folder=pathlib.Path(c['run_root'])/(('smoke-'if args.smoke else'')+quant);folder.mkdir(parents=True,exist_ok=True)
 lock=(HERE/'.runner.lock').open('w')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise RuntimeError('Another benchmark command is active.')
 for name,d in c['dataset'].items():
  if sha(d['path'])!=d['sha256']:raise RuntimeError('Immutable dataset hash changed: '+name)
 source_hashes={p.name:sha(p)for p in [pathlib.Path(__file__),HERE/'grading.py',HERE/'monitoring.py',HERE/'github_backup.py']};fingerprint=digest({'config':c,'sources':source_hashes});book=load(folder/'results.json')
 if book:
  if book['profile_fingerprint']!=fingerprint:raise RuntimeError('Config or evaluator changed since this run began. Preserve the old run; use a new study/run_root for changed conditions.')
 else:
  questions=load(c['dataset']['exam']['path'])['questions']
  if args.smoke:questions=[next(q for q in questions if q['category']!='algorithmic_python'),next(q for q in questions if q['category']=='algorithmic_python')][:c['smoke']['questions']]
  book={'schema_version':1,'run_id':uuid.uuid4().hex,'quant':quant,'purpose':purpose,'planned':len(questions),'profile_fingerprint':fingerprint,'created':now(),'questions':[{'id':q['id'],'category':q['category'],'family':q['id'].rsplit('-',1)[0],'quant':quant,'request':{'messages':[{'role':'user','content':q['question']}]},'inference_complete':False,'grade':{'status':'not_started','correct':None,'strict_correct':None}}for q in questions],'energy_segments':[]};save(folder/'results.json',book)
 recover(folder,book)
 for i,row in enumerate(book['questions']):document(folder,row,i)
 backup=Backup(c,folder,folder.name);metadata=load(folder/'configuration.json')
 if args.grade_only and any(not r['inference_complete']for r in book['questions']):raise RuntimeError('Inference is incomplete; run the normal model command first.')
 if not args.grade_only and any(not r['inference_complete']for r in book['questions']):
  checks={c['runtime']['binary']:c['runtime']['sha256'],c['models'][quant]['path']:c['models'][quant]['sha256'],**c['runtime'].get('shared_libraries',{})}
  for path,expected in checks.items():
   if sha(path)!=expected:raise RuntimeError('Pinned runtime/model changed: '+path)
 if not metadata:
  if args.grade_only:raise RuntimeError('Missing run configuration')
  if sha(c['runtime']['binary'])!=c['runtime']['sha256']:raise RuntimeError('Pinned engine binary hash changed')
  if sha(c['models'][quant]['path'])!=c['models'][quant]['sha256']:raise RuntimeError('Model file hash mismatch')
  metadata={'shared_config':c,'profile_fingerprint':fingerprint,'source_hashes':source_hashes,'quant':quant,'model':c['models'][quant],'system':system_info(),'question_order':[r['id']for r in book['questions']],'purpose':purpose,'started':now(),'primary_score':'solution_correct; strict formatting separate','placement':None};save(folder/'configuration.json',metadata)
 print(json.dumps(metadata,indent=2),flush=True)
 if not args.smoke and not args.grade_only and any(not r['inference_complete']for r in book['questions']):backup_preflight(c)
 if summary(book)['complete']and not args.regrade:
  comparison(c)
  persist(folder,book);finalize_energy(folder,book);backup.upload(force=True,wait=True);print(f"Already complete: {summary(book)['correct']}/{book['planned']}. No inference or grading repeated.");comparison(c);return 0 if load(folder/'upload.json',{}).get('success')else 3
 monitor=Monitor(folder,c);monitor.start();backup.start_periodic();server=Server(c,quant,folder,monitor);progress=Progress(folder,book)
 try:
  baseline=monitor.baseline_measure(c['monitor']['idle_seconds']);metadata.setdefault('idle_baselines',[]).append({'segment_id':monitor.segment_id,'time':now(),**baseline});save(folder/'configuration.json',metadata)
  if not args.grade_only and any(not r['inference_complete']for r in book['questions']):
   if process_servers():raise RuntimeError('Another llama-server is active; stop it before benchmarking.')
   placement=metadata.get('placement')
   if placement is None:
    if args.smoke:layers=c['smoke']['cpu_moe_layers'];trials=[]
    else:layers,trials=server.qualify()
    placement={'cpu_expert_layers':layers,'remaining_gpu_expert_layers':c['placement']['max_cpu_moe']-layers,'gpu_layers':'all with first N MoE experts overridden to CPU','qualification_trials':trials,'qualification':'short allocation/prefill probe, not a filled 128K context'};metadata['placement']=placement;save(folder/'configuration.json',metadata)
   props=server.start(placement['cpu_expert_layers']);
   if hashlib.sha256(props.get('chat_template','').encode()).hexdigest()!=c['chat_template_sha256']:raise RuntimeError('Chat template differs from shared reference')
   metadata['resolved_server_defaults']=props;metadata['exact_server_command']=server.command(placement['cpu_expert_layers']);save(folder/'configuration.json',metadata)
   print('\nResolved run configuration:\n'+json.dumps(metadata,indent=2),flush=True)
   keys=load(c['dataset']['answer_key']['path'])['answers'];book['_math_keys']=keys;progress.start();persist(folder,{k:v for k,v in book.items()if not k.startswith('_')});backup.upload(force=True)
   for row in book['questions']:
    if row['inference_complete']:continue
    infer(row,c,server,monitor,progress,folder,book);persist(folder,{k:v for k,v in book.items()if not k.startswith('_')});backup.upload()
   book.pop('_math_keys',None);progress.close();server.close();save(folder/'recovery.json',{'inference_complete':True,'time':now()})
  server.close();monitor.set_phase('coding_grading');grade_pending(folder,book,c,args.regrade);s=persist(folder,book)
 except BaseException as e:
  book.pop('_math_keys',None);event(folder,'run_interrupted',error=repr(e));raise
 finally:
  if progress.thread:progress.close()
  server.close();segment=monitor.stop();book.pop('_math_keys',None);book.setdefault('energy_segments',[]).append({'time':now(),**segment});persist(folder,book);finalize_energy(folder,book);comparison(c);backup.stop_periodic();backup.join();backup.upload(force=True,wait=True)
 s=persist(folder,book);finalize_energy(folder,book)
 # Documents are derived from the canonical results; verify all status headings.
 for i,r in enumerate(book['questions']):
  title=(folder/'prompts'/f"{i+1:03d}-{r['id']}.md").read_text().splitlines()[0]
  expected='# CORRECT'if r['grade']['correct']is True else'# INCORRECT'if r['grade']['correct']is False else'# INFRASTRUCTURE ERROR'if r['grade']['status']=='infrastructure_error'else'# PENDING'
  if title!=expected:raise RuntimeError('Document/result grade mismatch')
 print(f"\nFINAL: {s['correct']}/{book['planned']} correct; {s['incorrect']} incorrect; {s['pending']} pending; {s['infrastructure_errors']} infrastructure errors.")
 upload=load(folder/'upload.json',{})
 if not upload.get('success'):print('GitHub backup needs attention; local results are safe. Rerun the same command to retry the upload.')
 comparison(c)
 return 0 if upload.get('success')else 3

def cli():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('model');p.add_argument('--config',type=pathlib.Path,default=HERE/'config.json');p.add_argument('--smoke',action='store_true',help='two questions, 64 thinking / 1024 total tokens; separate output folder; excluded from study');p.add_argument('--grade-only',action='store_true',help='resume pending coding grades without loading any model');p.add_argument('--regrade',action='store_true',help='with --grade-only, regrade coding source and preserve previous grades');args=p.parse_args()
 if args.regrade and not args.grade_only:p.error('--regrade requires --grade-only')
 try:return run(args)or 0
 except(KeyboardInterrupt,Exception)as e:print('\nStopped:',e,file=sys.stderr);return 1
 return 0
if __name__=='__main__':sys.exit(cli())
