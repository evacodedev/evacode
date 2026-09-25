const CATALOG_LOC = '/collection/leftsidebar/0/'

export default defineSitemapEventHandler(async () => {
    const apiBase = String(useRuntimeConfig().public.apiBase || '').replace(/\/$/, '')
    if (!apiBase) {
        return [{ loc: CATALOG_LOC }]
    }
    try {
        const payload = await $fetch(`${apiBase}/market/sitemap/`)
        const urls = Array.isArray(payload?.urls) ? payload.urls : []
        const locs = urls
            .map((item) => (typeof item === 'string' ? item : item?.loc))
            .filter(Boolean)
            .map((loc) => (String(loc).startsWith('/') ? loc : `/${loc}`))
        if (!locs.includes(CATALOG_LOC)) {
            locs.unshift(CATALOG_LOC)
        }
        return locs.map((loc) => ({ loc }))
    } catch {
        return [{ loc: CATALOG_LOC }]
    }
})
