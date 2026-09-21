<template>
  <div>
    <Header />
    <AccountShell current="orders">
      <h2 class="account-lux__heading">Заказы</h2>
      <AccountEmpty
        icon="bag"
        lead="Заказов пока нет"
        text="Когда оформите, они появятся здесь."
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
