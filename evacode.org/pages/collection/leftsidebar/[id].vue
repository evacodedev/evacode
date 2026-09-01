<template>
    <Header/>
    <div>
        <section class="section-b-space ratio_asos products-section">
            <div class="collection-wrapper">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-3">
                            <WidgetsCollectionSidebar :current-category="currentCategory"/>
                        </div>
                        <div class="collection-content col">
                            <div class="page-main-content">
                                <div class="row">
                                    <div class="col-12">
                                        <div class="collection-product-wrapper">
                                            <div class="product-top-filter mb-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
                                                <span>Найдено: {{ totalProductsCount || 0 }}</span>
                                                <select v-model="ordering" class="form-select catalog-sort">
                                                    <option value="retail_price">Сначала дешевле</option>
                                                    <option value="-retail_price">Сначала дороже</option>
                                                    <option value="title">По названию</option>
                                                </select>
                                            </div>
                                            <div class="product-wrapper-grid">
                                                <div class="row">
                                                    <div class="col-12">
                                                        <div class="text-center section-t-space section-b-space"
                                                             v-if="!productsLoading && totalProductsCount == 0">
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
                                                    <div class="col-grid-box col-xl-3 col-lg-6 col-md-6 col-6"
                                                         v-for="(product, index) in products" :key="index">
                                                        <div class="product-box">
                                                            <ProductBoxProductBox1
                                                                @opencartmodel="showCart"
                                                                :product="product"
                                                                :index="index"
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="product-pagination mb-0"
                                                 v-if="totalProductsCount > itemsPerPage">
                                                <div class="theme-paggination-block">
                                                    <div class="row">
                                                        <div class="col-xl-6 col-md-6 col-sm-12">
                                                            <WidgetsShopProductsPagination
                                                                :previous="previous"
                                                                :next="next"
                                                                :current="currentPage"
                                                                :pages="pages"
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
                    </div>
                </div>
            </div>
        </section>
        <cart-modal-popup
            :openCart="showcartmodal"
            :product="cartproduct"
            @closeCart="closeCartModal"
        />
        <ShopBeautyTestimonials/>
        <ShopBeautyAboutSlider/>
        <Footer/>
    </div>
</template>
<script setup>
import {useRoute, useRouter} from 'vue-router';

definePageMeta({
    key: (route) => route.fullPath,
});

const route = useRoute();
const router = useRouter();

const itemsPerPage = ref(12);
const paginateRange = ref(3);

const currentPage = computed(() => parseFloat(route.query.page) || 1);
const currentCategory = computed(() => {
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
        await router.push({ path: route.path, query });
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
    return query;
});

const productsResponse = ref(null);
const productsLoading = ref(true);
const loadProducts = async () => {
    productsLoading.value = true;
    productsResponse.value = null;
    try {
        productsResponse.value = await $fetch(`${useRuntimeConfig().public.apiBase}/market/goods`, {
            query: { ...goodsQuery.value },
        });
    } finally {
        productsLoading.value = false;
    }
};
await loadProducts();
watch(() => route.fullPath, loadProducts);

const products = computed(() => productsResponse.value?.results);
const totalProductsCount = computed(() => productsResponse.value?.count);
const previous = computed(() => productsResponse.value?.previous ? `?${productsResponse.value?.previous.split('?')[1]}` : null);
const next = computed(() => productsResponse.value?.next ? `?${productsResponse.value?.next.split('?')[1]}` : null);
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

const showcartmodal = ref(false);
const cartproduct = ref({});
const showCart = (item, product) => {
    showcartmodal.value = item
    cartproduct.value = product
};

const closeCartModal = (item) => {
    showcartmodal.value = item
};

useHead({
    titleTemplate: `%s - Магазин`,
});

</script>
