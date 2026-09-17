<template>
  <div class="collection-filter" :class="{ 'is-open': filtersOpen }">
    <button
        type="button"
        class="catalog-filters-toggle"
        :aria-expanded="filtersOpen"
        aria-controls="catalog-filters-panel"
        @click="filtersOpen = !filtersOpen"
    >
      <span>Фильтры</span>
      <span class="product-pdp__acc-icon" aria-hidden="true"></span>
    </button>
    <div
        id="catalog-filters-panel"
        class="catalog-filters-panel"
        :class="{ 'is-open': filtersOpen }"
        :inert="panelInert"
    >
      <div class="catalog-filters-inner">
        <sidebar-categories
            :current-category="currentCategory"
            @applied="closeFilters"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import SidebarCategories from '~/components/widgets/sidebar-categories.vue';

defineProps({
  currentCategory: {
    type: Number,
    default: 0,
  },
});

const MOBILE_FILTERS = '(max-width: 991px)';
const isMobile = ref(false);
const filtersOpen = ref(false);
const panelInert = computed(() => isMobile.value && !filtersOpen.value);
const closeFilters = () => {
  filtersOpen.value = false;
};

onMounted(() => {
  const media = window.matchMedia(MOBILE_FILTERS);
  const sync = () => {
    isMobile.value = media.matches;
    if (!media.matches) {
      filtersOpen.value = true;
    }
  };
  sync();
  media.addEventListener('change', sync);
  onBeforeUnmount(() => {
    media.removeEventListener('change', sync);
  });
});
</script>
