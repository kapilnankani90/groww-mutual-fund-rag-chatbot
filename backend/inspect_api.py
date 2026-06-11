import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check ELSS fund (Balanced has lock-in for ELSS type)
# Also check all 5 funds for riskometer
slugs = [
    'icici-prudential-silver-etf-fof-direct-growth',
    'icici-prudential-large-cap-fund-direct-growth',
    'icici-prudential-balanced-direct-growth',
    'icici-prudential-liquid-fund-direct-plan-growth',
    'icici-prudential-corporate-bond-fund-direct-plan-growth',
]

headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

for slug in slugs:
    url = f'https://groww.in/v1/api/data/mf/web/v4/scheme/search/{slug}'
    resp = requests.get(url, headers=headers, timeout=10)
    data = resp.json()
    
    name = data.get('scheme_name', slug)[:60]
    lock_in = data.get('lock_in', {})
    risk = data.get('riskometer') or data.get('risk') or data.get('risk_level') or data.get('groww_rating')
    benchmark = data.get('benchmark_name', '')
    category = data.get('category', '')
    sub_cat = data.get('sub_category', '')
    tax = (data.get('category_info') or {}).get('tax_impact', '')
    
    print(f"Fund: {name}")
    print(f"  lock_in: {lock_in}")
    print(f"  riskometer/risk: {risk}")
    print(f"  benchmark: {benchmark}")
    print(f"  category: {category} / {sub_cat}")
    print(f"  tax_impact: {tax[:100] if tax else 'N/A'}")
    
    # search for riskometer anywhere in response
    txt = json.dumps(data)
    import re
    risko = re.findall(r'"[^"]*[Rr]isk[^"]*"\s*:\s*"[^"]+"', txt)[:3]
    if risko:
        print(f"  risk-related fields: {risko}")
    print()
