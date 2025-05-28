from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser, DietaryPreference  # Import your CustomUser model
from django.contrib.auth import authenticate #used for authenticating username/password

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name')  # Fields required for registration

    def validate_password(self, value):
        # Basic password validation (you can add more complexity)
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Hash the password
        return CustomUser.objects.create(**validated_data)
    
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False) # Can be username or email
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
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
                # Find user by email, then try to authenticate with their username
                # This assumes username is unique, or you want to allow email login
                # by finding the user and then authenticating with their username
                # which is what authenticate() expects.
                # A more robust email login might involve a custom authentication backend.
                 # For simplicity, let's assume username is also email if logging in via email for now,
                # or that a user object can be retrieved by email and then authenticated.
                # A common pattern is to fetch the user by email, then pass their username to authenticate().

                # More robust email login:
                # Try to find a user with the given email first
                temp_user = CustomUser.objects.get(email=email)
                user = authenticate(username=temp_user.username, password=password)

            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials.")


        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        # If user is found but not active, deny login
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data['user'] = user # Attach the user object to validated data
        return data

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True) # Make email optional and allow empty string
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    # We don't include 'username' here because it's generally not changed after registration.
    # We also don't include 'password' directly, as password changes should be a separate endpoint for security.
    # 'role' and 'is_verified_contributor' should not be editable by the user themselves.

    class Meta:
        model = CustomUser
        # Fields that a user can update themselves
        fields = ('email', 'first_name', 'last_name')
        # Ensure these fields are not required for an update
        extra_kwargs = {
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        # Allow email to be blank or the user's current email
        if value and value != self.instance.email:
            if CustomUser.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already in use.")
        return value
    
    def update(self, instance, validated_data):
        # Update only the provided fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance
    
class DietaryPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietaryPreference
        fields = ['preferences'] # Only exposing the 'preferences' field

    def to_representation(self, instance):
        # Convert the comma-separated string back to a list for output
        data = super().to_representation(instance)
        if data['preferences']:
            data['preferences'] = [p.strip() for p in data['preferences'].split(',')]
        else:
            data['preferences'] = []
        return data

    def to_internal_value(self, data):
        # Convert a list of preferences from input back to a comma-separated string
        if 'preferences' in data and isinstance(data['preferences'], list):
            data['preferences'] = ','.join(data['preferences'])
        return super().to_internal_value(data)
    
# Add this to your users/serializers.py file

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "New passwords must match."})
        # You might add more password validation here (e.g., strength checks)
        return data
    