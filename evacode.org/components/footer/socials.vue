<template>
  <div v-if="contacts" class="footer-social">
    <ul>
      <li><a target="_blank" :href="contacts.facebook"><i class="fa fa-facebook-f"></i></a></li>
      <li><a target="_blank" :href="contacts.instagram"><i class="fa fa-instagram"></i></a></li>
      <li><a target="_blank" :href="messengers.telegram[0].href"><i class="fa fa-telegram"></i></a></li>
    </ul>
  </div>
</template>

<script setup>
import {useContactsStore} from '~~/store/contacts'
const contacts = ref(null);
const messengers = useShopMessengers();

onMounted(async () => {
  contacts.value = await useContactsStore().contacts;
});
</script>

<style scoped>

</style>
