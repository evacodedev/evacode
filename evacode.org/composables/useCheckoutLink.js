import { useAuthStore } from '~/store/auth'

export const CONSULTANT_CART_ORDER = { path: '/account/consultant/new/', query: { from: 'cart' } }

export function useCheckoutLink() {
  const auth = useAuthStore()
  const isConsultant = computed(() => auth.isConsultant)
  const checkoutTo = computed(() => (isConsultant.value ? CONSULTANT_CART_ORDER : { path: '/page/account/checkout' }))
  return { isConsultant, checkoutTo }
}
