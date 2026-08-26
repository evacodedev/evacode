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
                                            <div class="product-wrapper-grid">
                                                <div class="row">
                                                    <div class="col-12">
                                                        <div class="text-center section-t-space section-b-space"
                                                             v-if="totalProductsCount == 0">
                                                            <img src="/images/evacode/empty-search.jpg"
                                                                 class="img-fluid" alt/>
                                                            <h3 class="mt-3">Извините! Не найден товар который Вы
                                                                искали!!!</h3>
                                                            <div class="col-12 mt-3">
                                                                <nuxt-link :to="{ path: '/collection/leftsidebar/0' }"
                                                                           class="btn btn-solid">Продолжить покупки
                                                                </nuxt-link>
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
import {useRoute} from 'vue-router';
const route = useRoute();

const currentPage = ref(parseFloat(route.query.page) || 1);
const currentCategory = ref(parseFloat(route.params.id) || null);
const {data: productsResponse} = await useAsyncData(
    'productsResponse',
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/goods`, {
        query: {
            page: currentPage.value,
            category: currentCategory.value
        }
    }),
    {
        server: false,
        watch: [currentPage, currentCategory]
    }
);

const products = computed(() => productsResponse.value?.results);
const totalProductsCount = computed(() => productsResponse.value?.count);
const previous = computed(() => productsResponse.value?.previous ? `?${productsResponse.value?.previous.split('?')[1]}` : null);
const next = computed(() => productsResponse.value?.next ? `?${productsResponse.value?.next.split('?')[1]}` : null);
const paginates = computed(() => Math.round(totalProductsCount.value / itemsPerPage.value));

const itemsPerPage = ref(12);
const paginateRange = ref(3);

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

watch(
    () => route.query.page,
    () => {
        currentPage.value = parseFloat(route.query.page) || 1;
    }
);

watch(
    () => route.query.category,
    () => {
        currentCategory.value = parseFloat(route.query.category) || null;
    }
);

useHead({
    titleTemplate: `%s - Магазин`,
});

</script>
