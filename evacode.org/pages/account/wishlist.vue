<template>
  <div>
    <Header />
    <AccountShell current="wishlist">
      <h2 class="account-lux__heading">Избранное</h2>
      <p v-if="loading" class="account-lux__status">Загружаем избранное…</p>
      <p v-else-if="loadError" class="account-lux__status">{{ loadError }}</p>
      <AccountEmpty
        v-else-if="!items.length"
        icon="heart"
        lead="В избранном пусто"
        text="Отметьте средство в каталоге, чтобы вернуться к нему."
        cta="В каталог"
        to="/collection/leftsidebar/0/"
      />
      <template v-else>
        <p class="account-wishlist__count">{{ countLabel }}</p>
        <div class="product-wrapper-grid account-wishlist">
          <div class="row">
            <div
              v-for="(product, index) in items"
              :key="product.id"
              class="col-grid-box col-lg-4 col-6"
            >
              <div class="product-box">
                <ProductBoxProductBox1 :product="product" :index="index" />
              </div>
            </div>
          </div>
        </div>
      </template>
    </AccountShell>
    <Footer />
  </div>
</template>

<script setup>
import { useWishlistStore } from '~/store/wishlist'

definePageMeta({
  middleware: 'account-auth',
})

useHead({
  titleTemplate: '%s — Избранное',
})
useNoIndex()

const wishlist = useWishlistStore()
const loading = ref(!wishlist.ready)
const loadError = ref('')

const items = computed(() => wishlist.items)
const countLabel = computed(() => {
  const count = items.value.length
  const mod10 = count % 10
  const mod100 = count % 100
  let word = 'средств'
  if (mod10 === 1 && mod100 !== 11) {
    word = 'средство'
  } else if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    word = 'средства'
  }
  return `${count} ${word}`
})

const load = async () => {
  loading.value = !wishlist.ready
  loadError.value = ''
  try {
    await wishlist.sync()
  } catch {
    if (!wishlist.items.length) {
      loadError.value = 'Не удалось загрузить избранное.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
