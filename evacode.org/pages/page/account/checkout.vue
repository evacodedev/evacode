<template>
<Header/>
  <div>
   <PaymentPage/>
  </div>
  <Footer />
</template>
<script setup>
useHead({
  titleTemplate: `%s - Оформить заказ`,
  meta: [
    {
      name: 'description',
      content: 'Evacode - интернет магазин корейской косметики - Оформить заказ'
    },
  ]
});

</script>
