import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

syllabi = json.load(open('data/syllabi.json','r',encoding='utf-8'))
total_cur = 0; total_target = 0
print(f"{'考纲':20s} {'当前':>5s} {'目标':>5s} {'缺口':>5s}  {'进度'}")
print('-'*60)
for s in syllabi:
    bf = s.get('question_bank','')
    if not bf: continue
    path = f'data/{bf}'
    cur = len(json.load(open(path,'r',encoding='utf-8'))) if os.path.exists(path) else 0
    target = s.get('target_count',1000)
    gap = max(0, target-cur)
    pct = f'{cur/target*100:.0f}%'
    done = '#' * int(cur/target*20) if target else ''
    left = '.' * max(0, 20-len(done))
    print(f'{s["name"]:20s} {cur:>5d}  {target:>5d}  {gap:>5d}  {pct:>4s} {done}{left}')
    total_cur += cur; total_target += target
print('-'*60)
print(f'{"合计":20s} {total_cur:>5d}  {total_target:>5d}  {max(0,total_target-total_cur):>5d}  {total_cur/total_target*100:.0f}%')
