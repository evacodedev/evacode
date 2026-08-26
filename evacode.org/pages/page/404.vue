<template>
<Header/>
  <div>
    <section class="p-0">
      <div class="container">
        <div class="row">
          <div class="col-12">
            <div class="error-section">
              <h1>404</h1>
              <h2>Страница не найдена</h2>
              <nuxt-link :to="{ path: '/'}" class="btn btn-solid">На главную</nuxt-link>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
   <Footer />
</template>
<script>

export default {

}
</script>
