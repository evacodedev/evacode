// Лимиты совпадают с SHARED_CART_MAX_IDS в src/market/filters.py.
export const SHARED_CART_MAX_ITEMS = 50
export const SHARED_CART_MAX_QTY = 99

export function encodeSharedCart(cart) {
  return (cart || [])
    .filter((item) => Number.isInteger(Number(item?.id)) && Number(item.quantity) > 0)
    .slice(0, SHARED_CART_MAX_ITEMS)
    .map((item) => `${Number(item.id)}-${Math.min(Number(item.quantity), SHARED_CART_MAX_QTY)}`)
    .join(',')
}

export function parseSharedCart(value) {
  const byId = new Map()
  for (const part of String(value || '').split(',')) {
    const match = part.trim().match(/^(\d{1,12})(?:-(\d{1,3}))?$/)
    if (!match) {
      continue
    }
    const id = Number(match[1])
    const quantity = Number(match[2] || 1)
    if (!id || !quantity) {
      continue
    }
    if (!byId.has(id) && byId.size >= SHARED_CART_MAX_ITEMS) {
      continue
    }
    byId.set(id, Math.min((byId.get(id) || 0) + quantity, SHARED_CART_MAX_QTY))
  }
  return [...byId].map(([id, quantity]) => ({ id, quantity }))
}

export function sharedCartUrl(origin, cart, country = '') {
  const items = encodeSharedCart(cart)
  if (!items) {
    return ''
  }
  const code = String(country || '').trim().toUpperCase()
  const countryPart = /^[A-Z]{2}$/.test(code) ? `&country=${code}` : ''
  return `${origin}/page/shared-cart?items=${items}${countryPart}`
}
