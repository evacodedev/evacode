<template>
    <Header/>
    <WidgetsBackButton />
    <div>
        <section class="contact-page section-b-space">
            <div class="container">
                <img class="contact-logo" src="/images/new_evacode/evacode-contact-logo.png"  alt=""/>
                <h2 class="contact-title">Контакты</h2>
                <div class="row contacts-row section-b-space">
                    <div class="col-xl-7 col-12">
                        <div v-if="contacts" class="contact-right">
                            <h3 class="our-address">Наш адрес</h3>
                            <p v-html="contacts.address"></p>
                            <h5 class="work-hours">Режим работы:</h5>
                            <p>
                                Воскресенье - Пятница с 10:00 - 19:00<br>
                                Суббота - Выходной день
                            </p>

                            <h3 class="our-address social">Соц сети</h3>

                            <a target="_blank" :href="contacts.instagram" class="social-contact"><img src="/images/new_evacode/instagram.png" />Instagram</a>
                            <a target="_blank" :href="contacts.telegram" class="social-contact"><img src="/images/new_evacode/telegram.png" />Telegram</a>
                            <a target="_blank" :href="contacts.tiktok" class="social-contact"><img src="/images/new_evacode/tiktok.png" />Tiktok</a>
                            <a target="_blank" :href="contacts.facebook" class="social-contact"><img src="/images/new_evacode/facebook.png" />Facebook</a>
                        </div>
                    </div>
                    <div class="col-xl-5 col-12 map">
                        <iframe
                            src="https://maps.google.com/maps?width=100%25&amp;height=600&amp;hl=ru&amp;q=Gyeonggi-do,%20Ansan-si,%20Danwon-gu,%20Choji-dong,%20742-3,%20210%ED%98%B8+(Evacode)&amp;t=&amp;z=14&amp;ie=UTF8&amp;iwloc=B&amp;output=embed"
                            allowfullscreen></iframe>
                    </div>
                </div>
            </div>
        </section>
    </div>
    <ShopBeautyTestimonials />
    <ShopBeautyAboutSlider />
    <Footer/>
</template>
<script setup>
import {useContactsStore} from '~~/store/contacts'
const contacts = await useContactsStore().contacts;

useHead({
    titleTemplate: `%s - Контакты`,
    meta: [
        {
            name: 'description',
            content: 'Evacode - интернет магазин корейской косметики - Контакты'
        },
    ]
});
</script>

<style scoped>
.map {
    height: 435px;
}

.contact-page label {
    text-transform: none;
}
</style>
