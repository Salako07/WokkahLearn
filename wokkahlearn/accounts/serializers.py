from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from .models import User, UserProfile, UserSkill, UserAchievement

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'role')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not username and not email:
            raise serializers.ValidationError('Username or email is required')
        
        # Since USERNAME_FIELD = 'email', authenticate() expects email in username param
        if email:
            # Use email directly for authentication
            auth_username = email
        else:
            # Convert username to email for authentication
            try:
                user_obj = User.objects.get(username=username)
                auth_username = user_obj.email  # Use email for authenticate()
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials')
        
        # Authenticate using email (in username parameter)
        user = authenticate(username=auth_username, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        
        # Check email verification in production
        if not user.is_verified:
            raise serializers.ValidationError({
                'error': 'Email not verified',
                'code': 'email_not_verified',
                'message': 'Please verify your email address before logging in.',
                'email': user.email,
                'user_id': str(user.id)
            })
        
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uid = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])
    
    def validate(self, attrs):
        try:
            user = User.objects.get(id=attrs['uid'])
            if not default_token_generator.check_token(user, attrs['token']):
                raise serializers.ValidationError('Invalid token')
            
            # Set new password
            user.set_password(attrs['password'])
            user.save()
            
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid user')
        
        return attrs


# User and Profile Serializers
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'bio', 'avatar', 'github_username', 'linkedin_url', 
            'preferred_languages', 'skill_level', 'is_verified', 'is_premium',
            'timezone', 'language'
        ]
        read_only_fields = ['id', 'is_verified', 'is_premium']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'total_lessons_completed', 'total_exercises_completed',
            'current_streak', 'longest_streak', 'programming_skills',
            'weekly_goal_hours', 'ai_assistance_level', 'preferred_explanation_style',
            'public_profile', 'show_progress'
        ]


class UserSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSkill
        fields = [
            'id', 'skill_name', 'category', 'proficiency_level',
            'verified', 'evidence_count', 'last_assessed'
        ]


class UserAchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement_id', 'achievement_type', 'title',
            'description', 'icon', 'earned_at', 'progress_data'
        ]

# Add this to your accounts/serializers.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that allows login with email or username"""
    
    username_field = 'email'  # This makes it accept email in the username field
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email field optional since we want to support both email and username
        self.fields['email'] = serializers.EmailField(required=False)
        self.fields['username'] = serializers.CharField(required=False)
        # Remove the default username field requirement
        self.fields[self.username_field].required = False
    
    def validate(self, attrs):
        # Get email, username, and password from request
        email = attrs.get('email')
        username = attrs.get('username') 
        password = attrs.get('password')
        
        # Require either email or username
        if not email and not username:
            raise serializers.ValidationError('Email or username is required')
        
        # Determine the user to authenticate
        if email:
            try:
                user = User.objects.get(email=email)
                username_for_auth = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid credentials')
        else:
            username_for_auth = username
        
        # Authenticate the user
        user = authenticate(username=username_for_auth, password=password)
        
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled')
        
        # Create tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last activity
        from django.utils import timezone
        user.last_activity = timezone.now()
        user.save(update_fields=['last_activity'])
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_verified': user.is_verified,
                'is_premium': user.is_premium,
            }
        }

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating main user information"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'username',
            'bio', 'role', 'skill_level', 'preferred_languages',
            'github_username', 'linkedin_url', 'website_url',
            'timezone', 'language', 'email_notifications', 'marketing_emails'
        ]
        read_only_fields = ['email', 'username']  # Don't allow email/username changes
    
    def validate_role(self, value):
        """Validate role changes (you might want to restrict this)"""
        user = self.context['request'].user
        
        # Example: Only allow certain role changes
        if user.role == User.Role.STUDENT and value != User.Role.STUDENT:
            # Allow students to upgrade to instructor
            if value not in [User.Role.INSTRUCTOR, User.Role.MENTOR]:
                raise serializers.ValidationError(
                    "Students can only upgrade to instructor or mentor roles"
                )
        
        return value

