import { useAuthStore } from '~/store/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  await auth.restore()
  if (auth.isLoggedIn) {
    return
  }
  return navigateTo({
    path: '/account/login/',
    query: { next: to.fullPath },
  })
})
