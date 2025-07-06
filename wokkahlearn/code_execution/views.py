# code_execution/views.py - Complete Implementation

import asyncio
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.core.cache import cache
from asgiref.sync import sync_to_async
import logging
from datetime import datetime, timedelta

from .models import (
    ExecutionEnvironment, CodeExecution, TestCase, TestResult,
    CodePlayground, PlaygroundCollaborator, ExecutionQuota, 
    CodeTemplate, ExecutionStatistics
)
from .serializers import (
    ExecutionEnvironmentSerializer, CodeExecutionSerializer, 
    TestCaseSerializer, TestResultSerializer, CodePlaygroundSerializer,
    CodeTemplateSerializer, ExecutionQuotaSerializer, ExecutionStatisticsSerializer
)
from .services import CodeExecutionService, TestRunner, QuotaManager
from courses.models import Exercise

logger = logging.getLogger(__name__)


class ExecutionEnvironmentViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for execution environments"""
    queryset = ExecutionEnvironment.objects.filter(status=ExecutionEnvironment.Status.ACTIVE)
    serializer_class = ExecutionEnvironmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        language = self.request.query_params.get('language')
        supports_feature = self.request.query_params.get('supports')
        
        if language:
            queryset = queryset.filter(language__iexact=language)
        
        if supports_feature:
            feature_map = {
                'input': 'supports_input',
                'graphics': 'supports_graphics',
                'networking': 'supports_networking',
                'files': 'supports_file_operations',
                'packages': 'supports_packages'
            }
            if supports_feature in feature_map:
                queryset = queryset.filter(**{feature_map[supports_feature]: True})
        
        return queryset.order_by('priority', 'language', 'version')
    
    @action(detail=False, methods=['get'])
    def languages(self, request):
        """Get list of available languages"""
        languages = self.get_queryset().values_list('language', flat=True).distinct()
        return Response(list(languages))
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get default environments for each language"""
        defaults = self.get_queryset().filter(is_default=True)
        serializer = self.get_serializer(defaults, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """Get available code templates for this environment"""
        environment = self.get_object()
        templates = CodeTemplate.objects.filter(
            environment=environment,
            is_active=True
        ).order_by('template_type', 'name')
        
        template_serializer = CodeTemplateSerializer(templates, many=True)
        return Response(template_serializer.data)


class CodeExecutionViewSet(viewsets.ModelViewSet):
    """API endpoints for code execution"""
    serializer_class = CodeExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CodeExecution.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by execution type
        exec_type = self.request.query_params.get('type')
        if exec_type:
            queryset = queryset.filter(execution_type=exec_type)
        
        # Filter by exercise
        exercise_id = self.request.query_params.get('exercise')
        if exercise_id:
            queryset = queryset.filter(exercise_id=exercise_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def create(self, request):
        """Execute code"""
        try:
            # Validate input
            source_code = request.data.get('source_code', '').strip()
            environment_id = request.data.get('environment_id')
            execution_type = request.data.get('execution_type', 'playground')
            
            if not source_code:
                return Response(
                    {'error': 'Source code is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not environment_id:
                return Response(
                    {'error': 'Environment ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get environment
            try:
                environment = ExecutionEnvironment.objects.get(
                    id=environment_id,
                    status=ExecutionEnvironment.Status.ACTIVE
                )
            except ExecutionEnvironment.DoesNotExist:
                return Response(
                    {'error': 'Invalid environment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check quota
            quota_manager = QuotaManager()
            if not quota_manager.check_quota(request.user, environment):
                return Response(
                    {'error': 'Execution quota exceeded'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Create execution record
            execution = CodeExecution.objects.create(
                user=request.user,
                environment=environment,
                execution_type=execution_type,
                source_code=source_code,
                stdin_input=request.data.get('stdin_input', ''),
                command_line_args=request.data.get('command_line_args', []),
                environment_vars=request.data.get('environment_vars', {}),
                exercise_id=request.data.get('exercise_id'),
                session_id=request.data.get('session_id', '')
            )
            
            # Execute code asynchronously
            execution_service = CodeExecutionService()
            
            # Run execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    execution_service.execute_code(execution)
                )
            finally:
                loop.close()
            
            # Update quota
            quota_manager.update_quota(request.user, execution)
            
            # If this is an exercise submission, run test cases
            if execution.exercise and execution.status == CodeExecution.Status.COMPLETED:
                test_runner = TestRunner()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    test_results = loop.run_until_complete(
                        test_runner.run_tests(execution)
                    )
                    result['test_results'] = test_results
                finally:
                    loop.close()
            
            # Return execution result
            serializer = self.get_serializer(execution)
            response_data = serializer.data
            response_data.update(result)
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Code execution error: {str(e)}")
            return Response(
                {'error': 'Code execution failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop a running execution"""
        execution = self.get_object()
        
        if execution.status not in [CodeExecution.Status.RUNNING, CodeExecution.Status.QUEUED]:
            return Response(
                {'error': 'Execution is not running'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            execution_service = CodeExecutionService()
            execution_service.stop_execution(execution)
            
            execution.status = CodeExecution.Status.CANCELLED
            execution.completed_at = timezone.now()
            execution.save()
            
            return Response({'message': 'Execution stopped'})
        except Exception as e:
            return Response(
                {'error': f'Failed to stop execution: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get detailed execution results including test results"""
        execution = self.get_object()
        
        # Get test results if available
        test_results = []
        if execution.exercise:
            test_results = TestResult.objects.filter(execution=execution)
            test_serializer = TestResultSerializer(test_results, many=True)
            test_results = test_serializer.data
        
        serializer = self.get_serializer(execution)
        data = serializer.data
        data['test_results'] = test_results
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get execution history with statistics"""
        queryset = self.get_queryset()
        
        # Get statistics
        stats = queryset.aggregate(
            total=Count('id'),
            successful=Count('id', filter=Q(status=CodeExecution.Status.COMPLETED)),
            failed=Count('id', filter=Q(status=CodeExecution.Status.FAILED)),
            avg_time=Avg('execution_time'),
            total_time=Sum('execution_time')
        )
        
        # Get recent executions
        recent = queryset[:20]
        serializer = self.get_serializer(recent, many=True)
        
        return Response({
            'statistics': stats,
            'recent_executions': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def quota(self, request):
        """Get user's execution quota status"""
        quota_manager = QuotaManager()
        quota_status = quota_manager.get_quota_status(request.user)
        return Response(quota_status)


class CodePlaygroundViewSet(viewsets.ModelViewSet):
    """API endpoints for code playground"""
    serializer_class = CodePlaygroundSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CodePlayground.objects.filter(
            Q(user=self.request.user) |
            Q(collaborators=self.request.user) |
            Q(visibility=CodePlayground.VisibilityType.PUBLIC)
        ).distinct()
        
        # Filter by visibility
        visibility = self.request.query_params.get('visibility')
        if visibility:
            queryset = queryset.filter(visibility=visibility)
        
        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(environment__language__iexact=language)
        
        # Filter by course
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.order_by('-updated_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute code in playground"""
        playground = self.get_object()
        
        # Check permissions
        if not self._can_execute(request.user, playground):
            return Response(
                {'error': 'No permission to execute'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create execution
        execution_data = {
            'source_code': request.data.get('source_code', playground.source_code),
            'environment_id': str(playground.environment.id),
            'execution_type': 'playground',
            'stdin_input': request.data.get('stdin_input', ''),
            'session_id': str(playground.id)
        }
        
        # Execute via CodeExecutionViewSet
        execution_view = CodeExecutionViewSet()
        execution_view.request = request
        execution_view.format_kwarg = None
        
        return execution_view.create(request)
    
    @action(detail=True, methods=['post'])
    def fork(self, request, pk=None):
        """Fork a playground"""
        original = self.get_object()
        
        # Create forked playground
        fork = CodePlayground.objects.create(
            user=request.user,
            environment=original.environment,
            title=f"Fork of {original.title}",
            description=f"Forked from {original.user.username}'s playground",
            source_code=original.source_code,
            visibility=CodePlayground.VisibilityType.PRIVATE,
            tags=original.tags.copy()
        )
        
        # Update fork count
        original.fork_count += 1
        original.save()
        
        serializer = self.get_serializer(fork)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share playground with collaborators"""
        playground = self.get_object()
        
        # Check ownership
        if playground.user != request.user:
            return Response(
                {'error': 'Only owner can share playground'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Add collaborators
        collaborator_emails = request.data.get('collaborators', [])
        permission_level = request.data.get('permission', 'view')
        
        added_collaborators = []
        for email in collaborator_emails:
            try:
                user = User.objects.get(email=email)
                collaborator, created = PlaygroundCollaborator.objects.get_or_create(
                    playground=playground,
                    user=user,
                    defaults={'permission': permission_level}
                )
                if created:
                    added_collaborators.append(user.email)
            except User.DoesNotExist:
                continue
        
        return Response({
            'message': f'Added {len(added_collaborators)} collaborators',
            'added': added_collaborators
        })
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured playgrounds"""
        featured = CodePlayground.objects.filter(
            is_featured=True,
            visibility=CodePlayground.VisibilityType.PUBLIC
        ).order_by('-updated_at')[:10]
        
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """Get playground templates"""
        templates = CodePlayground.objects.filter(
            is_template=True,
            visibility__in=[
                CodePlayground.VisibilityType.PUBLIC,
                CodePlayground.VisibilityType.COURSE
            ]
        ).order_by('environment__language', 'title')
        
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)
    
    def _can_execute(self, user, playground):
        """Check if user can execute code in playground"""
        if playground.user == user:
            return True
        
        if playground.visibility == CodePlayground.VisibilityType.PUBLIC:
            return True
        
        collaborator = PlaygroundCollaborator.objects.filter(
            playground=playground,
            user=user,
            permission__in=['edit', 'admin']
        ).exists()
        
        return collaborator


class TestCaseViewSet(viewsets.ModelViewSet):
    """API endpoints for test cases"""
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only instructors can manage test cases
        if not self.request.user.role in ['instructor', 'admin']:
            return TestCase.objects.none()
        
        queryset = TestCase.objects.all()
        
        # Filter by exercise
        exercise_id = self.request.query_params.get('exercise')
        if exercise_id:
            queryset = queryset.filter(exercise_id=exercise_id)
        
        # Filter by visibility
        include_private = self.request.query_params.get('include_private', 'false')
        if include_private.lower() != 'true':
            queryset = queryset.filter(is_public=True)
        
        return queryset.order_by('exercise', 'order')
    
    @action(detail=False, methods=['post'])
    def run_tests(self, request):
        """Run test cases against submitted code"""
        exercise_id = request.data.get('exercise_id')
        source_code = request.data.get('source_code')
        
        if not exercise_id or not source_code:
            return Response(
                {'error': 'Exercise ID and source code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create temporary execution
        execution = CodeExecution.objects.create(
            user=request.user,
            environment=exercise.environment,
            execution_type=CodeExecution.ExecutionType.ASSESSMENT,
            source_code=source_code,
            exercise=exercise
        )
        
        # Run tests
        test_runner = TestRunner()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                test_runner.run_tests(execution)
            )
            return Response(results)
        finally:
            loop.close()
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate a test case"""
        test_case = self.get_object()
        
        # Run test case against sample solution
        sample_code = request.data.get('sample_code')
        if not sample_code:
            return Response(
                {'error': 'Sample code is required for validation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create temporary execution for validation
        execution = CodeExecution.objects.create(
            user=request.user,
            environment=test_case.exercise.environment,
            execution_type=CodeExecution.ExecutionType.DEBUG,
            source_code=sample_code,
            exercise=test_case.exercise
        )
        
        # Run specific test case
        test_runner = TestRunner()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                test_runner.run_single_test(execution, test_case)
            )
            return Response(result)
        finally:
            loop.close()


class CodeTemplateViewSet(viewsets.ModelViewSet):
    """API endpoints for code templates"""
    serializer_class = CodeTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CodeTemplate.objects.filter(is_active=True)
        
        # Filter by environment
        environment_id = self.request.query_params.get('environment')
        if environment_id:
            queryset = queryset.filter(environment_id=environment_id)
        
        # Filter by template type
        template_type = self.request.query_params.get('type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        return queryset.order_by('environment', 'template_type', 'name')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured templates"""
        featured = self.get_queryset().filter(is_featured=True)[:10]
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Record template usage"""
        template = self.get_object()
        template.usage_count += 1
        template.save()
        
        return Response({'message': 'Template usage recorded'})


class ExecutionStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for execution statistics"""
    serializer_class = ExecutionStatisticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only admins can view platform statistics
        if self.request.user.role != 'admin':
            return ExecutionStatistics.objects.none()
        
        return ExecutionStatistics.objects.all().order_by('-date')
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard statistics"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get today's stats
        today = timezone.now().date()
        today_stats = ExecutionStatistics.objects.filter(date=today).first()
        
        # Get week stats
        week_ago = today - timedelta(days=7)
        week_stats = ExecutionStatistics.objects.filter(
            date__gte=week_ago
        ).aggregate(
            total_executions=Sum('total_executions'),
            successful_executions=Sum('successful_executions'),
            failed_executions=Sum('failed_executions'),
            unique_users=Sum('unique_users')
        )
        
        # Get environment usage
        env_usage = CodeExecution.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).values('environment__language').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'today': ExecutionStatisticsSerializer(today_stats).data if today_stats else None,
            'week': week_stats,
            'environment_usage': list(env_usage),
            'total_users': CodeExecution.objects.values('user').distinct().count(),
            'total_executions': CodeExecution.objects.count()
        })