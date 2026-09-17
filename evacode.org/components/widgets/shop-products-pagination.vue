<template>
  <nav class="evacode-pagination-wrap" aria-label="Page navigation">
    <p class="evacode-pagination-status">
      Страница {{ currentPage }} из {{ lastPageNumber }}
    </p>
    <ul class="evacode-pagination">
      <li class="page-item btn-bordered" :class="{ 'is-disabled': !canPrev }">
        <nuxt-link
            v-if="canPrev"
            class="page-link"
            :to="formatPageUrl(1)"
            aria-label="В начало"
        >
          <span aria-hidden="true">
            <i class="fa fa-angle-double-left"></i>
          </span>
        </nuxt-link>
        <span v-else class="page-link" aria-hidden="true">
          <i class="fa fa-angle-double-left"></i>
        </span>
      </li>
      <li class="page-item btn-bordered" :class="{ 'is-disabled': !canPrev }">
        <nuxt-link
            v-if="canPrev"
            class="page-link"
            :to="formatPageUrl(currentPage - 1)"
            aria-label="Назад"
        >
          <span aria-hidden="true">
            <i class="fa fa-chevron-left"></i>
          </span>
        </nuxt-link>
        <span v-else class="page-link" aria-hidden="true">
          <i class="fa fa-chevron-left"></i>
        </span>
      </li>
      <li
          class="page-item"
          v-for="(page_index, index) in pages"
          :key="index"
          :class="{ 'active': Number(page_index) === currentPage }"
      >
        <nuxt-link
            class="page-link"
            :to="formatPageUrl(page_index)"
            :aria-current="Number(page_index) === currentPage ? 'page' : undefined"
        >
          {{ page_index }}
        </nuxt-link>
      </li>
      <li class="page-item btn-bordered" :class="{ 'is-disabled': !canNext }">
        <nuxt-link
            v-if="canNext"
            class="page-link"
            :to="formatPageUrl(currentPage + 1)"
            aria-label="Вперёд"
        >
          <span aria-hidden="true">
            <i class="fa fa-chevron-right"></i>
          </span>
        </nuxt-link>
        <span v-else class="page-link" aria-hidden="true">
          <i class="fa fa-chevron-right"></i>
        </span>
      </li>
      <li class="page-item btn-bordered" :class="{ 'is-disabled': !canNext }">
        <nuxt-link
            v-if="canNext"
            class="page-link"
            :to="formatPageUrl(lastPageNumber)"
            aria-label="В конец"
        >
          <span aria-hidden="true">
            <i class="fa fa-angle-double-right"></i>
          </span>
        </nuxt-link>
        <span v-else class="page-link" aria-hidden="true">
          <i class="fa fa-angle-double-right"></i>
        </span>
      </li>
    </ul>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router';

const props = defineProps({
  previous: {
    type: [String, Object],
    default: '',
  },
  next: {
    type: [String, Object],
    default: '',
  },
  pages: {
    type: Array,
    default: () => [],
  },
  current: {
    type: [Number, Object],
    default: 0,
  },
  lastPage: {
    type: [Number, Object],
    default: 0,
  },
});

const route = useRoute();

const unwrapNumber = (value) => {
  let current = value;
  for (let i = 0; i < 3 && current && typeof current === 'object' && 'value' in current; i += 1) {
    current = current.value;
  }
  const n = Number(current);
  return Number.isFinite(n) ? n : 0;
};

const currentPage = computed(() => {
  const n = unwrapNumber(props.current);
  return n > 0 ? n : 1;
});

const lastPageNumber = computed(() => {
  const explicit = unwrapNumber(props.lastPage);
  if (explicit > 0) {
    return explicit;
  }
  const fromPages = (props.pages || []).map(Number).filter((n) => n > 0);
  return Math.max(currentPage.value, ...fromPages, 1);
});

const canPrev = computed(() => currentPage.value > 1);
const canNext = computed(() => currentPage.value < lastPageNumber.value);

const formatPageUrl = (pageIndex) => {
  const query = Object.assign({}, route.query);
  query.page = pageIndex;
  const queryKeys = Object.keys(query);
  const queryPath = queryKeys.map((key) => `${key}=${query[key]}`).join('&');
  return `?${queryPath}`;
};
</script>
