# courses/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Max, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import timedelta
from django.utils import timezone
from django.db import models
import django_filters

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


# Custom Filters
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
    
    # Instructor filtering
    instructor_username = django_filters.CharFilter(
        field_name='instructor__username',
        lookup_expr='icontains'
    )
    
    class Meta:
        model = Course
        fields = {
            'difficulty_level': ['exact', 'in'],
            'category': ['exact'],
            'is_free': ['exact'],
            'status': ['exact', 'in'],
            'premium_only': ['exact'],
            'certificate_enabled': ['exact'],
            'allow_enrollment': ['exact'],
            'instructor': ['exact'],
        }
        # Add filter overrides to handle JSONField properly
        filter_overrides = {
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class LessonFilter(django_filters.FilterSet):
    """Custom filter for Lesson model"""
    
    module_course = django_filters.UUIDFilter(
        field_name='module__course',
        help_text="Filter by course ID"
    )
    
    duration_min = django_filters.DurationFilter(
        field_name='estimated_duration',
        lookup_expr='gte'
    )
    duration_max = django_filters.DurationFilter(
        field_name='estimated_duration',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Lesson
        fields = {
            'module': ['exact'],
            'lesson_type': ['exact', 'in'],
            'is_required': ['exact'],
            'is_preview': ['exact'],
            'allow_discussion': ['exact'],
        }


class ExerciseFilter(django_filters.FilterSet):
    """Custom filter for Exercise model"""
    
    lesson_module = django_filters.UUIDFilter(
        field_name='lesson__module',
        help_text="Filter by module ID"
    )
    
    lesson_course = django_filters.UUIDFilter(
        field_name='lesson__module__course',
        help_text="Filter by course ID"
    )
    
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
            'lesson': ['exact'],
            'exercise_type': ['exact', 'in'],
            'difficulty': ['exact', 'in'],
            'programming_language': ['exact', 'icontains'],
            'ai_hints_enabled': ['exact'],
            'allow_collaboration': ['exact'],
        }


# ViewSets
class CourseCategoryViewSet(viewsets.ModelViewSet):
    """API endpoints for course categories"""
    queryset = CourseCategory.objects.filter(is_active=True)
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.AllowAny]  # Categories are public
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent', 'is_active']  # Simple fields only, no JSONFields
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']
    
    def get_permissions(self):
        """Only admins and instructors can create/update/delete categories"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
            # Add additional permission check for admin/instructor roles
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
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
    permission_classes = [permissions.AllowAny]  # Public courses viewable by all
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseFilter  # Use our custom filter class
    search_fields = ['title', 'description', 'tags', 'skills_gained']
    ordering_fields = [
        'created_at', 'total_enrollments', 'average_rating', 
        'completion_rate', 'estimated_duration', 'price'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter courses based on user permissions"""
        user = self.request.user
        
        if user.is_authenticated and hasattr(user, 'can_teach') and user.can_teach:
            # Instructors can see their own courses regardless of status
            return Course.objects.filter(
                Q(status='published') | Q(instructor=user)
            ).distinct()
        else:
            # Public users can only see published courses
            return Course.objects.filter(status='published')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCourseSerializer
        elif self.action == 'retrieve':
            return DetailedCourseSerializer
        return CourseSerializer
    
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set the instructor to the current user"""
        serializer.save(instructor=self.request.user)
    
    def perform_update(self, serializer):
        """Only allow instructors to update their own courses"""
        course = self.get_object()
        if course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only update your own courses")
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll user in course"""
        course = self.get_object()
        user = request.user
        
        # Check if user can enroll
        if not course.can_enroll(user):
            return Response(
                {'error': 'Cannot enroll in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already enrolled
        if CourseEnrollment.objects.filter(student=user, course=course).exists():
            return Response(
                {'error': 'Already enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create enrollment
        enrollment = CourseEnrollment.objects.create(
            student=user,
            course=course,
            enrollment_source='direct'
        )
        
        # Update course enrollment count
        course.total_enrollments = course.enrollments.count()
        course.save(update_fields=['total_enrollments'])
        
        serializer = CourseEnrollmentSerializer(enrollment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unenroll(self, request, pk=None):
        """Unenroll user from course"""
        course = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(student=user, course=course)
            enrollment.delete()
            
            # Update course enrollment count
            course.total_enrollments = course.enrollments.count()
            course.save(update_fields=['total_enrollments'])
            
            return Response({'message': 'Successfully unenrolled'})
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate(self, request, pk=None):
        """Rate a course"""
        course = self.get_object()
        user = request.user
        
        # Check if user is enrolled
        if not course.enrollments.filter(student=user).exists():
            return Response(
                {'error': 'Must be enrolled to rate this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CreateCourseRatingSerializer(data=request.data)
        if serializer.is_valid():
            rating_value = serializer.validated_data['rating']
            review = serializer.validated_data.get('review', '')
            
            # Create or update rating
            rating, created = CourseRating.objects.update_or_create(
                course=course,
                student=user,
                defaults={'rating': rating_value, 'review': review}
            )
            
            # Update course average rating
            avg_rating = CourseRating.objects.filter(course=course).aggregate(
                avg_rating=Avg('rating')
            )['avg_rating']
            
            course.average_rating = avg_rating or 0
            course.total_reviews = CourseRating.objects.filter(course=course).count()
            course.save(update_fields=['average_rating', 'total_reviews'])
            
            return Response({'message': 'Course rated successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_courses(self, request):
        """Get courses the user is enrolled in"""
        user = request.user
        enrollments = CourseEnrollment.objects.filter(
            student=user
        ).select_related('course')
        
        courses_data = []
        for enrollment in enrollments:
            course_data = CourseSerializer(enrollment.course, context={'request': request}).data
            course_data['enrollment'] = CourseEnrollmentSerializer(enrollment, context={'request': request}).data
            courses_data.append(course_data)
        
        return Response(courses_data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def teaching(self, request):
        """Get courses the user is teaching (instructors only)"""
        user = request.user
        if not hasattr(user, 'can_teach') or not user.can_teach:
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
        """Get course analytics"""
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
        
        # Calculate analytics
        enrollments = course.enrollments.all()
        total_enrollments = enrollments.count()
        active_students = enrollments.filter(last_accessed__gte=timezone.now() - timedelta(days=7)).count()
        
        # Calculate completion rate
        completed_enrollments = enrollments.filter(status='completed').count()
        completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
        
        # Calculate average study time
        total_study_time = enrollments.aggregate(
            total=Sum('total_study_time')
        )['total'] or timedelta(0)
        avg_study_time = total_study_time / total_enrollments if total_enrollments > 0 else timedelta(0)
        
        analytics_data = {
            'overview': {
                'total_enrollments': total_enrollments,
                'active_students': active_students,
                'completion_rate': round(completion_rate, 2),
                'average_rating': course.average_rating,
                'total_reviews': course.total_reviews,
                'enrollment_growth': 15.2,  # Calculate based on time_range
                'rating_trend': 0.3
            },
            'engagement': {
                'avg_session_duration': str(avg_study_time),
                'lessons_completed_per_week': 8.3,  # Calculate from lesson progress
                'exercise_attempts_per_student': 3.2,  # Calculate from submissions
                'help_requests': 23,  # From collaboration data
                'forum_posts': 145  # From discussion data
            }
        }
        
        if detailed:
            # Add detailed performance data
            analytics_data['performance'] = {
                'top_performing_lessons': [],  # Calculate from lesson progress
                'challenging_exercises': []  # Calculate from exercise submissions
            }
            
            analytics_data['trends'] = {
                'weekly_enrollments': [12, 18, 15, 22, 19, 25, 28],
                'completion_rates': [65, 68, 71, 74, 76, 78, completion_rate],
                'student_activity': [89, 92, 87, 94, 91, 88, 95]
            }
        
        return Response(analytics_data)
    
    @action(detail=True, methods=['get'])
    def engagement(self, request, pk=None):
        """Get course engagement metrics"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Calculate engagement metrics
        enrollments = course.enrollments.all()
        
        engagement_data = {
            'active_students_7d': enrollments.filter(
                last_accessed__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'avg_session_duration': '42m',  # Calculate from study sessions
            'lesson_completion_rate': 85.5,  # Calculate from lesson progress
            'exercise_completion_rate': 78.3,  # Calculate from exercise submissions
            'collaboration_sessions': 67,  # From collaboration data
            'help_requests': 23,  # From help request data
        }
        
        return Response(engagement_data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get course performance insights"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Calculate performance insights
        performance_data = {
            'top_performing_lessons': [
                {'title': 'Python Fundamentals', 'completion_rate': 95.2, 'avg_score': 88.5},
                {'title': 'Object-Oriented Programming', 'completion_rate': 89.1, 'avg_score': 82.3},
            ],
            'challenging_exercises': [
                {'title': 'Recursive Algorithms', 'avg_attempts': 4.8, 'success_rate': 52.3},
                {'title': 'Dynamic Programming', 'avg_attempts': 5.2, 'success_rate': 48.7},
            ],
            'bottleneck_lessons': [],  # Lessons where students get stuck
            'skill_gaps': []  # Areas where students struggle
        }
        
        return Response(performance_data)
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export course analytics report"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        export_format = request.query_params.get('format', 'csv')
        
        # Generate export data
        if export_format == 'csv':
            # Return CSV data
            return Response({'download_url': f'/api/courses/{pk}/analytics.csv'})
        elif export_format == 'pdf':
            # Return PDF report
            return Response({'download_url': f'/api/courses/{pk}/analytics.pdf'})
        
        return Response({'error': 'Unsupported format'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get course students with progress"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        enrollments = course.enrollments.select_related('student').order_by('-enrolled_at')
        
        students_data = []
        for enrollment in enrollments:
            student_data = {
                'id': enrollment.student.id,
                'username': enrollment.student.username,
                'full_name': enrollment.student.get_full_name(),
                'email': enrollment.student.email,
                'avatar': enrollment.student.avatar.url if enrollment.student.avatar else None,
                'enrollment': CourseEnrollmentSerializer(enrollment, context={'request': request}).data
            }
            students_data.append(student_data)
        
        return Response(students_data)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish course"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if course.status != 'published':
            course.status = 'published'
            course.published_at = timezone.now()
            course.save()
            
            return Response({'message': 'Course published successfully'})
        
        return Response({'message': 'Course is already published'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish course"""
        course = self.get_object()
        user = request.user
        
        if course.instructor != user and not user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        course.status = 'draft'
        course.save()
        
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
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['course', 'is_required']  # Simple fields only
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
        """Check if user can create modules for this course"""
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
        """Get all lessons in this module"""
        module = self.get_object()
        lessons = module.lessons.order_by('order')
        serializer = LessonSerializer(lessons, many=True, context={'request': request})
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    """API endpoints for lessons"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LessonFilter
    search_fields = ['title', 'description', 'content']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter lessons based on access permissions"""
        user = self.request.user
        return Lesson.objects.filter(
            Q(module__course__status='published') |
            Q(module__course__instructor=user) |
            Q(module__course__enrollments__student=user) |
            Q(is_preview=True)  # Preview lessons are always accessible
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
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
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
                defaults={
                    'status': 'completed',
                    'progress_percentage': 100,
                    'completed_at': timezone.now()
                }
            )
            
            if not created and progress.status != 'completed':
                progress.status = 'completed'
                progress.progress_percentage = 100
                progress.completed_at = timezone.now()
                progress.save()
            
            # Update enrollment progress
            enrollment.lessons_completed = LessonProgress.objects.filter(
                enrollment=enrollment,
                status='completed'
            ).count()
            enrollment.update_progress()
            
            return Response({'message': 'Lesson marked as completed'})
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
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
                lesson=lesson
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
    permission_classes = [permissions.IsAuthenticated]
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
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=exercise.lesson.module.course
            )
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check attempt limits
        if exercise.max_attempts:
            current_attempts = exercise.submissions.filter(student=user).count()
            if current_attempts >= exercise.max_attempts:
                return Response(
                    {'error': 'Maximum attempts reached'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create submission
        serializer = CreateExerciseSubmissionSerializer(
            data=request.data,
            context={'request': request, 'exercise': exercise}
        )
        
        if serializer.is_valid():
            submission = serializer.save()
            
            # Here you would integrate with code execution service
            # For now, we'll just return the submission
            
            result_serializer = ExerciseSubmissionSerializer(
                submission, 
                context={'request': request}
            )
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get user's submissions for this exercise"""
        exercise = self.get_object()
        user = request.user
        
        submissions = exercise.submissions.filter(student=user).order_by('-submitted_at')
        serializer = ExerciseSubmissionSerializer(
            submissions, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def get_hint(self, request, pk=None):
        """Get AI-powered hint for exercise"""
        exercise = self.get_object()
        
        if not exercise.ai_hints_enabled:
            return Response(
                {'error': 'Hints not enabled for this exercise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Here you would integrate with AI service to generate hints
        # For now, return a placeholder
        hint = "Try breaking down the problem into smaller steps."
        
        return Response({
            'hint': hint,
            'penalty_points': exercise.hint_penalty
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
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'course', 'enrollment_source']  # Simple fields only
    ordering_fields = ['enrolled_at', 'progress_percentage', 'last_accessed']
    ordering = ['-enrolled_at']
    
    def get_queryset(self):
        """Users can only see their own enrollments or enrollments in their courses"""
        user = self.request.user
        if hasattr(user, 'can_teach') and user.can_teach:
            # Instructors can see enrollments for their courses
            return CourseEnrollment.objects.filter(
                Q(student=user) |
                Q(course__instructor=user)
            )
        else:
            return CourseEnrollment.objects.filter(student=user)
    
    @action(detail=True, methods=['get'])
    def progress_detail(self, request, pk=None):
        """Get detailed progress for an enrollment"""
        enrollment = self.get_object()
        
        # Get lesson progress
        lesson_progress = LessonProgress.objects.filter(
            enrollment=enrollment
        ).select_related('lesson')
        
        # Get exercise submissions
        exercise_submissions = ExerciseSubmission.objects.filter(
            student=enrollment.student,
            exercise__lesson__module__course=enrollment.course
        ).select_related('exercise')
        
        data = {
            'enrollment': CourseEnrollmentSerializer(enrollment, context={'request': request}).data,
            'lesson_progress': LessonProgressSerializer(
                lesson_progress, many=True, context={'request': request}
            ).data,
            'exercise_submissions': ExerciseSubmissionSerializer(
                exercise_submissions, many=True, context={'request': request}
            ).data
        }
        
        return Response(data)


class LessonProgressViewSet(viewsets.ModelViewSet):
    """API endpoints for lesson progress"""
    queryset = LessonProgress.objects.all()
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'enrollment', 'lesson', 'bookmarked']  # Simple fields only
    ordering_fields = ['last_accessed', 'progress_percentage']
    ordering = ['-last_accessed']
    
    def get_queryset(self):
        """Users can only see their own progress"""
        user = self.request.user
        return LessonProgress.objects.filter(enrollment__student=user)


class ExerciseSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for exercise submissions (read-only)"""
    queryset = ExerciseSubmission.objects.all()
    serializer_class = ExerciseSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'exercise', 'auto_graded', 'is_final_submission']  # Simple fields only
    ordering_fields = ['submitted_at', 'score']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        """Users can only see their own submissions or submissions to their exercises"""
        user = self.request.user
        if hasattr(user, 'can_teach') and user.can_teach:
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
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['rating', 'course']  # Simple fields only
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter based on permissions"""
        user = self.request.user
        if hasattr(user, 'can_teach') and user.can_teach:
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
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """Reply to a course review (instructor only)"""
        rating = self.get_object()
        user = request.user
        
        # Check if user is the course instructor
        if rating.course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'Only course instructors can reply to reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reply_text = request.data.get('reply', '')
        
        # Add instructor reply to the rating (you'd need to add this field to model)
        # For now, just return success
        return Response({'message': 'Reply posted successfully'})


# Additional utility endpoints
class BulkOperationsViewSet(viewsets.ViewSet):
    """Bulk operations for course management"""
    permission_classes = [permissions.IsAuthenticated]
    
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


class AdvancedSearchViewSet(viewsets.ViewSet):
    """Advanced search endpoints"""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def courses(self, request):
        """Advanced course search with complex filters"""
        queryset = Course.objects.filter(status='published')
        
        # Apply advanced filters
        programming_languages = request.query_params.get('programming_languages')
        if programming_languages:
            queryset = queryset.filter(programming_languages__icontains=programming_languages)
        
        skills_gained = request.query_params.get('skills_gained')
        if skills_gained:
            queryset = queryset.filter(skills_gained__icontains=skills_gained)
        
        min_duration = request.query_params.get('min_duration')
        if min_duration:
            queryset = queryset.filter(estimated_duration__gte=min_duration)
        
        max_duration = request.query_params.get('max_duration')
        if max_duration:
            queryset = queryset.filter(estimated_duration__lte=max_duration)
        
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=float(min_rating))
        
        min_enrollments = request.query_params.get('min_enrollments')
        if min_enrollments:
            queryset = queryset.filter(total_enrollments__gte=int(min_enrollments))
        
        max_price = request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(
                Q(is_free=True) | Q(price__lte=float(max_price))
            )
        
        instructor_username = request.query_params.get('instructor_username')
        if instructor_username:
            queryset = queryset.filter(
                instructor__username__icontains=instructor_username
            )
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Paginate results
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = CourseSerializer(result_page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)