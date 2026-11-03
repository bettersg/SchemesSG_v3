"""Run real /content-check POST requests for previously failed scheme candidates.

WARNING: This is NOT a dry run. The endpoint may update Firestore baselines,
create contentChecks records, and invoke the AI reviewer.

The Firestore failure streak does not record failure reasons. Use --ids-file
for a verified list of missing-main-content failures, or --failed-from-firestore
to test all schemes with a positive failure streak (not exclusively main failures).

Example (from the host):
  python test_missing_main_content_post.py --failed-from-firestore --limit 20 --processor-url http://localhost:8081 --execute
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
from app.clients.firestore import get_firestore_client


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--ids', nargs='+', help='Verified scheme IDs')
    group.add_argument('--ids-file', help='File with one verified scheme ID per line')
    group.add_argument('--failed-from-firestore', action='store_true',
                       help='All positive failure streaks, NOT just missing-main failures')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--processor-url', default=os.getenv('PROCESSOR_SERVICE_URL', 'http://localhost:8081'))
    p.add_argument('--timeout', type=int, default=300)
    p.add_argument('--output', default='missing_main_content_post_results.json')
    p.add_argument('--execute', action='store_true', help='Required to send mutating POST requests')
    return p.parse_args()


def get_ids(args):
    if args.ids:
        return list(dict.fromkeys(args.ids))[:args.limit]
    if args.ids_file:
        lines = Path(args.ids_file).read_text(encoding='utf-8').splitlines()
        return list(dict.fromkeys(s.strip() for s in lines if s.strip() and not s.lstrip().startswith('#')))[:args.limit]
    db = get_firestore_client()
    if db is None:
        raise RuntimeError('Firestore client initialization failed')
    # Stream and filter in Python to avoid requiring a composite index.
    ids = []
    for doc in db.collection('schemes').stream():
        data = doc.to_dict() or {}
        if (data.get('content_check_fail_streak') or 0) > 0:
            ids.append(doc.id)
            if len(ids) >= args.limit:
                break
    return ids


def main():
    args = parse_args()
    if args.limit < 1:
        raise SystemExit('--limit must be positive')
    ids = get_ids(args)
    url = args.processor_url.rstrip('/') + '/content-check'
    print(f'Found {len(ids)} candidate schemes; endpoint={url}', flush=True)
    if args.failed_from_firestore:
        print('WARNING: positive failure streak includes other failure reasons.', flush=True)
    if not args.execute:
        print('Preview only. Pass --execute to send POST requests that may modify Firestore.', flush=True)
        for scheme_id in ids:
            print(scheme_id)
        return
    results = []
    for i, scheme_id in enumerate(ids, 1):
        try:
            response = requests.post(url, json={'scheme_ids': [scheme_id]},
                                     headers={'Content-Type': 'application/json'},
                                     timeout=args.timeout)
            response.raise_for_status()
            payload = response.json()
            matches = payload.get('results') or []
            if not matches:
                raise ValueError(f'No results in endpoint response: {str(payload)[:300]}')
            item = matches[0]
            item = {'scheme_id': scheme_id, 'outcome': item.get('outcome'),
                    'detail': item.get('detail'), 'check_id': item.get('check_id')}
        except (requests.RequestException, ValueError) as exc:
            item = {'scheme_id': scheme_id, 'outcome': 'request_error', 'detail': str(exc)[:500]}
        results.append(item)
        print(f'[{i}/{len(ids)}] {json.dumps(item, ensure_ascii=False)}', flush=True)
        Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Saved {len(results)} results to {args.output}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Test setup failed: {exc}', file=sys.stderr)
        raise SystemExit(1)
