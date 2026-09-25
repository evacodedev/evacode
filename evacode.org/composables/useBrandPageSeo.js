/**
 * Shared head tags + JSON-LD for brand pages (/brand/[slug], curacion, ttt).
 * Brand name stays in the brand's native (usually Latin) form from the API.
 */
export function useBrandPageSeo(brand) {
  const runtimeConfig = useRuntimeConfig()

  const description = computed(() => {
    const row = brand.value
    if (!row) {
      return 'Корейский бренд в магазине EvaCode.'
    }
    return row.lead
      || `${row.name} — оригинальный корейский уход в магазине EvaCode. Опт и розница, доставка из Кореи.`
  })

  useHead({
    title: () => (brand.value?.name
      ? `${brand.value.name} — купить в EvaCode`
      : 'Бренд — EvaCode'),
    meta: [
      { name: 'description', content: () => description.value },
      { property: 'og:title', content: () => (brand.value?.name
        ? `${brand.value.name} — EvaCode`
        : 'EvaCode') },
      { property: 'og:description', content: () => description.value },
      { property: 'og:type', content: 'website' },
    ],
    script: () => {
      if (!brand.value?.slug) {
        return []
      }
      const site = siteOrigin(runtimeConfig)
      const crumbs = breadcrumbListLd(site, [
        { name: 'Главная', path: '/' },
        { name: 'Каталог', path: '/collection/leftsidebar/0/' },
        { name: brand.value.name, path: `/brand/${brand.value.slug}/` },
      ])
      const brandLd = brandPageLd({
        site,
        brand: brand.value,
        description: description.value,
      })
      return [jsonLdScript(crumbs), jsonLdScript(brandLd)]
    },
  })
}
