"""
多考纲题库批量生成脚本 v2
读取 syllabi.json，自动计算差值，向目标题量（target_count）生成题目。

用法:
  python scripts/seed_all_banks.py                    # 全部考纲
  python scripts/seed_all_banks.py cet4               # 只生成 CET-4
  python scripts/seed_all_banks.py --dry              # 预览
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, re, time, io, uuid, argparse
from pathlib import Path
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from agents.llm_client import call_llm
from logging_config import logger

DATA_DIR = Path(__file__).parent.parent / "data"
BATCH_SIZE = 6

def extract_json_array(text):
    """用括号计数提取最外层 JSON 数组，正确处理嵌套 []"""
    start = text.find('[')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

# ──── 各题型 prompt ────

def build_prompt(syllabus, dim, sub, kp_name, count, qtype):
    dim_name = dim["name"]
    base = f"""你是 {syllabus['name']} 题库出题专家。生成 {count} 道 {qtype_map(qtype)}。考纲:{syllabus['name']} 维度:{dim_name} 子分类:{sub} 知识点:{kp_name} 难度3-8随机。每题返回严格JSON数组。"""

    if qtype in ('choice','choice_single'):
        return base + "每题4选项A/B/C/D，干扰项有迷惑性，答案写字母，解析详细。格式:{id, category, sub_category, kp_name, question_type:'choice', difficulty, content:{stem, options:[...]}, answer:'A', explanation:'...'}"
    if qtype == 'choice_multi':
        return base + "每题4选项，2-3个正确答案，答案写字母数组。格式:{..., question_type:'choice_multi', answer:['A','C'], ...}"
    if qtype == 'fill':
        return base + "答案简短单词或短语。格式:{..., question_type:'fill', content:{stem}, answer:'word', ...}"
    if qtype == 'cloze':
        return base + "一段话含2-3个空，答案数组。格式:{..., question_type:'cloze', content:{stem, options:[...]}, answer:['w1','w2'], ...}"
    if qtype == 'translation':
        return base + "给中文译英文（或反之）。格式:{..., question_type:'translation', content:{stem}, answer:'参考译文', ...}"
    if qtype == 'essay':
        return base + "命题作文题，答案给范文要点。格式:{..., question_type:'essay', content:{stem}, answer:'范文', ...}"
    if qtype == 'short_answer':
        return base + "简答题，答案2-3句。格式:{..., question_type:'short_answer', content:{stem}, answer:'要点', ...}"
    if qtype == 'calculation':
        return base + "数学计算题，答案数值或表达式。格式:{..., question_type:'calculation', content:{stem}, answer:'42', ...}"
    if qtype == 'programming':
        return base + f"""洛谷/ACM风格编程题。严禁在题目文本中写入任何元描述（如\"本题难度\"\"本题考察\"\"洛谷风格\"等）。
每题包含独立字段:
- content.stem: 纯题目描述+背景（不含输入输出格式）
- content.input_description: 输入格式说明
- content.output_description: 输出格式说明
- content.constraints: 数据范围
- content.test_cases: [{{input:'样例输入', output:'样例输出', description:'说明'}}, ...] 至少3组
- answer: Python3参考代码
格式:{{id, category, sub_category, kp_name, question_type:'programming', difficulty, topic:'{sub}', content:{{stem:'...', input_description:'...', output_description:'...', constraints:'...', test_cases:[{{...}}]}}, answer:'...'}}
题目描述简洁清晰，不包含解题思路或算法提示。难度3-5=普及 6-7=提高 8=省选/NOI-"""
    if qtype in ('case_analysis','teaching_design','analysis'):
        return base + "案例分析/论述题。格式:{..., content:{stem}, answer:'参考要点', ...}"
    return base

def qtype_map(t):
    return {'choice':'单选题','choice_single':'单选题','choice_multi':'多选题','choice_indefinite':'不定项',
            'fill':'填空题','cloze':'完形填空','translation':'翻译题','essay':'作文','short_answer':'简答',
            'calculation':'计算题','programming':'编程题','case_analysis':'案例分析',
            'teaching_design':'教学设计','analysis':'论述分析'}.get(t,t)


def load_questions(bank_file):
    path = DATA_DIR / bank_file
    if path.exists():
        try: return json.loads(path.read_text(encoding='utf-8'))
        except: return []
    return []

def save_questions(bank_file, questions):
    path = DATA_DIR / bank_file
    existing = load_questions(bank_file)
    seen = {q['id'] for q in existing}
    added = 0
    for q in questions:
        if q['id'] not in seen:
            existing.append(q)
            seen.add(q['id'])
            added += 1
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
    return added, len(existing)


def generate_for_syllabus(syllabus):
    sid = syllabus['id']
    bank_file = syllabus.get('question_bank')
    if not bank_file:
        print(f"  [{sid}] 无 question_bank，跳过")
        return []

    current = load_questions(bank_file)
    current_count = len(current)
    target = syllabus.get('target_count', 1000)
    needed = target - current_count

    if needed <= 0:
        print(f"  [{sid}] 已有 {current_count} 题，达标 ✅")
        return []

    dims = [d for d in syllabus.get('dimensions', []) if not d.get('grey')]
    types = syllabus.get('question_types_enabled', syllabus.get('question_types', []))
    diagnosis = syllabus.get('diagnosis_config', [])

    if not dims:
        print(f"  [{sid}] 无可用维度，跳过")
        return []

    per_dim = needed // len(dims) + 5
    all_new = []
    total_added = 0

    for dim in dims:
        dim_name = dim['name']
        # 找该维度下已有的子分类
        subs = list({d['sub'] for d in diagnosis if d['category'] == dim['category']})
        if not subs:
            subs = [dim_name + '基础', dim_name + '进阶']

        dim_done = 0
        attempts = 0

        while dim_done < per_dim and attempts < per_dim // BATCH_SIZE + 10:
            sub = subs[dim_done % len(subs)]
            qtype = types[dim_done % len(types)]
            n = min(BATCH_SIZE, per_dim - dim_done)
            kp = sub
            attempts += 1

            prompt = build_prompt(syllabus, dim, sub, kp, n, qtype)
            try:
                resp = call_llm([{"role":"user","content":prompt}], temperature=0.7)
                # 去掉 markdown 代码块标记
                cleaned = resp.strip()
                cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'\n?```\s*$', '', cleaned, flags=re.MULTILINE)
                # 括号计数提取外层数组（正确处理嵌套）
                raw_json = extract_json_array(cleaned)
                if not raw_json:
                    raw_json = extract_json_array(resp)  # fallback: 原始响应
                if not raw_json:
                    # 可能是截断 — 尝试补全
                    last_brace = cleaned.rfind('}')
                    last_bracket = cleaned.rfind(']')
                    if last_brace > 0:
                        try_fix = cleaned[:last_brace+1] + ']'
                        if try_fix.count('[') == try_fix.count(']'):
                            raw_json = try_fix
                    if not raw_json:
                        print(f"    [{sid}] JSON提取失败 len={len(resp)} truncated={not resp.rstrip().endswith(']')}")
                        continue
                # 尝试解析并修复常见错误
                batch = None
                try:
                    batch = json.loads(raw_json)
                except json.JSONDecodeError as e:
                    # 修复尾逗号
                    fixed = re.sub(r',\s*([}\]])', r'\1', raw_json)
                    fixed = re.sub(r'//[^\n]*', '', fixed)
                    try:
                        batch = json.loads(fixed)
                    except json.JSONDecodeError:
                        # 逐字符回退处理截断
                        for cut in range(len(fixed)-1, max(len(fixed)-500, 0), -1):
                            if fixed[cut] in '}]':  # 在结构边界切
                                try:
                                    batch = json.loads(fixed[:cut+1] + ']')
                                    break
                                except json.JSONDecodeError:
                                    continue
                        if not batch:
                            print(f"    [{sid}] JSON修复后仍失败 raw[:200]={raw_json[:200]!r}")
                            pass
                if not batch:
                    print(f"    [{sid}] batch=None after all attempts")
                    continue
                if not isinstance(batch, list):
                    print(f"    [{sid}] batch is not list, type={type(batch).__name__}")
                    continue
                # 过滤掉非 dict 的条目
                clean_batch = [q for q in batch if isinstance(q, dict)]
                if not clean_batch: continue
                for q in clean_batch:
                    q['id'] = str(uuid.uuid4())
                    q['category'] = dim['category']
                    q['sub_category'] = sub
                    q['kp_name'] = kp
                    q['question_type'] = qtype
                    q['difficulty'] = max(3, min(8, (dim_done % 6) + 3))
                added, total_now = save_questions(bank_file, clean_batch)
                dim_done += added
                total_added += added
                print(f"    [{sid}] {dim_name} {dim_done}/{per_dim} (总{total_now})")
                time.sleep(1.5)
            except Exception as e:
                print(f"    [{sid}] {dim_name} 出错: {e}")
                time.sleep(5)

    return all_new


# ──── main ────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("targets", nargs="*", default=None)
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()

    syllabi = json.loads((DATA_DIR / "syllabi.json").read_text(encoding='utf-8'))

    if args.targets:
        target_syllabi = [s for s in syllabi if s['id'] in args.targets]
    else:
        target_syllabi = [s for s in syllabi if s.get('question_bank')]

    if args.dry:
        total_needed = 0
        for s in target_syllabi:
            cur = len(load_questions(s.get('question_bank','')))
            target = s.get('target_count',1000)
            need = max(0, target - cur)
            dims = [d for d in s.get('dimensions',[]) if not d.get('grey')]
            total_needed += need
            print(f"  {s['id']:20s} {cur:4d}/{target:<4d} 需{need:4d}题  {len(dims)}维度  {', '.join(d['name'] for d in dims)}")
        print(f"\n  总计需生成: {total_needed} 题")
        sys.exit(0)

    total = 0
    for s in target_syllabi:
        cur = len(load_questions(s.get('question_bank','')))
        target = s.get('target_count',1000)
        need = max(0, target - cur)
        if need <= 0:
            print(f"\n{s['name']}: {cur}/{target} ✅ 已达标")
            continue
        print(f"\n{'='*60}")
        print(f"{s['name']} ({s['id']}): {cur} → {target} 需生成 {need} 题")
        print(f"{'='*60}")
        generate_for_syllabus(s)
        new_cur = len(load_questions(s.get('question_bank','')))
        print(f"  完成后: {new_cur} 题")
