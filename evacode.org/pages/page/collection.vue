<template>
<Header/>
  <div>
    <section class="collection section-b-space pt-0 ratio_square">
      <div class="container">
        <div class="row partition-collection">
          <div class="col-lg-3 col-md-6" v-for="(category, index) in categories" :key="index">
            <div class="collection-block">
              <div>
                <nuxt-link :to="`/collection/leftsidebar/${category.id}`">
                  <img v-if="category.images[0]" :src="category.images[0].url" class="img-fluid" alt="item.title" />
                </nuxt-link>
              </div>
              <div class="collection-content">
                <nuxt-link :to="`/collection/leftsidebar/${category.id}`">
                  <h3>{{category.name}}</h3>
                </nuxt-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
  <Footer />
</template>

<script setup>
const {data: categoriesResponse} = await useAsyncData(
    'categoriesResponse',
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/categories/`),
    {
      server: false,
    }
);

const categories = computed(() => categoriesResponse.value?.result.slice(1));

useHead({
  titleTemplate: `%s - Категории`,
  meta: [
    {
      name: 'description',
      content: 'Evacode - интернет магазин корейской косметики - Категории'
    },
  ]
});
</script>

<style scoped>

</style>
