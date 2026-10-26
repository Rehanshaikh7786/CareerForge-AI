from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pypdf import PdfReader
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import sqlite3, hashlib, secrets, re, json, urllib.request
from datetime import datetime

app=FastAPI(title='CareerForge AI Pro',version='2.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
DB='careerforge.db'
SKILLS=['python','java','c++','javascript','typescript','react','next.js','fastapi','django','flask','sql','mongodb','postgresql','aws','azure','docker','kubernetes','machine learning','deep learning','nlp','llm','rag','langchain','langgraph','crewai','git','github','data structures','algorithms','system design','pandas','numpy','tensorflow','pytorch','scikit-learn','rest api','ci/cd','mlops','linux','redis','firebase','power bi']
ROLEMAP={'AI/ML Engineer':['python','machine learning','deep learning','pytorch','tensorflow','sql','docker','aws'],'GenAI Engineer':['python','llm','rag','langchain','langgraph','fastapi','docker','aws'],'Software Engineer':['java','c++','python','data structures','algorithms','system design','git','sql'],'Data Scientist':['python','sql','pandas','numpy','machine learning','scikit-learn','power bi'],'Backend Engineer':['python','fastapi','sql','postgresql','rest api','docker','redis','aws'],'MLOps Engineer':['python','docker','kubernetes','aws','ci/cd','mlops','linux','git']}
COMPANIES={'AI/ML Engineer':['NVIDIA','Microsoft','Google','Amazon','Adobe','Qualcomm'],'GenAI Engineer':['Microsoft','Google','Amazon','Accenture','Deloitte','TCS'],'Software Engineer':['Microsoft','Google','Amazon','Atlassian','Zoho','Persistent Systems'],'Data Scientist':['Fractal','Tiger Analytics','Deloitte','Accenture','Amazon','Microsoft'],'Backend Engineer':['Atlassian','Amazon','Microsoft','Razorpay','PhonePe','Persistent Systems'],'MLOps Engineer':['NVIDIA','Amazon','Microsoft','Deloitte','Accenture','IBM']}
ROADMAP={'python':['Advanced Python','Build a FastAPI REST project'],'docker':['Docker fundamentals','Containerize one project'],'kubernetes':['Kubernetes basics','Deploy an app to a local cluster'],'system design':['System design fundamentals','Design URL shortener / chat service'],'rag':['Embeddings + vector databases','Build a RAG assistant'],'langgraph':['State graphs','Build a multi-agent workflow'],'sql':['SQL joins/window functions','Build analytics queries'],'aws':['IAM, EC2, S3 basics','Deploy one project on AWS'],'ci/cd':['GitHub Actions basics','Create test/build/deploy pipeline'],'mlops':['Experiment tracking','Model deployment + monitoring']}

def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
 c=db();c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,password TEXT,name TEXT,token TEXT);CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY,user_email TEXT,company TEXT,role TEXT,status TEXT,link TEXT,notes TEXT,created_at TEXT);""");c.commit();c.close()
init()
def read_upload(name,b): return '\n'.join((p.extract_text() or '') for p in PdfReader(BytesIO(b)).pages) if name.lower().endswith('.pdf') else b.decode('utf-8','ignore')
def skill_list(text):
 t=text.lower();return [s for s in SKILLS if s in t]
def auth(a):
 if not a or not a.startswith('Bearer '):raise HTTPException(401,'Login required')
 c=db();u=c.execute('select * from users where token=?',(a[7:],)).fetchone();c.close()
 if not u:raise HTTPException(401,'Invalid session')
 return u
def analysis(text,jd=''):
 t=text.lower();j=jd.lower();rs=skill_list(text);wanted=[s for s in SKILLS if s in j];matched=[s for s in wanted if s in rs];missing=[s for s in wanted if s not in rs]
 skill=round(100*len(matched)/max(1,len(wanted))) if wanted else min(100,len(rs)*4);sections=sum(1 for x in ['education','experience','projects','skills','summary'] if x in t);formatting=min(100,40+sections*9+(8 if '@' in text else 0)+(7 if re.search(r'linkedin|github',t) else 0));nums=len(re.findall(r'\b\d+(?:\.\d+)?%|\b\d+\+|\b\d+x\b',t));impact=min(100,40+nums*10);ats=round(.55*skill+.30*formatting+.15*impact)
 roles=[]
 for role,req in ROLEMAP.items():roles.append({'role':role,'score':round(100*sum(x in rs for x in req)/len(req)),'companies':COMPANIES[role]})
 roles.sort(key=lambda x:x['score'],reverse=True);target=missing if missing else [x for x in ROLEMAP[roles[0]['role']] if x not in rs];gaps=[{'skill':s,'priority':'High' if s in wanted else 'Medium','steps':ROADMAP.get(s,[f'Learn {s} fundamentals',f'Build a mini-project using {s}'])} for s in target[:8]]
 rec=[('Add missing target skills: '+', '.join(missing[:6])) if missing else 'Strong target-skill alignment.','Add measurable outcomes to internship/project bullets.' if impact<75 else 'Quantified impact is strong.','Keep Summary, Skills, Experience, Projects and Education as ATS-friendly headings.' if sections<5 else 'Core resume sections are present.']
 return {'ats_score':ats,'skill_score':skill,'format_score':formatting,'impact_score':impact,'skills':rs,'matched':matched,'missing':missing,'roles':roles,'roadmap':gaps,'recommendations':rec}

class Login(BaseModel):email:str;password:str;name:str|None=None
class Job(BaseModel):company:str;role:str;status:str='Saved';link:str='';notes:str=''

@app.get('/health')
def health():return {'status':'ok','version':'2.0'}
@app.post('/auth/register')
def register(x:Login):
 c=db();token=secrets.token_urlsafe(24)
 try:c.execute('insert into users(email,password,name,token) values(?,?,?,?)',(x.email.lower(),hashlib.sha256(x.password.encode()).hexdigest(),x.name or 'CareerForge User',token));c.commit()
 except sqlite3.IntegrityError:raise HTTPException(400,'Account already exists')
 finally:c.close()
 return {'token':token,'name':x.name or 'CareerForge User'}
@app.post('/auth/login')
def login(x:Login):
 c=db();u=c.execute('select * from users where email=? and password=?',(x.email.lower(),hashlib.sha256(x.password.encode()).hexdigest())).fetchone()
 if not u:c.close();raise HTTPException(401,'Invalid email or password')
 token=secrets.token_urlsafe(24);c.execute('update users set token=? where id=?',(token,u['id']));c.commit();c.close();return {'token':token,'name':u['name']}
@app.post('/analyze')
async def analyze(file:UploadFile=File(...),job_description:str=Form('')):return analysis(read_upload(file.filename,await file.read()),job_description)
@app.post('/compare')
async def compare(first:UploadFile=File(...),second:UploadFile=File(...),job_description:str=Form('')):
 a=analysis(read_upload(first.filename,await first.read()),job_description);b=analysis(read_upload(second.filename,await second.read()),job_description);return {'first':a,'second':b,'winner':'Version 2' if b['ats_score']>=a['ats_score'] else 'Version 1','improvement':b['ats_score']-a['ats_score']}
@app.post('/rewrite')
async def rewrite(file:UploadFile=File(...)):
 text=read_upload(file.filename,await file.read());lines=[x.strip() for x in text.splitlines() if x.strip()];out=[]
 for line in lines:
  if len(line)>35 and not re.search(r'\d',line) and any(v in line.lower() for v in ['develop','build','create','work','manage','implement']):out.append({'original':line[:220],'improved':'Strengthen this bullet with an action verb + technology + measurable result (%, time saved, users, accuracy, scale).','example':'Built [solution] using [technology], improving [metric] by [X%] for [users/team].'})
 return {'suggestions':out[:8],'note':'CareerForge avoids inventing achievements; replace placeholders with truthful metrics.'}
@app.post('/interview')
def interview(role:str=Form(...),skills_csv:str=Form('')):
 ss=[x.strip() for x in skills_csv.split(',') if x.strip()];qs=[f'Tell me about a project where you used {s}. What trade-offs did you make?' for s in ss[:4]]+[f'Why are you interested in a {role} role?','Describe a difficult technical problem you solved.','Explain one system you built from request to deployment.','What would you improve in your strongest project if you had one more month?'];return {'role':role,'questions':qs[:8],'answer_framework':'Use STAR: Situation → Task → Action → Result. For technical answers add architecture, trade-offs and measurable result.'}
@app.get('/github/{username}')
def github(username:str):
 try:
  req=urllib.request.Request(f'https://api.github.com/users/{username}/repos?per_page=100&sort=updated',headers={'User-Agent':'CareerForgeAI'});data=json.loads(urllib.request.urlopen(req,timeout=8).read());langs={};stars=0
  for r in data:
   if r.get('language'):langs[r['language']]=langs.get(r['language'],0)+1
   stars+=r.get('stargazers_count',0)
  return {'username':username,'public_repos':len(data),'stars':stars,'languages':langs,'score':min(100,20+min(len(data),20)*2+min(stars,20)+min(len(langs),8)*3),'advice':['Pin 4–6 strongest repositories.','Add screenshots, setup instructions and architecture to READMEs.','Use meaningful commits and add tests/CI to flagship projects.']}
 except Exception:raise HTTPException(404,'GitHub profile could not be analyzed')
@app.get('/templates')
def templates():return {'templates':[{'name':'ATS Pro','best_for':'Software, AI/ML, Data roles','style':'Single-column, ATS-first','sections':['Summary','Skills','Experience','Projects','Education']},{'name':'Student Launch','best_for':'Internships & freshers','style':'Projects-first','sections':['Summary','Skills','Projects','Experience','Education','Achievements']},{'name':'Engineer Impact','best_for':'Experienced engineers','style':'Impact and metrics','sections':['Summary','Core Skills','Experience','Selected Projects','Education']},{'name':'Research CV','best_for':'Research/academia','style':'Publications-focused','sections':['Profile','Education','Research','Publications','Projects','Skills','Awards']}],'rules':['Prefer 1 page for students/early career; use 2 only when content genuinely needs it.','Use standard headings and a clean single-column layout for ATS-heavy applications.','Start bullets with strong action verbs and show measurable impact.','Tailor keywords to each job description without keyword stuffing.','Do not use fake metrics or skills.','Keep fonts readable, spacing consistent, and links clickable.']}
@app.get('/jobs')
def jobs(authorization:str|None=Header(None)):
 u=auth(authorization);c=db();rows=[dict(x) for x in c.execute('select * from jobs where user_email=? order by id desc',(u['email'],))];c.close();return rows
@app.post('/jobs')
def add_job(x:Job,authorization:str|None=Header(None)):
 u=auth(authorization);c=db();c.execute('insert into jobs(user_email,company,role,status,link,notes,created_at) values(?,?,?,?,?,?,?)',(u['email'],x.company,x.role,x.status,x.link,x.notes,datetime.now().isoformat(timespec='seconds')));c.commit();c.close();return {'ok':True}
@app.delete('/jobs/{job_id}')
def del_job(job_id:int,authorization:str|None=Header(None)):
 u=auth(authorization);c=db();c.execute('delete from jobs where id=? and user_email=?',(job_id,u['email']));c.commit();c.close();return {'ok':True}
@app.post('/report')
async def report(file:UploadFile=File(...),job_description:str=Form('')):
 a=analysis(read_upload(file.filename,await file.read()),job_description);bio=BytesIO();doc=SimpleDocTemplate(bio,pagesize=A4);st=getSampleStyleSheet();story=[Paragraph('CareerForge AI — Career Intelligence Report',st['Title']),Spacer(1,12),Paragraph(f"ATS Score: {a['ats_score']}% | Skill Match: {a['skill_score']}% | Format: {a['format_score']}% | Impact: {a['impact_score']}%",st['Heading2']),Spacer(1,10),Paragraph('Top Role Matches',st['Heading2'])]
 for r in a['roles'][:4]:story.append(Paragraph(f"{r['role']}: {r['score']}% — Companies to research: {', '.join(r['companies'][:4])}",st['BodyText']))
 story+=[Spacer(1,10),Paragraph('Skill Gap Roadmap',st['Heading2'])]
 for g in a['roadmap']:story.append(Paragraph(f"{g['skill'].title()} ({g['priority']}): {' → '.join(g['steps'])}",st['BodyText']))
 doc.build(story);bio.seek(0);return StreamingResponse(bio,media_type='application/pdf',headers={'Content-Disposition':'attachment; filename=careerforge-report.pdf'})
