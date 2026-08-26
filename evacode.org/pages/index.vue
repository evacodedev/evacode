<template>
    <div>
        <Header/>
        <ShopBeautySlider/>
        <section class="products-main-section">
            <div class="container">
                <ShopBeautyProducts
                    :products="products"
                    :pagination-props="paginationProps"
                    :totalProductsCount="totalProductsCount"
                />
            </div>
        </section>
        <ShopBeautyAboutCons/>
        <ShopBeautyLeadership/>
        <ShopBeautyAssortiment/>
        <ShopBeautyPaymentTypes/>
        <ShopBeautyTestimonials />
        <ShopBeautyAboutSlider />
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
const previous = computed(() => productsResponse.value?.previous ? `?${productsResponse.value?.previous.split('?')[1]}` : '');
const next = computed(() => productsResponse.value?.next ? `?${productsResponse.value?.next.split('?')[1]}` : '');
const paginates = computed(() => Math.round(totalProductsCount.value / itemsPerPage.value));

const itemsPerPage = ref(6);
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

const paginationProps = computed(() => {
    return {
        currentPage,
        previous,
        next,
        paginates,
        itemsPerPage: 12,
        paginateRange: 3,
        pages: pages.value,
    }
});

watch(
    () => route.query.page,
    () => {
        currentPage.value = parseFloat(route.query.page) || 1;
    }
);
</script>
