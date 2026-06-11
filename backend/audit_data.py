import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('data/mutual_funds_corpus.json', 'r', encoding='utf-8') as f:
    corpus = json.load(f)

print(f'Total funds: {len(corpus)}\n')
for item in corpus:
    text = item.get('raw_text', '')
    title = item.get('title', '')[:55]
    # Check if expense ratio VALUE is present (a % number near 'Expense ratio')
    exp_match = re.search(r'Expense ratio[\s\S]{0,80}?(\d+\.\d+%)', text)
    # Check if min investment value is present
    min_match = re.search(r'Min\. for 1st investment[\s\S]{0,60}?(\u20b9[\d,]+)', text)
    # Check if fund manager name exists
    mgr_match = re.search(r'Fund management\n([A-Z][a-z]+ [A-Z][a-z]+)', text)
    print(f'{title:56s} | Exp%: {exp_match.group(1) if exp_match else "MISSING":8s} | Min: {min_match.group(1) if min_match else "MISSING":10s} | Mgr: {"YES" if mgr_match else "NO"}')
