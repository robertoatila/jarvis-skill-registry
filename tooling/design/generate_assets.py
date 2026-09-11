"""Rebuild original Milestone Zero SVG artwork; standard library only.

Run from any directory: python tooling/design/generate_assets.py
No network, external artwork, runtime execution, or personal memory reads.
"""
from html import escape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
BG, PANEL, LINE = '#080f19', '#101e2e', '#2b455d'
WHITE, MUTED, CYAN, BLUE = '#edf5ff', '#a9bfd1', '#5de0ec', '#84b5ff'
ASSETS = []

def text(x, y, value, size=20, color=WHITE, weight=400, extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" {extra}>{escape(value)}</text>'

def path(d, color=CYAN, width=2, extra=''):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" {extra}/>'

def rect(x, y, w, h, fill=PANEL, stroke=LINE, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" {extra}/>'

def dot(x, y, radius=5, color=CYAN):
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>'

def grid(w, h):
    return '<g opacity="0.22">' + ''.join(path(f'M{x} 0 V{h}', LINE, 1) for x in range(0,w,64)) + ''.join(path(f'M0 {y} H{w}', LINE,1) for y in range(0,h,64)) + '</g>'

def mark(x=0, y=0, scale=1, color=CYAN):
    return (f'<g transform="translate({x} {y}) scale({scale})" stroke="{color}" fill="none" stroke-width="2.5" stroke-linejoin="round">'
            '<path d="M16 3 L28 10 V22 L16 29 L4 22 V10 Z"/>'
            '<path d="M10 11 H21 V19 L16 22 L11 19"/></g>')

def save(rel, w, h, title, desc, body, purpose, source='Original geometric SVG artwork; no third-party visual assets.'):
    dest = ROOT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">'
           f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>'
           '<g font-family="Segoe UI, Arial, sans-serif">' + body + '</g></svg>\n')
    dest.write_text(svg, encoding='utf-8')
    ASSETS.append(dict(path=rel, format='SVG', width=w, height=h, purpose=purpose, source=source))

def canvas(w,h,title,kicker,subtitle):
    return (rect(0,0,w,h,BG,BG) + grid(w,h) + text(48,49,kicker,14,CYAN,600,extra='letter-spacing="2"') +
            text(48,98,title,34,WHITE,600) + text(48,134,subtitle,17,MUTED))

def card(x,y,w,h,title,lines,status='PLANNED'):
    color = CYAN if status == 'VALIDATED / UNIT SCOPE' else BLUE if status == 'PARTIAL' else MUTED
    dash = '' if status == 'VALIDATED / UNIT SCOPE' else 'stroke-dasharray="12 5 2 5"' if status == 'PARTIAL' else 'stroke-dasharray="6 6"'
    body = rect(x,y,w,h,stroke=color,extra=dash)
    body += text(x+22,y+32,status,11,color,600,extra='letter-spacing="1"')
    body += text(x+22,y+66,title,22,WHITE,600)
    for i,line in enumerate(lines):
        body += text(x+22,y+98+i*25,line,16,MUTED)
    return body

def main():
    body = rect(0,0,1400,560,BG,BG)+grid(1400,560)
    body += mark(54,47,1.5) + text(118,79,'INTELLIGENCE, WITH EVIDENCE.',16,CYAN,600,extra='letter-spacing="2"')
    body += text(56,218,'J.A.R.V.I.S.',88,WHITE,600)
    body += text(60,266,'AUTONOMOUS COGNITIVE RUNTIME',23,CYAN,600,extra='letter-spacing="2"')
    body += text(60,326,'A governed path from intent to verified outcomes.',22,MUTED)
    body += path('M60 369 H670',LINE,1)
    for x,y,s in [(60,414,'Skill Registry'),(350,414,'Agent Intelligence'),(60,461,'Persistent Memory'),(350,461,'Verified Execution')]:
        body += dot(x+4,y-7,3) + text(x+20,y,s,19,WHITE)
    body += text(60,522,'PROJECT DIRECTION / SEE ROADMAP FOR IMPLEMENTATION STATUS',11,MUTED,extra='letter-spacing="1"')
    for x,y in [(843,113),(1212,113),(1275,287),(1207,451),(845,451),(780,287)]:
        body += path(f'M1030 280 L{x} {y}',LINE,2)+dot(x,y,6,BLUE)
    body += path('M843 113 H1212 L1275 287 L1207 451 H845 L780 287 Z',BLUE,1,extra='opacity="0.5"')
    body += '<circle cx="1030" cy="280" r="122" fill="#101e2e" stroke="#5de0ec" stroke-width="2"/>'
    body += '<circle cx="1030" cy="280" r="145" fill="none" stroke="#2b455d" stroke-width="1" stroke-dasharray="3 9"/>'
    body += mark(982,225,3) + text(1030,353,'COGNITIVE CORE',14,CYAN,600,extra='text-anchor="middle" letter-spacing="2"')
    body += text(1030,87,'CONTEXT',13,MUTED,600,extra='text-anchor="middle" letter-spacing="2"')
    body += text(1030,496,'MEMORY · ACTION · EVIDENCE',13,MUTED,600,extra='text-anchor="middle" letter-spacing="1"')
    save('.github/assets/jarvis-hero.svg',1400,560,'J.A.R.V.I.S. — Autonomous Cognitive Runtime','Original project banner. Cognitive core illustration communicates the project direction, not implementation completeness.',body,'README hero')

    body=rect(0,0,1200,630,BG,BG)+grid(1200,630)+mark(73,64,2)
    body+=text(74,273,'J.A.R.V.I.S.',100,WHITE,600)+text(78,331,'AUTONOMOUS COGNITIVE RUNTIME',28,CYAN,600)
    body+=path('M78 390 H1105',LINE,2)+text(78,448,'Skill Registry  /  Agent Intelligence',25,WHITE)
    body+=text(78,493,'Persistent Memory  /  Verified Execution',25,WHITE)
    body+=text(78,572,'PROJECT DIRECTION · DEVELOPMENT IN PROGRESS',14,MUTED,extra='letter-spacing="2"')
    body+=mark(959,61,4)
    save('.github/assets/jarvis-social-preview.svg',1200,630,'J.A.R.V.I.S. social preview','Project identity and direction. Development in progress.',body,'Repository social sharing card')
    save('.github/assets/jarvis-mark.svg',32,32,'J.A.R.V.I.S. mark','Original open J geometry within a hexagonal boundary. Cyan on transparent background.',mark(), 'Small identity mark; dark backgrounds')
    save('.github/assets/jarvis-mark-mono.svg',32,32,'J.A.R.V.I.S. monochrome mark','Single dark color on a transparent background; for light surfaces.',mark(color=BG),'Small monochrome identity mark; light backgrounds')

    body=canvas(1200,900,'Runtime architecture','ARCHITECTURE / BASELINE + DIRECTION','Status applies to the stated scope. A passing unit test does not certify runtime integration.')
    cards=[(48,175,'Contracts & graph',['Attempt serialization; DAG invariants','84 selected tests across eight suites'],'VALIDATED / UNIT SCOPE'),
           (424,175,'Execution & evidence',['Policy, state, scheduler, verifier','Adapter and attempt wiring incomplete'],'PARTIAL'),
           (800,175,'Human observability',['HUD and Markdown vault exist','Live behavior not validated here'],'PARTIAL'),
           (48,421,'Cognitive Governor',['Budget, uncertainty and stop policy','Controls decisions; never runs tasks'],'PLANNED'),
           (424,421,'Context & routing',['Context receipts; tool/model choice','Progressive disclosure exists today'],'PLANNED'),
           (800,421,'Memory Fabric',['Working / episodic / semantic','Procedural; validated vault projection'],'PLANNED')]
    for x,y,title,lines,status in cards: body+=card(x,y,352,199,title,lines,status)
    body+=path('M224 390 V408 H976 V390',LINE)+path('M600 408 V421',LINE)
    body+=rect(48,671,1104,88)+text(72,705,'FOUNDATION GATE',14,CYAN,600)+text(72,737,'Versioned contracts → policy → durable attempts → provenance → verification → budgets',20,WHITE)
    body+=text(48,804,'SOLID: validated unit scope     DASH-DOT: partial implementation     DASHED: planned contract',15,MUTED)
    body+=text(48,852,'External workflows, infrastructure and federation remain gated behind local hardening.',17,MUTED)
    save('docs/assets/jarvis-runtime-architecture.svg',1200,900,'Runtime architecture and maturity','Three maturity states distinguish tested unit behavior, partially integrated components and planned cognitive systems. Lines express target dependency, not live data flow.',body,'Architecture overview')

    body=canvas(1200,740,'The cognitive execution loop','TARGET LIFECYCLE / NOT LIVE TELEMETRY','A verified outcome and a bounded learning step close the loop.')
    names=['OBSERVE','PLAN','RESOLVE','DELEGATE','EXECUTE','VERIFY','MEASURE','LEARN','ADAPT']
    descs=['Read state and intent','Build a scoped DAG','Select admissible resources','Assign bounded work','Record a real attempt','Check independent evidence','Record actual resource use','Admit supported knowledge','Promote bounded changes']
    for i,(name,desc) in enumerate(zip(names,descs)):
        row,col=divmod(i,3); x=48+col*376;y=175+row*153
        body+=rect(x,y,352,123,stroke=LINE)+text(x+20,y+29,f'0{i+1}',12,CYAN,600)+text(x+20,y+60,name,22,WHITE,600)+text(x+20,y+92,desc,16,MUTED)
        if col<2:body+=path(f'M{x+352} {y+57} h24',CYAN)
    body+=text(48,687,'Governor: inspect uncertainty → buy the cheapest useful evidence → continue, replan or stop.',17,CYAN)
    save('docs/assets/jarvis-cognitive-loop.svg',1200,740,'Target cognitive loop','Nine sequential numbered stages from observe to adapt. This is a target lifecycle, not evidence of an operational closed loop.',body,'Cognitive lifecycle diagram')

    body=canvas(1200,870,'Memory, with admission and provenance','MEMORY FABRIC / PLANNED TARGET','Validated machine records are authoritative. Obsidian is the human-readable projection.')
    for i,(title,lines) in enumerate([
        ('Working',['Transient mission context','Compact structured state']),('Episodic',['Attempts and decisions','Outcomes and recovery']),
        ('Semantic',['Repository / environment','Facts, scope and freshness']),('Procedural',['Verified workflows','Heuristics and promotion'])]):
        body+=card(48+i*282,181,258,207,title,lines)
    body+=rect(48,427,1104,83)+text(70,460,'ADMIT',14,CYAN,600)+text(70,488,'Value → evidence → provenance → confidence → deduplicate → conflict check → classify → store',17,WHITE)
    body+=rect(48,530,1104,83)+text(70,563,'RETRIEVE',14,CYAN,600)+text(70,591,'Exact ID → repository graph → metadata → lexical → semantic → broader search',18,WHITE)
    body+=path('M600 389 V427 M600 510 V530 M600 613 V651',CYAN)
    body+=rect(48,651,534,102)+text(70,686,'COMPACT & VALIDATE',14,CYAN,600)+text(70,720,'Facts + references; retain the separate audit trail',17,WHITE)
    body+=rect(610,651,542,102)+text(632,686,'PROJECT TO OBSIDIAN',14,CYAN,600)+text(632,720,'Aggregate → validate → publish navigable notes',17,WHITE)
    body+=text(48,816,'Freshness, scope, environment and contradiction history travel with every durable record.',17,MUTED)
    save('docs/assets/jarvis-memory-fabric.svg',1200,870,'Planned Memory Fabric','Four planned memory levels with admission, ordered retrieval, compaction, validation and an Obsidian projection. Existing vault support is not this complete architecture.',body,'Memory architecture diagram')

    moc=ROOT/'00 - J.A.R.V.I.S. Cognitive Vault.md'
    content=moc.read_text(encoding='utf-8-sig')
    choices=[('01','Skill catalog'),('02','Security ledger'),('03','Platform matrix'),('04','Ingestion & staging'),('09','Token budget'),('10','System architecture'),('11','Agent squads'),('15','Automation pipeline'),('17','Security protocol'),('18','Engine comparisons')]
    mapping=[]
    for number,label in choices:
        names=[p for p in ROOT.glob(f'{number} - *.md') if p.stem in content]
        if len(names)!=1: raise ValueError(f'Ambiguous or missing existing MOC link: {number}')
        mapping.append(dict(number=number,label=label,path=names[0].name))
    body=canvas(1200,840,'A navigable cognitive vault','EXISTING NOTES / DOCUMENT NAVIGATION MAP','Derived from ten existing links in the root MOC. This is a diagram, not an Obsidian screenshot.')
    body+=rect(400,179,400,94,stroke=CYAN)+text(600,217,'00 / MASTER MAP OF CONTENT',17,CYAN,600,extra='text-anchor="middle"')+text(600,248,'Markdown entry point',18,WHITE,extra='text-anchor="middle"')
    body+=path('M600 273 V308 M148 308 H1052',LINE)
    # Both rows branch from the MOC; no topic note is drawn as another's parent.
    body+=path('M600 308 H26 V500 H1052',LINE)
    for col in range(5):
        body+=path(f'M{148+col*226} 308 V345 M{148+col*226} 500 V537',LINE)
    for i,item in enumerate(mapping):
        row,col=divmod(i,5);x=48+col*226;y=345+row*192
        body+=rect(x,y,204,137)+text(x+18,y+32,item['number']+' / EXISTING NOTE',11,CYAN,600)
        for j,wordline in enumerate([item['label']] if len(item['label'])<20 else ['Engine','comparisons']):body+=text(x+18,y+72+j*24,wordline,17,WHITE,600)
        body+=text(x+18,y+116,'MOC navigation link',12,MUTED)
    body+=text(48,744,'Note presence is verified. Historical claims inside each note are not recertified by this map.',16,MUTED)
    body+=text(48,788,'Next: aggregated missions, decisions and verified learnings projected from structured memory.',16,CYAN)
    save('docs/assets/jarvis-cognitive-vault.svg',1200,840,'Existing cognitive vault navigation','Faithful diagram of ten existing root MOC links. No live application screenshot, personal memory content, or inferred semantic relationships.',body,'Faithful representation of existing vault navigation','Existing root MOC links and note filenames; original diagram. See vault-map-sources.json.')
    (ROOT/'docs/assets/vault-map-sources.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
    (ROOT/'docs/assets/asset-manifest.json').write_text(json.dumps(ASSETS,indent=2),encoding='utf-8')
    print(f'Generated {len(ASSETS)} original SVG assets.')

if __name__=='__main__':main()
