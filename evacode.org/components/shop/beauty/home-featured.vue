<template>
    <ShopBeautyHomeRail
        v-if="products.length || pending"
        eyebrow="Выбор EvaCode"
        title="Хиты"
        lead="То, что чаще всего берут повторно — проверенные формулы и любимые позиции."
        ritual="Спрос · Доверие · Повтор"
        watermark="Hits"
        feature-note="Акцент секции — хиты каталога."
        :products="products"
        :pending="pending"
        :more-to="{ path: '/collection/leftsidebar/0/' }"
        more-label="В каталог"
        tone="white"
        accent="left"
    />
</template>

<script setup>
const { payload, pending } = useHomePageSection()
const products = computed(() => payload.value?.bestsellers || [])
</script>
