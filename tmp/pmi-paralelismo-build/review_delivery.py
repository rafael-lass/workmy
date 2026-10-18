"""Auditoria de leitura dos artefatos entregues; não altera código ou apresentação."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from statistics import median
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'docs/evidencias/pmi-paralelismo-2026-10-13'
OUT = EVIDENCE / 'revisao'
OUT.mkdir(exist_ok=True)
deck = ROOT / 'output/pmi-paralelismo/WorkMy_Paralelismo_PMI_15-10-2026_Leonardo.pptx'
ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
slides = []
with ZipFile(deck) as archive:
    for i in range(1, 13):
        root = ET.fromstring(archive.read(f'ppt/slides/slide{i}.xml'))
        paragraphs = [''.join(p.itertext()) for p in []]
        paragraphs = [''.join(t.text or '' for t in p.findall('.//a:t', ns))
                      for p in root.findall('.//a:p', ns)]
        slides.append({'slide': i, 'text': [p for p in paragraphs if p]})
version = json.loads((EVIDENCE / 'versao.json').read_text(encoding='utf-8-sig'))
hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
          for name in version['sha256']}
source_matches = {name: hashes[name] == expected for name, expected in version['sha256'].items()}
bench = json.loads((EVIDENCE / 'comparacao-pool.json').read_text(encoding='utf-8'))
seq = [r['wall_time_seconds'] for r in bench['runs'] if r['mode'] == 'sequential']
par = [r['wall_time_seconds'] for r in bench['runs'] if r['mode'] == 'parallel']
tests = {}
for filename in ('testes-backend.xml', 'testes-frontend.xml'):
    root = ET.parse(OUT / filename).getroot()
    suites = list(root.iter('testsuite'))
    tests[filename] = {
        'suites': [s.attrib for s in suites],
        'skipped': [{'name': case.attrib['name'], 'reason': case.find('skipped').attrib}
                    for case in root.iter('testcase') if case.find('skipped') is not None],
    }
result = {
    'review_date': '2026-10-13', 'presentation_sha256': hashlib.sha256(deck.read_bytes()).hexdigest(),
    'source_matches_recorded_version': source_matches,
    'slides': slides, 'tests': tests,
    'benchmark_recalculated': {
        'sequential_median': median(seq), 'parallel_median': median(par),
        'saved_seconds': median(seq) - median(par),
        'reduction_percent': 100 * (1 - median(par) / median(seq)),
        'speedup': median(seq) / median(par),
        'sequential_range': [min(seq), max(seq)], 'parallel_range': [min(par), max(par)],
        'content_equal_all_runs': all(r['content_sha256'] == bench['runs'][0]['content_sha256'] for r in bench['runs']),
    },
    'performance_rerun_this_review': False,
    'native_powerpoint_open_verified': False,
}
(OUT / 'auditoria.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'slides'}, ensure_ascii=False, indent=2))
