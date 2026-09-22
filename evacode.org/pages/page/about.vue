<template>
    <Header/>
    <div class="about-lux">
        <section class="about-lux__hero">
            <img
                class="about-lux__hero-photo"
                src="/images/new_evacode/about-hero.jpg?v=4"
                alt="Студийный beauty-портрет"
                width="1600"
                height="2400"
                decoding="async"
                fetchpriority="high"
            >
            <div class="about-lux__hero-veil" aria-hidden="true"></div>
            <div class="about-lux__hero-inner">
                <p class="about-lux__brand">EvaCode</p>
                <h1 class="about-lux__title">{{ about.title || 'О нас' }}</h1>
                <p class="about-lux__lead">Люксовая корейская косметика. Официальные поставщики. Забота о каждой женщине.</p>
            </div>
        </section>

        <section v-reveal class="about-lux__intro">
            <div class="container">
                <div class="about-lux__manifesto">
                    <p class="about-lux__eyebrow">О бренде</p>
                    <h2 class="about-lux__manifesto-title">Люксовая корейская косметика с 2018&nbsp;года</h2>
                    <p class="about-lux__manifesto-lead">
                        EvaCode работает с официальными поставщиками корпораций LG Household&nbsp;&amp;&nbsp;HealthCare и Amore&nbsp;Pacific.
                        Офис в Южной Корее — доставка по всему миру.
                    </p>
                </div>

                <ul class="about-lux__facts" aria-label="Ключевые факты">
                    <li class="about-lux__fact">
                        <span class="about-lux__fact-value">7+</span>
                        <span class="about-lux__fact-label">лет на рынке</span>
                    </li>
                    <li class="about-lux__fact">
                        <span class="about-lux__fact-value">20+</span>
                        <span class="about-lux__fact-label">консультантов</span>
                    </li>
                    <li class="about-lux__fact">
                        <span class="about-lux__fact-value">KR</span>
                        <span class="about-lux__fact-label">офис в Корее</span>
                    </li>
                </ul>

                <div class="about-lux__brands">
                    <p class="about-lux__brands-label">Бренды в каталоге</p>
                    <ul class="about-lux__brands-list">
                        <li v-for="brand in featuredBrands" :key="brand">{{ brand }}</li>
                    </ul>
                </div>
            </div>
        </section>

        <section
            v-for="(block, index) in storyBlocks"
            :key="block.title"
            v-reveal
            class="about-lux__story"
            :class="{ 'is-reverse': index % 2 === 1, 'is-alt': index % 2 === 1 }"
        >
            <div class="container">
                <div class="about-lux__story-grid">
                    <figure class="about-lux__story-photo">
                        <img
                            :src="block.image"
                            :alt="block.alt"
                            width="1200"
                            height="1500"
                            loading="lazy"
                            decoding="async"
                        >
                    </figure>
                    <div class="about-lux__story-copy">
                        <p class="about-lux__eyebrow">{{ block.eyebrow }}</p>
                        <h2 class="about-lux__story-title">{{ block.title }}</h2>
                        <p class="about-lux__story-text">{{ block.text }}</p>
                    </div>
                </div>
            </div>
        </section>

        <section v-reveal class="about-lux__cta">
            <div class="container">
                <p class="about-lux__cta-brand">EvaCode</p>
                <h2 class="about-lux__cta-title">Откройте каталог</h2>
                <p class="about-lux__cta-text">Оригинальная корейская косметика с персональным подбором ухода.</p>
                <nuxt-link to="/collection/leftsidebar/0/" class="about-lux__cta-btn">В магазин</nuxt-link>
            </div>
        </section>
    </div>
    <ShopBeautyTestimonials />
    <ShopBeautyAboutSlider />
    <Footer/>
</template>

<script setup>
import {useAboutStore} from '~/store/about';

const about = await useAboutStore().aboutPage;

const img = (name) => `/images/new_evacode/${name}`;

const featuredBrands = [
    'THE HISTORY OF WHOO',
    'O HUI',
    'SU:M37',
    'CNP',
    'The Saga of Soo',
    'Sulwhasoo',
    'Hera',
    'Amorepacific',
];

const storyBlocks = [
    {
        eyebrow: 'Консультации',
        title: 'Персональный уход',
        text: 'Более 20 консультантов помогают подобрать уход для лица, тела и волос, оформить заказ и довести вас до желаемого результата.',
        image: img('about-story-consult.jpg'),
        alt: 'Студийный портрет консультанта',
    },
    {
        eyebrow: 'Ценности',
        title: 'Качество и осознанность',
        text: 'Осознанный подход к красоте и здоровью клиентов и только качественная продукция от официальных поставщиков.',
        image: img('about-story-values.jpg'),
        alt: 'Beauty-портрет в студийном свете',
    },
    {
        eyebrow: 'Забота',
        title: 'Для каждой женщины',
        text: 'Мы стремимся слышать женщин в любой стране и подбирать уход под их ритм жизни и потребности кожи.',
        image: img('about-story-care.jpg'),
        alt: 'Студийная beauty-фотография ухода',
    },
];

useHead({
    title: 'О нас — EvaCode, корейская косметика с 2018 года',
    meta: [
        {
            name: 'description',
            content: 'EvaCode — магазин люксовой корейской косметики. Офис в Южной Корее, поставки LG и Amorepacific, эксклюзив CH6, консультанты и доставка по миру.',
        },
    ],
});
</script>
