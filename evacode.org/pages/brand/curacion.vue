<template>
    <Header/>
    <div v-if="brand" class="brand-cura">
        <section class="brand-cura__hero">
            <img
                v-if="brand.hero"
                class="brand-cura__hero-photo"
                :src="brand.hero"
                :alt="brand.name"
                width="1920"
                height="1280"
                decoding="async"
                fetchpriority="high"
            >
            <div class="brand-cura__hero-veil" aria-hidden="true"></div>
            <div class="brand-cura__hero-inner">
                <p class="brand-cura__kicker">{{ brand.native_caption || 'EvaCode' }}</p>
                <h1 class="brand-cura__title">{{ brand.name }}</h1>
                <p v-if="brand.lead" class="brand-cura__lead">{{ brand.lead }}</p>
            </div>
        </section>

        <section v-if="origin" v-reveal class="brand-cura__year">
            <div class="container">
                <p class="brand-cura__year-value">{{ origin.value }}</p>
                <p class="brand-cura__year-label">{{ origin.label }}</p>
            </div>
        </section>

        <section v-if="brand.history" v-reveal class="brand-cura__story">
            <div class="container brand-cura__story-grid">
                <div class="brand-cura__story-copy">
                    <p class="brand-cura__eyebrow">История</p>
                    <h2 class="brand-cura__heading">{{ brand.history_title || 'История' }}</h2>
                    <p class="brand-cura__text">{{ brand.history }}</p>
                </div>
                <figure v-if="brand.history_image" class="brand-cura__story-photo">
                    <img
                        :src="brand.history_image"
                        :alt="brand.name"
                        width="1600"
                        height="1066"
                        loading="lazy"
                        decoding="async"
                    >
                </figure>
            </div>
        </section>

        <section v-if="brand.mission" v-reveal class="brand-cura__mission">
            <div class="container brand-cura__mission-grid">
                <figure v-if="brand.logo" class="brand-cura__mission-photo">
                    <img
                        :src="brand.logo"
                        :alt="brand.name"
                        width="1100"
                        height="834"
                        loading="lazy"
                        decoding="async"
                    >
                </figure>
                <div class="brand-cura__mission-copy">
                    <p class="brand-cura__eyebrow">Философия</p>
                    <h2 class="brand-cura__heading">{{ brand.mission_title || 'Lacto Care' }}</h2>
                    <p class="brand-cura__text">{{ brand.mission }}</p>
                </div>
            </div>
        </section>

        <section v-if="lines.length" v-reveal class="brand-cura__ritual">
            <div class="container">
                <p class="brand-cura__eyebrow brand-cura__eyebrow--center">Ритуал</p>
                <h2 class="brand-cura__heading brand-cura__heading--center">Lacto Care</h2>
                <ol class="brand-cura__steps">
                    <li v-for="(line, index) in lines" :key="line.title" class="brand-cura__step">
                        <span class="brand-cura__step-num">{{ String(index + 1).padStart(2, '0') }}</span>
                        <figure v-if="line.image" class="brand-cura__step-photo">
                            <img
                                :src="line.image"
                                :alt="line.title"
                                width="1200"
                                height="800"
                                loading="lazy"
                                decoding="async"
                            >
                        </figure>
                        <h3 class="brand-cura__step-title">{{ line.title }}</h3>
                        <p class="brand-cura__step-text">{{ line.body }}</p>
                    </li>
                </ol>
            </div>
        </section>

        <section v-if="brand.partnership" v-reveal class="brand-cura__partner">
            <div class="container">
                <p class="brand-cura__eyebrow brand-cura__eyebrow--center">EvaCode</p>
                <h2 class="brand-cura__heading brand-cura__heading--center">
                    {{ brand.partnership_title || 'Партнёрство' }}
                </h2>
                <p class="brand-cura__partner-text">{{ brand.partnership }}</p>
                <div v-if="gallery.length" class="brand-cura__gallery">
                    <figure
                        v-for="(shot, index) in gallery"
                        :key="shot.image"
                        class="brand-cura__gallery-item"
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

        <section id="brand-goods" v-reveal class="brand-cura__goods">
            <div class="container">
                <p class="brand-cura__eyebrow brand-cura__eyebrow--center">Каталог</p>
                <h2 class="brand-cura__heading brand-cura__heading--center">Товары {{ brand.name }}</h2>
                <div class="product-wrapper-grid catalog-grid-stable">
                    <div class="row">
                        <WidgetsProductSkeletons v-if="goodsPending" :count="6" />
                        <div v-else-if="!products.length" class="col-12">
                            <p class="brand-cura__empty">Сейчас нет товаров {{ brand.name }} в наличии.</p>
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

        <section v-reveal class="brand-cura__cta">
            <div class="container">
                <p class="brand-cura__cta-brand">{{ brand.name }}</p>
                <h2 class="brand-cura__cta-title">Смотреть каталог {{ brand.name }}</h2>
                <p class="brand-cura__cta-text">Оригинальный лакто-уход Nineone Cosmedi в EvaCode.</p>
                <a href="#brand-goods" class="brand-cura__cta-btn">К товарам</a>
            </div>
        </section>
    </div>
    <Footer/>
</template>

<script setup>
const runtimeConfig = useRuntimeConfig();

const { data: brand, error: brandError } = await useAsyncData(
    'brand-page:curacion',
    () => $fetch(`${runtimeConfig.public.apiBase}/market/brands/curacion/`),
);

if (brandError.value || !brand.value) {
    throw createError({
        statusCode: 404,
        statusMessage: 'Страница бренда не найдена',
        fatal: true,
    });
}

const { data: goodsResponse, pending: goodsPending } = await useAsyncData(
    'brand-goods:curacion',
    () => $fetch(`${runtimeConfig.public.apiBase}/market/goods`, {
        query: {
            brand: 'curacion',
            page_size: 100,
            ordering: 'title',
        },
    }),
);

const products = computed(() => goodsResponse.value?.results || []);
const facts = computed(() => brand.value?.facts || []);
const origin = computed(() => facts.value[0] || null);
const lines = computed(() => brand.value?.lines || []);
const gallery = computed(() => brand.value?.gallery || []);

useHead({
    title: () => (brand.value?.name
        ? `${brand.value.name} — купить в EvaCode`
        : 'Curación — EvaCode'),
    meta: [
        {
            name: 'description',
            content: () => brand.value?.lead
                || 'Curación — лакто-уход Nineone Cosmedi в магазине EvaCode.',
        },
    ],
});
</script>
