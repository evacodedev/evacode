<template>
    <div>
        <section v-if="deliveriesSafe.length" class="section-cancellation section-b-space">
            <div class="container">
                <img class="cancellation-image" src="/images/new_evacode/cancellation.png" />
                <h2 class="cancellation-title">Возврат и отмена</h2>
                <div class="container-wrapper">
                    <div class="row">
                        <div class="col-xl-6 col-12 text-column" v-html="deliveriesSafe[deliveriesSafe.length - 1].delivery_description">
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>
</template>

<script setup>
const deliveries = ref([]);
const deliveriesSafe = computed(() => Array.isArray(deliveries.value) ? deliveries.value : []);

onMounted(async () => {
    try {
        const res = await $fetch(`${useRuntimeConfig().public.apiBase}/core/delivery`);
        deliveries.value = res?.results || [];
    } catch (error) {
        console.error(error);
        deliveries.value = [];
    }
});
useHead({
    titleTemplate: `%s - Доставка`,
    meta: [
        {
            name: 'description',
            content: 'Evacode - интернет магазин корейской косметики - Доставка'
        },
    ]
});
</script>

<style scoped>

</style>
