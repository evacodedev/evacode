<template>
<Header/>
  <div>
    <!-- thank-you section start -->
    <section class="section-b-space light-layout">
      <div class="container">
        <div class="row">
          <div class="col-md-12">
            <div class="success-text">
              <i class="fa fa-check-circle" aria-hidden="true"></i>
              <h2>Спасибо за обращение!</h2>
              <p>В ближайшее время с Вами свяжется наш консультант!</p>
              <nuxt-link :to="{ path: '/'}" :class="'btn btn-solid'">На главную</nuxt-link>
            </div>
          </div>
        </div>
      </div>
    </section>
    <!-- Section ends -->
  </div>
  <Footer />
</template>
