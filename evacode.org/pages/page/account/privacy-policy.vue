<template>
    <Header/>
    <WidgetsBackButton />
    <ShopBeautyBigTextSection
        :content="privacyPolicy"
    />
    <ShopBeautyTestimonials />
    <ShopBeautyAboutSlider />
    <Footer/>
</template>
<script setup>

import {useAboutStore} from '~/store/about';
const privacyPolicy = await useAboutStore().aboutPrivacyPolicy;

useHead({
    titleTemplate: `%s - ${privacyPolicy.title || ''}`,
    meta: [
        {
            name: 'description',
            content: `Evacode - интернет магазин корейской косметики - ${privacyPolicy.title || ''}`
        },
    ]
});
</script>

