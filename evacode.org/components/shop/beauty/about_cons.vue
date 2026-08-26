<template>
  <div>
    <section class="beauty-about first-about">
      <div class="container">
        <div v-if="aboutHome" class="row">
          <div class="col-12 text-center">
            <div class="about-section">
              <div>
                <h2 class="evacode-main-about">Преимущества РАБОТЫ с EVACODE</h2>
                <div class="service small-section pb-0">
                  <div class="row">
                    <div class="col-4 service-block1">
                      <img class="service-icon" src="/images/new_evacode/Airplane.svg" alt="Airplane" />
                      <h5 class="service-about">{{ service_1 }}</h5>
                    </div>
                    <div class="col-4 service-block1">
                      <img class="service-icon" src="/images/new_evacode/24-7.svg" alt="24x7" />
                      <h5 class="service-about">{{ service_2 }}</h5>
                    </div>
                    <div class="col-4 service-block1">
                      <img class="service-icon" src="/images/new_evacode/Shop_bag.svg" alt="ShopBag" />
                      <h5 class="service-about">{{ service_3 }}</h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import {useAboutStore} from '~/store/about';
const aboutHome = await useAboutStore().aboutHome;

const service_1 = 'доставка по миру';
const service_2 ='24 X 7 сервис';
const service_3 = 'акционные предложения';

</script>
