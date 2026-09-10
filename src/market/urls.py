from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import (
    update_data,
    get_all_goods,
    GroupListAPIView,
    GoodsAPIView,
    GoodsByBarcodeView,
    GoodsKrwPricesView,
    Checkout,
)
from .order_views import (
    CheckoutSettingsView,
    CreateSiteOrderView,
    PayPalReturnView,
    ShippingDestinationsView,
    ShippingQuoteView,
    SiteOrderDetailView,
)

router = DefaultRouter()
router.register('goods', GoodsAPIView, basename='good')

urlpatterns = [
    path("goods/by-barcode/", GoodsByBarcodeView.as_view()),
    path("goods/<int:good_id>/prices/", GoodsKrwPricesView.as_view()),
    path("", include(router.urls)),
    path('categories/', GroupListAPIView.as_view()),
    path('update_data/', update_data),
    path('get_all_goods/', get_all_goods),
    path('checkout/', Checkout.as_view()),
    path('checkout-settings/', CheckoutSettingsView.as_view()),
    path('orders/', CreateSiteOrderView.as_view()),
    path('orders/paypal/return/', PayPalReturnView.as_view(), name='site_order_paypal_return'),
    path('orders/<str:public_id>/', SiteOrderDetailView.as_view()),
    path('shipping/destinations/', ShippingDestinationsView.as_view()),
    path('shipping/quote/', ShippingQuoteView.as_view()),
]