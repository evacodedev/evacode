import { useAuthStore } from '~/store/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  await auth.restore()
  if (!auth.isLoggedIn) {
    return navigateTo({
      path: '/account/login/',
      query: { next: to.fullPath },
    })
  }
  if (!auth.isConsultant) {
    return abortNavigation(createError({ statusCode: 404, statusMessage: 'Page not found' }))
  }
})
