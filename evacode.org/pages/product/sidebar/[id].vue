<script setup>
const route = useRoute();
await navigateTo(`/product/${route.params.id}/`, { redirectCode: 301, replace: true });
</script>
