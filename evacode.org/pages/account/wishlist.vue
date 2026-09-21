<template>
  <div>
    <Header />
    <AccountShell current="wishlist">
      <h2 class="account-lux__heading">Избранное</h2>
      <AccountEmpty
        lead="Пока ничего не отложили."
        text="Отметьте средство в каталоге, чтобы вернуться к нему позже."
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
  titleTemplate: '%s — Избранное',
})
</script>
