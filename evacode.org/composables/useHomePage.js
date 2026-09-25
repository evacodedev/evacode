const HOME_PAGE_KEY = 'home-page'

/**
 * Single SSR fetch for homepage rails and brand blocks.
 * Call from pages/index.vue; children read inject('homePage').
 */
export async function useHomePage() {
  const apiBase = useRuntimeConfig().public.apiBase
  const result = await useAsyncData(HOME_PAGE_KEY, () =>
    $fetch(`${apiBase}/market/home/`).catch(() => ({
      bestsellers: [],
      recommend: [],
      kinds: {},
      brands: {},
    })),
  )
  return result
}

export function useHomePageSection() {
  const home = inject('homePage', null)
  const pending = inject('homePagePending', ref(false))
  return {
    home,
    pending,
    payload: computed(() => home?.value || null),
  }
}
