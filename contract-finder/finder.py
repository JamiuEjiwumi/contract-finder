#!/usr/bin/env python3
"""Search-index candidate discovery; never claims a vacancy is verified live."""
import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROLE = r'\b(devops|platform engineer|site reliability|sre|cloud engineer|azure engineer|aws engineer)\b'
PART = r'\b(part[ -]?time|fractional|[1-3]\s*days?\s*(?:per|a|/)\s*week|evening|weekend)\b'
OUTSIDE = r'\boutside[ -]*(?:of\s+)?ir35\b'
REMOTE = r'\b(remote|work from home|home[ -]based)\b'
EXCLUDE = r'\b(full[ -]?time|inside[ -]*ir35|hybrid|on[ -]?site|expired|position filled|no longer available|not remote)\b'

def classify(title, description):
    text = html.unescape(re.sub('<[^>]+>', ' ', title + ' ' + description)).lower()
    evidence = {k: (m.group(0) if (m := re.search(p, text)) else None)
                for k, p in [('role', ROLE), ('part_time', PART), ('outside_ir35', OUTSIDE), ('remote', REMOTE)]}
    if re.search(EXCLUDE, text):
        return 'excluded', evidence
    return ('candidate' if all(evidence.values()) else 'unconfirmed'), evidence

def canonical(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password:
        return None
    query = [(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith('utm_') and k.lower() not in ('gclid','fbclid')]
    return urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip('/'), urllib.parse.urlencode(sorted(query)), ''))

def search(query, key):
    params = urllib.parse.urlencode({'q':query,'country':'GB','search_lang':'en','count':20,'freshness':'pm','extra_snippets':'true'})
    for attempt in range(4):
        req = urllib.request.Request('https://api.search.brave.com/res/v1/web/search?' + params, headers={'X-Subscription-Token':key,'Accept':'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response).get('web', {}).get('results', [])
        except urllib.error.HTTPError as error:
            if error.code not in (429,500,502,503,504) or attempt == 3:
                raise RuntimeError(f'Search API failed with HTTP {error.code}; response omitted to protect credentials') from None
            time.sleep(min(30, 2 ** (attempt + 1)))
    return []

def cell(value):
    return html.escape(str(value)).replace('|','&#124;').replace('\n',' ')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', help='Offline JSON search results for testing')
    args = parser.parse_args()
    cfg = json.loads(Path('config.json').read_text())
    state_path = Path('state/seen.json')
    seen = json.loads(state_path.read_text()) if state_path.exists() else {}
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    results = []
    if args.fixture:
        results = json.loads(Path(args.fixture).read_text())
    else:
        key = os.environ.get('BRAVE_SEARCH_API_KEY')
        if not key:
            raise SystemExit('Set BRAVE_SEARCH_API_KEY in GitHub Actions secrets or your local environment.')
        for query in cfg['queries']:
            results.extend(search(query, key))
            time.sleep(1.1)
    rows = {}
    for result in results:
        url = canonical(result.get('url',''))
        if not url:
            continue
        title = result.get('title','')
        description = ' '.join([result.get('description',''), *result.get('extra_snippets',[])])
        status, evidence = classify(title, description)
        if status == 'excluded' or not evidence['role']:
            continue
        row = {'title':title,'url':url,'status':status,'evidence':evidence,'snippet':description,
               'new':url not in seen,'first_seen':seen.get(url,now),'last_discovered':now,
               'vacancy_status':'Not verified; inspect original advert', 'index_age':result.get('age')}
        if url not in rows or status == 'candidate':
            rows[url] = row
    items = sorted(rows.values(), key=lambda r:(r['status'] != 'candidate',not r['new'],r['title']))
    for row in items:
        seen.setdefault(row['url'],now)
    Path('reports').mkdir(exist_ok=True)
    Path('state').mkdir(exist_ok=True)
    state_path.write_text(json.dumps(seen,indent=2))
    Path('reports/results.json').write_text(json.dumps({'searched_at':now,'results':items},indent=2))
    lines = ['# Part-time remote outside-IR35 contract candidates', '', f'Searched at: {now}', '',
             '**Search-index evidence only. Vacancy availability, rates, weekly hours and IR35 status require confirmation on the original advert.**', '',
             'Ambiguous or conflicting adverts are excluded or separated. Fractional/evening/weekend wording is a lead, not proof of contractual hours. No applications are submitted.', '']
    for status, heading in [('candidate','Matching candidates'),('unconfirmed','Unconfirmed — not part of the shortlist')]:
        lines += ['## '+heading,'','| Role | New | Evidence | Advert |','|---|---|---|---|']
        selected = [r for r in items if r['status']==status][:cfg['max_results_per_section']]
        for r in selected:
            evidence = '; '.join(f'{k}: {v or "unconfirmed"}' for k,v in r['evidence'].items())
            # HTML anchors avoid Markdown URL delimiter injection from external results.
            lines.append(f'| {cell(r["title"])} | {"Yes" if r["new"] else "Seen before"} | {cell(evidence)} | <a href="{html.escape(r["url"],quote=True)}">Open advert</a> |')
        if not selected:
            lines.append('| No results | — | No matching evidence this run | — |')
        lines.append('')
    Path('reports/shortlist.md').write_text('\n'.join(lines))
    print(f'Found {sum(r["status"]=="candidate" for r in items)} candidates and {sum(r["status"]=="unconfirmed" for r in items)} unconfirmed leads.')

if __name__ == '__main__':
    main()
