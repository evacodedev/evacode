const ALLOWED_PREFIX = 'https://a46291.business.ru/'

function toBase64Url(value) {
  if (typeof Buffer !== 'undefined') {
    return Buffer.from(value, 'utf8').toString('base64url')
  }
  const bytes = unescape(encodeURIComponent(value))
  return btoa(bytes).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

export function catalogImageUrl(source) {
  if (!source) {
    return ''
  }
  const prefix = String(useRuntimeConfig().public.imgproxyPrefix || '').replace(/\/$/, '')
  if (!prefix || !String(source).startsWith(ALLOWED_PREFIX)) {
    return source
  }
  return `${prefix}/insecure/rs:fit:800:800/q:75/f:webp/${toBase64Url(source)}`
}
