from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import update_data, get_all_goods, GroupListAPIView, GoodsAPIView, Checkout
from .order_views import CreateSiteOrderView, SiteOrderDetailView, PayPalReturnView

router = DefaultRouter()
router.register('goods', GoodsAPIView, basename='good')

urlpatterns = [
    path("", include(router.urls)),
    path('categories/', GroupListAPIView.as_view()),
    path('update_data/', update_data),
    path('get_all_goods/', get_all_goods),
    path('checkout/', Checkout.as_view()),
    path('orders/', CreateSiteOrderView.as_view()),
    path('orders/paypal/return/', PayPalReturnView.as_view(), name='site_order_paypal_return'),
    path('orders/<uuid:public_id>/', SiteOrderDetailView.as_view()),
]