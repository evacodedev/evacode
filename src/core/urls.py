from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, TagDetailView, TagView, AsideView, FeedBackView, RegisterView, LoginView, ProfileView, AddressListView, AddressDetailView, CommentView, \
    AboutUsView, ContactsView, DeliveryView, BannerView, SlideView,ReviewView, CurrenciesView, SectionWithVideoView
from .google_auth import GoogleConfigView, GoogleLoginView

router = DefaultRouter()
router.register('posts', PostViewSet, basename='posts')
router.register('about', AboutUsView, basename='about')
router.register('contacts', ContactsView, basename='contacts')
router.register('delivery', DeliveryView, basename='delivery')
router.register('banner', BannerView, basename='banner')
router.register('slide', SlideView, basename='slide')
router.register('review', ReviewView, basename='review')
router.register('video-section', SectionWithVideoView, basename='video-section')


urlpatterns = [
    path("", include(router.urls)),
    path("currencies/", CurrenciesView.as_view()),
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/google/", GoogleLoginView.as_view()),
    path("auth/google/config/", GoogleConfigView.as_view()),
    path("auth/me/", ProfileView.as_view()),
    path("auth/addresses/", AddressListView.as_view()),
    path("auth/addresses/<int:pk>/", AddressDetailView.as_view()),
    # path("tags/", TagView.as_view()),
    # path("tags/<slug:tag_slug>/", TagDetailView.as_view()),
    # path("aside/", AsideView.as_view()),
    # path("feedback/", FeedBackView.as_view()),
    # path('register/', RegisterView.as_view()),
    # path('profile/', ProfileView.as_view()),
    # path("comments/", CommentView.as_view()),
    # path("comments/<slug:post_slug>/", CommentView.as_view()),
]