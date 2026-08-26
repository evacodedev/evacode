<template>
  <nav aria-label="Page navigation">
    <ul class="evacode-pagination">
      <li class="page-item btn-bordered">
        <nuxt-link v-if="previous != null" class="page-link" :to="previous" tabindex="-1">
          <span aria-hidden="true">
            <i class="fa fa-chevron-left" aria-hidden="true"></i>
          </span>
        </nuxt-link>
        <a v-else class="page-link" href="#">
          <span aria-hidden="true">
            <i class="fa fa-chevron-left" aria-hidden="true"></i>
          </span>
        </a>
      </li>
      <li class="page-item" v-for="(page_index, index) in pages" :key="index" :class="{ 'active': page_index == current }">
        <nuxt-link class="page-link" :to="formatPageUrl(page_index)" tabindex="-1">
          {{ page_index }}
        </nuxt-link>
      </li>
      <li class="page-item btn-bordered">
        <nuxt-link v-if="next != null" class="page-link" :to="next" tabindex="-1">
          <span aria-hidden="true">
            <i class="fa fa-chevron-right" aria-hidden="true"></i>
          </span>
        </nuxt-link>
        <a v-else class="page-link" href="#">
          <span aria-hidden="true">
            <i class="fa fa-chevron-right" aria-hidden="true"></i>
          </span>
        </a>
      </li>
    </ul>
  </nav>
</template>

<script setup>
import {useRoute} from 'vue-router';

const props = defineProps({
  previous: {
    type: String,
    default: '',
  },
  next: {
    type: String,
    default: '',
  },
  pages: {
    type: Array,
    default: [],
  },
  current: {
    type: Number,
    default: 0,
  },
});

const route = useRoute();
const formatPageUrl = (pageIndex) => {
  const query = Object.assign({}, route.query);
  query.page = pageIndex;

  const queryKeys = Object.keys(query);
  const queryPath = queryKeys.map((key) => `${key}=${query[key]}`).join('&');
  return `?${queryPath}`
}
</script>
