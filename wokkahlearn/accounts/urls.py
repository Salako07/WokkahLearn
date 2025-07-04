from django.urls import path

from .views import (
    RegisterView, LoginView, LogoutView, UserProfileView, 
    ChangePasswordView, PasswordResetView, PasswordResetConfirmView,
    UserSkillsView, UserAchievementsView,
    EmailVerificationView, ResendVerificationEmailView, UserUpdateView, UserAvatarUploadView
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    #path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    #path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Email verification - ADD THESE NEW LINES
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
     path('user/', UserUpdateView.as_view(), name='user_update'),
    path('user/avatar/', UserAvatarUploadView.as_view(), name='user_avatar'),
    
    # Password reset
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # User data
    path('skills/', UserSkillsView.as_view(), name='user_skills'),
    path('achievements/', UserAchievementsView.as_view(), name='user_achievements'),
]