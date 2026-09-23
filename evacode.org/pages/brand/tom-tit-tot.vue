<template>
    <Header/>
    <div v-if="brand" class="brand-ttt">
        <section class="brand-ttt__hero">
            <img
                v-if="brand.hero"
                class="brand-ttt__hero-photo"
                :src="brand.hero"
                :alt="brand.name"
                width="1600"
                height="2200"
                decoding="async"
                fetchpriority="high"
            >
            <div class="brand-ttt__hero-veil" aria-hidden="true"></div>
            <div class="brand-ttt__hero-inner">
                <img
                    class="brand-ttt__mark"
                    src="/images/brands/tom-tit-tot/logo.png"
                    alt=""
                    width="212"
                    height="40"
                    decoding="async"
                >
                <p class="brand-ttt__kicker">{{ brand.native_caption || 'EvaCode' }}</p>
                <h1 class="brand-ttt__title">{{ brand.name }}</h1>
                <p v-if="brand.lead" class="brand-ttt__lead">{{ brand.lead }}</p>
            </div>
        </section>

        <section v-if="facts.length" v-reveal class="brand-ttt__certs">
            <div class="container brand-ttt__certs-grid">
                <div v-for="fact in facts" :key="fact.value" class="brand-ttt__cert">
                    <p class="brand-ttt__cert-value">{{ fact.value }}</p>
                    <p class="brand-ttt__cert-label">{{ fact.label }}</p>
                </div>
            </div>
        </section>

        <section v-if="brand.history" v-reveal class="brand-ttt__story">
            <div class="container brand-ttt__story-grid">
                <div class="brand-ttt__story-copy">
                    <p class="brand-ttt__eyebrow">История</p>
                    <h2 class="brand-ttt__heading">{{ brand.history_title || 'История' }}</h2>
                    <p class="brand-ttt__text">{{ brand.history }}</p>
                </div>
                <figure v-if="brand.history_image" class="brand-ttt__story-photo">
                    <img
                        :src="brand.history_image"
                        :alt="brand.name"
                        width="1600"
                        height="1200"
                        loading="lazy"
                        decoding="async"
                    >
                </figure>
            </div>
        </section>

        <section v-if="brand.mission" v-reveal class="brand-ttt__mission">
            <div class="container brand-ttt__mission-grid">
                <figure v-if="brand.logo" class="brand-ttt__mission-photo">
                    <img
                        :src="brand.logo"
                        :alt="brand.name"
                        width="800"
                        height="1100"
                        loading="lazy"
                        decoding="async"
                    >
                </figure>
                <div class="brand-ttt__mission-copy">
                    <p class="brand-ttt__eyebrow">Философия</p>
                    <h2 class="brand-ttt__heading">{{ brand.mission_title || 'Философия' }}</h2>
                    <p class="brand-ttt__text">{{ brand.mission }}</p>
                </div>
            </div>
        </section>

        <section v-if="lines.length" v-reveal class="brand-ttt__lines">
            <div class="container">
                <p class="brand-ttt__eyebrow brand-ttt__eyebrow--center">Линейки</p>
                <h2 class="brand-ttt__heading brand-ttt__heading--center">Высокая концентрация</h2>
                <ul class="brand-ttt__line-grid">
                    <li v-for="line in lines" :key="line.title" class="brand-ttt__line">
                        <figure v-if="line.image" class="brand-ttt__line-photo">
                            <img
                                :src="line.image"
                                :alt="line.title"
                                width="1200"
                                height="900"
                                loading="lazy"
                                decoding="async"
                            >
                        </figure>
                        <h3 class="brand-ttt__line-title">{{ line.title }}</h3>
                        <p class="brand-ttt__line-text">{{ line.body }}</p>
                    </li>
                </ul>
            </div>
        </section>

        <section v-if="brand.partnership" v-reveal class="brand-ttt__partner">
            <div class="container">
                <p class="brand-ttt__eyebrow brand-ttt__eyebrow--center">EvaCode</p>
                <h2 class="brand-ttt__heading brand-ttt__heading--center">
                    {{ brand.partnership_title || 'Партнёрство' }}
                </h2>
                <p class="brand-ttt__partner-text">{{ brand.partnership }}</p>
                <div v-if="gallery.length" class="brand-ttt__gallery">
                    <figure
                        v-for="(shot, index) in gallery"
                        :key="shot.image"
                        class="brand-ttt__gallery-item"
                        :class="{ 'is-lead': index === 0 }"
                    >
                        <img
                            :src="shot.image"
                            :alt="shot.alt || brand.name"
                            :width="index === 0 ? 1800 : 1600"
                            :height="index === 0 ? 1200 : 1600"
                            loading="lazy"
                            decoding="async"
                        >
                    </figure>
                </div>
            </div>
        </section>

        <section id="brand-goods" v-reveal class="brand-ttt__goods">
            <div class="container">
                <p class="brand-ttt__eyebrow brand-ttt__eyebrow--center">Каталог</p>
                <h2 class="brand-ttt__heading brand-ttt__heading--center">Товары {{ brand.name }}</h2>
                <div class="product-wrapper-grid catalog-grid-stable">
                    <div class="row">
                        <WidgetsProductSkeletons v-if="goodsPending" :count="6" />
                        <div v-else-if="!products.length" class="col-12">
                            <p class="brand-ttt__empty">Сейчас нет товаров {{ brand.name }} в наличии.</p>
                        </div>
                        <div
                            v-for="(product, index) in products"
                            v-else
                            :key="product.id"
                            class="col-grid-box col-xl-4 col-6"
                        >
                            <div class="product-box">
                                <ProductBoxProductBox1 :product="product" :index="index" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <section v-reveal class="brand-ttt__cta">
            <div class="container">
                <p class="brand-ttt__cta-brand">{{ brand.name }}</p>
                <h2 class="brand-ttt__cta-title">Смотреть каталог {{ brand.name }}</h2>
                <p class="brand-ttt__cta-text">Оригинальный уход TOM-TIT-TOT в EvaCode.</p>
                <a href="#brand-goods" class="brand-ttt__cta-btn">К товарам</a>
            </div>
        </section>
    </div>
    <Footer/>
</template>

<script setup>
const runtimeConfig = useRuntimeConfig();

const { data: brand, error: brandError } = await useAsyncData(
    'brand-page:tom-tit-tot',
    () => $fetch(`${runtimeConfig.public.apiBase}/market/brands/tom-tit-tot/`),
);

if (brandError.value || !brand.value) {
    throw createError({
        statusCode: 404,
        statusMessage: 'Страница бренда не найдена',
        fatal: true,
    });
}

const { data: goodsResponse, pending: goodsPending } = await useAsyncData(
    'brand-goods:tom-tit-tot',
    () => $fetch(`${runtimeConfig.public.apiBase}/market/goods`, {
        query: {
            brand: 'tom-tit-tot',
            page_size: 100,
            ordering: 'title',
        },
    }),
);

const products = computed(() => goodsResponse.value?.results || []);
const facts = computed(() => brand.value?.facts || []);
const lines = computed(() => brand.value?.lines || []);
const gallery = computed(() => brand.value?.gallery || []);

useHead({
    title: () => (brand.value?.name
        ? `${brand.value.name} — купить в EvaCode`
        : 'TOM-TIT-TOT — EvaCode'),
    meta: [
        {
            name: 'description',
            content: () => brand.value?.lead
                || 'TOM-TIT-TOT — премиальный корейский уход в магазине EvaCode.',
        },
    ],
});
</script>
