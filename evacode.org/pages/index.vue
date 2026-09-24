<template>
    <div>
        <Header/>
        <ShopBeautySlider/>
        <ShopBeautyHomeFeatured/>
        <ShopBeautyCuracion/>
        <ShopBeautyHomeKind
            :kind-slugs="['set']"
            eyebrow="Группа"
            title="Наборы"
            lead="Готовые комплекты ухода — удобный старт и выгода по сравнению с покупкой по отдельности."
            ritual="Комплект · Выгода · Старт"
            watermark="Set"
            feature-note="Акцент секции — готовые наборы ухода."
            tone="white"
            accent="right"
            :page-size="9"
        />
        <ShopBeautyJogabi/>
        <ShopBeautyHomeKind
            :kind-slugs="['cream', 'eye_cream']"
            resolve-largest
            eyebrow="Группа"
            title="Кремы"
            lead="Базовый ежедневный уход: текстуры и формулы под разные состояния кожи."
            ritual="Текстура · Плотность · Финиш"
            watermark="Cream"
            feature-note="Акцент секции — кремы, которые сейчас в фокусе."
            tone="white"
            accent="left"
            :page-size="9"
        />
        <ShopBeautyTomTitTot/>
        <ShopBeautyHomeRecommend/>
        <ShopBeautyTestimonials/>
        <Footer/>
    </div>
</template>

<script setup>
useHead({
    title: 'EvaCode — люксовая корейская косметика',
});
</script>
