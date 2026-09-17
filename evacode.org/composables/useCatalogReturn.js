const DEFAULT_CATALOG = '/collection/leftsidebar/0/'

const isCatalogPath = (path) =>
    typeof path === 'string' && path.includes('/collection/')

export const useCatalogReturn = () => {
    const lastPath = useState('catalog:return-path', () => DEFAULT_CATALOG)
    const lastProductId = useState('catalog:return-product', () => '')
    const lastScrollY = useState('catalog:return-scroll', () => 0)

    const rememberCatalogPath = (fullPath) => {
        if (isCatalogPath(fullPath)) {
            lastPath.value = fullPath
        }
    }

    const rememberFromCatalog = ({ path, productId, scrollY } = {}) => {
        if (isCatalogPath(path)) {
            lastPath.value = path
        }
        if (productId != null && productId !== '') {
            lastProductId.value = String(productId)
        }
        if (import.meta.client && Number.isFinite(scrollY)) {
            lastScrollY.value = Math.max(0, scrollY)
        }
    }

    const consumeReturnTarget = () => {
        const target = {
            productId: lastProductId.value || '',
            scrollY: lastScrollY.value || 0,
        }
        lastProductId.value = ''
        lastScrollY.value = 0
        return target
    }

    return {
        lastCatalogPath: lastPath,
        lastProductId,
        rememberCatalogPath,
        rememberFromCatalog,
        consumeReturnTarget,
    }
}
