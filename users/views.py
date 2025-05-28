from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token # Import Token model for authentication
from .serializers import DietaryPreferenceSerializer, UserRegistrationSerializer, UserLoginSerializer, UserProfileUpdateSerializer
from rest_framework.permissions import IsAuthenticated #import the new login serializer
from .permissions import IsAdminUser # Import the custom permission class
from .models import CustomUser, DietaryPreference # Import your CustomUser model
from django.contrib.auth import logout # Import logout function

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
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
        # Retrieve and return the current user's profile
        serializer = UserProfileUpdateSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        # Update the current user's profile
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True) # partial=True allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
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

    # Note: You might also consider a PATCH method for partial updates,
    # but for a single TextField of preferences, PUT works fine.
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