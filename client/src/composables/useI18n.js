import { ref, watch } from 'vue'
import en from '../locales/en.js'
import zhCN from '../locales/zh-CN.js'

const locales = { en, 'zh-CN': zhCN }
const currentLocale = ref(localStorage.getItem('locale') || 'en')

export function useI18n() {
  const t = (key) => {
    const keys = key.split('.')
    let val = locales[currentLocale.value] || locales.en
    for (const k of keys) {
      val = val?.[k]
    }
    return val || key
  }

  const setLocale = (locale) => {
    currentLocale.value = locale
    localStorage.setItem('locale', locale)
  }

  return { t, currentLocale, setLocale, availableLocales: Object.keys(locales) }
}
