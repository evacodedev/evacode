import { useAuthStore } from '~/store/auth'

export default defineNuxtRouteMiddleware(() => {
  if (useAuthStore().isConsultant) {
    return navigateTo('/account/consultant/', { replace: true })
  }
})
