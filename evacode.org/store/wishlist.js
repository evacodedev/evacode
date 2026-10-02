import { defineStore } from 'pinia'
import { useAuthStore } from '~/store/auth'

const PENDING_KEY = 'evacode_wishlist_pending'

let requestGen = 0

function rememberPending(goodsId) {
  if (!import.meta.client) {
    return
  }
  sessionStorage.setItem(PENDING_KEY, String(goodsId))
}

function takePending() {
  if (!import.meta.client) {
    return null
  }
  const raw = sessionStorage.getItem(PENDING_KEY)
  sessionStorage.removeItem(PENDING_KEY)
  const id = Number(raw)
  return id > 0 ? id : null
}

export const useWishlistStore = defineStore({
  id: 'wishlist-store',
  state: () => ({
    items: [],
    ready: false,
  }),
  actions: {
    reset() {
      this.items = []
      this.ready = false
    },
    contains(id) {
      if (id == null) {
        return false
      }
      return this.items.some((item) => item.id === id)
    },
    async sync() {
      const auth = useAuthStore()
      if (!auth.isLoggedIn) {
        this.reset()
        return
      }
      const gen = ++requestGen
      const data = await auth.authFetch('/market/wishlist/')
      if (gen !== requestGen) {
        return
      }
      this.items = Array.isArray(data) ? data : []
      this.ready = true
      const pending = takePending()
      if (!pending || this.contains(pending) || gen !== requestGen) {
        return
      }
      try {
        const saved = await auth.authFetch('/market/wishlist/', {
          method: 'POST',
          body: { goods_id: pending },
        })
        if (gen !== requestGen || !saved?.id) {
          return
        }
        this.items = [saved, ...this.items.filter((item) => item.id !== saved.id)]
      } catch {
        // Список уже на экране. Сердце можно нажать ещё раз.
      }
    },
    async toggle(product, nextPath) {
      const auth = useAuthStore()
      const id = product?.id
      if (id == null) {
        return
      }
      if (!auth.isLoggedIn) {
        rememberPending(id)
        const next = typeof nextPath === 'string' && nextPath.startsWith('/') ? nextPath : '/'
        await navigateTo({
          path: '/account/login/',
          query: { next },
        })
        return
      }
      const gen = ++requestGen
      const previous = this.items.slice()
      const removing = this.contains(id)
      if (removing) {
        this.items = this.items.filter((item) => item.id !== id)
      } else if (product.title) {
        this.items = [product, ...this.items]
      }
      try {
        if (removing) {
          await auth.authFetch(`/market/wishlist/${id}/`, { method: 'DELETE' })
        } else {
          const saved = await auth.authFetch('/market/wishlist/', {
            method: 'POST',
            body: { goods_id: id },
          })
          if (gen === requestGen && saved?.id) {
            this.items = [saved, ...previous.filter((item) => item.id !== saved.id)]
          }
        }
      } catch (error) {
        if (gen === requestGen) {
          this.items = previous
        }
        throw error
      }
    },
  },
})
