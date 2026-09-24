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
const apiBase = useRuntimeConfig().public.apiBase;

const { data, pending } = await useAsyncData(
    'home-featured-bestsellers',
    () =>
        $fetch(`${apiBase}/market/goods`, {
            query: {
                bestseller: true,
                page_size: 12,
            },
        }).catch(() => ({ results: [] })),
);

const products = computed(() => data.value?.results || []);
</script>
