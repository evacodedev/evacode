import { useAuthStore } from '~/store/auth'

export default defineNuxtPlugin(async () => {
  await useAuthStore().restore()
})
