<template>
  <div>
    <div class="product-pagination mb-0" v-if="totalProductsCount > paginationProps.itemsPerPage">
      <div class="theme-paggination-block">
        <div class="row">
          <WidgetsShopProductsPagination
              :previous="paginationProps.previous"
              :next="paginationProps.next"
              :current="paginationProps.currentPage"
              :pages="paginationProps.pages"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  paginationProps: {
    type: Object,
    required: true,
  },
  totalProductsCount: {
    type: Number,
    required: true,
  }
});

</script>
