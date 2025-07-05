# courses/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum
from datetime import timedelta

from .models import (
    CourseCategory, Course, Module, Lesson, Exercise,
    CourseEnrollment, LessonProgress, ExerciseSubmission, CourseRating
)

User = get_user_model()


# User serializer for course context
class CourseUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar', 'bio', 'role']


# Category Serializers
class CourseCategorySerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color',
            'parent', 'order', 'is_active', 'course_count', 'children',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_course_count(self, obj):
        return obj.course_set.filter(status='published').count()
    
    def get_children(self, obj):
        # Only include children in tree view context
        if self.context.get('include_children', False):
            children = obj.coursecategory_set.filter(is_active=True)
            return CourseCategorySerializer(children, many=True, context=self.context).data
        return []


# Course Serializers
class CourseSerializer(serializers.ModelSerializer):
    instructor = CourseUserSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    co_instructors = CourseUserSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    can_enroll = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'category', 'instructor', 'co_instructors', 'difficulty_level', 'status',
            'thumbnail', 'preview_video', 'estimated_duration',
            'duration_formatted', 'total_lessons', 'total_exercises',
            'learning_objectives', 'skills_gained', 'tags',
            'programming_languages', 'is_free', 'price', 'premium_only',
            'average_rating', 'total_enrollments', 'total_reviews',
            'completion_rate', 'is_enrolled', 'user_progress', 'can_enroll',
            'created_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'slug', 'total_lessons', 'total_exercises',
            'average_rating', 'total_enrollments', 'total_reviews',
            'completion_rate', 'created_at', 'published_at'
        ]
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(student=request.user).exists()
        return False
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.enrollments.get(student=request.user)
                return {
                    'progress_percentage': enrollment.progress_percentage,
                    'lessons_completed': enrollment.lessons_completed,
                    'exercises_completed': enrollment.exercises_completed,
                    'last_accessed': enrollment.last_accessed
                }
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_duration_formatted(self, obj):
        if obj.estimated_duration:
            total_seconds = int(obj.estimated_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return "N/A"
    
    def get_can_enroll(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_enroll(request.user)
        return obj.is_free and obj.allow_enrollment


class DetailedCourseSerializer(CourseSerializer):
    """Extended course serializer with modules and prerequisites"""
    modules = serializers.SerializerMethodField()
    prerequisites = CourseSerializer(many=True, read_only=True)
    required_skills = serializers.ListField(child=serializers.CharField(), read_only=True)
    recent_enrollments = serializers.SerializerMethodField()
    
    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + [
            'modules', 'prerequisites', 'required_skills', 
            'allow_enrollment', 'max_students', 'certificate_enabled',
            'discussion_enabled', 'recent_enrollments'
        ]
    
    def get_modules(self, obj):
        modules = obj.modules.order_by('order')
        return ModuleSerializer(modules, many=True, context=self.context).data
    
    def get_recent_enrollments(self, obj):
        recent = obj.enrollments.order_by('-enrolled_at')[:5]
        return [{
            'student': enrollment.student.get_full_name() or enrollment.student.username,
            'enrolled_at': enrollment.enrolled_at
        } for enrollment in recent]


class CreateCourseSerializer(serializers.ModelSerializer):
    """Serializer for creating courses"""
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'short_description', 'category',
            'difficulty_level', 'thumbnail', 'preview_video',
            'estimated_duration', 'learning_objectives', 'skills_gained',
            'tags', 'programming_languages', 'is_free', 'price',
            'premium_only', 'allow_enrollment', 'max_students'
        ]
    
    def create(self, validated_data):
        validated_data['instructor'] = self.context['request'].user
        return super().create(validated_data)


# Module Serializers
class ModuleSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    is_accessible = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order', 'is_required',
            'estimated_duration', 'lessons_count', 'user_progress',
            'is_accessible', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.course.enrollments.get(student=request.user)
                total_lessons = obj.lessons.count()
                completed_lessons = LessonProgress.objects.filter(
                    enrollment=enrollment,
                    lesson__module=obj,
                    status='completed'
                ).count()
                
                if total_lessons > 0:
                    progress = (completed_lessons / total_lessons) * 100
                else:
                    progress = 0
                
                return {
                    'completed_lessons': completed_lessons,
                    'total_lessons': total_lessons,
                    'progress_percentage': round(progress, 2)
                }
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_is_accessible(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Instructors can access all modules
        if obj.course.instructor == user:
            return True
        
        # Check if user is enrolled
        if not obj.course.enrollments.filter(student=user).exists():
            return False
        
        # Check prerequisites
        if obj.prerequisites.exists():
            enrollment = obj.course.enrollments.get(student=user)
            completed_prerequisites = LessonProgress.objects.filter(
                enrollment=enrollment,
                lesson__module__in=obj.prerequisites.all(),
                status='completed'
            ).values('lesson__module').distinct().count()
            
            return completed_prerequisites == obj.prerequisites.count()
        
        return True


class DetailedModuleSerializer(ModuleSerializer):
    """Extended module serializer with lessons"""
    lessons = serializers.SerializerMethodField()
    prerequisites = ModuleSerializer(many=True, read_only=True)
    
    class Meta(ModuleSerializer.Meta):
        fields = ModuleSerializer.Meta.fields + ['lessons', 'prerequisites']
    
    def get_lessons(self, obj):
        lessons = obj.lessons.order_by('order')
        return LessonSerializer(lessons, many=True, context=self.context).data


# Lesson Serializers
class LessonSerializer(serializers.ModelSerializer):
    module = serializers.StringRelatedField(read_only=True)
    exercises_count = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    is_accessible = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'lesson_type', 'description',
            'module', 'video_url', 'video_duration', 'order',
            'estimated_duration', 'duration_formatted', 'is_preview',
            'is_required', 'exercises_count', 'user_progress',
            'is_accessible', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_exercises_count(self, obj):
        return obj.exercises.count()
    
    def get_duration_formatted(self, obj):
        if obj.estimated_duration:
            total_seconds = int(obj.estimated_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return "N/A"
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.module.course.enrollments.get(student=request.user)
                progress = LessonProgress.objects.filter(
                    enrollment=enrollment,
                    lesson=obj
                ).first()
                
                if progress:
                    return {
                        'status': progress.status,
                        'progress_percentage': progress.progress_percentage,
                        'time_spent': str(progress.time_spent),
                        'bookmarked': progress.bookmarked,
                        'last_accessed': progress.last_accessed
                    }
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_is_accessible(self, obj):
        request = self.context.get('request')
        if not request:
            return obj.is_preview
        
        user = request.user
        
        # Always accessible for instructors and preview lessons
        if obj.module.course.instructor == user or obj.is_preview:
            return True
        
        if not user.is_authenticated:
            return False
        
        # Check if user is enrolled
        if not obj.module.course.enrollments.filter(student=user).exists():
            return False
        
        # Check prerequisites
        if obj.prerequisites.exists():
            enrollment = obj.module.course.enrollments.get(student=user)
            completed_prerequisites = LessonProgress.objects.filter(
                enrollment=enrollment,
                lesson__in=obj.prerequisites.all(),
                status='completed'
            ).count()
            
            return completed_prerequisites == obj.prerequisites.count()
        
        return True


class DetailedLessonSerializer(LessonSerializer):
    """Extended lesson serializer with content and exercises"""
    content = serializers.CharField()  # Include full content for detailed view
    exercises = serializers.SerializerMethodField()
    next_lesson = serializers.SerializerMethodField()
    previous_lesson = serializers.SerializerMethodField()
    additional_resources = serializers.ListField(read_only=True)
    prerequisites = LessonSerializer(many=True, read_only=True)
    
    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + [
            'content', 'exercises', 'next_lesson', 'previous_lesson',
            'additional_resources', 'prerequisites', 'allow_discussion'
        ]
    
    def get_exercises(self, obj):
        exercises = obj.exercises.order_by('order')
        return ExerciseSerializer(exercises, many=True, context=self.context).data
    
    def get_next_lesson(self, obj):
        try:
            next_lesson = Lesson.objects.filter(
                module=obj.module,
                order__gt=obj.order
            ).order_by('order').first()
            
            if next_lesson:
                return {
                    'id': next_lesson.id,
                    'title': next_lesson.title,
                    'slug': next_lesson.slug
                }
        except Lesson.DoesNotExist:
            pass
        return None
    
    def get_previous_lesson(self, obj):
        try:
            prev_lesson = Lesson.objects.filter(
                module=obj.module,
                order__lt=obj.order
            ).order_by('-order').first()
            
            if prev_lesson:
                return {
                    'id': prev_lesson.id,
                    'title': prev_lesson.title,
                    'slug': prev_lesson.slug
                }
        except Lesson.DoesNotExist:
            pass
        return None


# Exercise Serializers
class ExerciseSerializer(serializers.ModelSerializer):
    lesson = serializers.StringRelatedField(read_only=True)
    user_submissions = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'exercise_type', 'difficulty', 'description',
            'lesson', 'programming_language', 'order', 'max_attempts',
            'time_limit', 'points', 'ai_hints_enabled', 'ai_explanation_enabled',
            'allow_collaboration', 'user_submissions', 'best_score',
            'is_completed', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_submissions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submissions = obj.submissions.filter(student=request.user).count()
            return submissions
        return 0
    
    def get_best_score(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            best = obj.submissions.filter(
                student=request.user
            ).aggregate(best_score=serializers.Max('score'))['best_score']
            return best
        return None
    
    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.submissions.filter(
                student=request.user,
                status='passed'
            ).exists()
        return False


class DetailedExerciseSerializer(ExerciseSerializer):
    """Extended exercise serializer with full exercise data"""
    starter_code = serializers.CharField(read_only=True)
    test_case_data = serializers.ListField(read_only=True)
    execution_config = serializers.DictField(read_only=True)
    recent_submissions = serializers.SerializerMethodField()
    
    class Meta(ExerciseSerializer.Meta):
        fields = ExerciseSerializer.Meta.fields + [
            'starter_code', 'test_case_data', 'execution_config',
            'hint_penalty', 'peer_review_enabled', 'recent_submissions'
        ]
    
    def get_recent_submissions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submissions = obj.submissions.filter(
                student=request.user
            ).order_by('-submitted_at')[:5]
            
            return [{
                'id': sub.id,
                'status': sub.status,
                'score': sub.score,
                'attempt_number': sub.attempt_number,
                'submitted_at': sub.submitted_at
            } for sub in submissions]
        return []


# Enrollment Serializers
class CourseEnrollmentSerializer(serializers.ModelSerializer):
    student = CourseUserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    duration_enrolled = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'student', 'course', 'status', 'enrollment_source',
            'progress_percentage', 'lessons_completed', 'exercises_completed',
            'total_study_time', 'enrolled_at', 'completed_at', 'last_accessed',
            'certificate_issued', 'certificate_issued_at', 'duration_enrolled'
        ]
        read_only_fields = ['id', 'enrolled_at', 'last_accessed']
    
    def get_duration_enrolled(self, obj):
        from django.utils import timezone
        if obj.completed_at:
            duration = obj.completed_at - obj.enrolled_at
        else:
            duration = timezone.now() - obj.enrolled_at
        return str(duration.days) + " days"


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'status', 'progress_percentage', 'time_spent',
            'notes', 'bookmarked', 'started_at', 'completed_at', 'last_accessed'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'last_accessed']


class ExerciseSubmissionSerializer(serializers.ModelSerializer):
    student = CourseUserSerializer(read_only=True)
    exercise = ExerciseSerializer(read_only=True)
    graded_by = CourseUserSerializer(read_only=True)
    
    class Meta:
        model = ExerciseSubmission
        fields = [
            'id', 'student', 'exercise', 'submitted_code', 'status',
            'score', 'max_score', 'execution_output', 'execution_error',
            'test_results', 'execution_time', 'hints_used', 'ai_help_used',
            'auto_graded', 'graded_by', 'instructor_feedback',
            'attempt_number', 'is_final_submission', 'submitted_at', 'graded_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'graded_at']


class CreateExerciseSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for creating exercise submissions"""
    
    class Meta:
        model = ExerciseSubmission
        fields = ['submitted_code', 'is_final_submission']
    
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        validated_data['exercise'] = self.context['exercise']
        
        # Calculate attempt number
        existing_attempts = ExerciseSubmission.objects.filter(
            student=validated_data['student'],
            exercise=validated_data['exercise']
        ).count()
        validated_data['attempt_number'] = existing_attempts + 1
        
        return super().create(validated_data)


# Rating Serializers
class CourseRatingSerializer(serializers.ModelSerializer):
    student = CourseUserSerializer(read_only=True)
    
    class Meta:
        model = CourseRating
        fields = [
            'id', 'student', 'rating', 'review', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'student', 'created_at', 'updated_at']


class CreateCourseRatingSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating course ratings"""
    
    class Meta:
        model = CourseRating
        fields = ['rating', 'review']
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value