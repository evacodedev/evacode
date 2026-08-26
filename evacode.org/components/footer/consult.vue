<template>
    <div class="consulting">
        <div class="container">
            <section class="small-section border-section border-top-0">
                <div class="row">
                    <div class="col-lg-6">
                        <img class="consult-girl" src="/images/new_evacode/consult/consult-girl.png" alt="Consult-girl">
                    </div>
                    <div class="col-lg-6 consult-column">
                        <h2 class="request-tg-consult">Запросите консультацию!</h2>

                        <h4>Получите персональный подбор косметического ухода от наших консультантов</h4>

                        <form
                            action="https://pixelstrap.us19.list-manage.com/subscribe/post?u=5a128856334b598b395f1fc9b&amp;id=082f74cbda"
                            class="form-inline subscribe-form auth-form needs-validation" method="post"
                            id="mc-embedded-subscribe-form" name="mc-embedded-subscribe-form" target="_blank">
                            <div class="form-group">
                                <MazPhoneNumberInput
                                    v-model="phone_number"
                                    v-model:country-code="countryCode1"
                                    @update="updateResults"
                                    :translations="{
                                      countrySelector: {
                                        placeholder: 'Код страны',
                                        error: 'Выберите страну',
                                        searchPlaceholder: 'Искать страну',
                                      },
                                      phoneInput: {
                                        placeholder: 'Номер телефона',
                                        example: 'Пример:',
                                      },
                                    }"
                                />
                                <span class="validate-error">{{ phoneErrorMessage }}</span>
                            </div>
                            <button type="submit" class="btn evacode-btn" id="mc-submit" @click.prevent="onSubmit">
                                Связаться с консультантом
                            </button>
                        </form>
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import {useRouter} from 'vue-router';

const router = useRouter();
const phone_number = ref('');
const phoneErrorMessage = ref('');
const phone_results = ref('');
const countryCode1 = ref('KR');

const updateResults = (event) => {
    phone_results.value = event
};

const onSubmit = async () => {
    if (phone_results.value.isValid) {
        await $fetch(`${useRuntimeConfig().public.apiBase}/market/checkout/`, {
            method: 'POST',
            body: {
                user: {
                    phone: phone_number.value,
                },
                consult: true,
            }
        })

        router.push('/page/consult-success')
    } else {
        phoneErrorMessage.value = 'Обязательное поле';
    }
};
</script>

<style scoped>
.request-tg-consult {
    display: flex;
}

.form-group {
    display: flex;
    flex-direction: column;
}
</style>
