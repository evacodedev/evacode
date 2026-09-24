<template>
  <div ref="rootRef" class="catalog-bar-wrap" :class="{ 'is-global': global }">
    <div class="catalog-bar-row">
      <div class="catalog-bar">
      <div class="catalog-bar__left">
        <button
            type="button"
            class="catalog-bar__btn"
            :class="{ 'is-open': openPanel === 'kind', 'is-on': selectedKinds.length }"
            :aria-expanded="openPanel === 'kind'"
            aria-controls="catalog-pop-kind"
            @click="togglePanel('kind')"
        >
          <span>Категории</span>
          <span v-if="selectedKinds.length" class="catalog-bar__n">{{ selectedKinds.length }}</span>
          <span class="catalog-bar__chev" aria-hidden="true">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
              <path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </button>
        <button
            type="button"
            class="catalog-bar__btn"
            :class="{ 'is-open': openPanel === 'brand', 'is-on': selectedBrands.length }"
            :aria-expanded="openPanel === 'brand'"
            aria-controls="catalog-pop-brand"
            @click="togglePanel('brand')"
        >
          <span>Бренды</span>
          <span v-if="selectedBrands.length" class="catalog-bar__n">{{ selectedBrands.length }}</span>
          <span class="catalog-bar__chev" aria-hidden="true">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
              <path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </button>
        <button
            type="button"
            class="catalog-bar__btn"
            :class="{ 'is-open': openPanel === 'price', 'is-on': hasPrice }"
            :aria-expanded="openPanel === 'price'"
            aria-controls="catalog-pop-price"
            @click="togglePanel('price')"
        >
          <span>Цена</span>
          <span class="catalog-bar__chev" aria-hidden="true">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
              <path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </button>
      </div>
      <form class="catalog-bar__search" @submit.prevent="applySearch">
        <CheckoutField
            v-model="searchInput"
            label="Название товара"
            name="catalog-q"
            type="search"
            autocomplete="off"
        />
      </form>
        <div v-if="$slots.meta" class="catalog-bar__meta">
          <slot name="meta"/>
        </div>
      </div>

      <div
          v-if="openPanel === 'kind'"
          id="catalog-pop-kind"
          class="catalog-pop"
          role="dialog"
          aria-label="Категории"
      >
        <ul class="catalog-pop__list">
          <li v-for="kind in kinds" :key="kind.slug">
            <label
                class="catalog-pop__check"
                :class="{ 'is-on': selectedKinds.includes(kind.slug) }"
            >
              <input
                  type="checkbox"
                  :checked="selectedKinds.includes(kind.slug)"
                  @change="toggleFacet('kind', kind.slug)"
              >
              <span>{{ labelName(kind.name) }}</span>
              <span class="catalog-pop__count">{{ kind.count }}</span>
            </label>
          </li>
        </ul>
        <div class="catalog-pop__foot">
          <button class="catalog-pop__ghost" type="button" @click="clearFacet('kind')">Сбросить</button>
          <button class="catalog-pop__done" type="button" @click="closePanel">Показать</button>
        </div>
      </div>

      <div
          v-else-if="openPanel === 'brand'"
          id="catalog-pop-brand"
          class="catalog-pop"
          role="dialog"
          aria-label="Бренды"
      >
        <input
            v-if="brands.length > 8"
            v-model="brandSearch"
            class="form-control catalog-pop__search"
            type="search"
            placeholder="Найти бренд"
        >
        <ul class="catalog-pop__list catalog-pop__list--scroll">
          <li v-for="brand in visibleBrands" :key="brand.slug">
            <label
                class="catalog-pop__check"
                :class="{ 'is-on': selectedBrands.includes(brand.slug) }"
            >
              <input
                  type="checkbox"
                  :checked="selectedBrands.includes(brand.slug)"
                  @change="toggleFacet('brand', brand.slug)"
              >
              <span>{{ brand.name }}</span>
              <span class="catalog-pop__count">{{ brand.count }}</span>
            </label>
          </li>
        </ul>
        <p v-if="brandSearch && !visibleBrands.length" class="catalog-pop__empty">Бренд не найден</p>
        <div class="catalog-pop__foot">
          <button class="catalog-pop__ghost" type="button" @click="clearFacet('brand')">Сбросить</button>
          <button class="catalog-pop__done" type="button" @click="closePanel">Показать</button>
        </div>
      </div>

      <div
          v-else-if="openPanel === 'price'"
          id="catalog-pop-price"
          class="catalog-pop catalog-pop--price"
          role="dialog"
          aria-label="Цена"
      >
        <div class="catalog-pop__prices">
          <input
              v-model="minPriceInput"
              class="form-control"
              type="number"
              min="0"
              placeholder="От"
          >
          <input
              v-model="maxPriceInput"
              class="form-control"
              type="number"
              min="0"
              placeholder="До"
          >
        </div>
        <div class="catalog-pop__foot">
          <button class="catalog-pop__ghost" type="button" @click="clearFacet('price')">Сбросить</button>
          <button class="catalog-pop__done" type="button" @click="applyPrice">Показать</button>
        </div>
      </div>
    </div>

    <div v-if="chips.length" class="catalog-bar__chips">
      <button
          v-for="chip in chips"
          :key="chip.key"
          type="button"
          class="catalog-chip"
          @click="removeChip(chip)"
      >
        <span>{{ chip.label }}</span>
        <span aria-hidden="true">×</span>
      </button>
      <button type="button" class="catalog-chip catalog-chip--clear" @click="resetFilters">
        Сбросить все
      </button>
    </div>
  </div>
</template>

<script setup>
import {useRoute, useRouter} from 'vue-router';

const route = useRoute();
const router = useRouter();
const props = defineProps({
  /** Compact bar under global header (no page meta slot). */
  global: {
    type: Boolean,
    default: false,
  },
});
const rootRef = ref(null);
const openPanel = ref(null);
const brandSearch = ref('');
const searchInput = ref(route.query.q || '');
const minPriceInput = ref(route.query.min_price || '');
const maxPriceInput = ref(route.query.max_price || '');

const splitQuery = (value) => {
  const raw = Array.isArray(value) ? value : [value];
  return raw
      .flatMap((item) => String(item || '').split(','))
      .map((part) => part.trim())
      .filter(Boolean);
};

const joinQuery = (items) => (items.length ? items.join(',') : undefined);

const selectedBrands = computed(() => splitQuery(route.query.brand));
const selectedKinds = computed(() => splitQuery(route.query.kind));
const hasPrice = computed(() => Boolean(route.query.min_price || route.query.max_price));

const {data: facetsResponse} = await useAsyncData(
    'catalog-filters-facets',
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/catalog-filters/`),
);

const brands = computed(() => facetsResponse.value?.brands || []);
const kinds = computed(() => facetsResponse.value?.kinds || []);
const visibleBrands = computed(() => {
  const query = brandSearch.value.trim().toLowerCase();
  if (!query) {
    return brands.value;
  }
  return brands.value.filter((brand) => {
    const name = (brand.name || '').toLowerCase();
    const slug = (brand.slug || '').toLowerCase();
    return name.includes(query) || slug.includes(query);
  });
});

const labelName = (name) => {
  const text = (name || '').trim();
  if (!text) {
    return text;
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
};

const kindLabel = (slug) => {
  const kind = kinds.value.find((item) => item.slug === slug);
  return labelName(kind?.name || slug);
};

const brandLabel = (slug) => {
  const brand = brands.value.find((item) => item.slug === slug);
  return brand?.name || slug;
};

const chips = computed(() => {
  const items = [];
  selectedKinds.value.forEach((slug) => {
    items.push({key: `kind:${slug}`, type: 'kind', slug, label: kindLabel(slug)});
  });
  selectedBrands.value.forEach((slug) => {
    items.push({key: `brand:${slug}`, type: 'brand', slug, label: brandLabel(slug)});
  });
  if (hasPrice.value) {
    const min = route.query.min_price || '';
    const max = route.query.max_price || '';
    const label = min && max ? `${min}–${max}` : min ? `от ${min}` : `до ${max}`;
    items.push({key: 'price', type: 'price', label: `Цена ${label}`});
  }
  if (route.query.q) {
    items.push({key: 'q', type: 'q', label: String(route.query.q)});
  }
  return items;
});

watch(
    () => [route.query.q, route.query.min_price, route.query.max_price],
    () => {
      searchInput.value = route.query.q || '';
      minPriceInput.value = route.query.min_price || '';
      maxPriceInput.value = route.query.max_price || '';
    },
);

const patchQuery = async (patch) => {
  const query = {...route.query, ...patch};
  Object.keys(query).forEach((key) => {
    if (query[key] === undefined || query[key] === '' || query[key] === false) {
      delete query[key];
    }
  });
  await router.push({path: '/collection/leftsidebar/0', query});
};

const togglePanel = (name) => {
  if (name === 'price' && openPanel.value !== 'price') {
    minPriceInput.value = route.query.min_price || '';
    maxPriceInput.value = route.query.max_price || '';
  }
  if (name === 'brand' && openPanel.value !== 'brand') {
    brandSearch.value = '';
  }
  openPanel.value = openPanel.value === name ? null : name;
};

const closePanel = () => {
  openPanel.value = null;
};

const toggleFacet = async (key, slug) => {
  const current = key === 'brand' ? selectedBrands.value : selectedKinds.value;
  const next = current.includes(slug)
      ? current.filter((item) => item !== slug)
      : [...current, slug];
  await patchQuery({[key]: joinQuery(next), page: 1});
};

const applySearch = async () => {
  await patchQuery({
    q: String(searchInput.value || '').trim() || undefined,
    page: 1,
  });
};

const applyPrice = async () => {
  await patchQuery({
    min_price: minPriceInput.value || undefined,
    max_price: maxPriceInput.value || undefined,
    page: 1,
  });
  closePanel();
};

const clearFacet = async (type) => {
  if (type === 'kind') {
    await patchQuery({kind: undefined, page: 1});
  } else if (type === 'brand') {
    await patchQuery({brand: undefined, page: 1});
  } else if (type === 'price') {
    minPriceInput.value = '';
    maxPriceInput.value = '';
    await patchQuery({min_price: undefined, max_price: undefined, page: 1});
  }
};

const removeChip = async (chip) => {
  if (chip.type === 'kind' || chip.type === 'brand') {
    const key = chip.type;
    const current = key === 'brand' ? selectedBrands.value : selectedKinds.value;
    await patchQuery({[key]: joinQuery(current.filter((item) => item !== chip.slug)), page: 1});
    return;
  }
  if (chip.type === 'price') {
    await clearFacet('price');
    return;
  }
  searchInput.value = '';
  await patchQuery({q: undefined, page: 1});
};

const resetFilters = async () => {
  brandSearch.value = '';
  searchInput.value = '';
  minPriceInput.value = '';
  maxPriceInput.value = '';
  openPanel.value = null;
  const query = {};
  if (route.query.ordering) {
    query.ordering = route.query.ordering;
  }
  if (route.query.page_size) {
    query.page_size = route.query.page_size;
  }
  await router.push({path: '/collection/leftsidebar/0', query});
};

const onDocumentClick = (event) => {
  if (!openPanel.value || !rootRef.value) {
    return;
  }
  if (!rootRef.value.contains(event.target)) {
    closePanel();
  }
};

const onKeydown = (event) => {
  if (event.key === 'Escape') {
    closePanel();
  }
};

onMounted(() => {
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
  document.removeEventListener('keydown', onKeydown);
});
</script>

<style scoped>
.catalog-bar-wrap {
  position: relative;
  margin-bottom: 28px;
  z-index: 5;
}

.catalog-bar-row {
  position: relative;
}

.catalog-bar {
  display: flex;
  align-items: center;
  gap: 20px 28px;
  min-height: 52px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ece8e1;
}

.catalog-bar__left {
  display: flex;
  align-items: center;
  gap: 8px 20px;
  min-width: 0;
  align-self: center;
}

.catalog-bar__btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 44px;
  min-height: 44px;
  padding: 0 2px;
  border: 0;
  border-bottom: 1px solid transparent;
  background: transparent;
  color: #8a8680;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  line-height: 1;
  cursor: pointer;
  transform: scale(1);
  transform-origin: center;
  transition:
      color 240ms var(--motion-ease),
      border-color 240ms var(--motion-ease),
      transform 240ms var(--motion-ease);
}

.catalog-bar__btn:hover {
  color: #1a1917;
  transform: scale(1.03);
}

.catalog-bar__btn.is-open {
  color: #1a1917;
}

.catalog-bar__btn.is-on {
  color: #1a1917;
  border-bottom-color: #b89254;
}

.catalog-bar__n {
  color: #8a8680;
  font-size: 11px;
  letter-spacing: 0;
  font-weight: 400;
}

.catalog-bar__chev {
  display: inline-flex;
  transition: transform 240ms var(--motion-ease);
}

.catalog-bar__btn.is-open .catalog-bar__chev {
  transform: rotate(180deg);
}

@media (prefers-reduced-motion: reduce) {
  .catalog-bar__btn,
  .catalog-bar__chev,
  .catalog-pop__check,
  .catalog-pop__ghost,
  .catalog-pop__done,
  .catalog-chip {
    transition: none;
    transform: none;
  }
}

.catalog-bar__search {
  flex: 1 1 220px;
  min-width: 180px;
  max-width: 320px;
  margin-left: auto;
}

.catalog-bar__search :deep(.checkout-field) {
  margin-bottom: 0;
}

.catalog-bar__search :deep(.checkout-field input) {
  height: 56px;
  padding: 22px 14px 8px;
  border-color: #b89254;
  border-radius: 8px;
}

.catalog-bar__search :deep(.checkout-field label) {
  left: 14px;
}

.catalog-bar__meta {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 16px;
  color: #8a8680;
  font-size: 13px;
  white-space: nowrap;
}

.catalog-pop {
  position: absolute;
  top: calc(100% - 1px);
  left: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  width: min(388px, 100%);
  max-height: min(420px, calc(100vh - 180px));
  padding: 16px 16px 12px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #ece8e1;
}

.catalog-pop--price {
  width: min(320px, 100%);
}

.catalog-pop__search {
  margin-bottom: 12px;
}

.catalog-pop__list {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

.catalog-pop__list > li {
  display: block;
  width: 100%;
}

.catalog-pop__check {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 36px;
  padding: 0 8px 0 7px;
  border-left: 1px solid transparent;
  color: #1a1917;
  font-size: 14px;
  cursor: pointer;
  transition:
      background 240ms var(--motion-ease),
      border-color 240ms var(--motion-ease),
      color 240ms var(--motion-ease);
}

.catalog-pop__check:hover {
  background: #f7f4ef;
}

.catalog-pop__check.is-on {
  background: #f7f4ef;
  border-left-color: #b89254;
}

.catalog-pop__check.is-on span:nth-child(2) {
  font-weight: 500;
}

.catalog-pop__check input {
  width: 16px;
  height: 16px;
  margin: 0;
  flex: 0 0 16px;
  accent-color: #1a1917;
  cursor: pointer;
}

.catalog-pop__check span:nth-child(2) {
  flex: 1 1 auto;
}

.catalog-pop__count {
  color: #8a8680;
  font-size: 12px;
}

.catalog-pop__empty {
  margin: 8px 0 0;
  color: #8a8680;
  font-size: 13px;
}

.catalog-pop__prices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.catalog-pop__foot {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  background: #fff;
  border-top: 1px solid #ece8e1;
}

.catalog-pop__ghost,
.catalog-pop__done {
  min-height: 44px;
  padding: 0 16px;
  border-radius: 0;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  transition:
      color 240ms var(--motion-ease),
      background 240ms var(--motion-ease),
      border-color 240ms var(--motion-ease);
}

.catalog-pop__ghost {
  border: 1px solid #ece8e1;
  background: transparent;
  color: #8a8680;
}

.catalog-pop__ghost:hover {
  color: #1a1917;
  border-color: #1a1917;
}

.catalog-pop__done {
  flex: 1 1 auto;
  border: 1px solid #1a1917;
  background: #1a1917;
  color: #fff;
}

.catalog-pop__done:hover {
  background: #fff;
  color: #1a1917;
}

.catalog-bar__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.catalog-bar-wrap.is-global .catalog-bar__chips {
  margin-top: 10px;
  padding-bottom: 10px;
}

.catalog-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 0 10px;
  border: 1px solid #ece8e1;
  background: #fff;
  color: #1a1917;
  font-size: 13px;
  cursor: pointer;
  transition:
      color 240ms var(--motion-ease),
      border-color 240ms var(--motion-ease);
}

.catalog-chip:hover {
  border-color: #1a1917;
}

.catalog-chip--clear {
  border-color: transparent;
  color: #8a8680;
}

.catalog-chip--clear:hover {
  color: #1a1917;
  border-color: transparent;
}

@media (max-width: 991px) {
  .catalog-bar {
    flex-direction: column;
    align-items: stretch;
    flex-wrap: nowrap;
    gap: 10px 0;
  }

  .catalog-bar__left {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0;
    overflow: visible;
  }

  .catalog-bar__btn {
    width: 100%;
    justify-content: center;
    gap: 4px;
    height: 40px;
    min-height: 40px;
    font-size: 11px;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }

  .catalog-bar__search {
    max-width: none;
    width: 100%;
    margin: 0;
  }

  .catalog-bar__meta {
    width: 100%;
    margin: 8px 0 0;
    flex-wrap: wrap;
    white-space: normal;
    justify-content: space-between;
  }

  .catalog-pop {
    left: 0;
    right: 0;
    width: 100%;
  }
}
</style>
