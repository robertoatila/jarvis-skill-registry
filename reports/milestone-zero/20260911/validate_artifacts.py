"""Validate M0 deliverables against preserved source and captured unit evidence."""
from pathlib import Path
import ast
from datetime import datetime, timezone
import hashlib
import json
import re
import struct
import subprocess
from urllib.parse import unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def readjson(p):
    return json.loads(p.read_text(encoding='utf-8'))

def contrast(a,b):
    def luminance(s):
        vals=[int(s[i:i+2],16)/255 for i in (1,3,5)]
        vals=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in vals]
        return sum(v*c for v,c in zip(vals,(0.2126,0.7152,0.0722)))
    x,y=sorted((luminance(a),luminance(b)))
    return round((y+0.05)/(x+0.05),2)

def main():
    errors=[]
    baseline=readjson(OUT/'baseline.json')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if head!=baseline['head']:errors.append('HEAD changed')
    changed=[r for r,h in baseline['source_hashes'].items() if sha(ROOT/r)!=h]
    if changed:errors.append('Runtime/test sources changed: '+str(changed))
    for e in baseline['backups']:
        if sha(ROOT/'backups/milestone-zero-20260911'/e['path'])!=e['sha256']:
            errors.append('Backup mismatch '+e['path'])
    suites=readjson(OUT/'tests.json')
    for s in suites:
        if s['exit_code'] or s['tests']<1 or sha(OUT/s['output'])!=s['sha256']:
            errors.append('Invalid test evidence '+s['suite'])
    total=sum(s['tests'] for s in suites)
    if len(suites)!=8 or total!=84:errors.append('Unexpected test scope')
    assets=readjson(ROOT/'docs/assets/asset-manifest.json')
    records=[]
    for asset in assets:
        p=ROOT/asset['path']; tree=ET.parse(p); node=tree.getroot()
        ns='{http://www.w3.org/2000/svg}'
        if node.find(ns+'title') is None or node.find(ns+'desc') is None:errors.append('Missing SVG accessibility metadata '+str(p))
        for el in node.iter():
            if el.tag.rsplit('}',1)[-1] in ('script','foreignObject','image'):errors.append('Unexpected active/external SVG element '+str(p))
            if any(k.startswith('on') or k.endswith('href') for k in el.attrib):errors.append('Unexpected SVG event/link '+str(p))
        if (int(node.attrib['width']),int(node.attrib['height']))!=(asset['width'],asset['height']):errors.append('SVG dimensions mismatch')
        for ext in ('.svg','.png'):
            f=p.with_suffix(ext);data=f.read_bytes()
            if ext=='.png':
                assert data[:8]==b'\x89PNG\r\n\x1a\n'
                if struct.unpack('>II',data[16:24])!=(asset['width'],asset['height']):errors.append('PNG dimensions mismatch '+str(f))
            if len(data)>1_000_000:errors.append('Asset exceeds 1 MB '+str(f))
            records.append(dict(path=f.relative_to(ROOT).as_posix(),sha256=sha(f),bytes=len(data),width=asset['width'],height=asset['height']))
    if len(assets)!=8:errors.append('Expected eight SVG sources')
    docs=['README.md','docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md','docs/assets/ASSET_PROVENANCE.md','reports/MILESTONE_ZERO.md']
    link_count=0
    for rel in docs:
        p=ROOT/rel;s=p.read_text(encoding='utf-8')
        s=re.sub(r'```.*?```','',s,flags=re.S)
        targets=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',s)+re.findall(r'src="([^"]+)"',s)
        for dest in targets:
            if dest.startswith(('https:','http:','mailto:')):continue
            pathpart,_,anchor=dest.partition('#')
            target=(p.parent/unquote(pathpart)).resolve() if pathpart else p
            # The output manifest is written at the end of this check.
            if target==OUT/'artifact-validation.json':continue
            if not target.exists():errors.append(f'Broken link: {rel} -> {dest}')
            elif anchor and target.suffix=='.md':
                headings=re.findall(r'^#+\s+(.+)$',target.read_text(encoding='utf-8'),re.M)
                slugs=[re.sub(r'[^\w\- ]','',h.lower()).replace(' ','-') for h in headings]
                if anchor not in slugs:errors.append(f'Missing anchor: {rel} -> {dest}')
            link_count+=1
    plan=(ROOT/docs[1]).read_text(encoding='utf-8')
    sections=re.findall(r'^## (\d+)\. (.+)$',plan,re.M)
    if [int(n) for n,_ in sections]!=list(range(1,28)):errors.append('Roadmap section sequence incomplete')
    phase_ids=re.findall(r'^\| (\d{2}) ',plan,re.M)
    if phase_ids!=[f'{i:02}' for i in range(55)]:errors.append('Phase sequence incomplete')
    for section in re.split(r'^## \d+\. ',plan,flags=re.M)[1:]:
        for field in ['**Status:**','**Priority:**','**Requires:**','**Unlocks:**','**Risk:**','**Evidence Required:**']:
            if field not in section:errors.append('Missing section metadata '+field)
    # Bound the main typed dependency diagram; assert its graph is acyclic.
    mermaid=re.search(r'```mermaid\n(.*?)```',plan,re.S).group(1)
    edges=re.findall(r'^\s*(\w+)(?:\[[^\]]*\])?\s*-->\s*(\w+)',mermaid,re.M)
    graph={n:[] for e in edges for n in e}
    for a,b in edges:graph[a].append(b)
    seen=set();active=set()
    def visit(n):
        if n in active:raise ValueError('Cycle in roadmap diagram')
        if n in seen:return
        active.add(n)
        for c in graph[n]:visit(c)
        active.remove(n);seen.add(n)
    for n in graph:visit(n)
    moc=(ROOT/'00 - J.A.R.V.I.S. Cognitive Vault.md').read_text(encoding='utf-8')
    for entry in readjson(ROOT/'docs/assets/vault-map-sources.json'):
        if not (ROOT/entry['path']).exists() or Path(entry['path']).stem not in moc:errors.append('Vault source missing')
    for rel in ['tooling/design/generate_assets.py','reports/milestone-zero/20260911/recover_and_validate.py','reports/milestone-zero/20260911/validate_artifacts.py']:
        ast.parse((ROOT/rel).read_text(encoding='utf-8'),filename=rel)
    ratios={f'{fg} on {bg}':contrast(fg,bg) for fg in ['#edf5ff','#a9bfd1','#5de0ec','#84b5ff'] for bg in ['#080f19','#101e2e']}
    if min(ratios.values())<4.5:errors.append('Primary palette text contrast below 4.5')
    diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    if diff.returncode:errors.append('git diff --check: '+diff.stdout+diff.stderr)
    record=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),head=head,status='PASS' if not errors else 'FAIL',
        errors=errors,selected_test_count=total,selected_suite_count=len(suites),runtime_and_test_sources_unchanged=not changed,
        source_files_reverified=len(baseline['source_hashes']),original_backups_reverified=len(baseline['backups']),
        asset_sources=len(assets),asset_files=records,roadmap_sections=len(sections),roadmap_phases=len(phase_ids),
        dependency_diagram_acyclic=True,local_document_links_checked=link_count,palette_text_contrast=ratios,
        notes=['Local document paths and specified heading anchors checked; external URLs not fetched.',
               'SVG/XML, dimensions, hashes and contrast checks do not certify the live HUD.',
               'Only selected runtime tests were run; full system and external integrations remain unverified.'])
    (OUT/'artifact-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k not in ('asset_files','palette_text_contrast','notes')},indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
