<template>
  <div class="top-header">
    <div class="container">
      <div class="row">
        <div class="col-xl-3 col-lg-4 col-sm-4 top-header-left-column">
          <div class="top-header-left top-header-v-centered">
            <WidgetsContactPhone />
          </div>
        </div>
        <div class="col-xl-6 col-lg-4 col-sm-6 col-6 top-header-center-column">
          <div class="top-header-center top-header-v-centered">
            <WidgetsBrandLogo />
          </div>
        </div>
        <div class="col-xl-3 col-lg-4 col-sm-6 col-6 top-header-right-column">
          <div class="top-header-right top-header-v-centered">
            <WidgetsCurrency />
            <div class="main-menu">
              <div class="menu-right pull-right">
                <WidgetsNavbar />
                <WidgetsHeaderWidgets/>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
