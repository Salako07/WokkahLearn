from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import (
    ExecutionEnvironment, CodeExecution, TestCase, TestResult,
    CodePlayground, PlaygroundCollaborator, ExecutionQuota, 
    CodeTemplate, ExecutionStatistics
)

User = get_user_model()


class ExecutionEnvironmentSerializer(serializers.ModelSerializer):
    """Serializer for execution environments"""
    
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_available = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    
    class Meta:
        model = ExecutionEnvironment
        fields = [
            'id', 'name', 'language', 'language_display', 'version', 'docker_image',
            'status', 'status_display', 'is_default', 'is_available',
            'default_timeout', 'max_memory', 'max_cpu_time', 'max_file_size',
            'max_output_size', 'file_extension', 'features',
            'installed_packages', 'available_libraries', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_available(self, obj):
        """Check if environment is currently available"""
        return obj.status == ExecutionEnvironment.Status.ACTIVE
    
    def get_features(self, obj):
        """Get supported features as a list"""
        features = []
        if obj.supports_input:
            features.append('input')
        if obj.supports_graphics:
            features.append('graphics')
        if obj.supports_networking:
            features.append('networking')
        if obj.supports_file_operations:
            features.append('files')
        if obj.supports_packages:
            features.append('packages')
        return features


class CodeExecutionSerializer(serializers.ModelSerializer):
    """Serializer for code executions"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    environment_language = serializers.CharField(source='environment.language', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    execution_type_display = serializers.CharField(source='get_execution_type_display', read_only=True)
    duration = serializers.SerializerMethodField()
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    
    class Meta:
        model = CodeExecution
        fields = [
            'id', 'user', 'user_username', 'environment', 'environment_name', 
            'environment_language', 'execution_type', 'execution_type_display',
            'exercise', 'exercise_title', 'session_id', 'source_code', 
            'stdin_input', 'command_line_args', 'environment_vars',
            'stdout_output', 'stderr_output', 'exit_code', 'status', 
            'status_display', 'execution_time', 'memory_used', 'cpu_time',
            'duration', 'container_id', 'error_message', 'is_successful',
            'quality_score', 'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'user', 'stdout_output', 'stderr_output', 'exit_code', 'status',
            'execution_time', 'memory_used', 'cpu_time', 'container_id',
            'error_message', 'is_successful', 'quality_score', 'created_at',
            'started_at', 'completed_at'
        ]
    
    def get_duration(self, obj):
        """Get execution duration in seconds"""
        return obj.duration


class CreateCodeExecutionSerializer(serializers.ModelSerializer):
    """Serializer for creating new code executions"""
    
    class Meta:
        model = CodeExecution
        fields = [
            'environment', 'execution_type', 'exercise', 'session_id',
            'source_code', 'stdin_input', 'command_line_args', 'environment_vars'
        ]
    
    def validate_source_code(self, value):
        """Validate source code"""
        if not value.strip():
            raise serializers.ValidationError("Source code cannot be empty")
        
        # Add basic security checks
        dangerous_patterns = ['import os', 'import sys', 'import subprocess', 'eval(', 'exec(']
        for pattern in dangerous_patterns:
            if pattern in value.lower():
                raise serializers.ValidationError(f"Potentially dangerous code detected: {pattern}")
        
        return value


class TestCaseSerializer(serializers.ModelSerializer):
    """Serializer for test cases"""
    
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    
    class Meta:
        model = TestCase
        fields = [
            'id', 'exercise', 'exercise_title', 'name', 'description',
            'test_type', 'test_type_display', 'input_data', 'expected_output',
            'setup_code', 'teardown_code', 'timeout_override', 'memory_limit_override',
            'difficulty', 'difficulty_display', 'points', 'order', 'is_hidden',
            'is_required', 'is_public', 'hints', 'explanation', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TestResultSerializer(serializers.ModelSerializer):
    """Serializer for test results"""
    
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    execution_user = serializers.CharField(source='execution.user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TestResult
        fields = [
            'id', 'execution', 'execution_user', 'test_case', 'test_case_name',
            'status', 'status_display', 'actual_output', 'error_message',
            'execution_time', 'memory_used', 'points_earned', 'feedback',
            'details', 'created_at'
        ]
        read_only_fields = ['created_at']


class CodePlaygroundSerializer(serializers.ModelSerializer):
    """Serializer for code playgrounds"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    environment_language = serializers.CharField(source='environment.language', read_only=True)
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    collaborator_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = CodePlayground
        fields = [
            'id', 'user', 'user_username', 'environment', 'environment_name',
            'environment_language', 'title', 'description', 'source_code',
            'visibility', 'visibility_display', 'is_template', 'template_category',
            'tags', 'is_favorite', 'collaborator_count', 'can_edit',
            'created_at', 'updated_at', 'last_executed'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'last_executed']
    
    def get_collaborator_count(self, obj):
        """Get number of collaborators"""
        return obj.collaborators.count()
    
    def get_can_edit(self, obj):
        """Check if current user can edit"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        if obj.user == request.user:
            return True
        
        collaborator = PlaygroundCollaborator.objects.filter(
            playground=obj,
            user=request.user,
            permission__in=['edit', 'admin']
        ).exists()
        
        return collaborator


class PlaygroundCollaboratorSerializer(serializers.ModelSerializer):
    """Serializer for playground collaborators"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    playground_title = serializers.CharField(source='playground.title', read_only=True)
    permission_display = serializers.CharField(source='get_permission_display', read_only=True)
    
    class Meta:
        model = PlaygroundCollaborator
        fields = [
            'id', 'playground', 'playground_title', 'user', 'user_username',
            'permission', 'permission_display', 'invited_by', 'created_at'
        ]
        read_only_fields = ['invited_by', 'created_at']


class CodeTemplateSerializer(serializers.ModelSerializer):
    """Serializer for code templates"""
    
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    environment_language = serializers.CharField(source='environment.language', read_only=True)
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_level_display', read_only=True)
    
    class Meta:
        model = CodeTemplate
        fields = [
            'id', 'environment', 'environment_name', 'environment_language',
            'name', 'description', 'template_type', 'template_type_display',
            'source_code', 'difficulty_level', 'difficulty_display',
            'tags', 'usage_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['usage_count', 'created_at', 'updated_at']


class ExecutionQuotaSerializer(serializers.ModelSerializer):
    """Serializer for execution quotas"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    cpu_usage_percentage = serializers.SerializerMethodField()
    memory_usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ExecutionQuota
        fields = [
            'id', 'user', 'user_username', 'tier', 'tier_display',
            'daily_executions_limit', 'daily_executions_used',
            'cpu_time_limit_seconds', 'cpu_time_used_seconds',
            'memory_limit_mb', 'memory_used_mb', 'usage_percentage',
            'cpu_usage_percentage', 'memory_usage_percentage',
            'reset_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'daily_executions_used', 'cpu_time_used_seconds', 'memory_used_mb',
            'created_at', 'updated_at'
        ]
    
    def get_usage_percentage(self, obj):
        """Get execution usage percentage"""
        if obj.daily_executions_limit == 0:
            return 0
        return round((obj.daily_executions_used / obj.daily_executions_limit) * 100, 2)
    
    def get_cpu_usage_percentage(self, obj):
        """Get CPU usage percentage"""
        if obj.cpu_time_limit_seconds == 0:
            return 0
        return round((obj.cpu_time_used_seconds / obj.cpu_time_limit_seconds) * 100, 2)
    
    def get_memory_usage_percentage(self, obj):
        """Get memory usage percentage"""
        if obj.memory_limit_mb == 0:
            return 0
        return round((obj.memory_used_mb / obj.memory_limit_mb) * 100, 2)


class ExecutionStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for execution statistics"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ExecutionStatistics
        fields = [
            'id', 'user', 'user_username', 'environment', 'environment_name',
            'date', 'total_executions', 'successful_executions', 'failed_executions',
            'total_execution_time', 'total_memory_used', 'total_cpu_time',
            'average_execution_time', 'success_rate', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_success_rate(self, obj):
        """Calculate success rate percentage"""
        if obj.total_executions == 0:
            return 0
        return round((obj.successful_executions / obj.total_executions) * 100, 2)


# Summary serializers for dashboard/overview
class ExecutionSummarySerializer(serializers.Serializer):
    """Summary serializer for execution overview"""
    
    total_executions = serializers.IntegerField()
    successful_executions = serializers.IntegerField()
    failed_executions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    total_execution_time = serializers.FloatField()
    average_execution_time = serializers.FloatField()
    languages_used = serializers.ListField(child=serializers.CharField())
    most_used_environment = serializers.CharField()


class EnvironmentStatsSerializer(serializers.Serializer):
    """Statistics serializer for environments"""
    
    environment_id = serializers.UUIDField()
    environment_name = serializers.CharField()
    language = serializers.CharField()
    total_executions = serializers.IntegerField()
    successful_executions = serializers.IntegerField()
    average_execution_time = serializers.FloatField()
    success_rate = serializers.FloatField()