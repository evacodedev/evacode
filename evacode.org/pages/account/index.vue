<template>
  <div>
    <Header />
    <AccountShell current="orders">
      <h2 class="account-lux__heading">Заказы</h2>
      <AccountEmpty
        lead="Здесь появятся оформленные заказы."
        text="Пока ни одного. Когда оформите — заказ будет на этой странице."
        cta="В каталог"
        to="/collection/leftsidebar/0/"
      />
    </AccountShell>
    <Footer />
  </div>
</template>

<script setup>
definePageMeta({
  middleware: 'account-auth',
})

useHead({
  titleTemplate: '%s — Личный кабинет',
})
</script>
