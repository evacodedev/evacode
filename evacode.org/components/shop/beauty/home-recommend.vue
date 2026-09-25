<template>
    <ShopBeautyHomeRail
        v-if="products.length || pending"
        eyebrow="Рядом с хитами"
        title="Рекомендуем"
        lead="Похожие позиции к бестселлерам — те же типы ухода и бренды."
        ritual="Рядом · Похожие · Выбор"
        watermark="More"
        feature-note="Акцент секции — похожие к хитам каталога."
        :products="products"
        :pending="pending"
        :more-to="{ path: '/collection/leftsidebar/0/' }"
        more-label="В каталог"
        tone="white"
        accent="right"
    />
</template>

<script setup>
const { payload, pending } = useHomePageSection()
const products = computed(() => payload.value?.recommend || [])
</script>
