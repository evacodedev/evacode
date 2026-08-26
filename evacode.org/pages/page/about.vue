<template>
    <Header/>
    <div>
        <section class="about-section-with-img">
            <div class="container-img container">
                <div class="about-background">
                    <WidgetsBrandLogo :logo_type="'white'" />
                    <h2>{{ about.title }}</h2>
                </div>
            </div>
            <div class="container-img-fluid container-fluid about-background">
                <h2>{{ about.title }}</h2>
            </div>
        </section>
        <section class="about-page section-b-space">
            <div class="container">
                <div class="row">
                    <div class="col-lg-6 col-12">
                        <div class="banner-section">
                            <img src="/images/new_evacode/about-logo.png" alt/>
                        </div>
                    </div>
                    <div class="col-lg-6 col-12">
                        <div v-html="about.description"></div>
                    </div>
                </div>
            </div>
        </section>
        <section class="about-illustration-section first">
            <div class="container">
                <div class="row gx-5">
                    <div class="col-xl-3 col-12">
                        <img class="about-illustration-img" src="/images/new_evacode/about-illustr-1.png" alt="happy girl">
                    </div>
                    <div class="col-xl-9 col-12">
                        <div class="about-illustration-text-column">
                            <h3 class="about-illustration-title">Персональные консультации и уход</h3>
                            <p class="about-illustration-description">В нашем штате работают свыше 20 консультантов по всему миру, которые в любое время суток помогут подобрать индивидуальный уход для лица, тела и волос, при этом – оформить заказ и довести
                                вас до желаемого результата.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        <section class="about-illustration-section second">
            <div class="container">
                <div class="row gx-5">
                    <div class="col-xl-9 col-12">
                        <div class="about-illustration-text-column">
                            <h3 class="about-illustration-title">ЦЕННОСТИ EVACODE</h3>
                            <p class="about-illustration-description">Ценности нашей компании – осознанный подход к красоте и здоровью наших клиентов, а также качество поставляемой продукции.</p>
                        </div>
                    </div>
                    <div class="col-xl-3 col-12">
                        <img class="about-illustration-img" src="/images/new_evacode/about-illustr-2.png" alt="happy girl">
                    </div>
                </div>
            </div>
        </section>
        <section class="about-illustration-section third">
            <div class="container">
                <div class="row gx-5">
                    <div class="col-xl-3 col-12">
                        <img class="about-illustration-img" src="/images/new_evacode/about-illustr-3.png" alt="happy girl">
                    </div>
                    <div class="col-xl-9 col-12">
                        <div class="about-illustration-text-column">
                            <h3 class="about-illustration-title">Забота о каждой женщине</h3>
                            <p class="about-illustration-description">Мы стремимся слышать всех женщин, где бы они ни жили и чем бы ни занимались, и удовлетворять их потребности.</p>
                        </div>
                    </div>
                </div>
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
useHead({
    titleTemplate: `%s - ${about.title}`,
    meta: [
        {
            name: 'description',
            content: 'Evacode - интернет магазин корейской косметики - О нас'
        },
    ]
});
</script>
