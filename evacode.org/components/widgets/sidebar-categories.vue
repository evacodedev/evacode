<template>
  <div class="collection-filter-block">
    <div class="collection-mobile-back">
        <span class="filter-back" @click="onCLick()">
            <i class="fa fa-angle-left" aria-hidden="true"></i> Назад
        </span>
    </div>
    <div class="collection-collapse-block open">
      <h3 class="collapse-block-title">Поиск</h3>
      <div class="collection-collapse-block-content" :style="{ display: 'block'}">
        <form
            :key="appliedFiltersKey"
            class="catalog-filter-form"
            @submit.prevent="applyTextFilters"
        >
          <input
              v-model="searchInput"
              class="form-control"
              type="search"
              placeholder="Название товара"
          >
          <div class="catalog-price-row">
            <input
                v-model="minPriceInput"
                class="form-control"
                type="number"
                min="0"
                placeholder="Цена от"
            >
            <input
                v-model="maxPriceInput"
                class="form-control"
                type="number"
                min="0"
                placeholder="Цена до"
            >
          </div>
          <button class="evacode-btn fill-btn buy-btn catalog-apply-btn" type="submit">Применить</button>
          <button class="evacode-btn buy-btn btn-bordered catalog-reset-btn" type="button" @click="resetFilters">
            Сбросить фильтры
          </button>
        </form>
      </div>
    </div>
    <div class="collection-collapse-block open">
      <h3 class="collapse-block-title">Категории</h3>
      <div class="collection-collapse-block-content" :style="{ display: 'block'}">
        <div class="collection-brand-filter">
          <ul class="category-list">
            <li>
              <nuxt-link
                  :class="{ active: !currentCategory }"
                  :to="catalogListTo(null)"
              >
                Все товары
              </nuxt-link>
            </li>
            <li v-for="(category, index) in categories" :key="index">
              <nuxt-link
                  v-if="category.id !== 1"
                  :class="{ active: category.id === currentCategory }"
                  :to="catalogListTo(category.id)"
              >
                {{ category.name }}
              </nuxt-link>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {useRoute, useRouter} from 'vue-router';

const props = defineProps({
  currentCategory:{
    type: Number,
    default: 0,
  }
});

const emit = defineEmits(['clickBack']);
const route = useRoute();
const router = useRouter();

const appliedFiltersKey = computed(
  () => `${route.query.q || ''}|${route.query.min_price || ''}|${route.query.max_price || ''}`
);

const searchInput = ref(route.query.q || '');
const minPriceInput = ref(route.query.min_price || '');
const maxPriceInput = ref(route.query.max_price || '');

const categoryQuery = computed(() => {
  const query = { ...route.query };
  delete query.page;
  delete query.category;
  delete query.in_stock;
  delete query.bestseller;
  return query;
});

const catalogListTo = (categoryId) => {
  const query = { ...categoryQuery.value };
  if (categoryId) {
    query.category = String(categoryId);
  }
  return { path: '/collection/leftsidebar/0', query };
};

const {data: categoriesResponse} = await useAsyncData(
    'categoriesResponse',
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/categories/`),
    {
      server: false,
    }
);

const categories = computed(() => categoriesResponse.value?.result);

const onCLick = () => {
  emit('clickBack');
};

const patchQuery = async (patch) => {
  const query = { ...route.query, ...patch };
  Object.keys(query).forEach((key) => {
    if (query[key] === undefined || query[key] === '' || query[key] === false) {
      delete query[key];
    }
  });
  await router.push({ path: '/collection/leftsidebar/0', query });
};

const applyTextFilters = () => {
  patchQuery({
    q: searchInput.value.trim() || undefined,
    min_price: minPriceInput.value || undefined,
    max_price: maxPriceInput.value || undefined,
    page: 1,
  });
};

const resetFilters = () => {
  window.location.assign('/collection/leftsidebar/0');
};
</script>

<style scoped>
.category-list .router-link-active.active {
  color: var(--theme-deafult) !important;
}

.catalog-filter-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.catalog-price-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.catalog-apply-btn,
.catalog-reset-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
