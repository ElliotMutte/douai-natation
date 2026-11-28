"""Reconstruit site/data.json à partir de in/douai_update.json (collecte extranat) et des fichiers fixes de in/."""
import json, os, datetime
os.chdir(os.path.dirname(os.path.abspath(__file__)))
U=json.load(open('in/douai_update.json'))
M=json.load(open('in/iuf_map.json'))
EV={'NL':'NL','Dos':'Dos','Bra.':'Brasse','Pap.':'Pap','4 N.':'4N'}
def norm(e): d,s=e.split(' ',1); return f"{d} {EV.get(s,s)}"
def pdate(s): d,m,y=s.split('/'); return f"{y}-{m}-{d}"
cnc={c[0]:c[3] for c in U['cnc']}
sw=[]
for s in U['swimmers']:
    seen=set(); perfs=[]
    for e,b,t,pts,date,niv,lieu,cpt,club in s['p']:
        k=(e,b,t,date)
        if k in seen: continue
        seen.add(k); perfs.append([norm(e),b,t,pts,pdate(date),niv,lieu.title(),cpt,club])
    perfs.sort(key=lambda p:p[4])
    sex=s.get('s') or M['sex'].get(s['iuf'])
    sw.append({'id':s['iuf'],'nom':s['n'],'an':s['y'],'sexe':sex,'cnc26':cnc.get(s['n']),'p':perfs})
    M['iuf'][f"{s['n']}|{s['y']}"]=s['iuf']; M['sex'][s['iuf']]=sex
sw.sort(key=lambda x:x['nom'])
json.dump(M,open('in/iuf_map.json','w'),ensure_ascii=False)
have={s['nom'] for s in sw}
Y=int(U['date'][:4])
old=json.load(open('site/data.json'))['meta'] if os.path.exists('site/data.json') else {}
club={**old.get('club',{}),**{k:v for k,v in U['club'].items() if v is not None}}
Q=json.load(open('in/qualifs_depreg.json'))+json.load(open('in/nat_official.json'))
rkS=str(Y) if os.path.exists('in/rankings_season.txt') and open('in/rankings_season.txt').read().strip()==str(Y) else old.get('rkSeason',str(Y))
meta={'updated':datetime.date.fromisoformat(U['date']).strftime('%d/%m/%Y'),'season':Y,'refYear':Y,'rkSeason':rkS,'club':club,
      'cncExtra':[{'nom':c[0],'pts':c[3]} for c in U['cnc'] if c[0] not in have],'qualifs':Q,
      'g2':(lambda g:(g.update({'tests':json.load(open('in/tests_g2.json'))['tests']}) if os.path.exists('in/tests_g2.json') else None) or g)(json.load(open('in/groupe2.json'))),'tests':{k:json.load(open(f'in/tests_{k}.json'))['tests'] for k in ('g1','g3','av') if os.path.exists(f'in/tests_{k}.json')},'pts':json.load(open('in/points_ffn.json')),'avRank':(json.load(open('in/av_rank.json')) if os.path.exists('in/av_rank.json') else None)}
rk=json.load(open('in/rankings.json')) if os.path.exists('in/rankings.json') else {}
json.dump({'meta':meta,'swimmers':sw,'rankings':rk},open('site/data.json','w'),ensure_ascii=False,separators=(',',':'))
print('OK',len(sw),'nageurs',sum(len(s['p']) for s in sw),'perfs · club',club)
# copie autonome (un seul fichier, sans connexion requise)
h=open('site/index.html').read()
h=h.replace("const r=await fetch('data.json'); const j=await r.json();","const j=JSON.parse(document.getElementById('data').textContent);")
h=h.replace("<script>\n\"use strict\";",'<script type="application/json" id="data">'+open('site/data.json').read().replace('</','<\\/')+'</script>\n<script>\n"use strict";',1)
open('site/Douai_Natation_1897.html','w').write(h)
print('copie autonome : site/Douai_Natation_1897.html')
# version publique (GitHub Pages) : sans présences, chronos ni minimax du Groupe 2, onglet Entraînement masqué
D=json.load(open('site/data.json')); g=D['meta']['g2']
# version publique : chronos et tests 25 m visibles en mode entraîneur ; ni présences, ni contacts, ni dates de naissance
D['meta']['g2']={'nom':g['nom'],'full':g.get('full',{}),'dates':[],'presences':[],'chronos':[{'n':c['n'],'id':c.get('id'),'t':c['t']} for c in g.get('chronos',[])],'minimax':[],'membres':g.get('membres',[]),'planif':g['planif'],'tests':g.get('tests',[])}
p=open('site/index.html').read()
p=p.replace("const r=await fetch('data.json'); const j=await r.json();","const j=JSON.parse(document.getElementById('data').textContent);")
p=p.replace("<script>\n\"use strict\";",'<script type="application/json" id="data">'+json.dumps(D,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+'</script>\n<script>\n"use strict";',1)
open('site/public_index.html','w').write(p)
print('version publique : site/public_index.html')
# résumé des nouveautés (10 derniers jours) pour le compte rendu hebdomadaire
def ts(t):
    m,r=t.split(':'); return int(m)*60+float(r)
end=U['date']; start=(datetime.date.fromisoformat(end)-datetime.timedelta(days=10)).isoformat()
pbs=[]; qs=[]
for s in sw:
    club=[x for x in s['p'] if not x[8]]  # perfs réalisées sous les couleurs de Douai Natation 1897
    for p in club:
        if not (start<p[4]<=end): continue
        prev=[x for x in club if x[0]==p[0] and x[1]==p[1] and x[4]<=start]
        if prev and ts(p[2])<min(ts(x[2]) for x in prev): pbs.append(f"{s['nom']} · {p[0]} {p[1]}m {p[2]}")
        for q in Q:
            if not q.get('tps') or q['sexe']!=s['sexe'] or not(q['y1']<=s['an']<=q['y2']) or q['epr']!=p[0] or (q['bas']!='tous' and int(q['bas'])!=p[1]): continue
            if ts(p[2])<=ts(q['tps']) and not any(ts(x[2])<=ts(q['tps']) and x[4][:4]==str(Y) for x in prev): qs.append(f"{s['nom']} · {q['comp']} ({q['cat']}) · {p[0]} {p[2]}")
open('site/resume.txt','w').write(f"Records perso battus ({len(pbs)}):\n"+'\n'.join(pbs)+f"\n\nNouveaux temps qualificatifs ({len(set(qs))}):\n"+'\n'.join(sorted(set(qs))))
print('résumé : site/resume.txt')
