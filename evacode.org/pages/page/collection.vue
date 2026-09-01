<template>
<Header/>
  <div>
    <section class="collection section-b-space pt-0 ratio_square">
      <div class="container">
        <div class="row partition-collection">
          <template v-if="categoriesPending && !categories.length">
            <div class="col-lg-3 col-md-6" v-for="n in 8" :key="n">
              <div class="collection-block">
                <div class="skeleton-block" style="aspect-ratio: 1 / 1"></div>
                <div class="product-skeleton" style="padding: 16px 0">
                  <div class="skeleton-line"></div>
                </div>
              </div>
            </div>
          </template>
          <div
              class="col-lg-3 col-md-6 motion-appear"
              v-for="(category, index) in categories"
              :key="category.id || index"
              :style="{ '--i': index }"
          >
            <div class="collection-block">
              <div>
                <nuxt-link :to="`/collection/leftsidebar/${category.id}`">
                  <NuxtImg
                    v-if="category.images?.[0]?.url"
                    :src="category.images[0].url"
                    :alt="category.name"
                    :width="800"
                    fit="inside"
                    format="webp"
                    :quality="75"
                    densities="x1"
                    :loading="index < 4 ? 'eager' : 'lazy'"
                    class="img-fluid"
                  />
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
const {data: categoriesResponse, pending: categoriesPending} = await useAsyncData(
    'categoriesResponse',
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/categories/`),
    {
      server: false,
      lazy: true,
    }
);

const categories = computed(() => (categoriesResponse.value?.result || []).filter((c) => c.id !== 1));

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
