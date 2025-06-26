from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token # Import Token model for authentication
from .serializers import DietaryPreferenceSerializer, UserRegistrationSerializer, UserLoginSerializer, UserProfileUpdateSerializer, UserProfileSerializer
from rest_framework.permissions import IsAuthenticated #import the new login serializer
from .permissions import IsAdminUser # Import the custom permission class
from .models import CustomUser, DietaryPreference # Import your CustomUser model
from django.contrib.auth import logout # Import logout function
import requests
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class UserRegistrationView(APIView):
    permission_classes = []  # AllowAny by default

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = []  # AllowAny by default

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user) # Get or create a token for the user
            return Response({
                'message': 'Login successful.',
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_verified_contributor': user.is_verified_contributor
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated] # <--- This ensures only logged-in users can access

    def get(self, request):
        # Use the full UserProfileSerializer to include all fields (username, profile_photo, etc.)
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Update dietary preferences if present
            dietary_preferences = request.data.get('dietary_preferences')
            if dietary_preferences is not None:
                preference_obj, _ = DietaryPreference.objects.get_or_create(user=request.user)
                preference_obj.preferences = dietary_preferences
                preference_obj.save()
            # Update basic ingredients if present
            basic_ingredients = request.data.get('basic_ingredients')
            if basic_ingredients is not None:
                request.user.basic_ingredients = basic_ingredients
                request.user.save()
            # Return the full profile with all fields
            full_serializer = UserProfileSerializer(request.user, context={'request': request})
            return Response(full_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Update dietary preferences if present
            dietary_preferences = request.data.get('dietary_preferences')
            if dietary_preferences is not None:
                preference_obj, _ = DietaryPreference.objects.get_or_create(user=request.user)
                preference_obj.preferences = dietary_preferences
                preference_obj.save()
            # Update basic ingredients if present
            basic_ingredients = request.data.get('basic_ingredients')
            if basic_ingredients is not None:
                request.user.basic_ingredients = basic_ingredients
                request.user.save()
            # Return the full profile with all fields
            full_serializer = UserProfileSerializer(request.user, context={'request': request})
            return Response(full_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyContributorView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser] # <--- Requires login AND admin role

    def post(self, request, user_id): # user_id comes from the URL
        try:
            user_to_verify = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Prevent admins from verifying themselves or other admins
        if user_to_verify.role == 'admin':
            return Response({'detail': 'Cannot verify an admin user.'}, status=status.HTTP_400_BAD_REQUEST)

        if user_to_verify.is_verified_contributor:
            return Response({'detail': 'User is already a verified contributor.'}, status=status.HTTP_200_OK)

        user_to_verify.is_verified_contributor = True
        user_to_verify.save()

        # Return the updated user profile
        serializer = UserProfileUpdateSerializer(user_to_verify)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DietaryPreferenceView(APIView):
    permission_classes = [IsAuthenticated] # Only authenticated users can manage their preferences

    def get(self, request):
        # Get or create the dietary preference object for the current user
        preference, created = DietaryPreference.objects.get_or_create(user=request.user)
        serializer = DietaryPreferenceSerializer(preference)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        # Update the dietary preferences for the current user
        preference, created = DietaryPreference.objects.get_or_create(user=request.user)
        serializer = DietaryPreferenceSerializer(preference, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        # Partially update the dietary preferences for the current user
        preference, created = DietaryPreference.objects.get_or_create(user=request.user)
        serializer = DietaryPreferenceSerializer(preference, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        # Delete the dietary preferences for the current user
        try:
            preference = DietaryPreference.objects.get(user=request.user)
            preference.delete()
            return Response({'detail': 'Dietary preferences deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except DietaryPreference.DoesNotExist:
            return Response({'detail': 'Dietary preferences not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'detail': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)
# Note: This view allows users to change their password.
# It checks the old password, sets the new password, and saves the user.

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated] # Only authenticated users can log out

    def post(self, request):
        logout(request) # Invalidate the session
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

class GoogleLoginView(APIView):
    def post(self, request):
        access_token = request.data.get('access_token')
        if not access_token:
            return Response({'error': 'Access token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the token with Google
        google_userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        resp = requests.get(google_userinfo_url, headers={'Authorization': f'Bearer {access_token}'})
        if resp.status_code != 200:
            return Response({'error': 'Invalid Google access token.'}, status=status.HTTP_400_BAD_REQUEST)
        userinfo = resp.json()
        email = userinfo.get('email')
        if not email:
            return Response({'error': 'Google account email not found.'}, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        user, created = User.objects.get_or_create(email=email, defaults={
            'username': email.split('@')[0],
            'first_name': userinfo.get('given_name', ''),
            'last_name': userinfo.get('family_name', ''),
            'is_active': True
        })
        # Optionally update user info
        if not created:
            user.first_name = userinfo.get('given_name', user.first_name)
            user.last_name = userinfo.get('family_name', user.last_name)
            user.save()

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }, status=status.HTTP_200_OK)