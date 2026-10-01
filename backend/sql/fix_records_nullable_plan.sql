-- 让答题记录可以「不属于任何学科计划」（2026-10-01）
--
-- ============ 为什么 ============
--
-- 视频库做题、资源库做题、自定义计划 —— 这三条路来的用户**没有学习计划**
-- （他们的计划在 learning_plans，不在 subject_plans）。但记录表是硬绑在
-- 学科计划上的，插不进去：
--
--   实测线上 schema（不是文档，是 /rest/v1/ 的 OpenAPI spec）：
--     question_records  required = [id, user_id, plan_id, question_id, source]
--       plan_id → 外键 → subject_plans.id
--       task_id → 外键 → plan_daily_tasks.id
--     user_kp_mastery   required = [..., plan_id, ...]
--
-- 后果：POST /subject-plan/practice/submit 写 plan_id=null → 400；
--       而那段 httpx **没有检查状态码**（httpx 对 4xx 不抛异常）
--       → 用户做完题，看到判分和对错，**库里一条记录都没有**。
--
-- ============ 改什么 ============
--
--   ① 两处 plan_id 放开为可空（null = 「不挂在任何学科计划下」）
--   ② question_records.task_id 去掉外键 —— 它现在要能指向任一体系的 task
--      （既可能是 plan_daily_tasks 的行，也可能是 learning_tasks 的行）
--
-- **学科计划主链路完全不受影响** —— 它永远带 plan_id，行为一个字节都不变。
-- 放开 NOT NULL 只是让「另一条路」走得通。
--
-- 幂等，可重复执行。

-- ① plan_id 放开为可空
ALTER TABLE public.question_records ALTER COLUMN plan_id DROP NOT NULL;
ALTER TABLE public.user_kp_mastery  ALTER COLUMN plan_id DROP NOT NULL;

-- ② 去掉 task_id 指向 plan_daily_tasks 的外键
--    约束名是自动生成的，所以按定义去查，别猜名字。
DO $$
DECLARE c text;
BEGIN
  SELECT conname INTO c
  FROM pg_constraint
  WHERE conrelid = 'public.question_records'::regclass
    AND contype = 'f'
    AND pg_get_constraintdef(oid) ILIKE '%plan_daily_tasks%';
  IF c IS NOT NULL THEN
    EXECUTE format('ALTER TABLE public.question_records DROP CONSTRAINT %I', c);
    RAISE NOTICE '已删除外键约束: %', c;
  ELSE
    RAISE NOTICE 'task_id 上没有指向 plan_daily_tasks 的外键，跳过';
  END IF;
END $$;

-- ③ ⚠️⚠️ 去掉 question_id 指向 cet4_questions 的外键 —— **这条最要命**
--
--    2026-10-01 实测：question_records.question_id 有外键指向 public.cet4_questions，
--    而那张表**只有 110 行**（一张早期遗留表）。于是：
--
--        cet4          题库 1098 题 → 只有 110 道能写记录（10%）
--        cet6          题库 1073 题 → 0 道
--        ncre2-office  题库 1014 题 → 0 道
--        （其余 14 个考纲同理，全 0）
--
--    也就是说：**做 90% 的 CET-4 题、以及全部其他 16 个考纲的题，
--    答题记录都写不进去**；而 submit_answer 当时没检查状态码 → 静默丢弃。
--    实测 question_records 表**总共只有 7 行**，且这 7 条恰好都命中那 110 行 ——
--    完全对得上。
--
--    连锁影响（都读 question_records）：
--      · 错题本永远为空（/plans/{id}/mistakes）
--      · 「已做题」去重失效（_get_done_ids）→ 同一道题被反复分配
--      · 学情报告没有作答数据
--      （掌握度不受影响 —— user_kp_mastery 独立写，不引用 question_id）
--
--    为什么是**删约束**而不是补数据：题目现在有两个来源 ——
--    内存题库（local_question_bank，JSON 文件，19,338 题）和 questions 表（AI 生成）。
--    question_id 的值域是这两者的并集，**没有任何单张表能承载这个外键**。
DO $$
DECLARE c text;
BEGIN
  SELECT conname INTO c
  FROM pg_constraint
  WHERE conrelid = 'public.question_records'::regclass
    AND contype = 'f'
    AND pg_get_constraintdef(oid) ILIKE '%cet4_questions%';
  IF c IS NOT NULL THEN
    EXECUTE format('ALTER TABLE public.question_records DROP CONSTRAINT %I', c);
    RAISE NOTICE '已删除 question_id 的外键约束: %', c;
  ELSE
    RAISE NOTICE 'question_id 上没有指向 cet4_questions 的外键，跳过';
  END IF;
END $$;

-- ④ 题目全局统计要按 question_id 聚合，补索引
--
--    做题页要显示「提交数 / 通过率 / 平均通过时长」（所有人的，不是自己的）。
--    PostgREST 禁用聚合函数，只能在内存里加，但**筛选**还是走 SQL —— 没索引就是全表扫。
--    现在 question_records 只有 7 行无所谓，等记录攒起来就是慢查询。
--    原 DDL 只建了 user / plan / correct 三个索引，唯独漏了 question_id。
CREATE INDEX IF NOT EXISTS idx_question_records_qid
  ON public.question_records(question_id);
CREATE INDEX IF NOT EXISTS idx_question_records_qid_correct
  ON public.question_records(question_id, is_correct);

-- 自检（跑完看这三列）
--   qr_plan_nullable / ukm_plan_nullable  都应该是 YES
--   question_records 剩下的外键数          应该是 0（或只剩你确定要保留的）
SELECT
  (SELECT is_nullable FROM information_schema.columns
     WHERE table_schema = 'public' AND table_name = 'question_records'
       AND column_name = 'plan_id')  AS qr_plan_nullable,
  (SELECT is_nullable FROM information_schema.columns
     WHERE table_schema = 'public' AND table_name = 'user_kp_mastery'
       AND column_name = 'plan_id')  AS ukm_plan_nullable,
  (SELECT count(*) FROM pg_constraint
     WHERE conrelid = 'public.question_records'::regclass
       AND contype = 'f')            AS qr_remaining_fks;
