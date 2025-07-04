# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import uuid
from datetime import timedelta

class User(AbstractUser):
    """Custom user model with role-based access"""
    
    class Role(models.TextChoices):
        STUDENT = 'student', _('Student')
        INSTRUCTOR = 'instructor', _('Instructor')
        MENTOR = 'mentor', _('Mentor')
        TA = 'ta', _('Teaching Assistant')
        ADMIN = 'admin', _('Administrator')
        ORG_ADMIN = 'org_admin', _('Organization Administrator')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    
    # Profile information
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    github_username = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    
    # Learning preferences
    preferred_languages = models.JSONField(default=list, help_text="Programming languages user is interested in")
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert')
        ],
        default='beginner'
    )
    
    # Activity tracking
    last_activity = models.DateTimeField(null=True, blank=True)
    total_study_time = models.DurationField(default=timedelta)
    courses_completed = models.PositiveIntegerField(default=0)
    
    # Verification and status
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    premium_expires = models.DateTimeField(null=True, blank=True)
    
    # Organization relationship
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Preferences
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    # FIXED: Add related_name to avoid conflicts with built-in User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="wokkahlearn_user_set",
        related_query_name="wokkahlearn_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="wokkahlearn_user_set", 
        related_query_name="wokkahlearn_user",
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        # FIXED: Remove db_table to avoid conflicts with Django's built-in User
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR
    
    @property
    def is_mentor(self):
        return self.role == self.Role.MENTOR
    
    @property
    def is_ta(self):
        return self.role == self.Role.TA
    
    @property
    def can_teach(self):
        return self.role in [self.Role.INSTRUCTOR, self.Role.MENTOR, self.Role.TA]


class Organization(models.Model):
    """Organization model for schools, companies, etc."""
    
    class OrgType(models.TextChoices):
        SCHOOL = 'school', _('School')
        UNIVERSITY = 'university', _('University')
        COMPANY = 'company', _('Company')
        BOOTCAMP = 'bootcamp', _('Bootcamp')
        OTHER = 'other', _('Other')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    org_type = models.CharField(max_length=20, choices=OrgType.choices)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='org_logos/', null=True, blank=True)
    
    # Contact information
    contact_email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Settings
    domain_whitelist = models.JSONField(
        default=list,
        help_text="Email domains allowed for auto-enrollment"
    )
    is_active = models.BooleanField(default=True)
    max_users = models.PositiveIntegerField(null=True, blank=True)
    
    # Subscription
    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise')
        ],
        default='free'
    )
    subscription_expires = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Extended user profile with learning analytics"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Learning statistics
    total_lessons_completed = models.PositiveIntegerField(default=0)
    total_exercises_completed = models.PositiveIntegerField(default=0)
    total_projects_completed = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    # Skill ratings (0-100)
    programming_skills = models.JSONField(default=dict)  # {"python": 75, "javascript": 60}
    
    # Learning goals
    weekly_goal_hours = models.PositiveIntegerField(default=5)
    target_completion_date = models.DateField(null=True, blank=True)
    learning_objectives = models.JSONField(default=list)
    
    # AI tutor preferences
    ai_assistance_level = models.CharField(
        max_length=20,
        choices=[
            ('minimal', 'Minimal Help'),
            ('hints', 'Hints Only'),
            ('guided', 'Guided Learning'),
            ('full', 'Full Assistance')
        ],
        default='guided'
    )
    preferred_explanation_style = models.CharField(
        max_length=20,
        choices=[
            ('concise', 'Concise'),
            ('detailed', 'Detailed'),
            ('visual', 'Visual'),
            ('examples', 'Example-heavy')
        ],
        default='detailed'
    )
    
    # Social features
    public_profile = models.BooleanField(default=True)
    show_progress = models.BooleanField(default=True)
    allow_mentor_contact = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"
    
    def update_streak(self):
        """Update user's learning streak"""
        from datetime import date, timedelta
        
        today = date.today()
        if self.last_activity_date:
            if self.last_activity_date == today - timedelta(days=1):
                self.current_streak += 1
            elif self.last_activity_date != today:
                self.current_streak = 1
        else:
            self.current_streak = 1
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_activity_date = today
        self.save()


class UserSkill(models.Model):
    """Track user skills and proficiency levels"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        choices=[
            ('language', 'Programming Language'),
            ('framework', 'Framework'),
            ('tool', 'Tool'),
            ('concept', 'Concept'),
            ('soft_skill', 'Soft Skill')
        ]
    )
    proficiency_level = models.PositiveIntegerField(
        default=0,
        help_text="Skill level from 0-100"
    )
    verified = models.BooleanField(default=False)
    last_assessed = models.DateTimeField(auto_now=True)
    
    # Evidence of skill
    evidence_count = models.PositiveIntegerField(default=0)
    endorsements = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'skill_name']
        verbose_name = _('User Skill')
        verbose_name_plural = _('User Skills')
        ordering = ['-proficiency_level', 'skill_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.skill_name} ({self.proficiency_level}%)"


class UserAchievement(models.Model):
    """Track user achievements and badges"""
    
    class AchievementType(models.TextChoices):
        COMPLETION = 'completion', _('Completion')
        STREAK = 'streak', _('Streak')
        SKILL = 'skill', _('Skill Mastery')
        SOCIAL = 'social', _('Social')
        SPECIAL = 'special', _('Special')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_id = models.CharField(max_length=100)
    achievement_type = models.CharField(max_length=20, choices=AchievementType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=100, help_text="Icon class or URL")
    earned_at = models.DateTimeField(auto_now_add=True)
    
    # Achievement data
    progress_data = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ['user', 'achievement_id']
        verbose_name = _('User Achievement')
        verbose_name_plural = _('User Achievements')
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"
    


import secrets
from django.utils import timezone
from datetime import timedelta

def generate_verification_token():
    """Generate a random verification token"""
    return secrets.token_urlsafe(32)

class EmailVerificationToken(models.Model):
    """Email verification tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=64, unique=True, default=generate_verification_token)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 24 hours
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    class Meta:
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'