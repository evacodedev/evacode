const PRODUCTION_SITE = 'https://www.evacode.org'

export function siteOrigin(config) {
  return String(config?.public?.url || PRODUCTION_SITE).replace(/\/$/, '') || PRODUCTION_SITE
}

export function absoluteUrl(site, path) {
  if (!path) {
    return `${site}/`
  }
  if (/^https?:\/\//i.test(path)) {
    return path
  }
  return `${site}${path.startsWith('/') ? path : `/${path}`}`
}

export function jsonLdScript(data) {
  return {
    type: 'application/ld+json',
    innerHTML: JSON.stringify(data),
  }
}

/**
 * @param {string} site
 * @param {{ name: string, path: string }[]} items
 */
export function breadcrumbListLd(site, items) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: absoluteUrl(site, item.path),
    })),
  }
}

/**
 * Product + Offer for PDP. Prices on the site are KRW.
 */
export function productLd({
  site,
  product,
  description,
  imageUrl,
  brandName,
  inStock,
}) {
  const url = absoluteUrl(site, `/product/${product.id}/`)
  const price = product.retail_price
  const offer = {
    '@type': 'Offer',
    url,
    availability: inStock
      ? 'https://schema.org/InStock'
      : 'https://schema.org/OutOfStock',
    itemCondition: 'https://schema.org/NewCondition',
    seller: {
      '@type': 'Organization',
      name: 'EvaCode',
      url: `${site}/`,
    },
  }
  if (price != null && price !== '') {
    offer.price = String(price)
    offer.priceCurrency = 'KRW'
  }

  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.title,
    description: description || undefined,
    image: imageUrl || undefined,
    sku: String(product.id),
    productID: String(product.id),
    brand: brandName
      ? { '@type': 'Brand', name: brandName }
      : undefined,
    url,
    offers: offer,
  }
}

export function brandPageLd({ site, brand, description }) {
  const url = absoluteUrl(site, `/brand/${brand.slug}/`)
  return {
    '@context': 'https://schema.org',
    '@type': 'Brand',
    name: brand.name,
    description: description || undefined,
    url,
    logo: brand.logo ? absoluteUrl(site, brand.logo) : undefined,
    image: brand.hero
      ? absoluteUrl(site, brand.hero)
      : (brand.history_image ? absoluteUrl(site, brand.history_image) : undefined),
    sameAs: brand.official_url ? [brand.official_url] : undefined,
  }
}

export function slugLabel(slug) {
  return String(slug || '')
    .replace(/-/g, ' ')
    .trim()
}
