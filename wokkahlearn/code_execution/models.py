# code_execution/models.py - Complete Implementation

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json
from datetime import timedelta

User = get_user_model()


class ExecutionEnvironment(models.Model):
    """Execution environments for different programming languages"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        MAINTENANCE = 'maintenance', _('Maintenance')
        DEPRECATED = 'deprecated', _('Deprecated')
        DISABLED = 'disabled', _('Disabled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    language = models.CharField(max_length=50)
    version = models.CharField(max_length=20)
    docker_image = models.CharField(max_length=200)
    
    # Environment configuration
    default_timeout = models.PositiveIntegerField(default=30)  # seconds
    max_memory = models.PositiveIntegerField(default=128)  # MB
    max_cpu_time = models.PositiveIntegerField(default=10)  # seconds
    max_file_size = models.PositiveIntegerField(default=10)  # MB
    max_output_size = models.PositiveIntegerField(default=1)  # MB
    
    # Supported features
    supports_input = models.BooleanField(default=True)
    supports_graphics = models.BooleanField(default=False)
    supports_networking = models.BooleanField(default=False)
    supports_file_operations = models.BooleanField(default=True)
    supports_packages = models.BooleanField(default=True)
    
    # Language-specific settings
    compiler_command = models.CharField(max_length=200, blank=True)
    interpreter_command = models.CharField(max_length=200, blank=True)
    file_extension = models.CharField(max_length=10)
    entry_point = models.CharField(max_length=100, default='main')
    
    # Pre-installed packages
    installed_packages = models.JSONField(default=list)
    available_libraries = models.JSONField(default=list)
    
    # Security settings
    allowed_imports = models.JSONField(default=list)
    blocked_imports = models.JSONField(default=list)
    blocked_functions = models.JSONField(default=list)
    sandbox_level = models.CharField(max_length=20, default='strict')
    
    # Performance and resource limits
    concurrent_executions_limit = models.PositiveIntegerField(default=5)
    daily_execution_limit = models.PositiveIntegerField(default=100)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_default = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Execution Environment')
        verbose_name_plural = _('Execution Environments')
        ordering = ['priority', 'language', 'version']
        unique_together = ['language', 'version']
    
    def __str__(self):
        return f"{self.language} {self.version}"


class CodeExecution(models.Model):
    """Individual code execution instances"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        QUEUED = 'queued', _('Queued')
        RUNNING = 'running', _('Running')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        TIMEOUT = 'timeout', _('Timeout')
        CANCELLED = 'cancelled', _('Cancelled')
        ERROR = 'error', _('Error')
    
    class ExecutionType(models.TextChoices):
        EXERCISE = 'exercise', _('Exercise Submission')
        PLAYGROUND = 'playground', _('Playground Testing')
        ASSESSMENT = 'assessment', _('Assessment')
        COLLABORATION = 'collaboration', _('Collaborative Session')
        DEBUG = 'debug', _('Debug Session')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_executions')
    environment = models.ForeignKey(ExecutionEnvironment, on_delete=models.CASCADE)
    
    # Execution context
    execution_type = models.CharField(max_length=20, choices=ExecutionType.choices)
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)  # For collaboration/playground
    
    # Code and input
    source_code = models.TextField()
    stdin_input = models.TextField(blank=True)
    command_line_args = models.JSONField(default=list)
    environment_vars = models.JSONField(default=dict)
    
    # Execution results
    stdout_output = models.TextField(blank=True)
    stderr_output = models.TextField(blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    
    # Performance metrics
    execution_time = models.FloatField(null=True, blank=True)  # seconds
    memory_used = models.BigIntegerField(null=True, blank=True)  # bytes
    cpu_time = models.FloatField(null=True, blank=True)  # seconds
    
    # Execution metadata
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    container_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Quality metrics
    is_successful = models.BooleanField(null=True, blank=True)
    quality_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Code Execution')
        verbose_name_plural = _('Code Executions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['exercise', 'user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['execution_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.environment.language} ({self.status})"
    
    @property
    def duration(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class TestCase(models.Model):
    """Test cases for code exercises"""
    
    class TestType(models.TextChoices):
        UNIT = 'unit', _('Unit Test')
        INTEGRATION = 'integration', _('Integration Test')
        PERFORMANCE = 'performance', _('Performance Test')
        EDGE_CASE = 'edge_case', _('Edge Case Test')
        STRESS = 'stress', _('Stress Test')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, related_name='test_cases')
    
    # Test configuration
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    test_type = models.CharField(max_length=20, choices=TestType.choices, default=TestType.UNIT)
    
    # Test data
    input_data = models.TextField(blank=True)
    expected_output = models.TextField()
    expected_error = models.TextField(blank=True)
    expected_exit_code = models.IntegerField(default=0)
    
    # Test constraints
    timeout_seconds = models.PositiveIntegerField(default=30)
    max_memory_mb = models.PositiveIntegerField(default=128)
    
    # Test metadata
    is_public = models.BooleanField(default=True)  # Visible to students
    is_sample = models.BooleanField(default=False)  # Sample test case
    weight = models.FloatField(default=1.0)  # Weight in grading
    points = models.PositiveIntegerField(default=1)
    
    # Test execution settings
    strict_output_matching = models.BooleanField(default=True)
    ignore_whitespace = models.BooleanField(default=False)
    ignore_case = models.BooleanField(default=False)
    custom_checker = models.TextField(blank=True)  # Custom comparison logic
    
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Test Case')
        verbose_name_plural = _('Test Cases')
        ordering = ['exercise', 'order']
        unique_together = ['exercise', 'name']
    
    def __str__(self):
        return f"{self.exercise.title} - {self.name}"


class TestResult(models.Model):
    """Results of running test cases against code executions"""
    
    class Status(models.TextChoices):
        PASSED = 'passed', _('Passed')
        FAILED = 'failed', _('Failed')
        ERROR = 'error', _('Error')
        TIMEOUT = 'timeout', _('Timeout')
        SKIPPED = 'skipped', _('Skipped')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(CodeExecution, on_delete=models.CASCADE, related_name='test_results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='results')
    
    # Test results
    status = models.CharField(max_length=20, choices=Status.choices)
    actual_output = models.TextField(blank=True)
    actual_error = models.TextField(blank=True)
    actual_exit_code = models.IntegerField(null=True, blank=True)
    
    # Performance metrics
    execution_time = models.FloatField(null=True, blank=True)
    memory_used = models.BigIntegerField(null=True, blank=True)
    
    # Comparison results
    output_diff = models.TextField(blank=True)
    similarity_score = models.FloatField(null=True, blank=True)
    
    # Grading
    points_earned = models.FloatField(default=0.0)
    feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Test Result')
        verbose_name_plural = _('Test Results')
        ordering = ['test_case__order']
        unique_together = ['execution', 'test_case']
    
    def __str__(self):
        return f"{self.execution.user.username} - {self.test_case.name} ({self.status})"


class CodePlayground(models.Model):
    """Playground sessions for experimentation"""
    
    class VisibilityType(models.TextChoices):
        PRIVATE = 'private', _('Private')
        PUBLIC = 'public', _('Public')
        SHARED = 'shared', _('Shared with Link')
        COURSE = 'course', _('Course Members Only')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playgrounds')
    environment = models.ForeignKey(ExecutionEnvironment, on_delete=models.CASCADE)
    
    # Playground metadata
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=20, choices=VisibilityType.choices, default=VisibilityType.PRIVATE)
    
    # Code content
    source_code = models.TextField(default='')
    saved_inputs = models.JSONField(default=list)  # Saved input scenarios
    
    # Collaboration
    collaborators = models.ManyToManyField(User, through='PlaygroundCollaborator', related_name='shared_playgrounds')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Usage tracking
    execution_count = models.PositiveIntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    tags = models.JSONField(default=list)
    is_featured = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)
    fork_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Code Playground')
        verbose_name_plural = _('Code Playgrounds')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}'s {self.title}"


class PlaygroundCollaborator(models.Model):
    """Collaborators for playground sessions"""
    
    class Permission(models.TextChoices):
        VIEW = 'view', _('View Only')
        EDIT = 'edit', _('Edit Code')
        ADMIN = 'admin', _('Admin Access')
    
    playground = models.ForeignKey(CodePlayground, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.CharField(max_length=20, choices=Permission.choices, default=Permission.VIEW)
    
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['playground', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.playground.title} ({self.permission})"


class ExecutionQuota(models.Model):
    """Track user execution quotas and limits"""
    
    class QuotaType(models.TextChoices):
        DAILY = 'daily', _('Daily Quota')
        MONTHLY = 'monthly', _('Monthly Quota')
        TOTAL = 'total', _('Total Quota')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='execution_quotas')
    quota_type = models.CharField(max_length=20, choices=QuotaType.choices)
    
    # Quota limits
    max_executions = models.PositiveIntegerField()
    max_cpu_time = models.PositiveIntegerField()  # seconds
    max_memory = models.PositiveIntegerField()  # MB
    
    # Current usage
    executions_used = models.PositiveIntegerField(default=0)
    cpu_time_used = models.FloatField(default=0.0)
    memory_used = models.BigIntegerField(default=0)
    
    # Reset periods
    reset_date = models.DateField()
    last_reset = models.DateTimeField(auto_now_add=True)
    
    # Status
    is_exceeded = models.BooleanField(default=False)
    is_warning_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Execution Quota')
        verbose_name_plural = _('Execution Quotas')
        unique_together = ['user', 'quota_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_quota_type_display()}"
    
    @property
    def remaining_executions(self):
        return max(0, self.max_executions - self.executions_used)
    
    @property
    def usage_percentage(self):
        if self.max_executions == 0:
            return 0
        return (self.executions_used / self.max_executions) * 100


class CodeTemplate(models.Model):
    """Code templates for different exercises and languages"""
    
    class TemplateType(models.TextChoices):
        STARTER = 'starter', _('Starter Template')
        SOLUTION = 'solution', _('Solution Template')
        EXAMPLE = 'example', _('Example Code')
        BOILERPLATE = 'boilerplate', _('Boilerplate')
        FRAMEWORK = 'framework', _('Framework Template')
        LIBRARY = 'library', _('Library Template')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TemplateType.choices)
    environment = models.ForeignKey(ExecutionEnvironment, on_delete=models.CASCADE)
    
    # Template content
    code_template = models.TextField()
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    placeholder_comments = models.JSONField(default=list)  # Comments indicating where users should add code
    
    # Template metadata
    tags = models.JSONField(default=list)
    difficulty_level = models.CharField(max_length=20, default='beginner')
    estimated_time = models.PositiveIntegerField(null=True, blank=True)  # minutes
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    average_completion_time = models.FloatField(null=True, blank=True)
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Author information
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_templates')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Code Template')
        verbose_name_plural = _('Code Templates')
        ordering = ['environment', 'name']
        indexes = [
            models.Index(fields=['environment', 'template_type']),
            models.Index(fields=['difficulty_level', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.environment.language})"


class ExecutionStatistics(models.Model):
    """Daily statistics for code execution usage"""
    
    date = models.DateField(unique=True)
    
    # Execution metrics
    total_executions = models.PositiveIntegerField(default=0)
    successful_executions = models.PositiveIntegerField(default=0)
    failed_executions = models.PositiveIntegerField(default=0)
    timeout_executions = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    average_execution_time = models.FloatField(default=0.0)
    total_cpu_time = models.FloatField(default=0.0)
    total_memory_used = models.BigIntegerField(default=0)
    
    # Language breakdown
    language_stats = models.JSONField(default=dict)  # {'python': 150, 'javascript': 89, ...}
    
    # User engagement
    unique_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    
    # Resource utilization
    peak_concurrent_executions = models.PositiveIntegerField(default=0)
    total_container_hours = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Execution Statistics')
        verbose_name_plural = _('Execution Statistics')
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats for {self.date}"