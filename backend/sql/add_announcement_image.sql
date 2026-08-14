-- 给 system_announcements 表加 image_url 字段
ALTER TABLE system_announcements ADD COLUMN IF NOT EXISTS image_url TEXT;
