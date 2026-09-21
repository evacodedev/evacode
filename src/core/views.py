from rest_framework import viewsets, permissions, pagination, generics, filters
from rest_framework.viewsets import ModelViewSet
from django_filters import rest_framework
from forex_python.converter import CurrencyRates, CurrencyCodes
from .serializers import PostSerializer, ContactsSerializer, AboutUsSerializer, DeliverySerializer, SlideSerializer, \
    BannerSerializer, ReviewSerializer, SectionWithVideoSerializer
from .models import Post, Slide, Review, Currency
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponse, JsonResponse
from taggit.models import Tag
from babel import Locale, UnknownLocaleError
from .serializers import TagSerializer, ContactSerailizer
from taggit.models import Tag
from rest_framework.views import View, APIView
from django.core.mail import send_mail
from .serializers import RegisterSerializer, AccountUserSerializer, LoginSerializer, CommentSerializer
from .models import Comment, Contacts, AboutUs, Banner, Delivery, SectionWithVideo
from django_filters import FilterSet, CharFilter
from babel.numbers import get_currency_symbol, UnknownCurrencyError
from currency_symbols import CurrencySymbols
from currency_converter.currency_converter import CurrencyConverter
from babel import Locale, UnknownLocaleError
import locale
from pycbrf import ExchangeRates
import datetime


class BannerFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='exact', required=False)

    class Meta:
        model = Banner
        fields = ['id', 'name']


class AboutFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='exact', required=False)

    class Meta:
        model = AboutUs
        fields = ['id', 'name']


class SectionWithVideoFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='exact', required=False)

    class Meta:
        model = SectionWithVideo
        fields = ['id', 'name']


class PageNumberSetPagination(pagination.PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    ordering = 'created_at'


class TagDetailView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = PageNumberSetPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        tag_slug = self.kwargs['tag_slug'].lower()
        tag = Tag.objects.get(slug=tag_slug)
        return Post.objects.filter(tags=tag)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    pagination_class = PageNumberSetPagination


class TagView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class AsideView(generics.ListAPIView):
    queryset = Post.objects.all().order_by('-id')[:5]
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]


class FeedBackView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ContactSerailizer

    def post(self, request, *args, **kwargs):
        serializer_class = ContactSerailizer(data=request.data)
        if serializer_class.is_valid():
            data = serializer_class.validated_data
            name = data.get('name')
            from_email = data.get('email')
            subject = data.get('subject')
            message = data.get('message')
            send_mail(f'От {name} | {subject}', message, from_email, ['amromashov@gmail.com'])
            return Response({"success": "Sent"})


class PostViewSet(viewsets.ModelViewSet):
    search_fields = ['content', 'h1']
    filter_backends = (filters.SearchFilter,)
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    pagination_class = PageNumberSetPagination


def _auth_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": AccountUserSerializer(user).data,
    }


class RegisterView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(_auth_payload(user), status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(_auth_payload(serializer.validated_data["user"]))


class ProfileView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AccountUserSerializer

    def get(self, request, *args, **kwargs):
        return Response(AccountUserSerializer(request.user).data)

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CommentView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        post_slug = self.kwargs['post_slug'].lower()
        post = Post.objects.get(slug=post_slug)
        return Comment.objects.filter(post=post)


class BannerView(ModelViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    filter_backends = (rest_framework.DjangoFilterBackend,)
    filterset_class = BannerFilter


class ContactsView(ModelViewSet):
    queryset = Contacts.objects.all()
    serializer_class = ContactsSerializer


class AboutUsView(ModelViewSet):
    queryset = AboutUs.objects.all()
    serializer_class = AboutUsSerializer
    filter_backends = (rest_framework.DjangoFilterBackend,)
    filterset_class = AboutFilter


class DeliveryView(ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer


class SlideView(ModelViewSet):
    queryset = Slide.objects.all()
    serializer_class = SlideSerializer


class ReviewView(ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class SectionWithVideoView(ModelViewSet):
    queryset = SectionWithVideo.objects.all()
    serializer_class = SectionWithVideoSerializer
    filter_backends = (rest_framework.DjangoFilterBackend,)
    filterset_class = SectionWithVideoFilter


@method_decorator(csrf_exempt, name='dispatch')
class CurrenciesView(View):

    # rare_signs = {
    #     'UZS': "Soʻm"
    # }
    def get(self, request):
        currencies = request.GET.getlist('currencies')

        if not currencies:
            currencies = [
                "USD",
                "RUB",
                "EUR",
                "KZT",
                "UZS",
                "KGS"
            ]

        currency_data = [
            {
                'value': 'KRW',
                'curr': 1,
                'symbol': '₩',
                'locale': 'ko-KR',
            }
        ]
        c = ExchangeRates(str(datetime.datetime.now())[:10])

        for curr in currencies:
            if curr == "RUB":
                rub_kor = 1 / float(Currency.objects.get(key='krw-rub-kzt').value)
                currency_data.append(
                    {
                        'value': curr,
                        'curr': rub_kor,
                        'symbol': CurrencySymbols.get_symbol(curr),
                        'locale': 'ru',
                    }
                )
                continue
            try:
                if curr in ('USD', 'EUR'):
                    rub_kor = 1 / float(Currency.objects.get(key='krw-rub-eur').value)
                else:
                    rub_kor = 1 / float(Currency.objects.get(key='krw-rub-kzt').value)
                print(rub_kor, float(c[curr].rate))
                currency_data.append(
                    {
                        'value': curr,
                        'curr': rub_kor / float(c[curr].rate),
                        'symbol': CurrencySymbols.get_symbol(curr),
                        'locale': '',
                    }
                )
            except Exception as e:
                print(e)
                currency_data.append(
                    {
                        'value': curr,
                        'curr': 0,
                        'symbol': '',
                        'locale': '',
                    }
                )

        return JsonResponse({'currencies': currency_data}, status=200)
