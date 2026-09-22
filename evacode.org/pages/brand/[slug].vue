<template>
    <Header/>
    <div v-if="brand" class="brand-lux">
        <section class="brand-lux__hero">
            <img
                v-if="brand.hero"
                class="brand-lux__hero-photo"
                :src="brand.hero"
                :alt="brand.name"
                width="1920"
                height="1080"
                decoding="async"
                fetchpriority="high"
            >
            <div class="brand-lux__hero-veil" aria-hidden="true"></div>
            <div class="brand-lux__hero-inner">
                <p class="brand-lux__kicker">EvaCode</p>
                <h1 class="brand-lux__title">{{ brand.name }}</h1>
                <p v-if="brand.lead" class="brand-lux__lead">{{ brand.lead }}</p>
            </div>
        </section>

        <section v-if="origin" v-reveal class="brand-lux__intro">
            <div class="container">
                <p class="brand-lux__origin-year">{{ origin.value }}</p>
                <p class="brand-lux__origin-text">{{ origin.label }}</p>
            </div>
        </section>

        <section v-if="brand.history" v-reveal class="brand-lux__story">
            <div class="container">
                <div class="brand-lux__story-grid">
                    <figure v-if="brand.history_image" class="brand-lux__story-photo">
                        <img
                            :src="brand.history_image"
                            :alt="brand.name"
                            width="1600"
                            height="1066"
                            loading="lazy"
                            decoding="async"
                        >
                    </figure>
                    <div class="brand-lux__story-copy">
                        <p class="brand-lux__eyebrow">История</p>
                        <h2 class="brand-lux__story-title">{{ brand.history_title || 'История' }}</h2>
                        <p class="brand-lux__story-text">{{ brand.history }}</p>
                    </div>
                </div>
            </div>
        </section>

        <section v-if="brand.mission" v-reveal class="brand-lux__story is-alt is-reverse">
            <div class="container">
                <div class="brand-lux__story-grid">
                    <figure v-if="brand.logo" class="brand-lux__story-photo">
                        <img
                            :src="brand.logo"
                            :alt="brand.name"
                            width="1400"
                            height="2100"
                            loading="lazy"
                            decoding="async"
                        >
                    </figure>
                    <div class="brand-lux__story-copy">
                        <p class="brand-lux__eyebrow">Миссия</p>
                        <h2 class="brand-lux__story-title">{{ brand.mission_title || 'Миссия' }}</h2>
                        <p class="brand-lux__story-text">{{ brand.mission }}</p>
                    </div>
                </div>
            </div>
        </section>

        <section v-if="lines.length" v-reveal class="brand-lux__lines">
            <div class="container">
                <p class="brand-lux__eyebrow brand-lux__eyebrow--center">Линии</p>
                <h2 class="brand-lux__section-title">Три линии JOGABI</h2>
                <ul class="brand-lux__line-grid">
                    <li v-for="line in lines" :key="line.title" class="brand-lux__line">
                        <figure v-if="line.image" class="brand-lux__line-photo">
                            <img
                                :src="line.image"
                                :alt="line.title"
                                width="1400"
                                height="2100"
                                loading="lazy"
                                decoding="async"
                            >
                        </figure>
                        <h3 class="brand-lux__line-title">{{ line.title }}</h3>
                        <p class="brand-lux__line-text">{{ line.body }}</p>
                    </li>
                </ul>
            </div>
        </section>

        <section v-if="brand.partnership" v-reveal class="brand-lux__partner">
            <div class="container">
                <p class="brand-lux__eyebrow brand-lux__eyebrow--center">EvaCode</p>
                <h2 class="brand-lux__section-title">{{ brand.partnership_title || 'Партнёрство' }}</h2>
                <p class="brand-lux__partner-text">{{ brand.partnership }}</p>
                <div v-if="gallery.length" class="brand-lux__gallery">
                    <figure
                        v-for="(shot, index) in gallery"
                        :key="shot.image"
                        class="brand-lux__gallery-item"
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
                <div v-if="videoEmbed" class="brand-lux__film">
                    <p class="brand-lux__eyebrow brand-lux__eyebrow--center">{{ brand.video_title || 'Фильм' }}</p>
                    <div class="brand-lux__film-frame">
                        <button
                            v-if="!videoPlaying"
                            class="brand-lux__film-play"
                            type="button"
                            :aria-label="'Смотреть фильм ' + brand.name"
                            @click="videoPlaying = true"
                        >
                            <img
                                class="brand-lux__film-poster"
                                :src="videoPoster"
                                :alt="brand.video_title || brand.name"
                                width="1280"
                                height="720"
                                loading="lazy"
                                decoding="async"
                            >
                            <span class="brand-lux__film-btn" aria-hidden="true"></span>
                        </button>
                        <iframe
                            v-else
                            class="brand-lux__film-iframe"
                            :src="videoEmbed"
                            :title="brand.video_title || ('Фильм ' + brand.name)"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                            allowfullscreen
                        ></iframe>
                    </div>
                </div>
            </div>
        </section>

        <section id="brand-goods" v-reveal class="brand-lux__goods">
            <div class="container">
                <p class="brand-lux__eyebrow brand-lux__eyebrow--center">Каталог</p>
                <h2 class="brand-lux__section-title">Товары {{ brand.name }}</h2>
                <div class="product-wrapper-grid catalog-grid-stable">
                    <div class="row">
                        <WidgetsProductSkeletons v-if="goodsPending" :count="6" />
                        <div v-else-if="!products.length" class="col-12">
                            <p class="brand-lux__empty">Сейчас нет товаров {{ brand.name }} в наличии.</p>
                            <p class="brand-lux__empty-link">
                                <nuxt-link to="/collection/leftsidebar/0">Открыть каталог</nuxt-link>
                            </p>
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

        <section v-reveal class="brand-lux__cta">
            <div class="container">
                <p class="brand-lux__cta-brand">{{ brand.name }}</p>
                <h2 class="brand-lux__cta-title">Смотреть все товары {{ brand.name }}</h2>
                <p class="brand-lux__cta-text">EvaCode — эксклюзивный партнёр {{ brand.name }} в России и СНГ.</p>
                <a href="#brand-goods" class="brand-lux__cta-btn">К товарам</a>
            </div>
        </section>
    </div>
    <Footer/>
</template>

<script setup>
const route = useRoute();
const runtimeConfig = useRuntimeConfig();
const slug = computed(() => String(route.params.slug || ''));

const { data: brand, error: brandError } = await useAsyncData(
    `brand-page:${slug.value}`,
    () => $fetch(`${runtimeConfig.public.apiBase}/market/brands/${encodeURIComponent(slug.value)}/`),
);

if (brandError.value || !brand.value) {
    throw createError({
        statusCode: 404,
        statusMessage: 'Страница бренда не найдена',
        fatal: true,
    });
}

const { data: goodsResponse, pending: goodsPending } = await useAsyncData(
    `brand-goods:${slug.value}`,
    () => $fetch(`${runtimeConfig.public.apiBase}/market/goods`, {
        query: {
            brand: slug.value,
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
const videoPlaying = ref(false);

const youtubeId = (url) => {
    const raw = String(url || '');
    const match = raw.match(
        /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{6,})/,
    );
    return match ? match[1] : '';
};

const videoId = computed(() => youtubeId(brand.value?.video_url));
const videoEmbed = computed(() => {
    if (!videoId.value) {
        return '';
    }
    const params = 'autoplay=1&rel=0&modestbranding=1&color=white';
    return `https://www.youtube-nocookie.com/embed/${videoId.value}?${params}`;
});
const videoPoster = computed(() => brand.value?.hero || brand.value?.history_image || '');

useHead({
    title: () => (brand.value?.name
        ? `${brand.value.name} — купить в EvaCode`
        : 'Бренд — EvaCode'),
    meta: [
        {
            name: 'description',
            content: () => brand.value?.lead
                || (brand.value?.name
                    ? `${brand.value.name} — оригинальный корейский уход в магазине EvaCode. Опт и розница, доставка из Кореи.`
                    : 'Корейский бренд в магазине EvaCode.'),
        },
    ],
});
</script>
