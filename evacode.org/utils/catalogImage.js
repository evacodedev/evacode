import { httpsMedia } from '~/utils/httpsMedia'

const ALLOWED_PREFIX = 'https://a46291.business.ru/'

function toBase64Url(value) {
  if (typeof Buffer !== 'undefined') {
    return Buffer.from(value, 'utf8').toString('base64url')
  }
  const bytes = unescape(encodeURIComponent(value))
  return btoa(bytes).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function imgproxyPrefix() {
  return String(useRuntimeConfig().public.imgproxyPrefix || '').replace(/\/$/, '')
}

function normalizeBusinessRu(source) {
  return String(source || '').replace(
    /^http:\/\/a46291\.business\.ru/i,
    'https://a46291.business.ru',
  )
}

/**
 * Business.Ru CDN → /img/ (webp). Without IMGPROXY_PREFIX returns the original URL.
 * @param {string} source
 * @param {{ width?: number, height?: number, quality?: number }} [opts]
 */
export function catalogImageUrl(source, opts = {}) {
  if (!source) {
    return ''
  }
  const width = opts.width ?? 800
  const height = opts.height ?? 800
  const quality = opts.quality ?? 75
  const url = normalizeBusinessRu(source)
  const prefix = imgproxyPrefix()
  if (!prefix || !url.startsWith(ALLOWED_PREFIX)) {
    return url
  }
  return `${prefix}/insecure/rs:fit:${width}:${height}/q:${quality}/f:webp/${toBase64Url(url)}`
}

/**
 * Local /media/ files via imgproxy local:// (reviews, uploads).
 * Requires media volume mounted on imgproxy with IMGPROXY_LOCAL_FILESYSTEM_ROOT.
 */
export function mediaImageUrl(source, opts = {}) {
  if (!source) {
    return ''
  }
  const width = opts.width ?? 400
  const height = opts.height ?? 400
  const quality = opts.quality ?? 75
  const prefix = imgproxyPrefix()
  const safe = httpsMedia(source)
  if (!prefix) {
    return safe
  }

  let path = String(source)
  path = path.replace(/^https?:\/\/(www\.)?evacode\.org\/media\//i, '')
  path = path.replace(/^\/media\//, '')
  if (!path || path.includes('://')) {
    return safe
  }
  path = path.replace(/^\/+/, '')
  const local = `local:///${path}`
  return `${prefix}/insecure/rs:fit:${width}:${height}/q:${quality}/f:webp/${toBase64Url(local)}`
}
