import { defineStore } from 'pinia'

const ACCESS_MAX_AGE = 60 * 60
const REFRESH_MAX_AGE = 60 * 60 * 24 * 2

function cookieOptions(maxAge) {
  return {
    path: '/',
    sameSite: 'lax',
    maxAge,
  }
}

export function accountErrorMessage(error, fallback) {
  const data = error?.data
  if (!data) {
    return fallback
  }
  if (typeof data.detail === 'string') {
    return data.detail
  }
  if (Array.isArray(data.detail) && data.detail[0]) {
    return data.detail[0]
  }
  for (const value of Object.values(data)) {
    if (typeof value === 'string') {
      return value
    }
    if (Array.isArray(value) && value[0]) {
      return String(value[0])
    }
  }
  return fallback
}

export function safeAccountNext(raw) {
  if (!raw || typeof raw !== 'string') {
    return '/account/'
  }
  if (!raw.startsWith('/') || raw.startsWith('//')) {
    return '/account/'
  }
  return raw
}

export const useAuthStore = defineStore({
  id: 'auth-store',
  state: () => ({
    user: null,
    ready: false,
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.user),
    displayName: (state) => {
      const name = String(state.user?.first_name || '').trim()
      return name || state.user?.email || ''
    },
  },
  actions: {
    accessCookie() {
      return useCookie('evacode_access', cookieOptions(ACCESS_MAX_AGE))
    },
    refreshCookie() {
      return useCookie('evacode_refresh', cookieOptions(REFRESH_MAX_AGE))
    },
    authHeader() {
      const token = this.accessCookie().value
      if (!token) {
        return {}
      }
      return { Authorization: `Bearer ${token}` }
    },
    setSession(payload) {
      this.accessCookie().value = payload.access
      this.refreshCookie().value = payload.refresh
      this.user = payload.user || null
    },
    clearSession() {
      this.accessCookie().value = null
      this.refreshCookie().value = null
      this.user = null
    },
    apiUrl(path) {
      return `${useRuntimeConfig().public.apiBase}${path}`
    },
    async restore() {
      if (this.ready) {
        return
      }
      const token = this.accessCookie().value
      if (!token) {
        this.user = null
        this.ready = true
        return
      }
      try {
        this.user = await $fetch(this.apiUrl('/core/auth/me/'), {
          headers: this.authHeader(),
        })
      } catch {
        this.clearSession()
      }
      this.ready = true
    },
    async login(email, password) {
      const payload = await $fetch(this.apiUrl('/core/auth/login/'), {
        method: 'POST',
        body: { email, password },
      })
      this.setSession(payload)
      this.ready = true
    },
    async register(fields) {
      const payload = await $fetch(this.apiUrl('/core/auth/register/'), {
        method: 'POST',
        body: fields,
      })
      this.setSession(payload)
      this.ready = true
    },
    async saveProfile(fields) {
      this.user = await $fetch(this.apiUrl('/core/auth/me/'), {
        method: 'PATCH',
        headers: this.authHeader(),
        body: fields,
      })
    },
    logout() {
      this.clearSession()
      this.ready = true
    },
  },
})
