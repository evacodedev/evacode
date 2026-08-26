<template>
    <Header/>
    <WidgetsBackButton />
    <ShopBeautyBigTextSection
        :content="aboutTermsOfUse"
    />
    <ShopBeautyTestimonials />
    <ShopBeautyAboutSlider />
    <Footer/>
</template>
<script setup>

import {useAboutStore} from '~/store/about';
const aboutTermsOfUse = await useAboutStore().aboutTermsOfUse;

useHead({
    titleTemplate: `%s - ${aboutTermsOfUse.title || ''}`,
    meta: [
        {
            name: 'description',
            content: `Evacode - интернет магазин корейской косметики - ${aboutTermsOfUse.title || ''}`
        },
    ]
});
</script>

