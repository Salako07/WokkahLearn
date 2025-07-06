# courses/models.py
import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

User = get_user_model()


class CourseCategory(models.Model):
    """Categories for organizing courses"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class or emoji")
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    
    # Hierarchy support
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Settings
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Course Category')
        verbose_name_plural = _('Course Categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """Main course model"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        REVIEW = 'review', _('Under Review')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')
    
    class DifficultyLevel(models.TextChoices):
        BEGINNER = 'beginner', _('Beginner')
        INTERMEDIATE = 'intermediate', _('Intermediate')
        ADVANCED = 'advanced', _('Advanced')
        EXPERT = 'expert', _('Expert')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300)
    
    # Relationships
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL, null=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_teaching')
    co_instructors = models.ManyToManyField(User, blank=True, related_name='courses_co_teaching')
    
    # Course details
    difficulty_level = models.CharField(max_length=20, choices=DifficultyLevel.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    
    # Media
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True)
    preview_video = models.URLField(blank=True)
    
    # Course structure
    estimated_duration = models.DurationField(help_text="Total estimated course duration")
    learning_objectives = models.JSONField(default=list, help_text="List of learning objectives")
    skills_gained = models.JSONField(default=list, help_text="Skills students will gain")
    tags = models.JSONField(default=list, help_text="Course tags for search")
    
    # Prerequisites and requirements
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    required_skills = models.JSONField(default=list, help_text="Required skills/knowledge")
    programming_languages = models.JSONField(default=list, help_text="Programming languages used")
    
    # Pricing
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_only = models.BooleanField(default=False)
    
    # Settings
    allow_enrollment = models.BooleanField(default=True)
    max_students = models.PositiveIntegerField(null=True, blank=True)
    certificate_enabled = models.BooleanField(default=True)
    discussion_enabled = models.BooleanField(default=True)
    
    # Analytics
    total_enrollments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'difficulty_level']),
            models.Index(fields=['category', 'is_free']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED
    
    @property
    def total_lessons(self):
        return sum(module.lessons.count() for module in self.modules.all())
    
    @property
    def total_exercises(self):
        return sum(
            lesson.exercises.count() 
            for module in self.modules.all() 
            for lesson in module.lessons.all()
        )
    
    def can_enroll(self, user):
        """Check if user can enroll in this course"""
        if not self.allow_enrollment or not self.is_published:
            return False
        
        if self.premium_only and not user.is_premium:
            return False
        
        if self.max_students:
            if self.total_enrollments >= self.max_students:
                return False
        
        return True
    
    def get_absolute_url(self):
        return reverse('course-detail', kwargs={'slug': self.slug})
       


class Module(models.Model):
    """Course modules for organizing lessons"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Module settings
    is_required = models.BooleanField(default=True)
    estimated_duration = models.DurationField()
    
    # Prerequisites
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Module')
        verbose_name_plural = _('Modules')
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """Individual lessons within modules"""
    
    class LessonType(models.TextChoices):
        VIDEO = 'video', _('Video Lesson')
        TEXT = 'text', _('Text/Reading')
        INTERACTIVE = 'interactive', _('Interactive Content')
        QUIZ = 'quiz', _('Quiz')
        EXERCISE = 'exercise', _('Coding Exercise')
        PROJECT = 'project', _('Project')
        LIVE = 'live', _('Live Session')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices)
    description = models.TextField(blank=True)
    
    # Content
    content = models.TextField(blank=True, help_text="Main lesson content (markdown)")
    video_url = models.URLField(blank=True)
    video_duration = models.DurationField(null=True, blank=True)
    
    # Lesson structure
    order = models.PositiveIntegerField(default=0)
    estimated_duration = models.DurationField()
    
    # Settings
    is_preview = models.BooleanField(default=False, help_text="Available without enrollment")
    is_required = models.BooleanField(default=True)
    allow_discussion = models.BooleanField(default=True)
    
    # Prerequisites
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Resources
    additional_resources = models.JSONField(
        default=list,
        help_text="Additional resources like links, files, etc."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        ordering = ['module', 'order']
        unique_together = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Exercise(models.Model):
    """Coding exercises within lessons"""
    
    class ExerciseType(models.TextChoices):
        CODING = 'coding', _('Coding Exercise')
        MULTIPLE_CHOICE = 'multiple_choice', _('Multiple Choice')
        FILL_BLANK = 'fill_blank', _('Fill in the Blanks')
        PROJECT = 'project', _('Project')
        CHALLENGE = 'challenge', _('Challenge')
        QUIZ = 'quiz', _('Quiz')
    
    class Difficulty(models.TextChoices):
        EASY = 'easy', _('Easy')
        MEDIUM = 'medium', _('Medium')
        HARD = 'hard', _('Hard')
        EXPERT = 'expert', _('Expert')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=200)
    exercise_type = models.CharField(max_length=20, choices=ExerciseType.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    description = models.TextField()
    
    # Coding exercise specific
    programming_language = models.CharField(max_length=50, blank=True)
    starter_code = models.TextField(blank=True)
    solution_code = models.TextField(blank=True)
    execution_config = models.JSONField(
        default=dict,
        help_text="Environment configuration for code execution"
    )
    
    # Testing and validation
    test_case_data = models.JSONField(
        default=list,
        help_text="Test cases for automatic grading"
    )
    validation_code = models.TextField(
        blank=True,
        help_text="Custom validation code"
    )
    
    # Exercise settings
    order = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(null=True, blank=True)
    time_limit = models.DurationField(null=True, blank=True)
    points = models.PositiveIntegerField(default=10)
    
    # AI assistance
    ai_hints_enabled = models.BooleanField(default=True)
    ai_explanation_enabled = models.BooleanField(default=True)
    hint_penalty = models.PositiveIntegerField(default=0, help_text="Points deducted for hints")
    
    # Collaboration
    allow_collaboration = models.BooleanField(default=False)
    peer_review_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Exercise')
        verbose_name_plural = _('Exercises')
        ordering = ['lesson', 'order']
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class CourseEnrollment(models.Model):
    """Track student enrollments in courses"""
    
    class Status(models.TextChoices):
        ENROLLED = 'enrolled', _('Enrolled')
        COMPLETED = 'completed', _('Completed')
        DROPPED = 'dropped', _('Dropped')
        SUSPENDED = 'suspended', _('Suspended')
    
    class EnrollmentSource(models.TextChoices):
        DIRECT = 'direct', _('Direct Enrollment')
        INVITATION = 'invitation', _('Invitation')
        BULK = 'bulk', _('Bulk Enrollment')
        API = 'api', _('API')
        ADMIN = 'admin', _('Admin')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)
    enrollment_source = models.CharField(max_length=20, choices=EnrollmentSource.choices, default=EnrollmentSource.DIRECT)
    
    # Progress tracking
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    lessons_completed = models.PositiveIntegerField(default=0)
    exercises_completed = models.PositiveIntegerField(default=0)
    total_study_time = models.DurationField(default=timedelta(0))
    
    # Timestamps
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Course Enrollment')
        verbose_name_plural = _('Course Enrollments')
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    def update_progress(self):
        """Update progress based on completed lessons and exercises"""
        total_lessons = self.course.total_lessons
        total_exercises = self.course.total_exercises
        
        if total_lessons > 0:
            lesson_progress = (self.lessons_completed / total_lessons) * 60  # 60% weight
        else:
            lesson_progress = 0
        
        if total_exercises > 0:
            exercise_progress = (self.exercises_completed / total_exercises) * 40  # 40% weight
        else:
            exercise_progress = 0
        
        self.progress_percentage = min(100, lesson_progress + exercise_progress)
        self.save(update_fields=['progress_percentage'])


class LessonProgress(models.Model):
    """Track individual lesson progress"""
    
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', _('Not Started')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        SKIPPED = 'skipped', _('Skipped')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    
    # Progress tracking
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    time_spent = models.DurationField(default=timedelta(0))
    
    # Engagement
    notes = models.TextField(blank=True)
    bookmarked = models.BooleanField(default=False)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Lesson Progress')
        verbose_name_plural = _('Lesson Progress')
        unique_together = ['enrollment', 'lesson']
        ordering = ['lesson__order']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title}"


class ExerciseSubmission(models.Model):
    """Track exercise submissions and attempts"""
    
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', _('Submitted')
        PASSED = 'passed', _('Passed')
        FAILED = 'failed', _('Failed')
        PARTIAL = 'partial', _('Partially Correct')
        ERROR = 'error', _('Execution Error')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_submissions')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='submissions')
    
    # Submission data
    submitted_code = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    
    # Execution results
    execution_output = models.TextField(blank=True)
    execution_error = models.TextField(blank=True)
    test_results = models.JSONField(default=dict)
    execution_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    
    # AI assistance
    hints_used = models.PositiveIntegerField(default=0)
    ai_help_used = models.BooleanField(default=False)
    
    # Grading
    auto_graded = models.BooleanField(default=True, help_text="Whether submission was automatically graded")
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    instructor_feedback = models.TextField(blank=True)
    
    # Attempt tracking
    attempt_number = models.PositiveIntegerField(default=1)
    is_final_submission = models.BooleanField(default=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Exercise Submission')
        verbose_name_plural = _('Exercise Submissions')
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['student', 'exercise']),
            models.Index(fields=['exercise', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.exercise.title} (Attempt {self.attempt_number})"


class CourseRating(models.Model):
    """Course ratings and reviews"""
    
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Course Rating')
        verbose_name_plural = _('Course Ratings')
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.course.title} - {self.rating}/5 by {self.student.username}"