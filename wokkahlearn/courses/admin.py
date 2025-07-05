# courses/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    CourseCategory, Course, Module, Lesson, Exercise, 
    CourseEnrollment, LessonProgress, ExerciseSubmission, CourseRating
)


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order', 'is_active', 'course_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    
    def course_count(self, obj):
        return obj.course_set.count()
    course_count.short_description = 'Courses'


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ('title', 'order', 'is_required', 'estimated_duration')
    ordering = ['order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'instructor', 'category', 'difficulty_level', 
        'status', 'total_enrollments', 'average_rating', 'is_free'
    )
    list_filter = (
        'status', 'difficulty_level', 'category', 'is_free', 
        'premium_only', 'certificate_enabled', 'allow_enrollment'
    )
    search_fields = ('title', 'description', 'instructor__username', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('co_instructors', 'prerequisites')
    inlines = [ModuleInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'category')
        }),
        ('Instructors & Status', {
            'fields': ('instructor', 'co_instructors', 'difficulty_level', 'status')
        }),
        ('Media', {
            'fields': ('thumbnail', 'preview_video')
        }),
        ('Course Structure', {
            'fields': ('estimated_duration', 'learning_objectives', 'skills_gained', 'tags')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites', 'required_skills', 'programming_languages')
        }),
        ('Pricing', {
            'fields': ('is_free', 'price', 'premium_only')
        }),
        ('Settings', {
            'fields': (
                'allow_enrollment', 'max_students', 'certificate_enabled', 
                'discussion_enabled'
            )
        }),
        ('Analytics', {
            'fields': (
                'total_enrollments', 'average_rating', 'total_reviews', 
                'completion_rate'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'total_enrollments', 'average_rating', 'total_reviews', 
        'completion_rate', 'created_at', 'updated_at', 'published_at'
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'published':
            readonly.append('instructor')  # Can't change instructor after publishing
        return readonly


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('title', 'lesson_type', 'order', 'is_required', 'estimated_duration', 'is_preview')
    ordering = ['order']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_required', 'lesson_count', 'estimated_duration')
    list_filter = ('is_required', 'course__category', 'course__difficulty_level')
    search_fields = ('title', 'description', 'course__title')
    inlines = [LessonInline]
    ordering = ['course', 'order']
    
    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = 'Lessons'


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 0
    fields = ('title', 'exercise_type', 'difficulty', 'order', 'points', 'programming_language')
    ordering = ['order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'module', 'lesson_type', 'order', 'is_required', 
        'estimated_duration', 'is_preview', 'exercise_count'
    )
    list_filter = (
        'lesson_type', 'is_required', 'is_preview', 'allow_discussion',
        'module__course__category'
    )
    search_fields = ('title', 'description', 'module__title', 'module__course__title')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ExerciseInline]
    ordering = ['module__course', 'module__order', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'module', 'lesson_type', 'description')
        }),
        ('Content', {
            'fields': ('content', 'video_url', 'video_duration', 'additional_resources')
        }),
        ('Structure', {
            'fields': ('order', 'estimated_duration', 'prerequisites')
        }),
        ('Settings', {
            'fields': ('is_preview', 'is_required', 'allow_discussion')
        }),
    )
    
    filter_horizontal = ('prerequisites',)
    
    def exercise_count(self, obj):
        return obj.exercises.count()
    exercise_count.short_description = 'Exercises'


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'lesson', 'exercise_type', 'difficulty', 
        'programming_language', 'points', 'submission_count'
    )
    list_filter = (
        'exercise_type', 'difficulty', 'programming_language',
        'ai_hints_enabled', 'allow_collaboration', 'lesson__module__course__category'
    )
    search_fields = ('title', 'description', 'lesson__title')
    ordering = ['lesson__module__course', 'lesson__module__order', 'lesson__order', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'lesson', 'exercise_type', 'difficulty', 'description')
        }),
        ('Code Exercise', {
            'fields': (
                'programming_language', 'starter_code', 'solution_code', 
                'execution_config'
            ),
            'classes': ('collapse',)
        }),
        ('Testing & Validation', {
            'fields': ('test_case_data', 'validation_code'),
            'classes': ('collapse',)
        }),
        ('Exercise Settings', {
            'fields': ('order', 'max_attempts', 'time_limit', 'points')
        }),
        ('AI Features', {
            'fields': ('ai_hints_enabled', 'ai_explanation_enabled', 'hint_penalty')
        }),
        ('Collaboration', {
            'fields': ('allow_collaboration', 'peer_review_enabled')
        }),
    )
    
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = 'Submissions'


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'course', 'status', 'progress_percentage', 
        'lessons_completed', 'enrolled_at', 'certificate_issued'
    )
    list_filter = (
        'status', 'enrollment_source', 'certificate_issued', 
        'course__category', 'course__difficulty_level'
    )
    search_fields = ('student__username', 'student__email', 'course__title')
    date_hierarchy = 'enrolled_at'
    ordering = ['-enrolled_at']
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course', 'status', 'enrollment_source')
        }),
        ('Progress', {
            'fields': (
                'progress_percentage', 'lessons_completed', 'exercises_completed',
                'total_study_time'
            )
        }),
        ('Timestamps', {
            'fields': ('enrolled_at', 'completed_at', 'last_accessed')
        }),
        ('Certificate', {
            'fields': ('certificate_issued', 'certificate_issued_at')
        }),
    )
    
    readonly_fields = ('enrolled_at', 'last_accessed')
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing enrollment
            readonly.extend(['student', 'course'])
        return readonly


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        'student_name', 'lesson', 'status', 'progress_percentage', 
        'time_spent', 'bookmarked', 'last_accessed'
    )
    list_filter = (
        'status', 'bookmarked', 'lesson__lesson_type', 
        'enrollment__course__category'
    )
    search_fields = (
        'enrollment__student__username', 'lesson__title', 
        'enrollment__course__title'
    )
    date_hierarchy = 'last_accessed'
    ordering = ['-last_accessed']
    
    def student_name(self, obj):
        return obj.enrollment.student.get_full_name() or obj.enrollment.student.username
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'enrollment__student__username'
    
    fieldsets = (
        ('Progress Information', {
            'fields': ('enrollment', 'lesson', 'status', 'progress_percentage')
        }),
        ('Engagement', {
            'fields': ('time_spent', 'notes', 'bookmarked')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'last_accessed')
        }),
    )
    
    readonly_fields = ('started_at', 'completed_at', 'last_accessed')


@admin.register(ExerciseSubmission)
class ExerciseSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'exercise', 'status', 'score', 'max_score',
        'attempt_number', 'auto_graded', 'submitted_at'
    )
    list_filter = (
        'status', 'auto_graded', 'exercise__programming_language',
        'exercise__difficulty', 'is_final_submission'
    )
    search_fields = (
        'student__username', 'exercise__title', 
        'exercise__lesson__title'
    )
    date_hierarchy = 'submitted_at'
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('student', 'exercise', 'submitted_code')
        }),
        ('Grading', {
            'fields': (
                'status', 'score', 'max_score', 'auto_graded', 
                'graded_by', 'instructor_feedback'
            )
        }),
        ('Execution Results', {
            'fields': (
                'execution_output', 'execution_error', 'test_results', 
                'execution_time'
            ),
            'classes': ('collapse',)
        }),
        ('AI Assistance', {
            'fields': ('hints_used', 'ai_help_used')
        }),
        ('Attempt Information', {
            'fields': ('attempt_number', 'is_final_submission')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'graded_at')
        }),
    )
    
    readonly_fields = ('submitted_at', 'graded_at')
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing submission
            readonly.extend(['student', 'exercise', 'submitted_code', 'attempt_number'])
        return readonly
    
    def save_model(self, request, obj, form, change):
        if change and not obj.auto_graded and not obj.graded_by:
            obj.graded_by = request.user
            obj.graded_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(CourseRating)
class CourseRatingAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'rating', 'created_at', 'has_review')
    list_filter = ('rating', 'course__category', 'course__difficulty_level')
    search_fields = ('course__title', 'student__username', 'review')
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def has_review(self, obj):
        return bool(obj.review)
    has_review.boolean = True
    has_review.short_description = 'Has Review'
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('student', 'course', 'rating')
        }),
        ('Review', {
            'fields': ('review',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


# Custom admin site configuration
admin.site.site_header = "WokkahLearn Administration"
admin.site.site_title = "WokkahLearn Admin"
admin.site.index_title = "Welcome to WokkahLearn Administration"