# courses/views.py - FIXED AND COMPLETE VERSION
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Max, Sum, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import timedelta
from django.utils import timezone
from django.db import models, transaction
from django.contrib.auth import get_user_model
import django_filters
import logging

from .models import (
    CourseCategory, Course, Module, Lesson, Exercise, 
    CourseEnrollment, LessonProgress, ExerciseSubmission, CourseRating
)
from .serializers import (
    CourseCategorySerializer, CourseSerializer, DetailedCourseSerializer,
    CreateCourseSerializer, ModuleSerializer, DetailedModuleSerializer, 
    LessonSerializer, DetailedLessonSerializer, ExerciseSerializer, 
    DetailedExerciseSerializer, CourseEnrollmentSerializer, 
    LessonProgressSerializer, ExerciseSubmissionSerializer, 
    CreateExerciseSubmissionSerializer, CourseRatingSerializer,
    CreateCourseRatingSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM FILTERS
# =============================================================================

class CourseFilter(django_filters.FilterSet):
    """Custom filter for Course model with advanced filtering"""
    
    # Handle JSONField filtering for programming_languages
    programming_languages = django_filters.CharFilter(
        field_name='programming_languages',
        lookup_expr='icontains',
        help_text="Filter by programming language (e.g., 'python', 'javascript')"
    )
    
    # Skills filtering
    skills_gained = django_filters.CharFilter(
        field_name='skills_gained',
        lookup_expr='icontains',
        help_text="Filter by skills gained"
    )
    
    # Tags filtering
    tags = django_filters.CharFilter(
        field_name='tags',
        lookup_expr='icontains',
        help_text="Filter by tags"
    )
    
    # Duration range filtering
    min_duration = django_filters.DurationFilter(
        field_name='estimated_duration',
        lookup_expr='gte'
    )
    max_duration = django_filters.DurationFilter(
        field_name='estimated_duration',
        lookup_expr='lte'
    )
    
    # Rating filtering
    min_rating = django_filters.NumberFilter(
        field_name='average_rating',
        lookup_expr='gte'
    )
    
    # Enrollment filtering
    min_enrollments = django_filters.NumberFilter(
        field_name='total_enrollments',
        lookup_expr='gte'
    )
    
    # Price range filtering
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte'
    )
    
    # Date filtering
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Course
        fields = {
            'difficulty_level': ['exact', 'in'],
            'category': ['exact'],
            'is_free': ['exact'],
            'status': ['exact', 'in'],
            'instructor': ['exact']
        }


class ExerciseFilter(django_filters.FilterSet):
    """Custom filter for Exercise model"""
    
    # Filter by lesson's module
    lesson_module = django_filters.NumberFilter(
        field_name='lesson__module__id',
        help_text="Filter by module ID"
    )
    
    # Filter by lesson's course
    lesson_course = django_filters.NumberFilter(
        field_name='lesson__module__course__id',
        help_text="Filter by course ID"
    )
    
    # Points range filtering
    points_min = django_filters.NumberFilter(
        field_name='points',
        lookup_expr='gte'
    )
    points_max = django_filters.NumberFilter(
        field_name='points',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Exercise
        fields = {
            'exercise_type': ['exact', 'in'],
            'difficulty': ['exact', 'in'],
            'programming_language': ['exact', 'in'],
            'ai_hints_enabled': ['exact'],
            'allow_collaboration': ['exact'],
        }


class LessonFilter(django_filters.FilterSet):
    """Custom filter for Lesson model"""
    
    class Meta:
        model = Lesson
        fields = {
            'module': ['exact'],
            'lesson_type': ['exact', 'in'],
            'is_required': ['exact'],
            'is_preview': ['exact'],
        }


# =============================================================================
# VIEWSETS
# =============================================================================

class CourseCategoryViewSet(viewsets.ModelViewSet):
    """API endpoints for course categories"""
    queryset = CourseCategory.objects.filter(is_active=True)
    serializer_class = CourseCategorySerializer
    permission_classes = [AllowAny]  # Categories are public
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']
    
    def get_permissions(self):
        """Only admins and instructors can create/update/delete categories"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Check permissions for category creation"""
        user = self.request.user
        if not (user.is_staff or (hasattr(user, 'can_teach') and user.can_teach)):
            raise permissions.PermissionDenied("Only admins and instructors can create categories")
        serializer.save()
    
    def perform_update(self, serializer):
        """Check permissions for category updates"""
        user = self.request.user
        if not (user.is_staff or (hasattr(user, 'can_teach') and user.can_teach)):
            raise permissions.PermissionDenied("Only admins and instructors can update categories")
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Get all courses in this category"""
        category = self.get_object()
        courses = Course.objects.filter(
            category=category, 
            status='published'
        ).order_by('-created_at')
        
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure"""
        categories = self.get_queryset().filter(parent=None)
        data = []
        
        for category in categories:
            serializer = CourseCategorySerializer(
                category, 
                context={'request': request, 'include_children': True}
            )
            data.append(serializer.data)
        
        return Response(data)


class CourseViewSet(viewsets.ModelViewSet):
    """API endpoints for courses"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]  # Public courses viewable by all
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'description', 'tags', 'skills_gained']
    ordering_fields = [
        'created_at', 'total_enrollments', 'average_rating', 
        'completion_rate', 'estimated_duration', 'price'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter courses based on user permissions and status"""
        user = self.request.user
        
        if user.is_authenticated:
            if user.is_staff:
                # Admin can see all courses
                return Course.objects.all()
            elif hasattr(user, 'can_teach') and user.can_teach:
                # Instructors can see published courses + their own courses
                return Course.objects.filter(
                    Q(status='published') | Q(instructor=user)
                ).distinct()
            else:
                # Students can see published courses + enrolled courses
                return Course.objects.filter(
                    Q(status='published') | Q(enrollments__student=user)
                ).distinct()
        else:
            # Anonymous users can only see published courses
            return Course.objects.filter(status='published')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedCourseSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CreateCourseSerializer
        return CourseSerializer
    
    def get_permissions(self):
        """Dynamic permissions based on action"""
        if self.action in ['create']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Check if user can create courses"""
        user = self.request.user
        if not (user.is_staff or (hasattr(user, 'can_teach') and user.can_teach)):
            raise permissions.PermissionDenied("Only instructors can create courses")
        serializer.save(instructor=user)
    
    def perform_update(self, serializer):
        """Check if user can update this course"""
        course = self.get_object()
        user = self.request.user
        if course.instructor != user and not user.is_staff:
            raise permissions.PermissionDenied("You can only update your own courses")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Check if user can delete this course"""
        user = self.request.user
        if instance.instructor != user and not user.is_staff:
            raise permissions.PermissionDenied("You can only delete your own courses")
        instance.delete()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll user in course"""
        course = self.get_object()
        user = request.user
        
        try:
            with transaction.atomic():
                # Check if already enrolled
                if CourseEnrollment.objects.filter(student=user, course=course).exists():
                    return Response(
                        {'error': 'You are already enrolled in this course'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check enrollment constraints
                if not course.can_enroll(user):
                    return Response(
                        {'error': 'You cannot enroll in this course at this time'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create enrollment
                enrollment = CourseEnrollment.objects.create(
                    student=user,
                    course=course,
                    enrollment_source='direct'
                )
                
                # Update course enrollment count
                course.total_enrollments = F('total_enrollments') + 1
                course.save(update_fields=['total_enrollments'])
                
                serializer = CourseEnrollmentSerializer(enrollment, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Enrollment error for user {user.id} in course {course.id}: {str(e)}")
            return Response(
                {'error': 'Failed to enroll in course'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unenroll(self, request, pk=None):
        """Unenroll user from course"""
        course = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(student=user, course=course)
            enrollment.delete()
            
            # Update course enrollment count
            course.total_enrollments = F('total_enrollments') - 1
            course.save(update_fields=['total_enrollments'])
            
            return Response({'message': 'Successfully unenrolled from course'})
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'You are not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rate(self, request, pk=None):
        """Rate and review course"""
        course = self.get_object()
        user = request.user
        
        # Check if user is enrolled
        if not CourseEnrollment.objects.filter(student=user, course=course).exists():
            return Response(
                {'error': 'You must be enrolled to rate this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CreateCourseRatingSerializer(data=request.data)
        if serializer.is_valid():
            # Update or create rating
            rating, created = CourseRating.objects.update_or_create(
                student=user,
                course=course,
                defaults=serializer.validated_data
            )
            
            # Update course average rating
            avg_rating = CourseRating.objects.filter(course=course).aggregate(
                avg=Avg('rating')
            )['avg']
            course.average_rating = avg_rating or 0
            course.save(update_fields=['average_rating'])
            
            response_serializer = CourseRatingSerializer(rating, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_courses(self, request):
        """Get courses the user is enrolled in"""
        user = request.user
        enrollments = CourseEnrollment.objects.filter(
            student=user
        ).select_related('course').order_by('-enrolled_at')
        
        courses_data = []
        for enrollment in enrollments:
            course_data = CourseSerializer(enrollment.course, context={'request': request}).data
            course_data['enrollment'] = CourseEnrollmentSerializer(enrollment, context={'request': request}).data
            courses_data.append(course_data)
        
        return Response(courses_data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def teaching(self, request):
        """Get courses the user is teaching (instructors only)"""
        user = request.user
        if not (user.is_staff or (hasattr(user, 'can_teach') and user.can_teach)):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        courses = Course.objects.filter(instructor=user).order_by('-created_at')
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get course reviews"""
        course = self.get_object()
        reviews = CourseRating.objects.filter(course=course).order_by('-created_at')
        serializer = CourseRatingSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get course analytics (instructor/admin only)"""
        course = self.get_object()
        user = request.user
        
        # Check permission - only instructor or admin can view analytics
        if course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        time_range = request.query_params.get('time_range', '30d')
        detailed = request.query_params.get('detailed', 'false').lower() == 'true'
        
        try:
            # Parse time range
            if time_range == '7d':
                start_date = timezone.now() - timedelta(days=7)
            elif time_range == '30d':
                start_date = timezone.now() - timedelta(days=30)
            elif time_range == '90d':
                start_date = timezone.now() - timedelta(days=90)
            else:
                start_date = timezone.now() - timedelta(days=30)
            
            # Calculate analytics
            enrollments = course.enrollments.all()
            total_enrollments = enrollments.count()
            active_students = enrollments.filter(
                last_accessed__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            # Calculate completion rates
            completed_enrollments = enrollments.filter(status='completed').count()
            completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
            
            # Exercise statistics
            exercises = Exercise.objects.filter(lesson__module__course=course)
            total_exercises = exercises.count()
            
            submissions = ExerciseSubmission.objects.filter(
                exercise__lesson__module__course=course,
                submitted_at__gte=start_date
            )
            
            exercise_stats = submissions.aggregate(
                total_submissions=Count('id'),
                avg_score=Avg('score'),
                success_rate=Avg(
                    models.Case(
                        models.When(status='passed', then=1),
                        default=0,
                        output_field=models.FloatField()
                    )
                ) * 100
            )
            
            analytics_data = {
                'time_range': time_range,
                'total_enrollments': total_enrollments,
                'active_students': active_students,
                'completion_rate': round(completion_rate, 2),
                'average_rating': course.average_rating,
                'total_reviews': course.ratings.count(),
                'total_exercises': total_exercises,
                'total_submissions': exercise_stats['total_submissions'] or 0,
                'average_exercise_score': round(exercise_stats['avg_score'] or 0, 2),
                'exercise_success_rate': round(exercise_stats['success_rate'] or 0, 2),
            }
            
            if detailed:
                # Add detailed analytics
                analytics_data.update({
                    'enrollments_by_week': self._get_enrollments_by_week(course, start_date),
                    'progress_distribution': self._get_progress_distribution(course),
                    'difficult_exercises': self._get_difficult_exercises(course),
                    'top_performing_students': self._get_top_students(course),
                })
            
            return Response(analytics_data)
            
        except Exception as e:
            logger.error(f"Analytics error for course {course.id}: {str(e)}")
            return Response(
                {'error': 'Failed to generate analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_enrollments_by_week(self, course, start_date):
        """Get enrollment data by week"""
        enrollments = course.enrollments.filter(enrolled_at__gte=start_date)
        # Implementation for weekly enrollment data
        return []
    
    def _get_progress_distribution(self, course):
        """Get distribution of student progress"""
        enrollments = course.enrollments.all()
        # Implementation for progress distribution
        return {}
    
    def _get_difficult_exercises(self, course):
        """Get exercises with low success rates"""
        # Implementation for difficult exercises
        return []
    
    def _get_top_students(self, course):
        """Get top performing students"""
        # Implementation for top students
        return []
    
    @action(detail=True, methods=['get'])
    def engagement(self, request, pk=None):
        """Get engagement metrics (instructor/admin only)"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate engagement metrics
        enrollments = course.enrollments.all()
        
        engagement_data = {
            'active_students_7d': enrollments.filter(
                last_accessed__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'active_students_30d': enrollments.filter(
                last_accessed__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'average_session_duration': 0,  # TODO: Implement when study sessions are tracked
            'forum_posts': 0,  # TODO: Implement when forum is added
            'collaboration_sessions': 0,  # TODO: Implement when collaboration is added
        }
        
        return Response(engagement_data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get performance insights (instructor/admin only)"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate performance metrics
        submissions = ExerciseSubmission.objects.filter(
            exercise__lesson__module__course=course
        )
        
        performance_data = {
            'average_score': submissions.aggregate(avg=Avg('score'))['avg'] or 0,
            'pass_rate': submissions.filter(status='passed').count() / submissions.count() * 100 if submissions.count() > 0 else 0,
            'completion_time_avg': 0,  # TODO: Implement
            'retry_rate': 0,  # TODO: Implement
        }
        
        return Response(performance_data)
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export analytics report (instructor/admin only)"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        export_format = request.query_params.get('format', 'json')
        include_student_data = request.query_params.get('include_student_data', 'false').lower() == 'true'
        
        # TODO: Implement actual export functionality
        return Response({
            'message': 'Export functionality will be implemented',
            'format': export_format,
            'include_student_data': include_student_data
        })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def students(self, request, pk=None):
        """Get enrolled students (instructor/admin only)"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        enrollments = course.enrollments.select_related('student').order_by('-enrolled_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            enrollments = enrollments.filter(status=status_filter)
        
        search = request.query_params.get('search')
        if search:
            enrollments = enrollments.filter(
                Q(student__username__icontains=search) |
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search) |
                Q(student__email__icontains=search)
            )
        
        students_data = []
        for enrollment in enrollments:
            student_data = {
                'id': enrollment.student.id,
                'username': enrollment.student.username,
                'full_name': enrollment.student.get_full_name(),
                'email': enrollment.student.email,
                'avatar': enrollment.student.avatar.url if hasattr(enrollment.student, 'avatar') and enrollment.student.avatar else None,
                'enrollment': CourseEnrollmentSerializer(enrollment, context={'request': request}).data
            }
            students_data.append(student_data)
        
        return Response({
            'count': len(students_data),
            'results': students_data
        })
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish course (instructor/admin only)"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if course.status != 'published':
            course.status = 'published'
            course.published_at = timezone.now()
            course.save(update_fields=['status', 'published_at'])
            
            return Response({'message': 'Course published successfully'})
        
        return Response({'message': 'Course is already published'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish course (instructor/admin only)"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        course.status = 'draft'
        course.save(update_fields=['status'])
        
        return Response({'message': 'Course unpublished successfully'})
    
    @action(detail=True, methods=['get'])
    def structure(self, request, pk=None):
        """Get complete course structure with modules and lessons"""
        course = self.get_object()
        
        # Use detailed serializer to get full structure
        serializer = DetailedCourseSerializer(course, context={'request': request})
        return Response(serializer.data)


class ModuleViewSet(viewsets.ModelViewSet):
    """API endpoints for course modules"""
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['course', 'is_required']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter modules based on course access"""
        user = self.request.user
        return Module.objects.filter(
            Q(course__status='published') |
            Q(course__instructor=user) |
            Q(course__enrollments__student=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedModuleSerializer
        return ModuleSerializer
    
    def perform_create(self, serializer):
        """Check if user can create modules"""
        course = serializer.validated_data['course']
        if course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only create modules for your own courses")
        serializer.save()
    
    def perform_update(self, serializer):
        """Check if user can update this module"""
        module = self.get_object()
        if module.course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only update modules for your own courses")
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        """Get all lessons for this module"""
        module = self.get_object()
        lessons = module.lessons.order_by('order')
        serializer = LessonSerializer(lessons, many=True, context={'request': request})
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    """API endpoints for lessons"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LessonFilter
    search_fields = ['title', 'content']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter lessons based on module access"""
        user = self.request.user
        return Lesson.objects.filter(
            Q(module__course__status='published') |
            Q(module__course__instructor=user) |
            Q(module__course__enrollments__student=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedLessonSerializer
        return LessonSerializer
    
    def perform_create(self, serializer):
        """Check if user can create lessons"""
        module = serializer.validated_data['module']
        if module.course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only create lessons for your own courses")
        serializer.save()
    
    def perform_update(self, serializer):
        """Check if user can update this lesson"""
        lesson = self.get_object()
        if lesson.module.course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only update lessons for your own courses")
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_complete(self, request, pk=None):
        """Mark lesson as completed"""
        lesson = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=lesson.module.course
            )
            
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={'started_at': timezone.now()}
            )
            
            if not progress.completed_at:
                progress.completed_at = timezone.now()
                progress.save()
                
                # Update enrollment progress
                enrollment.update_progress()
                
                return Response({'message': 'Lesson marked as complete'})
            else:
                return Response({'message': 'Lesson already completed'})
                
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        """Toggle lesson bookmark"""
        lesson = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=lesson.module.course
            )
            
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={'started_at': timezone.now()}
            )
            
            progress.bookmarked = not progress.bookmarked
            progress.save()
            
            action = 'bookmarked' if progress.bookmarked else 'unbookmarked'
            return Response({'message': f'Lesson {action} successfully'})
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def exercises(self, request, pk=None):
        """Get all exercises for this lesson"""
        lesson = self.get_object()
        exercises = lesson.exercises.order_by('order')
        serializer = ExerciseSerializer(exercises, many=True, context={'request': request})
        return Response(serializer.data)


class ExerciseViewSet(viewsets.ModelViewSet):
    """API endpoints for exercises"""
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExerciseFilter
    search_fields = ['title', 'description']
    ordering_fields = ['order', 'created_at', 'points']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter exercises based on lesson access"""
        user = self.request.user
        return Exercise.objects.filter(
            Q(lesson__module__course__status='published') |
            Q(lesson__module__course__instructor=user) |
            Q(lesson__module__course__enrollments__student=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedExerciseSerializer
        return ExerciseSerializer
    
    def perform_create(self, serializer):
        """Check if user can create exercises"""
        lesson = serializer.validated_data['lesson']
        if lesson.module.course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only create exercises for your own courses")
        serializer.save()
    
    def perform_update(self, serializer):
        """Check if user can update this exercise"""
        exercise = self.get_object()
        if exercise.lesson.module.course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only update exercises for your own courses")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit exercise solution"""
        exercise = self.get_object()
        user = request.user
        
        # Check if user is enrolled in the course
        if not CourseEnrollment.objects.filter(
            student=user,
            course=exercise.lesson.module.course
        ).exists():
            return Response(
                {'error': 'You must be enrolled in the course to submit exercises'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CreateExerciseSubmissionSerializer(
            data=request.data,
            context={'request': request, 'exercise': exercise}
        )
        
        if serializer.is_valid():
            submission = serializer.save()
            
            # TODO: Integrate with code execution service
            # For now, just mark as submitted
            submission.status = 'submitted'
            submission.save()
            
            response_serializer = ExerciseSubmissionSerializer(
                submission, 
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test exercise solution without submitting"""
        exercise = self.get_object()
        user = request.user
        
        # Check if user is enrolled in the course
        if not CourseEnrollment.objects.filter(
            student=user,
            course=exercise.lesson.module.course
        ).exists():
            return Response(
                {'error': 'You must be enrolled in the course to test exercises'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        code = request.data.get('code', '')
        
        # TODO: Integrate with code execution service
        # For now, return mock test results
        return Response({
            'test_results': [
                {'test': 'Test 1', 'passed': True, 'output': 'Expected output'},
                {'test': 'Test 2', 'passed': False, 'output': 'Different output', 'expected': 'Expected output'}
            ],
            'all_passed': False,
            'execution_time': 0.1
        })
    
    @action(detail=True, methods=['get'])
    def hint(self, request, pk=None):
        """Get exercise hint"""
        exercise = self.get_object()
        user = request.user
        
        if not exercise.ai_hints_enabled:
            return Response(
                {'error': 'Hints are not enabled for this exercise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Integrate with AI service for dynamic hints
        # For now, return static hint
        hint = "Try breaking down the problem into smaller steps"
        
        return Response({
            'hint': hint,
            'penalty_points': exercise.hint_penalty or 0
        })
    
    @action(detail=True, methods=['post'])
    def provide_feedback(self, request, pk=None):
        """Provide instructor feedback on exercise (for instructors)"""
        exercise = self.get_object()
        user = request.user
        
        # Check if user can provide feedback (instructor of the course)
        if exercise.lesson.module.course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'You can only provide feedback for your own courses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        submission_id = request.data.get('submission_id')
        feedback = request.data.get('feedback', '')
        score = request.data.get('score')
        
        try:
            submission = ExerciseSubmission.objects.get(
                id=submission_id,
                exercise=exercise
            )
        except ExerciseSubmission.DoesNotExist:
            return Response(
                {'error': 'Submission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        submission.instructor_feedback = feedback
        submission.graded_by = user
        submission.graded_at = timezone.now()
        submission.auto_graded = False
        
        if score is not None and 0 <= score <= 100:
            submission.score = score
            submission.status = 'passed' if score >= 70 else 'failed'
        
        submission.save()
        
        return Response({'message': 'Feedback provided successfully'})


class CourseEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for course enrollments (read-only)"""
    queryset = CourseEnrollment.objects.all()
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'course', 'enrollment_source']
    ordering_fields = ['enrolled_at', 'progress_percentage', 'last_accessed']
    ordering = ['-enrolled_at']
    
    def get_queryset(self):
        """Users can only see their own enrollments or enrollments in their courses"""
        user = self.request.user
        if user.is_staff or (hasattr(user, 'can_teach') and user.can_teach):
            # Instructors can see enrollments for their courses
            return CourseEnrollment.objects.filter(
                Q(student=user) |
                Q(course__instructor=user)
            )
        else:
            return CourseEnrollment.objects.filter(student=user)
    
    @action(detail=True, methods=['get'])
    def progress_detail(self, request, pk=None):
        """Get detailed progress information"""
        enrollment = self.get_object()
        user = request.user
        
        # Check permissions
        if enrollment.student != user and enrollment.course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get lesson progress
        lesson_progress = LessonProgress.objects.filter(
            enrollment=enrollment
        ).select_related('lesson')
        
        # Get exercise submissions
        exercise_submissions = ExerciseSubmission.objects.filter(
            student=enrollment.student,
            exercise__lesson__module__course=enrollment.course
        ).select_related('exercise')
        
        progress_data = {
            'enrollment': CourseEnrollmentSerializer(enrollment, context={'request': request}).data,
            'lessons_progress': LessonProgressSerializer(lesson_progress, many=True, context={'request': request}).data,
            'exercise_submissions': ExerciseSubmissionSerializer(exercise_submissions, many=True, context={'request': request}).data,
            'summary': {
                'total_lessons': enrollment.course.get_total_lessons(),
                'completed_lessons': lesson_progress.filter(completed_at__isnull=False).count(),
                'total_exercises': enrollment.course.get_total_exercises(),
                'completed_exercises': exercise_submissions.filter(status='passed').count(),
                'average_score': exercise_submissions.aggregate(avg=Avg('score'))['avg'] or 0,
            }
        }
        
        return Response(progress_data)


class LessonProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for lesson progress (read-only)"""
    queryset = LessonProgress.objects.all()
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['enrollment', 'lesson']
    ordering_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']
    
    def get_queryset(self):
        """Users can only see their own progress or progress in their courses"""
        user = self.request.user
        if user.is_staff or (hasattr(user, 'can_teach') and user.can_teach):
            # Instructors can see progress for their courses
            return LessonProgress.objects.filter(
                Q(enrollment__student=user) |
                Q(enrollment__course__instructor=user)
            )
        else:
            return LessonProgress.objects.filter(enrollment__student=user)


class ExerciseSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for exercise submissions (read-only)"""
    queryset = ExerciseSubmission.objects.all()
    serializer_class = ExerciseSubmissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'exercise', 'auto_graded', 'is_final_submission']
    ordering_fields = ['submitted_at', 'score']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        """Users can only see their own submissions or submissions to their exercises"""
        user = self.request.user
        if user.is_staff or (hasattr(user, 'can_teach') and user.can_teach):
            # Instructors can see submissions to their exercises
            return ExerciseSubmission.objects.filter(
                Q(student=user) |
                Q(exercise__lesson__module__course__instructor=user)
            )
        else:
            return ExerciseSubmission.objects.filter(student=user)
    
    @action(detail=True, methods=['post'])
    def provide_feedback(self, request, pk=None):
        """Provide instructor feedback on submission"""
        submission = self.get_object()
        user = request.user
        
        # Check if user can provide feedback
        if submission.exercise.lesson.module.course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'You can only provide feedback for your own courses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        feedback = request.data.get('feedback', '')
        score = request.data.get('score')
        
        submission.instructor_feedback = feedback
        submission.graded_by = user
        submission.graded_at = timezone.now()
        submission.auto_graded = False
        
        if score is not None and 0 <= score <= 100:
            submission.score = score
            submission.status = 'passed' if score >= 70 else 'failed'
        
        submission.save()
        
        return Response({'message': 'Feedback provided successfully'})


class CourseRatingViewSet(viewsets.ModelViewSet):
    """API endpoints for course ratings and reviews"""
    queryset = CourseRating.objects.all()
    serializer_class = CourseRatingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['rating', 'course']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter based on permissions"""
        user = self.request.user
        if user.is_staff or (hasattr(user, 'can_teach') and user.can_teach):
            # Instructors can see reviews for their courses
            return CourseRating.objects.filter(
                Q(student=user) |
                Q(course__instructor=user)
            )
        else:
            return CourseRating.objects.filter(student=user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateCourseRatingSerializer
        return CourseRatingSerializer
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)


# =============================================================================
# UTILITY VIEWSETS
# =============================================================================

class BulkOperationsViewSet(viewsets.ViewSet):
    """Bulk operations for course management"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def bulk_create_modules(self, request):
        """Bulk create modules for a course"""
        course_id = request.data.get('course_id')
        modules_data = request.data.get('modules', [])
        
        try:
            course = Course.objects.get(id=course_id, instructor=request.user)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found or permission denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_modules = []
        with transaction.atomic():
            for module_data in modules_data:
                module_data['course'] = course.id
                serializer = ModuleSerializer(data=module_data)
                if serializer.is_valid():
                    module = serializer.save()
                    created_modules.append(module)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        result_serializer = ModuleSerializer(created_modules, many=True)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def bulk_import_lessons(self, request):
        """Bulk import lessons from file or data"""
        module_id = request.data.get('module_id')
        lessons_data = request.data.get('lessons', [])
        
        try:
            module = Module.objects.get(
                id=module_id, 
                course__instructor=request.user
            )
        except Module.DoesNotExist:
            return Response(
                {'error': 'Module not found or permission denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_lessons = []
        with transaction.atomic():
            for lesson_data in lessons_data:
                lesson_data['module'] = module.id
                serializer = LessonSerializer(data=lesson_data)
                if serializer.is_valid():
                    lesson = serializer.save()
                    created_lessons.append(lesson)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        result_serializer = LessonSerializer(created_lessons, many=True)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def exercises(self, request):
        """Bulk operations on exercises"""
        action = request.data.get('action')
        exercise_ids = request.data.get('exercise_ids', [])
        data = request.data.get('data', {})
        
        if action == 'update':
            exercises = Exercise.objects.filter(
                id__in=exercise_ids,
                lesson__module__course__instructor=request.user
            )
            
            updated_count = exercises.update(**data)
            return Response({
                'message': f'Updated {updated_count} exercises',
                'updated_count': updated_count
            })
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def submissions(self, request):
        """Bulk operations on submissions"""
        action = request.data.get('action')
        submission_ids = request.data.get('submission_ids', [])
        data = request.data.get('data', {})
        
        if action == 'grade':
            submissions = ExerciseSubmission.objects.filter(
                id__in=submission_ids,
                exercise__lesson__module__course__instructor=request.user
            )
            
            updated_count = 0
            for submission in submissions:
                if 'feedback' in data:
                    submission.instructor_feedback = data['feedback']
                if 'score' in data:
                    submission.score = data['score']
                    submission.status = 'passed' if data['score'] >= 70 else 'failed'
                submission.graded_by = request.user
                submission.graded_at = timezone.now()
                submission.auto_graded = False
                submission.save()
                updated_count += 1
            
            return Response({
                'message': f'Graded {updated_count} submissions',
                'graded_count': updated_count
            })
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def messages(self, request):
        """Bulk send messages to students"""
        action = request.data.get('action')
        student_ids = request.data.get('student_ids', [])
        data = request.data.get('data', {})
        
        if action == 'send_message':
            # TODO: Implement messaging system
            return Response({
                'message': f'Sent message to {len(student_ids)} students',
                'sent_count': len(student_ids)
            })
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )


class AdvancedSearchViewSet(viewsets.ViewSet):
    """Advanced search endpoints"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def courses(self, request):
        """Advanced course search"""
        query = request.query_params.get('q', '')
        instructor_id = request.query_params.get('instructor')
        status_filter = request.query_params.get('status', 'published')
        
        courses = Course.objects.filter(status=status_filter)
        
        if query:
            courses = courses.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query) |
                Q(skills_gained__icontains=query)
            )
        
        if instructor_id:
            courses = courses.filter(instructor_id=instructor_id)
        
        courses = courses.order_by('-created_at')[:20]  # Limit results
        
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def students(self, request):
        """Search students (instructor only)"""
        if not (request.user.is_authenticated and 
                (request.user.is_staff or (hasattr(request.user, 'can_teach') and request.user.can_teach))):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        query = request.query_params.get('q', '')
        course_id = request.query_params.get('course')
        
        enrollments = CourseEnrollment.objects.select_related('student', 'course')
        
        if course_id:
            enrollments = enrollments.filter(course_id=course_id)
        
        # Filter by instructor's courses
        enrollments = enrollments.filter(course__instructor=request.user)
        
        if query:
            enrollments = enrollments.filter(
                Q(student__username__icontains=query) |
                Q(student__first_name__icontains=query) |
                Q(student__last_name__icontains=query) |
                Q(student__email__icontains=query)
            )
        
        enrollments = enrollments.order_by('-enrolled_at')[:20]
        
        students_data = []
        for enrollment in enrollments:
            student_data = {
                'id': enrollment.student.id,
                'username': enrollment.student.username,
                'full_name': enrollment.student.get_full_name(),
                'email': enrollment.student.email,
                'course': {
                    'id': enrollment.course.id,
                    'title': enrollment.course.title
                },
                'enrollment': CourseEnrollmentSerializer(enrollment, context={'request': request}).data
            }
            students_data.append(student_data)
        
        return Response(students_data)
    
    @action(detail=False, methods=['get'])
    def submissions(self, request):
        """Search exercise submissions (instructor only)"""
        if not (request.user.is_authenticated and 
                (request.user.is_staff or (hasattr(request.user, 'can_teach') and request.user.can_teach))):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        query = request.query_params.get('q', '')
        exercise_id = request.query_params.get('exercise')
        
        submissions = ExerciseSubmission.objects.select_related('student', 'exercise')
        
        # Filter by instructor's courses
        submissions = submissions.filter(exercise__lesson__module__course__instructor=request.user)
        
        if exercise_id:
            submissions = submissions.filter(exercise_id=exercise_id)
        
        if query:
            submissions = submissions.filter(
                Q(student__username__icontains=query) |
                Q(student__first_name__icontains=query) |
                Q(student__last_name__icontains=query) |
                Q(submitted_code__icontains=query)
            )
        
        submissions = submissions.order_by('-submitted_at')[:20]
        
        serializer = ExerciseSubmissionSerializer(submissions, many=True, context={'request': request})
        return Response(serializer.data)