-- 视频库 storage 上传策略（2026-09-04 实测发现：缺 anon INSERT 策略导致上传 403）
-- storage.objects 的列名因 Supabase 版本不同（新 bucket 文本列 / 旧 bucket_id），
-- 双分支各自尝试，编译不通过的分支静默跳过，任何版本都能执行成功。
do $$
begin
  -- 新 schema：bucket 文本列
  begin
    drop policy if exists "video-lib upload" on storage.objects;
    create policy "video-lib upload" on storage.objects for insert to anon
      with check (bucket = 'video-lib');
    exception when others then null;
  end;
  -- 旧 schema：bucket_id 列
  begin
    drop policy if exists "video-lib upload" on storage.objects;
    create policy "video-lib upload" on storage.objects for insert to anon
      with check (bucket_id = 'video-lib');
    exception when others then null;
  end;
  -- 公共读兜底（public 桶本身可读；失败也不影响）
  begin
    drop policy if exists "video-lib read" on storage.objects;
    create policy "video-lib read" on storage.objects for select
      using (bucket = 'video-lib' or bucket_id = 'video-lib');
    exception when others then null;
  end;
end $$;