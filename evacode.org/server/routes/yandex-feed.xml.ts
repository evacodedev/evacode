export default defineEventHandler(async (event) => {
    const apiBase = String(useRuntimeConfig().public.apiBase || '').replace(/\/$/, '')
    if (!apiBase) {
        throw createError({ statusCode: 503, statusMessage: 'Feed unavailable' })
    }
    try {
        const body = await $fetch<string>(`${apiBase}/market/yandex-feed/`, {
            responseType: 'text',
            timeout: 60000,
        })
        setHeader(event, 'Content-Type', 'application/xml; charset=utf-8')
        setHeader(event, 'Cache-Control', 'public, max-age=3600')
        return body
    } catch {
        throw createError({ statusCode: 503, statusMessage: 'Feed unavailable' })
    }
})
