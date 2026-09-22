import { defineStore } from 'pinia'
import { normalizeAddressList } from '~/utils/account-address'

let addressesPromise = null

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
    addresses: [],
    addressesLoaded: false,
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.user),
    displayName: (state) => {
      const name = String(state.user?.first_name || '').trim()
      return name || state.user?.email || ''
    },
    defaultAddress: (state) => state.addresses[0] || null,
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
      this.addresses = []
      this.addressesLoaded = false
      addressesPromise = null
    },
    clearSession() {
      this.accessCookie().value = null
      this.refreshCookie().value = null
      this.user = null
      this.addresses = []
      this.addressesLoaded = false
      addressesPromise = null
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
        this.preloadAddresses()
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
      this.preloadAddresses()
    },
    async loginWithGoogle(credential) {
      const payload = await $fetch(this.apiUrl('/core/auth/google/'), {
        method: 'POST',
        body: { credential },
      })
      this.setSession(payload)
      this.ready = true
      this.preloadAddresses()
    },
    async register(fields) {
      const payload = await $fetch(this.apiUrl('/core/auth/register/'), {
        method: 'POST',
        body: fields,
      })
      this.setSession(payload)
      this.ready = true
      this.preloadAddresses()
    },
    async saveProfile(fields) {
      this.user = await $fetch(this.apiUrl('/core/auth/me/'), {
        method: 'PATCH',
        headers: this.authHeader(),
        body: fields,
      })
    },
    async listAddresses() {
      return $fetch(this.apiUrl('/core/auth/addresses/'), {
        headers: this.authHeader(),
      })
    },
    async preloadAddresses(force = false) {
      if (!this.isLoggedIn) {
        this.addresses = []
        this.addressesLoaded = true
        return this.addresses
      }
      if (!force && this.addressesLoaded) {
        return this.addresses
      }
      if (addressesPromise) {
        return addressesPromise
      }
      addressesPromise = this.listAddresses()
        .then((data) => {
          this.addresses = normalizeAddressList(data)
          return this.addresses
        })
        .catch(() => {
          this.addresses = []
          return this.addresses
        })
        .finally(() => {
          this.addressesLoaded = true
          addressesPromise = null
        })
      return addressesPromise
    },
    async ensureAddresses() {
      if (!this.isLoggedIn) {
        this.addresses = []
        return this.addresses
      }
      if (process.client && this.addressesLoaded && !this.addresses.length) {
        this.addressesLoaded = false
      }
      if (this.addressesLoaded) {
        return this.addresses
      }
      return this.preloadAddresses()
    },
    rememberAddress(saved) {
      if (!saved?.id) {
        return
      }
      const index = this.addresses.findIndex((row) => row.id === saved.id)
      if (index >= 0) {
        const next = this.addresses.slice()
        next[index] = saved
        this.addresses = next
      } else {
        this.addresses = [...this.addresses, saved]
      }
      this.addressesLoaded = true
    },
    async saveAddress(fields, id) {
      const path = id ? `/core/auth/addresses/${id}/` : '/core/auth/addresses/'
      const saved = await $fetch(this.apiUrl(path), {
        method: id ? 'PATCH' : 'POST',
        headers: this.authHeader(),
        body: fields,
      })
      this.rememberAddress(saved)
      return saved
    },
    async deleteAddress(id) {
      await $fetch(this.apiUrl(`/core/auth/addresses/${id}/`), {
        method: 'DELETE',
        headers: this.authHeader(),
      })
      this.addresses = this.addresses.filter((row) => row.id !== id)
    },
    logout() {
      this.clearSession()
      this.ready = true
    },
  },
})
