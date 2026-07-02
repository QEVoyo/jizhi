import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'jizhi-theme'

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getStoredTheme() {
  return localStorage.getItem(STORAGE_KEY) || 'system'
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref(getStoredTheme())
  const currentTheme = ref(getCurrentTheme())

  function getCurrentTheme() {
    if (mode.value === 'system') {
      return getSystemTheme()
    }
    return mode.value
  }

  function setMode(newMode) {
    mode.value = newMode
    localStorage.setItem(STORAGE_KEY, newMode)
    applyTheme()
  }

  function toggleTheme() {
    if (mode.value === 'light') setMode('dark')
    else if (mode.value === 'dark') setMode('system')
    else setMode('light')
  }

  function applyTheme() {
    const theme = getCurrentTheme()
    currentTheme.value = theme
    document.documentElement.setAttribute('data-theme', theme)
  }

  // 监听系统主题变化
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', () => {
    if (mode.value === 'system') {
      applyTheme()
    }
  })

  // 初始化
  applyTheme()

  return {
    mode,
    currentTheme,
    setMode,
    toggleTheme,
    applyTheme
  }
})