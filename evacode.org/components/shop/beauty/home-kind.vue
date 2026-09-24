<template>
    <ShopBeautyHomeRail
        v-if="visible"
        :eyebrow="eyebrow"
        :title="sectionTitle"
        :lead="sectionLead"
        :ritual="ritual"
        :watermark="watermark"
        :feature-note="featureNote"
        :products="products"
        :pending="pending"
        :more-to="moreTo"
        :more-label="moreLabel"
        :tone="tone"
        :accent="accent"
    />
</template>

<script setup>
const props = defineProps({
    kindSlugs: { type: Array, required: true },
    resolveLargest: { type: Boolean, default: false },
    eyebrow: { type: String, default: 'Линейка' },
    title: { type: String, default: '' },
    lead: { type: String, default: '' },
    ritual: { type: String, default: '' },
    watermark: { type: String, default: '' },
    featureNote: { type: String, default: '' },
    tone: { type: String, default: 'white' },
    accent: { type: String, default: 'left' },
    pageSize: { type: Number, default: 9 },
});

const apiBase = useRuntimeConfig().public.apiBase;
const asyncKey = `home-kind-${props.kindSlugs.join('-')}-${props.resolveLargest ? 'max' : 'first'}`;

const { data, pending } = await useAsyncData(asyncKey, async () => {
    const facets = await $fetch(`${apiBase}/market/catalog-filters/`).catch(() => ({ kinds: [] }));
    const kinds = facets?.kinds || [];
    const wanted = props.kindSlugs
        .map((slug) => kinds.find((row) => row.slug === slug))
        .filter(Boolean);

    let chosen = wanted[0] || {
        slug: props.kindSlugs[0],
        name: props.title || props.kindSlugs[0],
        count: 0,
    };
    if (props.resolveLargest && wanted.length) {
        chosen = [...wanted].sort((a, b) => (b.count || 0) - (a.count || 0))[0];
    }

    const goods = await $fetch(`${apiBase}/market/goods`, {
        query: {
            kind: chosen.slug,
            page_size: props.pageSize,
        },
    }).catch(() => ({ results: [] }));

    return {
        chosen,
        results: goods?.results || [],
    };
});

const products = computed(() => data.value?.results || []);
const visible = computed(() => pending.value || products.value.length > 0);
const sectionTitle = computed(() => props.title || data.value?.chosen?.name || 'Товары');
const sectionLead = computed(() => props.lead);
const moreTo = computed(() => ({
    path: '/collection/leftsidebar/0/',
    query: { kind: data.value?.chosen?.slug || props.kindSlugs[0] },
}));
const moreLabel = computed(() => `Все: ${sectionTitle.value}`);
</script>
