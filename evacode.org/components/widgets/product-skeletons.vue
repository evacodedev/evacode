<template>
  <div
      v-for="n in count"
      :key="n"
      class="col-grid-box col-xl-4 col-6"
  >
    <div class="product-box product-skeleton" aria-hidden="true">
      <div class="product-card">
        <div class="img-wrapper skeleton-block"></div>
        <div class="product-detail">
          <div class="skeleton-line"></div>
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
    default: 12,
  },
});
</script>
