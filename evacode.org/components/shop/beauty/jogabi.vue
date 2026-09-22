<template>
    <section v-reveal class="home-brand">
        <div class="container">
            <div class="home-brand__stage">
                <nuxt-link v-if="cover" class="home-brand__photo" to="/brand/jogabi">
                    <img
                        :src="cover"
                        :alt="brandName"
                        width="1200"
                        height="900"
                        loading="lazy"
                        decoding="async"
                    >
                </nuxt-link>
                <div class="home-brand__copy">
                    <p class="home-brand__kicker">Эксклюзив</p>
                    <h2 class="home-brand__title">{{ brandName }}</h2>
                    <p v-if="lead" class="home-brand__lead">{{ lead }}</p>
                    <nuxt-link class="home-brand__about" to="/brand/jogabi">О бренде</nuxt-link>
                </div>
            </div>

            <div class="product-wrapper-grid home-brand__goods">
                <div class="row">
                    <template v-if="goodsPending">
                        <div
                            v-for="n in 4"
                            :key="'sk-' + n"
                            class="col-grid-box col-xl-3 col-md-3 col-6"
                        >
                            <div class="product-box product-skeleton" aria-hidden="true">
                                <div class="product-card">
                                    <div class="img-wrapper skeleton-block"></div>
                                    <div class="product-detail">
                                        <div class="skeleton-line"></div>
                                        <div class="skeleton-line"></div>
                                        <div class="skeleton-line short"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </template>
                    <div
                        v-for="(product, index) in products"
                        v-else
                        :key="product.id"
                        class="col-grid-box col-xl-3 col-md-3 col-6"
                    >
                        <div class="product-box">
                            <ProductBoxProductBox1 :product="product" :index="index" />
                        </div>
                    </div>
                </div>
            </div>

            <p class="home-brand__more">
                <nuxt-link to="/brand/jogabi">Все товары {{ brandName }}</nuxt-link>
            </p>
        </div>
    </section>
</template>

<script setup>
const runtimeConfig = useRuntimeConfig();
const apiBase = runtimeConfig.public.apiBase;

const { data: brand } = await useAsyncData(
    'home-brand-jogabi',
    () => $fetch(`${apiBase}/market/brands/jogabi/`).catch(() => null),
);

const { data: goodsResponse, pending: goodsPending } = await useAsyncData(
    'home-brand-jogabi-goods',
    () => $fetch(`${apiBase}/market/goods`, {
        query: {
            brand: 'jogabi',
            page_size: 4,
            ordering: 'title',
        },
    }).catch(() => ({ results: [] })),
);

const products = computed(() => goodsResponse.value?.results || []);
const brandName = computed(() => brand.value?.name || 'JOGABI');
const lead = computed(() => brand.value?.lead || '');
const cover = computed(() => brand.value?.history_image || brand.value?.hero || '');
</script>
