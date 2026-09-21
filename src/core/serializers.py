from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from taggit.serializers import TagListSerializerField, TaggitSerializer
from taggit.models import Tag
from .models import (
    Post,
    Slide,
    Review,
    Comment,
    Banner,
    AboutUs,
    Contacts,
    Delivery,
    SectionWithVideo,
    AccountProfile,
    AccountAddress,
)


class PostSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField()
    author = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())

    class Meta:
        model = Post
        fields = ("id", "h1", "title", "slug", "description", "content", "image", "created_at", "author", "tags")
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("name",)
        lookup_field = 'name'
        extra_kwargs = {
            'url': {'lookup_field': 'name'}
        }


class ContactSerailizer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.CharField()
    subject = serializers.CharField()
    message = serializers.CharField()


class AccountUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=64)
    birth_date = serializers.DateField(required=False, allow_null=True)
    whatsapp = serializers.CharField(required=False, allow_blank=True, max_length=64)
    telegram = serializers.CharField(required=False, allow_blank=True, max_length=64)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password2 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    current_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "birth_date",
            "whatsapp",
            "telegram",
            "password",
            "password2",
            "current_password",
        )
        read_only_fields = ("id", "email")
        extra_kwargs = {
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
            if data.get("birth_date") == "":
                data["birth_date"] = None
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        profile = getattr(instance, "account_profile", None)
        data["phone"] = profile.phone if profile else ""
        data["birth_date"] = profile.birth_date.isoformat() if profile and profile.birth_date else None
        data["whatsapp"] = profile.whatsapp if profile else ""
        data["telegram"] = profile.telegram if profile else ""
        data.pop("password", None)
        data.pop("password2", None)
        data.pop("current_password", None)
        return data

    def validate(self, attrs):
        password = attrs.get("password") or ""
        password2 = attrs.get("password2") or ""
        current_password = attrs.get("current_password") or ""
        if password or password2 or current_password:
            if not current_password:
                raise serializers.ValidationError({"current_password": "Укажите текущий пароль"})
            if self.instance is None or not self.instance.check_password(current_password):
                raise serializers.ValidationError({"current_password": "Неверный текущий пароль"})
            if not password:
                raise serializers.ValidationError({"password": "Введите новый пароль"})
            if password != password2:
                raise serializers.ValidationError({"password2": "Пароли не совпадают"})
            try:
                validate_password(password, user=self.instance)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None) or ""
        validated_data.pop("password2", None)
        validated_data.pop("current_password", None)
        profile_fields = {
            key: validated_data.pop(key)
            for key in ("phone", "birth_date", "whatsapp", "telegram")
            if key in validated_data
        }
        instance = super().update(instance, validated_data)
        if profile_fields:
            profile, _ = AccountProfile.objects.get_or_create(user=instance)
            for key, value in profile_fields.items():
                if key in ("phone", "whatsapp", "telegram") and value is not None:
                    value = str(value).strip()
                setattr(profile, key, value)
            profile.save()
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance


class AccountAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountAddress
        fields = ("id", "country", "country_code", "city", "street", "house", "apartment", "postal_code", "comment")
        extra_kwargs = {
            "country": {"required": True, "allow_blank": False},
            "country_code": {"required": True, "allow_blank": False},
            "postal_code": {"required": True, "allow_blank": False},
        }

    def validate_country(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Укажите страну")
        return value

    def validate_country_code(self, value):
        value = (value or "").strip().upper()[:8]
        if not value:
            raise serializers.ValidationError("Укажите страну")
        return value

    def validate_city(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Укажите город")
        return value

    def validate_street(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Укажите улицу")
        return value

    def validate_house(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Укажите дом")
        return value

    def validate_postal_code(self, value):
        value = (value or "").strip()[:32]
        if not value:
            raise serializers.ValidationError("Укажите индекс")
        return value

    def validate_apartment(self, value):
        return (value or "").strip()

    def validate_comment(self, value):
        return (value or "").strip()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_email(self, value):
        email = value.strip().lower()
        if len(email) > 150:
            raise serializers.ValidationError("Слишком длинный email")
        taken = User.objects.filter(username__iexact=email).exists() or User.objects.filter(
            email__iexact=email
        ).exists()
        if taken:
            raise serializers.ValidationError("Такой email уже зарегистрирован")
        return email

    def validate(self, attrs):
        password = attrs["password"]
        if password != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Пароли не совпадают"})
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        email = validated_data["email"]
        user = User(
            username=email,
            email=email,
            first_name=(validated_data.get("first_name") or "").strip(),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        user = authenticate(username=email, password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Неверный email или пароль")
        attrs["email"] = email
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())
    post = serializers.SlugRelatedField(slug_field="slug", queryset=Post.objects.all())

    class Meta:
        model = Comment
        fields = ("id", "post", "username", "text", "created_date")
        lookup_field = 'id'
        extra_kwargs = {
            'url': {'lookup_field': 'id'}
        }


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'


class AboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = '__all__'


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = '__all__'


class ContactsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacts
        fields = '__all__'


class SlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slide
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class SectionWithVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionWithVideo
        fields = '__all__'