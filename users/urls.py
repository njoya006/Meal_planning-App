from django.urls import path, include
from .views import UserLoginView, UserRegistrationView, UserProfileView, VerifyContributorView, DietaryPreferenceView, ChangePasswordView, UserLogoutView, GoogleLoginView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('verify/<int:user_id>/', VerifyContributorView.as_view(), name='verify-contributor'),
    path('preferences/', DietaryPreferenceView.as_view(), name='dietary-preferences'),
    path('preferences/<int:user_id>/', DietaryPreferenceView.as_view(), name='dietary-preferences-user'),
    path('preferences/<int:user_id>/update/', DietaryPreferenceView.as_view(), name='dietary-preferences-update'),
    path('preferences/<int:user_id>/delete/', DietaryPreferenceView.as_view(), name='dietary-preferences-delete'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
]
