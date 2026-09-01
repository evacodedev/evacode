<template>
  <div
      v-for="n in count"
      :key="n"
      class="col-grid-box col-xl-3 col-lg-6 col-md-4 col-6"
  >
    <div class="product-box product-skeleton" aria-hidden="true">
      <div>
        <div class="img-wrapper skeleton-block"></div>
        <div class="product-detail">
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  count: {
    type: Number,
    default: 8,
  },
});
</script>
