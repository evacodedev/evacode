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
    sectionKey: { type: String, default: '' },
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

const { payload, pending } = useHomePageSection();
const key = computed(() => props.sectionKey || props.kindSlugs[0]);
const section = computed(() => payload.value?.kinds?.[key.value] || null);

const products = computed(() => section.value?.results || []);
const visible = computed(() => pending.value || products.value.length > 0);
const sectionTitle = computed(() => props.title || section.value?.chosen?.name || 'Товары');
const sectionLead = computed(() => props.lead);
const moreTo = computed(() => ({
    path: '/collection/leftsidebar/0/',
    query: { kind: section.value?.chosen?.slug || props.kindSlugs[0] },
}));
const moreLabel = computed(() => `Все: ${sectionTitle.value}`);
</script>
