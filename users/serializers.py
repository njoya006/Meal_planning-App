import base64

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import CustomUser, DietaryPreference, VerificationApplication
from recipes.models import Recipe

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name')

    def validate_password(self, value):
        """Validate password strength."""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        """Create a new user with hashed password."""
        validated_data['password'] = make_password(validated_data['password'])
        return CustomUser.objects.create(**validated_data)
    
class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login with username or email."""
    
    username = serializers.CharField(required=False)  # Can be username or email
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Validate login credentials."""
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not (username or email):
            raise serializers.ValidationError("Please provide either username or email.")

        if not password:
            raise serializers.ValidationError("Password is required.")

        user = None
        if username:
            # Authenticate by username
            user = authenticate(username=username, password=password)
        elif email:
            # Authenticate by email
            try:
                # Find user by email, then authenticate with their username
                temp_user = CustomUser.objects.get(email=email)
                user = authenticate(username=temp_user.username, password=password)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials.")

        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        # If user is found but not active, deny login
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data['user'] = user  # Attach the user object to validated data
        return data

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile information."""
    
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(allow_blank=True, required=False)
    date_of_birth = serializers.DateField(allow_null=True, required=False)
    location = serializers.CharField(allow_blank=True, required=False)
    basic_ingredients = serializers.CharField(allow_blank=True, required=False)
    profile_photo = serializers.ImageField(required=False, allow_null=True, write_only=True)
    profile_photo_base64 = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 
            'location', 'basic_ingredients', 'profile_photo', 'profile_photo_base64'
        )
        extra_kwargs = {
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False},
            'date_of_birth': {'required': False},
            'location': {'required': False},
            'basic_ingredients': {'required': False},
            'profile_photo': {'required': False},
            'profile_photo_base64': {'required': False},
        }

    def validate_email(self, value):
        """Validate that email is unique."""
        if value and value != self.instance.email:
            if CustomUser.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already in use.")
        return value
    
    def update(self, instance, validated_data):
        """Update user profile with optional base64 image handling."""
        profile_photo_base64 = validated_data.pop('profile_photo_base64', None)
        if profile_photo_base64:
            format_str, imgstr = (
                profile_photo_base64.split(';base64,') 
                if ';base64,' in profile_photo_base64 
                else (None, profile_photo_base64)
            )
            ext = format_str.split('/')[-1] if format_str else 'jpg'
            instance.profile_photo = ContentFile(
                base64.b64decode(imgstr), 
                name=f'profile_{instance.pk}.{ext}'
            )
        
        # Update only the provided fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
class DietaryPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for dietary preferences."""
    
    class Meta:
        model = DietaryPreference
        fields = ['preferences']

    def to_representation(self, instance):
        """Convert preferences string to list for API response."""
        data = super().to_representation(instance)
        if data['preferences']:
            data['preferences'] = [p.strip() for p in data['preferences'].split(',')]
        else:
            data['preferences'] = []
        return data

    def to_internal_value(self, data):
        """Convert preferences list to string for database storage."""
        if 'preferences' in data and isinstance(data['preferences'], list):
            data['preferences'] = ','.join(data['preferences'])
        return super().to_internal_value(data)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """Validate that new passwords match."""
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "New passwords must match."})
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile display."""
    
    username = serializers.CharField(read_only=True)
    profile_photo = serializers.SerializerMethodField()
    dietary_preferences = serializers.SerializerMethodField()
    verified_badge = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'is_verified_contributor', 'verified_badge', 'phone_number', 'date_of_birth',
            'location', 'basic_ingredients', 'dietary_preferences', 'profile_photo'
        ]

    def get_profile_photo(self, obj):
        """Return the full URL for the profile photo."""
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            else:
                return obj.profile_photo.url
        return None

    def get_dietary_preferences(self, obj):
        """Return dietary preferences as a list."""
        try:
            prefs = obj.dietary_preferences.preferences
            if prefs:
                return [p.strip() for p in prefs.split(',')]
        except (AttributeError, DietaryPreference.DoesNotExist):
            pass
        return []

    def get_verified_badge(self, obj):
        if getattr(obj, 'is_verified_contributor', False):
            return {
                'label': 'Verified Contributor',
                'icon': '✅',
                'color': '#2ecc40'
            }
        return None

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe display with contributor info."""
    
    contributor = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_contributor(self, obj):
        """Return minimal contributor information."""
        user = obj.contributor
        return {
            'username': user.username,
            'basic_ingredients': user.basic_ingredients
        } if user else None

class VerificationApplicationSerializer(serializers.ModelSerializer):
    """Serializer for verification application submission."""
    
    class Meta:
        model = VerificationApplication
        fields = [
            'full_name', 'cooking_experience', 'specialties', 
            'social_media_links', 'sample_recipes', 'motivation'
        ]
    
    def create(self, validated_data):
        """Create verification application for the current user."""
        user = self.context['request'].user
        
        # Check if user already has an application
        if hasattr(user, 'verification_application'):
            raise serializers.ValidationError(
                "You already have a verification application submitted."
            )
        
        # Update user verification status to pending
        user.verification_status = 'pending'
        user.save()
        
        # Create the application
        application = VerificationApplication.objects.create(
            user=user,
            **validated_data
        )
        return application

class VerificationApplicationDetailSerializer(serializers.ModelSerializer):
    """Serializer for viewing verification application details (admin use)."""
    
    user = serializers.StringRelatedField()
    reviewed_by = serializers.StringRelatedField()
    
    class Meta:
        model = VerificationApplication
        fields = '__all__'

class VerificationApplicationReviewSerializer(serializers.Serializer):
    """Serializer for admin to approve/reject verification applications."""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('admin_notes'):
            raise serializers.ValidationError(
                "Admin notes are required when rejecting an application."
            )
        return data
