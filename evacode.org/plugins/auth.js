import { useAuthStore } from '~/store/auth'
import { useWishlistStore } from '~/store/wishlist'

export default defineNuxtPlugin(async () => {
  const auth = useAuthStore()
  const wishlist = useWishlistStore()
  await auth.restore()
  try {
    await wishlist.sync()
  } catch {
    wishlist.ready = false
  }
  auth.$onAction(({ name, after }) => {
    if (name !== 'setSession' && name !== 'clearSession') {
      return
    }
    after(() => {
      wishlist.sync().catch(() => {
        wishlist.ready = false
      })
    })
  })
})
