"""Deterministic extraction and grading. Untrusted source executes ONLY in Docker."""
import ast,copy,json,re,subprocess,tempfile,uuid
from pathlib import Path

def same(a,b):
 if type(a)is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys() and all(same(a[k],b[k])for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(same(x,y)for x,y in zip(a,b))
 return a==b

def decode(s):
 def pairs(xs):
  d={}
  for k,v in xs:
   if k in d:raise ValueError('duplicate keys')
   d[k]=v
  return d
 return json.JSONDecoder(object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))).raw_decode(s)

def math_grade(text,answer,truncated=False):
 text=text.strip();pos=text.rfind('FINAL_JSON:');tail=text[pos+11:].lstrip()if pos>=0 else text;parsed=None;strict=False
 try:
  parsed,end=decode(tail);strict=pos>=0 and isinstance(parsed,dict)and not tail[end:].strip()
 except ValueError:pass
 if parsed is None:
  # Last complete JSON answer object in final content, without repairing it.
  for m in re.finditer(r'\{',tail):
   try:
    v,_=decode(tail[m.start():])
    if isinstance(v,dict)and set(v)=={'answer'}:parsed=v
   except ValueError:pass
 ok=same(parsed,{'answer':answer})
 return dict(status='correct'if ok else 'incorrect',correct=ok,solution_correct=ok,strict_correct=bool(ok and strict and not truncated),format_ok=strict,reason='exact_answer_match'if ok else 'missing_or_wrong_exact_answer')

def extract_code(text):
 text=text.strip();pos=text.rfind('FINAL_CODE:');tail=text[pos+11:].lstrip()if pos>=0 else text
 openings=list(re.finditer(r'(?m)^```(?:python)?[ \t]*\n',tail));candidates=[]
 for op in openings:
  closes=list(re.finditer(r'(?m)^```[ \t]*(?:\n|$)',tail[op.end():]))
  for cl in closes:
   end=op.end()+cl.start();code=tail[op.end():end].rstrip('\n');boundary=op.end()+cl.end()
   try:ast.parse(code)
   except SyntaxError:continue
   candidates.append((code,pos>=0 and op.start()==0 and not tail[boundary:].strip()));break
 if candidates:return candidates[-1]
 # Retain syntactically invalid source as written for policy/syntax rejection.
 m=re.search(r'```(?:python)?[ \t]*\n(.*)\n```[ \t]*$',tail,re.S)
 return (m[1],False)if m else (None,False)

def policy(code):
 try:t=ast.parse(code)
 except SyntaxError:return 'syntax_error'
 if not t.body:return 'empty_code'
 forbidden={'eval','exec','open','compile','globals','locals','getattr','setattr','delattr','vars','input','breakpoint'}
 for n in ast.walk(t):
  if isinstance(n,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.AsyncFunctionDef)):return 'forbidden_construct'
  if isinstance(n,ast.FunctionDef):
   if n.decorator_list:return 'decorators_forbidden'
   for default in n.args.defaults+[x for x in n.args.kw_defaults if x is not None]:
    try:ast.literal_eval(default)
    except (ValueError,TypeError):return 'nonliteral_default'
  if isinstance(n,ast.Name)and(n.id.startswith('__')or n.id in forbidden):return 'forbidden_name'
  if isinstance(n,ast.Attribute)and n.attr.startswith('_'):return 'forbidden_attribute'
 for n in t.body:
  if isinstance(n,ast.FunctionDef):continue
  if isinstance(n,(ast.Assign,ast.AnnAssign)):
   targets=n.targets if isinstance(n,ast.Assign)else[n.target]
   if not all(isinstance(x,ast.Name)for x in targets):return 'top_level_policy'
   try:ast.literal_eval(n.value)
   except (ValueError,TypeError):return 'top_level_policy'
  else:return 'top_level_policy'
 if not any(isinstance(n,ast.FunctionDef)and n.name=='solve'for n in t.body):return 'missing_solve'
 return None

SAFE_NAMES=['abs','all','any','bool','dict','enumerate','filter','float','int','isinstance','len','list','map','max','min','next','range','reversed','round','set','sorted','str','sum','tuple','zip','ValueError','TypeError','ord','chr','divmod','frozenset','pow','iter','repr','bin','oct','hex','format','bytes','bytearray','complex','slice','type','callable','issubclass','object','Exception','RuntimeError','IndexError','KeyError','StopIteration','ZeroDivisionError']
RUNNER=r'''import json,copy,sys,__future__,time,resource
p=json.load(open('/task/payload.json'));print(json.dumps({'started':True}),flush=True)
ns={'__builtins__':{n:getattr(__import__('builtins'),n)for n in p['safe_names']}}
def same(a,b):
 if type(a)is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys()and all(same(a[k],b[k])for k in a)
 if isinstance(a,list):return len(a)==len(b)and all(same(x,y)for x,y in zip(a,b))
 return a==b
passed=0;first=None;cpu=time.process_time();wall=time.monotonic()
try:
 exec(compile(p['code'],'<model>','exec',flags=__future__.annotations.compiler_flag,dont_inherit=True),ns)
 fn=ns['solve']
 for i,c in enumerate(p['cases']):
  value=copy.deepcopy(c['input']);before=copy.deepcopy(value);status=None
  try:
   result=fn(value)
   if value!=before:status='input_mutation'
   elif not same(json.loads(json.dumps(result,allow_nan=False)),c['expected']):status='wrong_output'
  except BaseException as e:status='exception_'+type(e).__name__
  if status is None:passed+=1
  elif first is None:first={'index_0_based':i,'status':status}
  print(json.dumps({'case_finished':i,'passed':passed,'first_failure':first}),flush=True)
 print(json.dumps({'finished':True,'passed':passed,'total':len(p['cases']),'first_failure':first,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}),flush=True)
except BaseException as e:print(json.dumps({'finished':True,'passed':passed,'total':len(p['cases']),'first_failure':{'index_0_based':None,'status':'definition_'+type(e).__name__}}),flush=True)
'''

def sandbox_grade(code,cases,config,owner='test'):
 failure=policy(code)
 base=dict(total=len(cases),passed=0,first_failure=None)
 if failure:return dict(base,status='incorrect',correct=False,reason=failure)
 try:subprocess.run(['docker','image','inspect',config['image']],check=True,capture_output=True,timeout=10)
 except (OSError,subprocess.SubprocessError):return dict(base,status='infrastructure_error',correct=None,reason='docker_image_unavailable')
 name='qbench-'+uuid.uuid4().hex;result=None
 with tempfile.TemporaryDirectory(prefix='qbench-code-')as tmp:
  root=Path(tmp);root.chmod(0o755)
  for file,value in [('payload.json',json.dumps({'code':code,'cases':cases,'safe_names':SAFE_NAMES})),('runner.py',RUNNER)]:
   f=root/file;f.write_text(value);f.chmod(0o644)
  cmd=['docker','run','--name',name,'--label','qbench.owner='+owner,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory',str(config['memory_mib'])+'m','--memory-swap',str(config['memory_mib'])+'m','--cpus',str(config['cpus']),'--pids-limit',str(config['pids']),'--user','65534:65534','--ulimit',f"cpu={config['cpu_seconds']}:{config['cpu_seconds']}",'--tmpfs',f"/tmp:rw,noexec,nosuid,size={config['tmp_mib']}m",'-v',str(root)+':/task:ro',config['image'],'python','-I','/task/runner.py']
  raw='';timed_out=False;returncode=None
  try:
   proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
   try:raw,err=proc.communicate(timeout=config['wall_seconds']);returncode=proc.returncode
   except subprocess.TimeoutExpired:
    timed_out=True;subprocess.run(['docker','kill',name],capture_output=True,timeout=10)
    try:raw,err=proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:proc.kill();raw,err=proc.communicate()
   events=[]
   for line in raw.splitlines():
    try:events.append(json.loads(line))
    except ValueError:pass
   started=any(x.get('started')for x in events)
   last=next((x for x in reversed(events)if'passed'in x),base)
   if not started:result=dict(base,status='infrastructure_error',correct=None,reason='container_did_not_start',detail=err[-1000:])
   elif timed_out:result=dict(last,status='incorrect',correct=False,reason='wall_time_limit',total=len(cases),first_failure=last.get('first_failure')or{'index_0_based':last.get('case_finished',-1)+1,'status':'wall_time_limit'})
   elif last.get('finished')and returncode==0:result=dict(last,status='correct'if last['passed']==len(cases)and not last.get('first_failure')else'incorrect',correct=last['passed']==len(cases)and not last.get('first_failure'))
   elif returncode in (137,139,152):result=dict(last,status='incorrect',correct=False,reason='resource_limit_or_signal',total=len(cases),first_failure=last.get('first_failure')or{'index_0_based':last.get('case_finished',-1)+1,'status':'resource_limit_or_signal'})
   else:result=dict(last,status='infrastructure_error',correct=None,reason='unexpected_container_exit',exit_code=returncode,total=len(cases))
  except (OSError,subprocess.SubprocessError)as e:result=dict(base,status='infrastructure_error',correct=None,reason=type(e).__name__)
  finally:
   try:subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
   except (OSError,subprocess.SubprocessError):pass
 return result

def code_grade(text,cases,config,truncated=False,owner='test'):
 code,format_ok=extract_code(text)
 if code is None:return dict(status='incorrect',correct=False,solution_correct=False,strict_correct=False,format_ok=False,reason='no_code_block',passed=0,total=len(cases),first_failure=None)
 r=sandbox_grade(code,cases,config,owner);r.update(solution_correct=r['correct'],strict_correct=None if r['correct']is None else bool(r['correct']and format_ok and not truncated),format_ok=format_ok)
 return r
