import { ref, watch } from 'vue'

const THEME_KEY = 'theme'
const theme = ref(localStorage.getItem(THEME_KEY) || 'system')

function applyTheme(mode) {
  const html = document.documentElement
  if (mode === 'dark') {
    html.classList.add('dark')
  } else if (mode === 'light') {
    html.classList.remove('dark')
  } else {
    // system
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    html.classList.toggle('dark', prefersDark)
  }
}

// Listen for system changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if (theme.value === 'system') applyTheme('system')
})

applyTheme(theme.value)

export function useTheme() {
  const setTheme = (mode) => {
    theme.value = mode
    localStorage.setItem(THEME_KEY, mode)
    applyTheme(mode)
  }
  return { theme, setTheme }
}
