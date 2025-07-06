# api/serializers.py - FIXED VERSION with safe imports
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

# Safe imports - only import from apps we know exist
try:
    from courses.models import (
        Course, Module, Lesson, Exercise, CourseEnrollment, 
        LessonProgress, ExerciseSubmission, CourseCategory
    )
    from courses.serializers import (
        CourseSerializer as BaseCourseSerializer,
        LessonSerializer as BaseLessonSerializer,
        ExerciseSerializer as BaseExerciseSerializer,
        CourseEnrollmentSerializer as BaseCourseEnrollmentSerializer,
        ExerciseSubmissionSerializer as BaseExerciseSubmissionSerializer,
        ModuleSerializer as BaseModuleSerializer
    )
    COURSES_AVAILABLE = True
except ImportError:
    COURSES_AVAILABLE = False

try:
    from accounts.models import UserProfile, UserSkill, UserAchievement
    ACCOUNTS_AVAILABLE = True
except ImportError:
    ACCOUNTS_AVAILABLE = False

try:
    from ai_tutor.models import AITutorSession, AIMessage, LearningPathRecommendation
    from ai_tutor.serializers import (
        AITutorSessionSerializer as BaseAITutorSessionSerializer,
        AIMessageSerializer as BaseAIMessageSerializer
    )
    AI_TUTOR_AVAILABLE = True
except ImportError:
    AI_TUTOR_AVAILABLE = False

# Optional imports for apps that might not be ready yet
try:
    from code_execution.models import CodeExecution, ExecutionEnvironment, TestResult
    CODE_EXECUTION_AVAILABLE = True
except ImportError:
    CODE_EXECUTION_AVAILABLE = False

try:
    from analytics.models import LearningAnalytics, StudySession, PerformanceMetric
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

try:
    from collaboration.models import CollaborationRoom, RoomParticipant, ChatMessage
    COLLABORATION_AVAILABLE = True
except ImportError:
    COLLABORATION_AVAILABLE = False


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


# Conditional serializers based on app availability
if ACCOUNTS_AVAILABLE:
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
                'experience_years', 'is_primary', 'verified_by',
                'last_used', 'created_at'
            ]
else:
    class UserProfileSerializer(serializers.Serializer):
        message = serializers.CharField(default="User profiles not available")

    class UserSkillSerializer(serializers.Serializer):
        message = serializers.CharField(default="User skills not available")


if COURSES_AVAILABLE:
    # Re-export course serializers
    CourseSerializer = BaseCourseSerializer
    LessonSerializer = BaseLessonSerializer
    ExerciseSerializer = BaseExerciseSerializer
    CourseEnrollmentSerializer = BaseCourseEnrollmentSerializer
    ExerciseSubmissionSerializer = BaseExerciseSubmissionSerializer
    ModuleSerializer = BaseModuleSerializer
else:
    # Placeholder serializers
    class CourseSerializer(serializers.Serializer):
        message = serializers.CharField(default="Courses not available")

    class LessonSerializer(serializers.Serializer):
        message = serializers.CharField(default="Lessons not available")

    class ExerciseSerializer(serializers.Serializer):
        message = serializers.CharField(default="Exercises not available")

    class CourseEnrollmentSerializer(serializers.Serializer):
        message = serializers.CharField(default="Enrollments not available")

    class ExerciseSubmissionSerializer(serializers.Serializer):
        message = serializers.CharField(default="Submissions not available")

    class ModuleSerializer(serializers.Serializer):
        message = serializers.CharField(default="Modules not available")


if AI_TUTOR_AVAILABLE:
    # Re-export AI tutor serializers
    AITutorSessionSerializer = BaseAITutorSessionSerializer
    AIMessageSerializer = BaseAIMessageSerializer
    
    class LearningPathRecommendationSerializer(serializers.ModelSerializer):
        class Meta:
            model = LearningPathRecommendation
            fields = [
                'id', 'recommendation_type', 'priority', 'title',
                'description', 'reasoning', 'confidence_score',
                'estimated_completion_time', 'is_accepted', 'created_at'
            ]
else:
    class AITutorSessionSerializer(serializers.Serializer):
        message = serializers.CharField(default="AI Tutor not available")

    class AIMessageSerializer(serializers.Serializer):
        message = serializers.CharField(default="AI Messages not available")

    class LearningPathRecommendationSerializer(serializers.Serializer):
        message = serializers.CharField(default="Learning paths not available")


# Placeholder serializers for unimplemented apps
class CodeExecutionSerializer(serializers.Serializer):
    message = serializers.CharField(default="Code execution not yet implemented")
    available = serializers.BooleanField(default=CODE_EXECUTION_AVAILABLE)

class ExecutionEnvironmentSerializer(serializers.Serializer):
    message = serializers.CharField(default="Execution environments not yet implemented")
    available = serializers.BooleanField(default=CODE_EXECUTION_AVAILABLE)

class CollaborationRoomSerializer(serializers.Serializer):
    message = serializers.CharField(default="Collaboration not yet implemented")
    available = serializers.BooleanField(default=COLLABORATION_AVAILABLE)

class RoomParticipantSerializer(serializers.Serializer):
    message = serializers.CharField(default="Room participants not yet implemented")
    available = serializers.BooleanField(default=COLLABORATION_AVAILABLE)

class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField(default="Chat messages not yet implemented")
    available = serializers.BooleanField(default=COLLABORATION_AVAILABLE)

class LearningAnalyticsSerializer(serializers.Serializer):
    message = serializers.CharField(default="Learning analytics not yet implemented")
    available = serializers.BooleanField(default=ANALYTICS_AVAILABLE)

class PerformanceMetricSerializer(serializers.Serializer):
    message = serializers.CharField(default="Performance metrics not yet implemented")
    available = serializers.BooleanField(default=ANALYTICS_AVAILABLE)