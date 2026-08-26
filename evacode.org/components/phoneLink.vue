<template>
  <a class="phone-href" :href="`tel:${phone}`">{{ phone }}</a>
</template>
<script>
export default {
  props: ['phone'],
}
</script>
<style scoped>
.phone-href {
  color: #777777;
}
</style>
