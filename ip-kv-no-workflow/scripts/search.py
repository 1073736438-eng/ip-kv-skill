#!/usr/bin/env python3
"""Offline catalog search. No model/API calls."""
import argparse,json,re,unicodedata,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def normalize(value):
    return re.sub(r'[\W_]+', '', unicodedata.normalize('NFKC', value).casefold())


def search(query, business=None, colors=None, atmosphere=None):
    rows = json.loads((ROOT / 'references/catalog.json').read_text())
    q = normalize(query)
    titles = [dict(row, match_stage='title', score=100 if normalize(row['kv_title']) == q else 90)
              for row in rows if q and (q in normalize(row['kv_title']) or normalize(row['kv_title']) in q)]
    if q in {'活动', '大促', '派对', 'kv', '营销', '福利'}:
        titles = []
    if titles:
        return sorted(titles, key=lambda row: -row['score'])
    # Agent supplies semantic business tags; direct title/tag containment is also supported.
    business = business or []
    colors = colors or []
    atmosphere = atmosphere or []
    ranked = []
    for row in rows:
        hits = [tag for tag in row['business_tags'] if normalize(tag) in q or
                any(normalize(term) in normalize(tag) or normalize(tag) in normalize(term)
                    for term in business if normalize(term))]
        if not hits:
            continue
        matched = {}
        for field, requested in [('color_tags', colors), ('atmosphere', atmosphere)]:
            found = [tag for tag in row[field] if any(normalize(term) == normalize(tag) for term in requested)]
            if requested and not found:
                break
            matched[field] = found
        else:
            ranked.append(dict(row, match_stage='business', score=len(hits)*10 + sum(map(len, matched.values())),
                               matches=dict(business_tags=hits, **matched)))
    return sorted(ranked, key=lambda row: -row['score'])



def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--title',required=True)
    for name in ('business','color','atmosphere'):
        p.add_argument('--'+name,action='append',default=[])
    a=p.parse_args()
    try:
        rows=search(a.title,a.business,a.color,a.atmosphere)
        mapping=json.loads((ROOT/'references/asset-map.json').read_text())
        for row in rows:row['image_path']=str(ROOT/mapping[row['asset_id']])
        result={'status':'matched' if rows else 'no_match','route':'reference' if rows else 'fallback','candidates':rows}
        if not rows:
            result['fallback']={'asset_id':'KV_026','image_path':str(ROOT/mapping['KV_026']),'model_policy':'best_available_gpt_image','output_count':2}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status':'error','error':str(error)},ensure_ascii=False),file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
