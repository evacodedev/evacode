import { useAuthStore } from '~/store/auth'
import { CONSULTANT_CART_ORDER } from '~/composables/useCheckoutLink'

export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore()
  await auth.restore()
  if (auth.isConsultant) {
    return navigateTo(CONSULTANT_CART_ORDER, { replace: true })
  }
})
