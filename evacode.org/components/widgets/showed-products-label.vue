<template>
  <h5>Отображены товары {{ from }}-{{ Math.min(to, total) }} из {{ total }}</h5>
</template>

<script setup>
const props = defineProps({
  from: {
    type: Number,
    default: 0,
  },
  to: {
    type: Number,
    default: 0,
  },
  total: {
    type: Number,
    default: 0,
  },
});
</script>
