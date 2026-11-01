"""Whole-device GPU and CPU-package energy; no estimates of CPU/wall power."""
import csv,json,os,pathlib,statistics,subprocess,threading,time,uuid

def cpu_counters():
 out=[]
 for p in pathlib.Path('/sys/class/powercap').glob('intel-rapl:*'):
  try:
   if not(p/'name').read_text().strip().startswith('package-'):continue
   out.append((p/'energy_uj',int((p/'max_energy_range_uj').read_text())))
  except OSError:pass
 return out

def energy_delta(old,new,maximum):return(new-old)%maximum

class Monitor:
 def __init__(self,folder,config,pid=None):
  self.segment_id=uuid.uuid4().hex;self.folder=folder;self.config=config;self.pid=pid;self.phase='idle';self.question=None;self.guard=None;self.last=None;self.cpu_prev=None;self.lock=threading.RLock();self.halt=threading.Event();self.thread=None;self.totals={'gpu_j':0.,'cpu_j':0.};self.counters=cpu_counters();self.by_phase={};self.question_start=None;self.baseline=None;self.errors=[]
  self.cpu_readable=bool(self.counters)
  for p,_ in self.counters:
   try:p.read_text()
   except OSError:self.cpu_readable=False
  if config['monitor']['require_cpu_energy']and not self.cpu_readable:raise RuntimeError('CPU package energy unavailable. Run sudo ./enable-cpu-energy.sh once; then retry the same command.')
 def reading(self):
  fields=['utilization.gpu','memory.used','memory.total','power.draw','temperature.gpu','clocks.sm','clocks.mem','clocks_throttle_reasons.active']
  raw=subprocess.check_output(['nvidia-smi','--query-gpu='+','.join(fields),'--format=csv,noheader,nounits'],text=True,timeout=5).strip().splitlines()[0]
  values=next(csv.reader([raw],skipinitialspace=True));gpu=dict(zip(fields,values))
  for k in fields[:-1]:
   try:gpu[k]=float(gpu[k])
   except ValueError:gpu[k]=None
  stat=list(map(int,pathlib.Path('/proc/stat').read_text().splitlines()[0].split()[1:]));total=sum(stat);idle=stat[3]+stat[4];usage=None
  if self.cpu_prev:usage=100*(1-(idle-self.cpu_prev[1])/max(1,total-self.cpu_prev[0]))
  self.cpu_prev=(total,idle)
  mem={l.split(':')[0]:int(l.split(':')[1].split()[0])for l in pathlib.Path('/proc/meminfo').read_text().splitlines()if':'in l}
  cpu_energy=[int(p.read_text())for p,_ in self.counters]if self.cpu_readable else None
  temps={}
  for p in pathlib.Path('/sys/class/hwmon').glob('hwmon*'):
   try:name=(p/'name').read_text().strip()
   except OSError:continue
   for f in p.glob('temp*_input'):
    try:temps[name+'/'+f.stem]=int(f.read_text())/1000
    except(OSError,ValueError):pass
  clocks=[]
  for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines():
   if line.startswith('cpu MHz'):clocks.append(float(line.split(':')[1]))
  throttles={}
  for f in pathlib.Path('/sys/devices/system/cpu').glob('cpu*/thermal_throttle/*throttle_count'):
   try:throttles[str(f)]=int(f.read_text())
   except(OSError,ValueError):pass
  process={}
  if self.pid:
   try:process={l.split(':')[0]:int(l.split(':')[1].split()[0])for l in pathlib.Path(f'/proc/{self.pid}/smaps_rollup').read_text().splitlines()if':'in l}
   except(OSError,ValueError):pass
  return dict(segment_id=self.segment_id,time=time.time(),monotonic=time.monotonic(),phase=self.phase,question=self.question,gpu=gpu,cpu_usage_percent=usage,cpu_package_energy_uj=cpu_energy,cpu_clock_mean_mhz=statistics.mean(clocks)if clocks else None,temperatures_c=temps,cpu_throttle_counters=throttles or None,host_memory_kib=mem,model_process_memory_kib=process)
 def sample(self):
  with self.lock:
   r=self.reading()
   if self.last:
    dt=r['monotonic']-self.last['monotonic'];a=self.last['gpu']['power.draw'];b=r['gpu']['power.draw'];gj=(a+b)*dt/2 if a is not None and b is not None else None
    cj=sum(energy_delta(a,b,m)for a,b,(_,m)in zip(self.last['cpu_package_energy_uj'],r['cpu_package_energy_uj'],self.counters))/1e6 if r['cpu_package_energy_uj']is not None and self.last['cpu_package_energy_uj']is not None else None
    if gj is not None:self.totals['gpu_j']+=gj
    if cj is not None:self.totals['cpu_j']+=cj
    bucket=self.by_phase.setdefault(self.last['phase'],{'gpu_j':0.,'cpu_j':0.,'seconds':0.});bucket['seconds']+=dt;bucket['gpu_j']+=gj or 0;bucket['cpu_j']+=cj or 0
    r['interval_gpu_j']=gj;r['interval_cpu_j']=cj;r['interval_seconds']=dt;r['interval_phase']=self.last['phase'];r['interval_question']=self.last['question'];r['idle_reference']=self.baseline
   self.last=r
   gpu=r['gpu'];pm=r['model_process_memory_kib'];free=gpu['memory.total']-gpu['memory.used'];available=r['host_memory_kib']['MemAvailable']/1024
   if self.pid and pm:
    if pm.get('Swap',0)>0 or free<self.config['placement']['minimum_free_vram_mib']or available<self.config['placement']['minimum_host_available_mib']:self.guard={'free_vram_mib':free,'process_swap_kib':pm.get('Swap',0),'host_available_mib':available}
   with (self.folder/'stress.jsonl').open('a')as f:f.write(json.dumps(r)+'\n');f.flush();os.fsync(f.fileno())
   return r
 def start(self):
  self.sample()
  def loop():
   while not self.halt.wait(self.config['monitor']['sample_seconds']):
    try:self.sample()
    except Exception as e:self.errors.append(repr(e))
  self.thread=threading.Thread(target=loop,daemon=True);self.thread.start()
 def set_phase(self,phase,pid=None):
  with self.lock:self.sample();self.phase=phase;self.pid=pid;self.last['phase']=phase;self.last['question']=self.question
 def baseline_measure(self,seconds):
  self.set_phase('idle');t=time.monotonic();before=dict(self.totals)
  while time.monotonic()-t<seconds:time.sleep(max(0,min(1,seconds-(time.monotonic()-t))))
  self.sample();dt=time.monotonic()-t;self.baseline={'seconds':dt,'gpu_watts':(self.totals['gpu_j']-before['gpu_j'])/dt,'cpu_watts':(self.totals['cpu_j']-before['cpu_j'])/dt if self.cpu_readable else None,'method':'GPU trapezoidal driver watts; CPU package accumulated microjoules, wrap-corrected; whole device/package, includes other activity'};return self.baseline
 def begin_question(self,qid):
  with self.lock:self.sample();self.phase='inference';self.question=qid;self.question_start=(time.monotonic(),dict(self.totals));self.last['phase']='inference';self.last['question']=qid
 def end_question(self):
  with self.lock:
   self.sample();t,before=self.question_start;seconds=time.monotonic()-t;gj=self.totals['gpu_j']-before['gpu_j'];cj=self.totals['cpu_j']-before['cpu_j']if self.cpu_readable else None;self.question=None;self.question_start=None;self.last['question']=None
   raw={'gpu_kwh':gj/3600000,'cpu_kwh':cj/3600000 if cj is not None else None,'combined_kwh':(gj+cj)/3600000 if cj is not None else None};base=self.baseline
   above={'gpu_kwh':(gj-base['gpu_watts']*seconds)/3600000,'cpu_kwh':(cj-base['cpu_watts']*seconds)/3600000 if cj is not None else None};above['combined_kwh']=sum(above.values())if all(v is not None for v in above.values())else None
   return {'seconds':seconds,'raw':raw,'above_idle_signed':above,'idle_baseline':base,'scope':'GPU device plus CPU package; not whole-machine wall energy'}
 def stop(self):
  self.halt.set()
  if self.thread:self.thread.join(timeout=7)
  try:self.sample()
  except Exception as e:self.errors.append(repr(e))
  return {'segment_id':self.segment_id,'totals_j':self.totals,'by_phase':self.by_phase,'baseline':self.baseline,'cpu_counters':[{'path':str(p),'max_energy_range_uj':m}for p,m in self.counters],'telemetry_errors':self.errors,'scope':'Observed execution segment; includes baseline, loading/qualification, inference, grading and backup work. CPU/GPU only, not wall energy.'}
