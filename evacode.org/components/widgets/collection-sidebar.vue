<template>
  <div>
    <div class="row">
      <div class="col-xl-12">
        <div class="categories-btn">
          <button
              class="evacode-btn"
              :class="filter ? 'fill-btn' : ''"
              @click="filter = !filter"
          >
            Категории
          </button>
        </div>
      </div>
    </div>
    <div class="collection-filter" :class="filter ? 'openFilterbar' : ''">
      <sidebar-categories @clickBack="filter = !filter" :current-category="currentCategory"/>
    </div>
  </div>
</template>

<script setup>
import SidebarCategories from '~/components/widgets/sidebar-categories.vue';
const filter = ref(false);
const props = defineProps({
  currentCategory: {
    type: Number,
    default: 0,
  }
})
</script>
