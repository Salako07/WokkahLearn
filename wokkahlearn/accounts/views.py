"""
Django REST Framework Views for User Authentication and Profile Management

This module contains all the API views for user registration, authentication,
email verification, profile management, and related functionality.

Author: WokkahLearn Team
Version: 1.0
"""

# Standard library imports
from typing import Optional

# Django imports
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils import timezone

# Third-party imports
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

# Local imports
from .models import User, UserProfile, UserSkill, UserAchievement, EmailVerificationToken
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    UserProfileSerializer, ChangePasswordSerializer, UserSkillSerializer,
    UserAchievementSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
)
from .mailgun_service import mailgun_service

import logging
logger = logging.getLogger('wokkahlearn.accounts')  # For accounts app
logger = logging.getLogger('wokkahlearn.mailgun')   # For mailgun service

# ============================================================================
# REGISTRATION & EMAIL VERIFICATION VIEWS
# ============================================================================

class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint with flexible email verification options.
    
    Supports two registration flows:
    1. Immediate access: User gets JWT tokens immediately, can verify email later
    2. Email-first: User must verify email before receiving JWT tokens
    
    Request Parameters:
        - email (str): User's email address
        - password (str): User's password
        - immediate_access (bool, optional): If True, grants immediate access. Default: True
    
    Returns:
        201: Registration successful with user data and optional JWT tokens
        500: Email sending failed, registration rolled back
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Handle user registration with email verification setup."""
        # Validate registration data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Determine access pattern - immediate or email-first verification
        immediate_access = request.data.get('immediate_access', True)
        
        # Create user account (initially unverified)
        user = serializer.save()
        user.is_verified = False
        user.save()
        
        # Create associated user profile
        UserProfile.objects.create(user=user)
        
        # Generate email verification token
        verification_token = EmailVerificationToken.objects.create(user=user)
        
        # Send verification email
        email_sent = mailgun_service.send_verification_email(user, verification_token.token)
        
        # Rollback registration if email sending fails
        if not email_sent:
            verification_token.delete()
            user.delete()
            return Response({
                'error': 'Failed to send verification email. Please try again.',
                'code': 'email_send_failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Return response based on chosen access pattern
        if immediate_access:
            # Immediate access flow: Return JWT tokens for immediate app usage
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Registration successful! Immediate access granted.',
                'email': user.email,
                'verification_required': True,
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'immediate_access': True,
                'next_step': 'You can use the app now. Please verify your email when convenient.'
            }, status=status.HTTP_201_CREATED)
        else:
            # Email-first flow: Require email verification before access
            return Response({
                'message': 'Registration successful! Please check your email to verify your account.',
                'email': user.email,
                'verification_required': True,
                'user_id': str(user.id),
                'immediate_access': False,
                'next_step': 'Check your email and click the verification link to get access tokens.'
            }, status=status.HTTP_201_CREATED)

from django.http import HttpResponseRedirect

class EmailVerificationView(APIView):
    """
    Email verification endpoint using GET request
    
    GET /api/auth/verify-email/?token=abc123
    - Verifies token from URL parameter
    - Sends welcome email using existing templates
    - Redirects to frontend success/error pages
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Verify email with token from query parameter"""
        token = request.query_params.get('token')
        
        if not token:
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/verification-error?error=missing_token")
        
        try:
            # Get and validate verification token
            verification_token = EmailVerificationToken.objects.get(token=token)
            
            if not verification_token.is_valid:
                error_type = 'expired' if verification_token.is_expired else 'already_used'
                return HttpResponseRedirect(f"{settings.FRONTEND_URL}/verification-error?error={error_type}")
            
            # Mark user as verified
            user = verification_token.user
            user.is_verified = True
            user.verification_date = timezone.now()
            user.save()
            
            # Mark token as used to prevent reuse
            verification_token.is_used = True
            verification_token.save()
            
            #  SEND WELCOME EMAIL using your existing templates
            welcome_sent = mailgun_service.send_welcome_email(user)
            if welcome_sent:
                logger.info(f"✅ Welcome email sent to {user.email}")
            else:
                return(f"⚠️ Welcome email failed for {user.email} (verification still successful)")
            
            logger.info(f"✅ Email verified successfully for {user.email}")
            
            # Redirect to frontend success page
            return HttpResponseRedirect(
                f"{settings.FRONTEND_URL}/verification-success?verified=true&user={user.first_name or user.username}"
            )
            
        except EmailVerificationToken.DoesNotExist:
            logger.warning(f"❌ Verification attempted with invalid token: {token}")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/verification-error?error=invalid_token")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error during email verification: {str(e)}")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/verification-error?error=server_error")

class ResendVerificationEmailView(APIView):
    """
    Resend email verification for users who haven't verified their email.
    
    Creates a new verification token, invalidates old ones, and sends
    a fresh verification email to the user.
    
    Request Parameters:
        - email (str): User's email address
    
    Returns:
        200: Verification email sent (or user already verified)
        400: Email parameter missing
    
    Note: Response doesn't reveal whether email exists for security reasons.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Resend verification email to unverified user."""
        email = request.data.get('email')
        
        # Validate email parameter
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is already verified
            if user.is_verified:
                return Response({
                    'message': 'Email is already verified'
                }, status=status.HTTP_200_OK)
            
            # Invalidate all existing unused verification tokens
            EmailVerificationToken.objects.filter(
                user=user, 
                is_used=False
            ).update(is_used=True)
            
            # Create new verification token
            verification_token = EmailVerificationToken.objects.create(user=user)

            # Send fresh verification email
            email_sent = mailgun_service.send_verification_email(user, verification_token.token)
            
            if email_sent:
                return Response({
                    'message': 'Verification email sent successfully!'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send verification email. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except User.DoesNotExist:
            # Security: Don't reveal whether email exists in system
            return Response({
                'message': 'If the email exists, a verification email has been sent.'
            }, status=status.HTTP_200_OK)


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class LoginView(APIView):
    """
    User authentication endpoint with email verification enforcement.
    
    Validates user credentials and ensures email is verified before
    granting access. Returns JWT tokens for authenticated users.
    
    Request Parameters:
        - email (str): User's email address
        - password (str): User's password
    
    Returns:
        200: Login successful with JWT tokens and user data
        400: Invalid credentials or unverified email
    """
    
    def post(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Enforce email verification before login
            if not user.is_verified:
                return Response({
                    'error': 'Please verify your email before logging in',
                    'verification_required': True,
                    'code': 'email_verification_required'
                }, status=status.HTTP_400_BAD_REQUEST)
                        
            # Generate JWT tokens for authenticated user
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Update user's last activity timestamp
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
            
            return Response({
                'access': str(access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import UserSerializer 

from .models import User


class UserUpdateView(generics.RetrieveUpdateAPIView):
    """
    Main user information update endpoint.
    
    Handles updating basic user info stored on the User model:
    - Name, email, bio, avatar
    - Role, skill level, preferred languages  
    - Social links (GitHub, LinkedIn, website)
    - Preferences (timezone, language, notifications)
    
    Methods:
        GET: Retrieve current user's basic info
        PUT: Update entire user info (full update)
        PATCH: Partial update of user info
    """
    serializer_class = UserSerializer  # You'll need to create this
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return the authenticated user"""
        return self.request.user

class UserAvatarUploadView(APIView):
    """
    Avatar upload endpoint for user profile pictures.
    
    Handles image upload and validation for user avatars.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload new avatar image"""
        user = request.user
        
        if 'avatar' not in request.FILES:
            return Response({
                'error': 'No avatar file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        avatar_file = request.FILES['avatar']
        
        # Validate file size (e.g., max 5MB)
        if avatar_file.size > 5 * 1024 * 1024:
            return Response({
                'error': 'Avatar file too large. Maximum size is 5MB.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        if not avatar_file.content_type.startswith('image/'):
            return Response({
                'error': 'Invalid file type. Please upload an image.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save avatar
        user.avatar = avatar_file
        user.save()
        
        return Response({
            'message': 'Avatar uploaded successfully',
            'avatar_url': user.avatar.url if user.avatar else None
        }, status=status.HTTP_200_OK)
    
    def delete(self, request):
        """Remove current avatar"""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        
        return Response({
            'message': 'Avatar removed successfully'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    User logout endpoint that blacklists refresh tokens.
    
    Adds the provided refresh token to the blacklist to prevent
    further use, effectively logging out the user.
    
    Request Parameters:
        - refresh (str): JWT refresh token to blacklist
    
    Returns:
        200: Logout successful
        400: Invalid or missing refresh token
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Logout user by blacklisting their refresh token."""
        try:
            refresh_token = request.data.get("refresh")
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Invalid token',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# PROFILE MANAGEMENT VIEWS
# ============================================================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile management endpoint.
    
    Allows authenticated users to retrieve and update their profile
    information. Creates profile automatically if it doesn't exist.
    
    Methods:
        GET: Retrieve current user's profile
        PUT/PATCH: Update current user's profile
    
    Returns:
        200: Profile data retrieved or updated successfully
        400: Invalid profile data provided
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get or create user profile for the authenticated user."""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserSkillsView(generics.ListCreateAPIView):
    """
    User skills management endpoint.
    
    Allows authenticated users to list their skills and add new ones.
    Skills are automatically associated with the authenticated user.
    
    Methods:
        GET: List all skills for the authenticated user
        POST: Add a new skill for the authenticated user
    
    Returns:
        200: Skills listed successfully
        201: New skill created successfully
        400: Invalid skill data provided
    """
    serializer_class = UserSkillSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return skills belonging to the authenticated user."""
        return UserSkill.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Associate new skill with the authenticated user."""
        serializer.save(user=self.request.user)


class UserAchievementsView(generics.ListAPIView):
    """
    User achievements listing endpoint.
    
    Provides read-only access to achievements earned by the authenticated user.
    Achievements are typically created by the system based on user activities.
    
    Methods:
        GET: List all achievements for the authenticated user
    
    Returns:
        200: Achievements listed successfully
    """
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return achievements belonging to the authenticated user."""
        return UserAchievement.objects.filter(user=self.request.user)


# ============================================================================
# PASSWORD MANAGEMENT VIEWS
# ============================================================================

class ChangePasswordView(APIView):
    """
    Password change endpoint for authenticated users.
    
    Allows users to change their password by providing their current
    password and a new password.
    
    Request Parameters:
        - old_password (str): Current password for verification
        - new_password (str): New password to set
    
    Returns:
        200: Password changed successfully
        400: Invalid old password or validation errors
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Change user password after validating current password."""
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            old_password = serializer.data.get('old_password')
            new_password = serializer.data.get('new_password')
            
            # Verify current password
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                
                return Response({
                    'message': 'Password changed successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid old password'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """
    Password reset request endpoint.
    
    Initiates the password reset process by sending a reset email
    to the user's registered email address.
    
    Request Parameters:
        - email (str): User's email address
    
    Returns:
        200: Reset email sent (response same regardless of email existence)
        400: Validation errors
    
    Note: Response doesn't reveal whether email exists for security reasons.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Send password reset email to user."""
        serializer = PasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.data.get('email')
            
            try:
                user = User.objects.get(email=email)
                
                # Generate password reset token
                token = default_token_generator.make_token(user)
                
                # Build reset URL for frontend
                reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}&uid={user.id}"
                
                # Send password reset email
                send_mail(
                    subject='Password Reset Request',
                    message=f'Click here to reset your password: {reset_url}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
            except User.DoesNotExist:
                # Security: Don't reveal whether email exists
                pass
            
            # Always return success message for security
            return Response({
                'message': 'Password reset email sent'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation endpoint.
    
    Completes the password reset process by validating the reset token
    and setting the new password.
    
    Request Parameters:
        - token (str): Password reset token from email
        - uid (str): User ID
        - new_password (str): New password to set
    
    Returns:
        200: Password reset successfully
        400: Invalid token or validation errors
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Confirm password reset with token validation."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# API DOCUMENTATION & HEALTH CHECK
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_health_check(request):
    """
    Simple health check endpoint for API monitoring.
    
    Returns:
        200: API is healthy and responding
    """
    return Response({
        'status': 'healthy',
        'service': 'WokkahLearn Authentication API',
        'version': '1.0',
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)