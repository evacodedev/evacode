<template>
    <Header/>
    <div>
        <section class="section-b-space ratio_asos products-section">
            <div class="collection-wrapper">
                <div class="container">
                    <div class="catalog-page-meta">
                        <span>Найдено: {{ displayedProductsCount }}</span>
                        <div class="catalog-toolbar">
                            <label class="catalog-page-size">
                                <span>На странице</span>
                                <select v-model="pageSize" class="form-select catalog-sort">
                                    <option :value="20">20</option>
                                    <option :value="50">50</option>
                                    <option :value="100">100</option>
                                </select>
                            </label>
                            <select v-model="ordering" class="form-select catalog-sort">
                                <option value="retail_price">Сначала дешевле</option>
                                <option value="-retail_price">Сначала дороже</option>
                                <option value="title">По названию</option>
                            </select>
                        </div>
                    </div>
                    <div class="collection-content">
                        <div class="page-main-content">
                            <div class="row">
                                <div class="col-12">
                                    <div class="collection-product-wrapper">
                                            <div
                                                class="product-wrapper-grid catalog-grid-stable"
                                                :class="{ 'catalog-grid-fade': animateCatalogEnter }"
                                                :style="{ '--catalog-skel': skeletonCount }"
                                            >
                                                <div class="row">
                                                    <WidgetsProductSkeletons
                                                        v-if="!catalogReady"
                                                        :count="skeletonCount"
                                                    />
                                                    <div
                                                        v-else-if="!displayedProductsCount"
                                                        class="col-12"
                                                    >
                                                        <div class="text-center section-t-space section-b-space">
                                                            <img src="/images/evacode/empty-search.jpg"
                                                                 class="img-fluid" alt/>
                                                            <h3 class="mt-3">Извините! Не найден товар который Вы
                                                                искали!!!</h3>
                                                            <div class="col-12 mt-3">
                                                                <a href="/collection/leftsidebar/0"
                                                                   class="btn btn-solid">Сбросить фильтры
                                                                </a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <template v-else>
                                                        <div
                                                            class="col-grid-box col-xl-4 col-6"
                                                            v-for="(product, index) in (products || [])"
                                                            :key="product.id || index"
                                                            :data-catalog-product="product.id"
                                                        >
                                                            <div class="product-box">
                                                                <ProductBoxProductBox1
                                                                    :product="product"
                                                                    :index="index"
                                                                />
                                                            </div>
                                                        </div>
                                                    </template>
                                                </div>
                                            </div>
                                            <div class="product-pagination mb-0"
                                                 v-if="displayedProductsCount > itemsPerPage">
                                                <div class="theme-paggination-block">
                                                    <WidgetsShopProductsPagination
                                                        :current="currentPage"
                                                        :pages="pages"
                                                        :last-page="paginates"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                    </div>
                </div>
            </div>
        </section>
        <Footer/>
    </div>
</template>
<script setup>
import {useRoute, useRouter} from 'vue-router';

definePageMeta({
    scrollToTop: false,
});

const CATALOG_PATH = '/collection/leftsidebar/0';

const route = useRoute();
const router = useRouter();
const { lastProductId, consumeReturnTarget } = useCatalogReturn();

const PAGE_SIZES = [20, 50, 100];
const DEFAULT_PAGE_SIZE = 20;
const paginateRange = ref(3);

const currentPage = computed(() => parseFloat(route.query.page) || 1);
const itemsPerPage = computed(() => {
    const size = Number(route.query.page_size);
    return PAGE_SIZES.includes(size) ? size : DEFAULT_PAGE_SIZE;
});
const pageSize = computed({
    get: () => itemsPerPage.value,
    set: async (value) => {
        const size = PAGE_SIZES.includes(Number(value)) ? Number(value) : DEFAULT_PAGE_SIZE;
        const query = { ...route.query, page_size: size, page: 1 };
        delete query.in_stock;
        delete query.bestseller;
        await router.push({ path: CATALOG_PATH, query });
    },
});
const currentCategory = computed(() => {
    const fromQuery = parseFloat(route.query.category);
    if (fromQuery && fromQuery > 0) {
        return fromQuery;
    }
    const id = parseFloat(route.params.id);
    return id && id > 0 ? id : null;
});
const allowedOrdering = ['retail_price', '-retail_price', 'title'];
const ordering = computed({
    get: () => allowedOrdering.includes(route.query.ordering) ? route.query.ordering : 'title',
    set: async (value) => {
        const query = { ...route.query, ordering: value, page: 1 };
        delete query.in_stock;
        delete query.bestseller;
        await router.push({ path: CATALOG_PATH, query });
    },
});

const goodsQuery = computed(() => {
    const query = {
        page: currentPage.value,
        page_size: itemsPerPage.value,
        ordering: allowedOrdering.includes(route.query.ordering) ? route.query.ordering : 'title',
    };
    if (currentCategory.value) {
        query.category = currentCategory.value;
    }
    if (route.query.q) {
        query.search = route.query.q;
    }
    if (route.query.min_price) {
        query.min_price = route.query.min_price;
    }
    if (route.query.max_price) {
        query.max_price = route.query.max_price;
    }
    if (route.query.brand) {
        query.brand = Array.isArray(route.query.brand)
            ? route.query.brand.join(',')
            : route.query.brand;
    }
    if (route.query.kind) {
        query.kind = Array.isArray(route.query.kind)
            ? route.query.kind.join(',')
            : route.query.kind;
    }
    return query;
});

const { data: productsResponse } = await useAsyncData(
    `catalog-goods:${route.fullPath}`,
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/goods`, {
        query: { ...goodsQuery.value },
    }),
);

const catalogReady = ref(import.meta.server && !!productsResponse.value);
const animateCatalogEnter = ref(false);
const loadedPath = ref(import.meta.server && productsResponse.value ? route.fullPath : '');
let catalogLoadId = 0;
let firstCatalogEnterDone = false;
let fadeTimer;

const revealCatalog = async (animate) => {
    if (!import.meta.client) {
        catalogReady.value = true;
        return;
    }
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const returningToProduct = Boolean(lastProductId.value);
    const shouldFade = animate && !firstCatalogEnterDone && !prefersReduced && !returningToProduct;
    catalogReady.value = true;
    animateCatalogEnter.value = shouldFade;
    if (shouldFade) {
        firstCatalogEnterDone = true;
        await nextTick();
        window.clearTimeout(fadeTimer);
        fadeTimer = window.setTimeout(() => {
            animateCatalogEnter.value = false;
        }, 320);
    }
};

const loadCatalog = async ({ animate = false } = {}) => {
    const loadId = ++catalogLoadId;
    const hasProducts = Boolean(productsResponse.value?.results?.length);
    if (animate || !hasProducts) {
        catalogReady.value = false;
    }
    try {
        const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/goods`, {
            query: { ...goodsQuery.value },
        });
        if (loadId !== catalogLoadId) {
            return;
        }
        productsResponse.value = data;
        loadedPath.value = route.fullPath;
    } catch (error) {
        console.error(error);
        if (loadId !== catalogLoadId) {
            return;
        }
    }
    if (loadId !== catalogLoadId) {
        return;
    }
    await revealCatalog(animate);
};

const catalogItemSelector = (productId) =>
    `[data-catalog-product="${String(productId).replace(/"/g, '')}"]`;

const restoreCatalogFocus = async () => {
    if (!import.meta.client) {
        return;
    }
    const { productId, scrollY } = consumeReturnTarget();
    if (!productId && !scrollY) {
        return;
    }
    await nextTick();
    const align = () => {
        const item = productId
            ? document.querySelector(catalogItemSelector(productId))
            : null;
        if (item) {
            item.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'auto' });
            const link = item.querySelector('.product-detail-link');
            if (link && typeof link.focus === 'function') {
                link.focus({ preventScroll: true });
            }
            return true;
        }
        if (scrollY) {
            window.scrollTo(0, scrollY);
        }
        return false;
    };
    align();
    window.setTimeout(align, 50);
    window.setTimeout(align, 200);
    window.setTimeout(align, 500);
};

onMounted(async () => {
    if (productsResponse.value) {
        loadedPath.value = route.fullPath;
        const alreadyVisible = catalogReady.value;
        await revealCatalog(!alreadyVisible);
        await restoreCatalogFocus();
        return;
    }
    await loadCatalog({ animate: true });
    await restoreCatalogFocus();
});

onBeforeUnmount(() => {
    window.clearTimeout(fadeTimer);
});

watch(
    () => route.fullPath,
    async (to, from) => {
        if (!from || to === from) {
            return;
        }
        await loadCatalog({ animate: false });
    },
    { flush: 'pre' },
);

const products = computed(() => productsResponse.value?.results);
const lastProductsCount = ref(0);
watch(
    productsResponse,
    (data) => {
        if (data && typeof data.count === 'number') {
            lastProductsCount.value = data.count;
        }
    },
    { immediate: true },
);
const displayedProductsCount = computed(() => {
    if (typeof productsResponse.value?.count === 'number') {
        return productsResponse.value.count;
    }
    return lastProductsCount.value;
});
const skeletonCount = computed(() => {
    const count = displayedProductsCount.value;
    const size = Math.min(itemsPerPage.value, 20);
    if (!count) {
        return size;
    }
    return Math.min(size, count);
});
const totalProductsCount = displayedProductsCount;
const paginates = computed(() => Math.ceil((totalProductsCount.value || 0) / itemsPerPage.value));

const pages = computed(() => {
    let start = currentPage.value < paginateRange.value - 1 ? 1 : currentPage.value - 1
    let end = currentPage.value < paginateRange.value - 1 ? start + paginateRange.value - 1 : currentPage.value + 1;

    start = Math.max(1, start);
    end = Math.min(end, paginates.value);

    const _pages = []
    for (let i = start; i <= end; i++) {
        _pages.push(i)
    }
    return _pages;
});

const runtimeConfig = useRuntimeConfig();

useHead({
    title: 'Каталог корейской косметики — EvaCode',
    meta: [
        {
            name: 'description',
            content: 'Каталог EvaCode: люксовая корейская косметика Whoo, O HUI, SU:M37, CNP, Sulwhasoo, Jogabi. Опт и розница, доставка из Кореи.',
        },
    ],
    script: () => {
        const site = siteOrigin(runtimeConfig);
        const items = [
            { name: 'Главная', path: '/' },
            { name: 'Каталог', path: '/collection/leftsidebar/0/' },
        ];
        const brand = route.query.brand;
        const kind = route.query.kind;
        if (brand) {
            const slug = String(Array.isArray(brand) ? brand[0] : brand);
            items.push({
                name: slugLabel(slug),
                path: `/collection/leftsidebar/0/?brand=${encodeURIComponent(slug)}`,
            });
        } else if (kind) {
            const slug = String(Array.isArray(kind) ? kind[0] : kind);
            items.push({
                name: slugLabel(slug),
                path: `/collection/leftsidebar/0/?kind=${encodeURIComponent(slug)}`,
            });
        }
        return [jsonLdScript(breadcrumbListLd(site, items))];
    },
});

</script>
