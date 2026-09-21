import { useAuthStore } from '~/store/auth'

export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore()
  await auth.restore()
  if (auth.isLoggedIn) {
    return navigateTo('/account/')
  }
})
