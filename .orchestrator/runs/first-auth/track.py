"""Run-local evidence/checklist helper; graph remains the source of truth."""
import json, pathlib, subprocess, sys, datetime
root=pathlib.Path(__file__).resolve().parents[3]; folder=pathlib.Path(__file__).resolve().parent; path=folder/'run.json'
def cli(*args): subprocess.run(['node',str(root/'.orchestrator/bin/orchestrator.mjs'),*map(str,args)],cwd=root,check=True)
def checklist():
 r=json.loads(path.read_text()); lines=['# FIRST normal auth checklist','', 'Kaynak gerçek: `run.json`. Kanıtlar: `results/`, `evidence/`; eski başarısız denemeler korunur.','']
 for i in r['items']:
  if i['id'] in ['contract','backend','frontend','review','verify','integration']:continue
  lines.extend(['## '+i['title'], '',f"Düğüm: `{i['id']}` — **{i['status']}**; bağımlılık: {', '.join(i['relations']['dependsOn'])}", ''])
  lines += [(' - [x] ' if i['status']=='done' else ' - [ ] ')+a for a in i['acceptanceCriteria']]
  lines += ['', 'Kanıt: '+str(i['resultRef']), '']
 lines+=['## Ortam sınırları','', 'Gerçek PostgreSQL, Redis atomiklik/TTL/arıza, SMTP teslimi, dinleyen uygulama, tarayıcı E2E ve deploy: **not_verified** — kullanıcı kapsamı dışında.']
 (folder/'checklist.md').write_text('\n'.join(lines)+'\n')
if len(sys.argv)>1:
 action,id=sys.argv[1:3]
 if action=='start':
  cli('sync',path); cli('transition',path,id,'active','--reason','Bağımlı kapılar tamam; görev başlatıldı.','--actor','manager')
 elif action in ('pass', 'fail'):
  evidence=sys.argv[3]; identity=sys.argv[4] if len(sys.argv)>4 else 'manager';r=json.loads(path.read_text());i=next(i for i in r['items'] if i['id']==id)
  result={'schemaVersion':'1.0.0','runId':r['runId'],'itemId':id,'agent':{'platform':'codex','identity':identity,'sessionRef':None},'outcome':action,'summary':evidence,'artifacts':[{'type':'evidence','path':None,'change':'reported','description':'Görev/dosya/komut/sonuç ve kapsam dışı kontroller'}],'acceptance':[{'criterion':a,'status':'passed' if action=='pass' else 'failed','evidence':evidence} for a in i['acceptanceCriteria']],'checks':[{'name':'Aşama kanıtı','status':'passed' if action=='pass' else 'failed','evidence':evidence},{'name':'Gerçek servisler ve E2E','status':'not_run','evidence':'Kullanıcı sınırı; not_verified.'}],'risks':['PostgreSQL/Redis/SMTP çalışma zamanı ve E2E not_verified.'],'followUps':[],'completedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  dest=folder/'evidence'/f'{id}-result.json';dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');cli('record',path,dest,'--actor','manager')
checklist()
