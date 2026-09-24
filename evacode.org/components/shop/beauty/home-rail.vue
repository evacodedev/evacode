<template>
    <section v-reveal class="home-rail" :class="sectionClass">
        <div class="container">
            <header class="home-rail__head">
                <p v-if="eyebrow" class="home-rail__eyebrow">{{ eyebrow }}</p>
                <div class="home-rail__titles">
                    <h2 class="home-rail__title">{{ title }}</h2>
                    <p v-if="lead" class="home-rail__lead">{{ lead }}</p>
                    <p v-if="ritual" class="home-rail__ritual" aria-hidden="true">{{ ritual }}</p>
                </div>
                <nuxt-link v-if="moreTo" class="home-rail__more" :to="moreTo">{{ moreLabel }}</nuxt-link>
            </header>

            <div
                v-if="pending && !products.length"
                class="home-rail__track home-rail__track--spotlight"
                :class="{ 'home-rail__track--accent-right': accentRight }"
            >
                <div
                    v-for="n in 3"
                    :key="'sk-' + n"
                    class="home-rail__slide"
                    :class="{ 'home-rail__slide--feature': n === 1 }"
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
            </div>

            <p v-else-if="!products.length" class="home-rail__empty">Скоро здесь появятся товары.</p>

            <div
                v-else
                class="home-rail__spotlight"
                :class="{ 'home-rail__spotlight--accent-right': accentRight }"
            >
                <div class="home-rail__feature">
                    <div class="home-rail__feature-stage">
                        <p v-if="watermark" class="home-rail__watermark" aria-hidden="true">{{ watermark }}</p>
                        <ClientOnly>
                            <Transition name="home-rail-fade" mode="out-in">
                                <div
                                    :key="featured.id"
                                    class="product-box home-rail__feature-card"
                                >
                                    <ProductBoxProductBox1 :product="featured" :index="0" />
                                </div>
                            </Transition>
                        </ClientOnly>
                    </div>
                    <div class="home-rail__feature-meta">
                        <p v-if="featureNote" class="home-rail__feature-note">{{ featureNote }}</p>
                        <div
                            v-if="featurePool.length > 1"
                            class="home-rail__dots"
                            role="tablist"
                            :aria-label="`Смена акцента: ${title}`"
                        >
                            <button
                                v-for="(item, i) in featurePool"
                                :key="item.id"
                                type="button"
                                class="home-rail__dot"
                                :class="{ 'is-active': i === featureIndex }"
                                :aria-label="`Показать ${item.title}`"
                                :aria-selected="i === featureIndex"
                                role="tab"
                                @click="selectFeature(i)"
                            />
                        </div>
                    </div>
                </div>

                <div class="home-rail__side">
                    <ClientOnly>
                        <swiper
                            class="home-rail__swiper home-rail__swiper--side"
                            :modules="modules"
                            :slides-per-view="1.2"
                            :space-between="16"
                            :navigation="true"
                            :breakpoints="sideBreakpoints"
                        >
                            <swiper-slide
                                v-for="(product, index) in sideProducts"
                                :key="product.id"
                                class="home-rail__slide"
                            >
                                <div class="product-box">
                                    <ProductBoxProductBox1 :product="product" :index="index + 1" />
                                </div>
                            </swiper-slide>
                        </swiper>
                    </ClientOnly>
                </div>
            </div>
        </div>
    </section>
</template>

<script setup>
import { Swiper, SwiperSlide } from 'swiper/vue';
import { Navigation } from 'swiper';
import 'swiper/css';
import 'swiper/css/navigation';

const props = defineProps({
    eyebrow: { type: String, default: '' },
    title: { type: String, required: true },
    lead: { type: String, default: '' },
    ritual: { type: String, default: '' },
    watermark: { type: String, default: '' },
    featureNote: { type: String, default: '' },
    products: { type: Array, default: () => [] },
    pending: { type: Boolean, default: false },
    moreTo: { type: [String, Object], default: '' },
    moreLabel: { type: String, default: 'Смотреть все' },
    tone: { type: String, default: 'white' },
    /** left | right — сторона крупного акцента */
    accent: { type: String, default: 'left' },
});

const modules = [Navigation];
const sideBreakpoints = {
    576: { slidesPerView: 2, spaceBetween: 16 },
    992: { slidesPerView: 2, spaceBetween: 20 },
};

const accentRight = computed(() => props.accent === 'right');

const sectionClass = computed(() => [
    props.tone === 'ivory' ? 'home-rail--ivory' : 'home-rail--white',
    'home-rail--spotlight',
    accentRight.value ? 'home-rail--accent-right' : 'home-rail--accent-left',
]);

const featurePool = computed(() => (props.products || []).slice(0, 3));
const featureIndex = ref(0);
let rotateTimer = null;

const featured = computed(
    () => featurePool.value[featureIndex.value] || props.products[0] || null,
);

const sideProducts = computed(() => {
    const id = featured.value?.id;
    return (props.products || []).filter((item) => item.id !== id).slice(0, 8);
});

const selectFeature = (index) => {
    featureIndex.value = index;
    restartRotate();
};

const restartRotate = () => {
    if (!import.meta.client) {
        return;
    }
    if (rotateTimer) {
        clearInterval(rotateTimer);
        rotateTimer = null;
    }
    if (featurePool.value.length < 2) {
        return;
    }
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) {
        return;
    }
    rotateTimer = setInterval(() => {
        featureIndex.value = (featureIndex.value + 1) % featurePool.value.length;
    }, 5200);
};

watch(
    () => props.products,
    () => {
        featureIndex.value = 0;
        restartRotate();
    },
    { deep: false },
);

onMounted(() => {
    restartRotate();
});

onBeforeUnmount(() => {
    if (rotateTimer) {
        clearInterval(rotateTimer);
    }
});
</script>
