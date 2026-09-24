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
const apiBase = useRuntimeConfig().public.apiBase;

const { data, pending } = await useAsyncData('home-recommend-bundle', async () => {
    const hitsPayload = await $fetch(`${apiBase}/market/goods`, {
        query: { bestseller: true, page_size: 12 },
    }).catch(() => ({ results: [] }));

    const hits = hitsPayload?.results || [];
    const hitIds = new Set(hits.map((item) => item.id));
    const brands = [...new Set(hits.map((item) => item.content_brand?.slug).filter(Boolean))].slice(0, 6);
    const kinds = [...new Set(hits.map((item) => item.content_kind?.slug).filter(Boolean))].slice(0, 6);

    if (!brands.length && !kinds.length) {
        return { results: [] };
    }

    const query = { page_size: 24 };
    if (brands.length) {
        query.brand = brands.join(',');
    }
    if (kinds.length) {
        query.kind = kinds.join(',');
    }

    const similarPayload = await $fetch(`${apiBase}/market/goods`, { query }).catch(() => ({ results: [] }));
    const results = (similarPayload?.results || [])
        .filter((item) => !hitIds.has(item.id))
        .slice(0, 9);

    return { results };
});

const products = computed(() => data.value?.results || []);
</script>
