<template>
  <a class="phone-href" :href="`mailto:${email}`">{{ email }}</a>
</template>
<script>
export default {
  props: ['email'],
}
</script>
<style scoped>
.phone-href {
  color: #777777;
}
</style>
