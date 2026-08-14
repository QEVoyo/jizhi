<template>
  <div class="image-upload">
    <!-- 已上传图片预览 -->
    <div class="image-preview" v-if="modelValue">
      <img :src="modelValue" alt="preview" />
      <button class="remove-btn" @click="removeImage" title="移除图片">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <!-- 上传按钮 -->
    <label class="upload-trigger" v-if="!modelValue">
      <input
        type="file"
        accept="image/png,image/jpeg,image/gif,image/webp"
        @change="handleFile"
        hidden
      />
      <div class="upload-area" :class="{ uploading }">
        <template v-if="uploading">
          <div class="mini-spinner"></div>
          <span>上传中...</span>
        </template>
        <template v-else>
          <i class="fas fa-cloud-arrow-up"></i>
          <span>点击上传图片</span>
          <span class="hint">PNG / JPEG / GIF / WebP，最大 5MB</span>
        </template>
      </div>
    </label>

    <!-- 替换按钮 -->
    <button class="replace-btn" v-if="modelValue && !uploading" @click="triggerReplace">
      <i class="fas fa-rotate"></i> 替换图片
    </button>
    <input
      ref="replaceInput"
      type="file"
      accept="image/png,image/jpeg,image/gif,image/webp"
      @change="handleFile"
      hidden
    />

    <!-- 错误提示 -->
    <p class="upload-error" v-if="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])

const uploading = ref(false)
const error = ref('')
const replaceInput = ref(null)

function triggerReplace() {
  replaceInput.value?.click()
}

async function handleFile(e) {
  const file = e.target.files?.[0]
  if (!file) return

  // 校验大小
  if (file.size > 5 * 1024 * 1024) {
    error.value = '图片大小不能超过 5MB'
    return
  }

  error.value = ''
  uploading.value = true

  try {
    // 通过后端上传到 Supabase Storage
    const formData = new FormData()
    formData.append('file', file)

    const baseUrl = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
    const token = localStorage.getItem('jizhi-token')

    const res = await fetch(`${baseUrl}/admin/upload-image`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '上传失败')
    }

    const data = await res.json()
    emit('update:modelValue', data.url)
    ElMessage.success('图片上传成功')
  } catch (e) {
    error.value = e.message || '上传失败'
    ElMessage.error(error.value)
  } finally {
    uploading.value = false
    // 重置 input 以允许重复上传同一文件
    e.target.value = ''
  }
}

function removeImage() {
  emit('update:modelValue', '')
}
</script>

<style scoped>
.image-upload {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 预览 */
.image-preview {
  position: relative;
  display: inline-block;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.2);
}

.image-preview img {
  display: block;
  max-width: 320px;
  max-height: 200px;
  object-fit: contain;
}

.remove-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.remove-btn:hover {
  background: rgba(245, 108, 108, 0.8);
  transform: scale(1.1);
}

/* 上传区域 */
.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 28px 20px;
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.02);
}
.upload-area:hover {
  border-color: rgba(64, 158, 255, 0.3);
  background: rgba(64, 158, 255, 0.04);
}
.upload-area.uploading {
  opacity: 0.6;
  cursor: default;
}

.upload-area i {
  font-size: 24px;
  color: rgba(255, 255, 255, 0.3);
}
.upload-area span {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}
.upload-area .hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.2);
}

/* 迷你旋转 */
.mini-spinner {
  width: 22px;
  height: 22px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: #409eff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 替换按钮 */
.replace-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  align-self: flex-start;
}
.replace-btn:hover {
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.7);
}

.upload-error {
  font-size: 12px;
  color: #f56c6c;
  margin: 0;
}
</style>
