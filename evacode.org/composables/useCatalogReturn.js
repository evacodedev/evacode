const DEFAULT_CATALOG = '/collection/leftsidebar/0/'

const isCatalogPath = (path) =>
    typeof path === 'string' && path.includes('/collection/')

export const useCatalogReturn = () => {
    const lastPath = useState('catalog:return-path', () => DEFAULT_CATALOG)

    const rememberCatalogPath = (fullPath) => {
        if (isCatalogPath(fullPath)) {
            lastPath.value = fullPath
        }
    }

    return { lastCatalogPath: lastPath, rememberCatalogPath }
}
