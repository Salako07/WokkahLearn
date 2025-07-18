# api/views.py - FIXED VERSION with correct filter fields
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import timedelta
from django.http import JsonResponse

# Safe imports - only import from apps we know exist
try:
    from courses.models import Course, Lesson, Exercise, CourseEnrollment, LessonProgress, ExerciseSubmission, Module
    from courses.serializers import CourseSerializer, LessonSerializer, ExerciseSerializer
    COURSES_AVAILABLE = True
except ImportError:
    COURSES_AVAILABLE = False

try:
    from ai_tutor.models import AITutorSession, AIMessage
    AI_TUTOR_AVAILABLE = True
except ImportError:
    AI_TUTOR_AVAILABLE = False

# Optional imports for apps that might not be ready yet
try:
    from code_execution.models import CodeExecution, ExecutionEnvironment
    CODE_EXECUTION_AVAILABLE = True
except ImportError:
    CODE_EXECUTION_AVAILABLE = False

try:
    from collaboration.models import CollaborationRoom, RoomParticipant, ChatMessage
    COLLABORATION_AVAILABLE = True
except ImportError:
    COLLABORATION_AVAILABLE = False

try:
    from analytics.models import LearningAnalytics, PerformanceMetric
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False


# Only create ViewSets for available apps
if COURSES_AVAILABLE:
    class CourseViewSet(viewsets.ModelViewSet):
        """API endpoints for courses"""
        queryset = Course.objects.filter(status='published')
        serializer_class = CourseSerializer
        filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
        
        # FIXED: Only use simple model fields (no JSONFields like programming_languages)
        filterset_fields = [
            'difficulty_level',  # CharField with choices - OK
            'category',          # ForeignKey - OK  
            'is_free',           # BooleanField - OK
            'status',            # CharField with choices - OK
            'premium_only',      # BooleanField - OK
            'instructor',        # ForeignKey - OK
        ]
        # NOTE: programming_languages, tags, skills_gained are JSONFields and need custom filters
        
        # FIXED: Only search in text fields that exist
        search_fields = ['title', 'description', 'short_description']
        
        # FIXED: Only order by fields that exist
        ordering_fields = ['created_at', 'total_enrollments', 'average_rating', 'title']
        ordering = ['-created_at']
        
        def get_permissions(self):
            if self.action in ['create', 'update', 'partial_update', 'destroy']:
                permission_classes = [IsAuthenticated]
            else:
                permission_classes = [permissions.AllowAny]
            return [permission() for permission in permission_classes]

    class LessonViewSet(viewsets.ModelViewSet):
        """API endpoints for lessons"""
        queryset = Lesson.objects.all()
        serializer_class = LessonSerializer
        permission_classes = [IsAuthenticated]
        filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
        
        # FIXED: Only use simple model fields
        filterset_fields = ['module', 'lesson_type', 'is_preview', 'is_required']
        search_fields = ['title', 'description']
        ordering_fields = ['order', 'created_at', 'title']
        ordering = ['order']

    class ExerciseViewSet(viewsets.ModelViewSet):
        """API endpoints for exercises"""
        queryset = Exercise.objects.all()
        serializer_class = ExerciseSerializer
        permission_classes = [IsAuthenticated]
        filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
        
        # FIXED: Use correct field names from Exercise model
        filterset_fields = [
            'lesson',              # ForeignKey - OK
            'exercise_type',       # CharField with choices - OK
            'difficulty',          # CharField with choices - OK (not difficulty_level)
            'programming_language' # CharField - OK (not programming_languages)
        ]
        search_fields = ['title', 'description']
        ordering_fields = ['order', 'created_at', 'title']
        ordering = ['order']

else:
    # Create dummy ViewSets if courses app is not available
    class CourseViewSet(viewsets.ViewSet):
        def list(self, request):
            return Response({'error': 'Courses app not available'}, 
                          status=status.HTTP_503_SERVICE_UNAVAILABLE)

    class LessonViewSet(viewsets.ViewSet):
        def list(self, request):
            return Response({'error': 'Courses app not available'}, 
                          status=status.HTTP_503_SERVICE_UNAVAILABLE)

    class ExerciseViewSet(viewsets.ViewSet):
        def list(self, request):
            return Response({'error': 'Courses app not available'}, 
                          status=status.HTTP_503_SERVICE_UNAVAILABLE)


if AI_TUTOR_AVAILABLE:
    class AITutorViewSet(viewsets.ModelViewSet):
        """AI Tutor sessions"""
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            return AITutorSession.objects.filter(student=self.request.user)
        
        def list(self, request):
            return Response({
                'message': 'AI Tutor service available',
                'sessions': []
            })
else:
    class AITutorViewSet(viewsets.ViewSet):
        def list(self, request):
            return Response({'error': 'AI Tutor app not available'}, 
                          status=status.HTTP_503_SERVICE_UNAVAILABLE)


# Placeholder ViewSets for apps not ready yet
class CodeExecutionViewSet(viewsets.ViewSet):
    """Code execution endpoints (placeholder)"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        return Response({
            'message': 'Code execution service not yet implemented',
            'available': CODE_EXECUTION_AVAILABLE
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

class CollaborationRoomViewSet(viewsets.ViewSet):
    """Collaboration room endpoints (placeholder)"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        return Response({
            'message': 'Collaboration service not yet implemented',
            'available': COLLABORATION_AVAILABLE
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

class AnalyticsViewSet(viewsets.ViewSet):
    """Analytics endpoints (placeholder)"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        return Response({
            'message': 'Analytics service not yet implemented',
            'available': ANALYTICS_AVAILABLE
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


# Error handlers for API
def bad_request(request, exception):
    return JsonResponse({'error': 'Bad Request', 'status': 400}, status=400)

def permission_denied(request, exception):
    return JsonResponse({'error': 'Permission Denied', 'status': 403}, status=403)

def not_found(request, exception):
    return JsonResponse({'error': 'Not Found', 'status': 404}, status=404)

def server_error(request):
    return JsonResponse({'error': 'Internal Server Error', 'status': 500}, status=500)
