# code_execution/services.py - Complete Implementation

import docker
import asyncio
import json
import time
import tempfile
import os
import shutil
import difflib
import re
from datetime import timezone, datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from typing import Dict, Any, Optional, List
import logging

from .models import (
    CodeExecution, ExecutionEnvironment, TestCase, TestResult,
    ExecutionQuota, ExecutionStatistics
)

logger = logging.getLogger(__name__)


class CodeExecutionService:
    """Service for executing code in Docker containers"""
    
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
            self.network_name = getattr(settings, 'DOCKER_NETWORK', 'wokkahlearn_execution')
            self._ensure_network_exists()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise
    
    def _ensure_network_exists(self):
        """Ensure the Docker network exists"""
        try:
            self.docker_client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.docker_client.networks.create(
                self.network_name,
                driver="bridge",
                options={"com.docker.network.bridge.enable_icc": "false"}
            )
    
    async def execute_code(self, execution: CodeExecution) -> Dict[str, Any]:
        """Execute code and return results"""
        try:
            execution.status = CodeExecution.Status.RUNNING
            execution.started_at = timezone.now()
            execution.save()
            
            # Prepare execution environment
            container_config = self._prepare_container_config(execution)
            
            # Create and start container
            container = self.docker_client.containers.run(
                **container_config,
                detach=True
            )
            
            execution.container_id = container.id
            execution.save()
            
            # Wait for execution to complete
            result = await self._wait_for_completion(container, execution)
            
            # Update execution with results
            execution.stdout_output = result.get('stdout', '')
            execution.stderr_output = result.get('stderr', '')
            execution.exit_code = result.get('exit_code', -1)
            execution.execution_time = result.get('execution_time', 0)
            execution.memory_used = result.get('memory_used', 0)
            execution.cpu_time = result.get('cpu_time', 0)
            execution.is_successful = result.get('exit_code', -1) == 0
            execution.status = CodeExecution.Status.COMPLETED
            execution.completed_at = timezone.now()
            execution.save()
            
            # Clean up container
            try:
                container.remove()
            except:
                pass  # Container might already be removed
            
            return result
            
        except docker.errors.ContainerError as e:
            execution.status = CodeExecution.Status.FAILED
            execution.stderr_output = str(e)
            execution.error_message = f"Container error: {str(e)}"
            execution.completed_at = timezone.now()
            execution.save()
            raise
        
        except asyncio.TimeoutError:
            execution.status = CodeExecution.Status.TIMEOUT
            execution.error_message = "Execution timed out"
            execution.completed_at = timezone.now()
            execution.save()
            
            # Stop container
            try:
                container = self.docker_client.containers.get(execution.container_id)
                container.stop(timeout=5)
                container.remove()
            except:
                pass
            
            raise
        
        except Exception as e:
            execution.status = CodeExecution.Status.ERROR
            execution.stderr_output = f"Internal error: {str(e)}"
            execution.error_message = str(e)
            execution.completed_at = timezone.now()
            execution.save()
            logger.error(f"Code execution error: {str(e)}")
            raise
    
    def _prepare_container_config(self, execution: CodeExecution) -> Dict[str, Any]:
        """Prepare Docker container configuration"""
        env = execution.environment
        
        # Create temporary directory with user code
        temp_dir = self._create_code_directory(execution)
        
        # Build container configuration
        config = {
            'image': env.docker_image,
            'command': self._build_command(execution, temp_dir),
            'mem_limit': f"{env.max_memory}m",
            'cpu_period': 100000,
            'cpu_quota': env.max_cpu_time * 1000,
            'network': self.network_name,
            'remove': False,
            'detach': True,
            'volumes': {
                temp_dir: {
                    'bind': '/workspace',
                    'mode': 'rw'
                }
            },
            'working_dir': '/workspace',
            'user': 'nobody:nogroup',
            'read_only': False,  # Need write access for compilation
            'tmpfs': {
                '/tmp': 'noexec,nosuid,size=10m',
                '/var/tmp': 'noexec,nosuid,size=10m'
            },
            'security_opt': ['no-new-privileges:true'],
            'cap_drop': ['ALL'],
            'cap_add': ['CHOWN', 'DAC_OVERRIDE', 'FOWNER', 'SETGID', 'SETUID'],
            'environment': {
                'TIMEOUT': str(env.default_timeout),
                'MAX_MEMORY': str(env.max_memory),
                'PYTHONDONTWRITEBYTECODE': '1',
                'PYTHONUNBUFFERED': '1',
                'NODE_ENV': 'sandbox',
                'HOME': '/workspace'
            },
            'labels': {
                'wokkah.execution.id': str(execution.id),
                'wokkah.user.id': str(execution.user.id),
                'wokkah.environment': env.language
            }
        }
        
        # Add stdin if provided
        if execution.stdin_input:
            config['stdin_open'] = True
            config['tty'] = False
        
        # Add environment variables
        if execution.environment_vars:
            config['environment'].update(execution.environment_vars)
        
        return config
    
    def _create_code_directory(self, execution: CodeExecution) -> str:
        """Create temporary directory with user code and dependencies"""
        env = execution.environment
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='wokkah_exec_')
        
        # Write main code file
        main_filename = f"main{env.file_extension}"
        main_filepath = os.path.join(temp_dir, main_filename)
        
        with open(main_filepath, 'w', encoding='utf-8') as f:
            f.write(execution.source_code)
        
        # Create additional files based on language
        self._create_language_specific_files(execution, temp_dir)
        
        # Set proper permissions
        os.chmod(temp_dir, 0o755)
        for root, dirs, files in os.walk(temp_dir):
            for dir_name in dirs:
                os.chmod(os.path.join(root, dir_name), 0o755)
            for file_name in files:
                os.chmod(os.path.join(root, file_name), 0o644)
        
        return temp_dir
    
    def _create_language_specific_files(self, execution: CodeExecution, temp_dir: str):
        """Create language-specific configuration files"""
        env = execution.environment
        
        if env.language.lower() == 'python':
            # Create requirements.txt if needed
            requirements_path = os.path.join(temp_dir, 'requirements.txt')
            with open(requirements_path, 'w') as f:
                f.write("# No additional requirements\n")
        
        elif env.language.lower() == 'javascript':
            # Create package.json for Node.js
            package_json = {
                "name": "wokkah-execution",
                "version": "1.0.0",
                "main": "main.js",
                "scripts": {
                    "start": "node main.js"
                }
            }
            package_path = os.path.join(temp_dir, 'package.json')
            with open(package_path, 'w') as f:
                json.dump(package_json, f, indent=2)
        
        elif env.language.lower() == 'java':
            # Create a simple Main.java wrapper if needed
            if 'class Main' not in execution.source_code:
                wrapper = f"""
public class Main {{
    public static void main(String[] args) {{
        // User code execution
        {execution.source_code}
    }}
}}
"""
                main_java_path = os.path.join(temp_dir, 'Main.java')
                with open(main_java_path, 'w') as f:
                    f.write(wrapper)
    
    def _build_command(self, execution: CodeExecution, temp_dir: str) -> List[str]:
        """Build execution command"""
        env = execution.environment
        
        if env.language.lower() == 'python':
            cmd = ['python3', 'main.py']
        elif env.language.lower() == 'javascript':
            cmd = ['node', 'main.js']
        elif env.language.lower() == 'java':
            cmd = ['sh', '-c', 'javac *.java && java Main']
        elif env.language.lower() == 'cpp' or env.language.lower() == 'c++':
            cmd = ['sh', '-c', 'g++ -o main main.cpp && ./main']
        elif env.language.lower() == 'c':
            cmd = ['sh', '-c', 'gcc -o main main.c && ./main']
        elif env.language.lower() == 'go':
            cmd = ['go', 'run', 'main.go']
        elif env.language.lower() == 'rust':
            cmd = ['sh', '-c', 'rustc main.rs && ./main']
        else:
            # Use environment-specific command
            if env.interpreter_command:
                cmd = [env.interpreter_command, f"main{env.file_extension}"]
            elif env.compiler_command:
                output_file = 'main'
                cmd = ['sh', '-c', f"{env.compiler_command} main{env.file_extension} -o {output_file} && ./{output_file}"]
            else:
                cmd = [f"main{env.file_extension}"]
        
        # Add command line arguments
        if execution.command_line_args:
            cmd.extend(execution.command_line_args)
        
        return cmd
    
    async def _wait_for_completion(self, container, execution: CodeExecution) -> Dict[str, Any]:
        """Wait for container execution to complete"""
        start_time = time.time()
        timeout = execution.environment.default_timeout
        
        try:
            # Wait for container to complete or timeout
            result = container.wait(timeout=timeout)
            execution_time = time.time() - start_time
            
            # Get output
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
            
            # Truncate output if too large
            max_output_size = execution.environment.max_output_size * 1024 * 1024  # Convert MB to bytes
            if len(stdout) > max_output_size:
                stdout = stdout[:max_output_size] + "\n... (output truncated)"
            if len(stderr) > max_output_size:
                stderr = stderr[:max_output_size] + "\n... (error output truncated)"
            
            # Get resource usage
            try:
                stats = container.stats(stream=False)
                memory_used = stats['memory_stats'].get('usage', 0)
                cpu_usage = stats['cpu_stats'].get('cpu_usage', {}).get('total_usage', 0)
            except:
                memory_used = 0
                cpu_usage = 0
            
            return {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': result['StatusCode'],
                'execution_time': execution_time,
                'memory_used': memory_used,
                'cpu_time': cpu_usage / 1000000000.0,  # Convert nanoseconds to seconds
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Container execution error: {str(e)}")
            return {
                'stdout': '',
                'stderr': f"Execution error: {str(e)}",
                'exit_code': -1,
                'execution_time': time.time() - start_time,
                'memory_used': 0,
                'cpu_time': 0,
                'status': 'error'
            }
    
    def stop_execution(self, execution: CodeExecution):
        """Stop a running execution"""
        if execution.container_id:
            try:
                container = self.docker_client.containers.get(execution.container_id)
                container.stop(timeout=5)
                container.remove()
            except docker.errors.NotFound:
                pass  # Container already stopped/removed
            except Exception as e:
                logger.error(f"Failed to stop container {execution.container_id}: {str(e)}")
    
    def cleanup_old_executions(self, days_old: int = 7):
        """Clean up old execution containers and files"""
        cutoff_date = timezone.now() - timedelta(days=days_old)
        old_executions = CodeExecution.objects.filter(
            completed_at__lt=cutoff_date,
            container_id__isnull=False
        )
        
        for execution in old_executions:
            try:
                container = self.docker_client.containers.get(execution.container_id)
                container.remove(force=True)
            except docker.errors.NotFound:
                pass
            except Exception as e:
                logger.error(f"Failed to clean up container {execution.container_id}: {str(e)}")
            
            # Clear container ID
            execution.container_id = ''
            execution.save()


class TestRunner:
    """Service for running test cases against code executions"""
    
    def __init__(self):
        self.execution_service = CodeExecutionService()
    
    async def run_tests(self, execution: CodeExecution) -> Dict[str, Any]:
        """Run all test cases for an exercise"""
        if not execution.exercise:
            return {'error': 'No exercise associated with execution'}
        
        test_cases = TestCase.objects.filter(
            exercise=execution.exercise,
            is_active=True
        ).order_by('order')
        
        results = []
        total_points = 0
        earned_points = 0
        passed_tests = 0
        
        for test_case in test_cases:
            result = await self.run_single_test(execution, test_case)
            results.append(result)
            
            total_points += test_case.points
            if result['status'] == 'passed':
                earned_points += test_case.points
                passed_tests += 1
        
        # Calculate overall score
        overall_score = (earned_points / total_points * 100) if total_points > 0 else 0
        
        # Update execution quality score
        execution.quality_score = overall_score
        execution.save()
        
        return {
            'total_tests': len(test_cases),
            'passed_tests': passed_tests,
            'failed_tests': len(test_cases) - passed_tests,
            'total_points': total_points,
            'earned_points': earned_points,
            'score_percentage': overall_score,
            'results': results
        }
    
    async def run_single_test(self, execution: CodeExecution, test_case: TestCase) -> Dict[str, Any]:
        """Run a single test case"""
        # Create test execution with test input
        test_execution = CodeExecution.objects.create(
            user=execution.user,
            environment=execution.environment,
            execution_type=CodeExecution.ExecutionType.ASSESSMENT,
            source_code=execution.source_code,
            stdin_input=test_case.input_data,
            exercise=execution.exercise
        )
        
        try:
            # Execute code with test input
            result = await self.execution_service.execute_code(test_execution)
            
            # Compare output
            test_result = self._compare_output(
                test_execution,
                test_case,
                result.get('stdout', ''),
                result.get('stderr', ''),
                result.get('exit_code', -1)
            )
            
            # Save test result
            TestResult.objects.create(
                execution=execution,
                test_case=test_case,
                status=test_result['status'],
                actual_output=result.get('stdout', ''),
                actual_error=result.get('stderr', ''),
                actual_exit_code=result.get('exit_code', -1),
                execution_time=result.get('execution_time', 0),
                memory_used=result.get('memory_used', 0),
                output_diff=test_result.get('diff', ''),
                similarity_score=test_result.get('similarity', 0),
                points_earned=test_result.get('points', 0),
                feedback=test_result.get('feedback', '')
            )
            
            return test_result
            
        except Exception as e:
            # Save error result
            TestResult.objects.create(
                execution=execution,
                test_case=test_case,
                status=TestResult.Status.ERROR,
                actual_error=str(e),
                feedback=f"Test execution failed: {str(e)}"
            )
            
            return {
                'test_case_name': test_case.name,
                'status': 'error',
                'error': str(e),
                'points': 0
            }
        
        finally:
            # Clean up test execution
            test_execution.delete()
    
    def _compare_output(self, execution: CodeExecution, test_case: TestCase, 
                       actual_output: str, actual_error: str, actual_exit_code: int) -> Dict[str, Any]:
        """Compare actual output with expected output"""
        
        # Check exit code first
        if test_case.expected_exit_code != actual_exit_code:
            return {
                'test_case_name': test_case.name,
                'status': 'failed',
                'expected_exit_code': test_case.expected_exit_code,
                'actual_exit_code': actual_exit_code,
                'feedback': f"Expected exit code {test_case.expected_exit_code}, got {actual_exit_code}",
                'points': 0,
                'similarity': 0
            }
        
        # Check for expected error
        if test_case.expected_error:
            if test_case.expected_error.strip() not in actual_error:
                return {
                    'test_case_name': test_case.name,
                    'status': 'failed',
                    'expected_error': test_case.expected_error,
                    'actual_error': actual_error,
                    'feedback': "Expected error not found in output",
                    'points': 0,
                    'similarity': 0
                }
        
        # Compare output
        expected = test_case.expected_output.strip()
        actual = actual_output.strip()
        
        # Apply comparison options
        if test_case.ignore_whitespace:
            expected = re.sub(r'\s+', ' ', expected)
            actual = re.sub(r'\s+', ' ', actual)
        
        if test_case.ignore_case:
            expected = expected.lower()
            actual = actual.lower()
        
        # Calculate similarity
        similarity = self._calculate_similarity(expected, actual)
        
        # Determine if test passed
        if test_case.strict_output_matching:
            passed = expected == actual
        else:
            passed = similarity >= 0.9  # 90% similarity threshold
        
        # Generate diff if failed
        diff = ''
        if not passed:
            diff = '\n'.join(difflib.unified_diff(
                expected.splitlines(),
                actual.splitlines(),
                fromfile='expected',
                tofile='actual',
                lineterm=''
            ))
        
        # Calculate points
        if passed:
            points = test_case.points
        elif similarity > 0.5:
            points = test_case.points * similarity  # Partial credit
        else:
            points = 0
        
        # Generate feedback
        if passed:
            feedback = "Test passed!"
        elif similarity > 0.8:
            feedback = "Output is very close but not exact"
        elif similarity > 0.5:
            feedback = "Output has some similarities but significant differences"
        else:
            feedback = "Output is significantly different from expected"
        
        return {
            'test_case_name': test_case.name,
            'status': 'passed' if passed else 'failed',
            'expected_output': test_case.expected_output,
            'actual_output': actual_output,
            'diff': diff,
            'similarity': similarity,
            'points': points,
            'feedback': feedback
        }
    
    def _calculate_similarity(self, expected: str, actual: str) -> float:
        """Calculate similarity between expected and actual output"""
        if not expected and not actual:
            return 1.0
        
        if not expected or not actual:
            return 0.0
        
        # Use SequenceMatcher for similarity calculation
        matcher = difflib.SequenceMatcher(None, expected, actual)
        return matcher.ratio()


class QuotaManager:
    """Service for managing execution quotas"""
    
    def check_quota(self, user, environment: ExecutionEnvironment) -> bool:
        """Check if user has quota available for execution"""
        
        # Get or create daily quota
        today = timezone.now().date()
        daily_quota, created = ExecutionQuota.objects.get_or_create(
            user=user,
            quota_type=ExecutionQuota.QuotaType.DAILY,
            defaults={
                'max_executions': self._get_user_daily_limit(user),
                'max_cpu_time': 3600,  # 1 hour
                'max_memory': 1024,  # 1 GB
                'reset_date': today
            }
        )
        
        # Reset quota if needed
        if daily_quota.reset_date < today:
            daily_quota.executions_used = 0
            daily_quota.cpu_time_used = 0
            daily_quota.memory_used = 0
            daily_quota.reset_date = today
            daily_quota.is_exceeded = False
            daily_quota.save()
        
        # Check limits
        if daily_quota.executions_used >= daily_quota.max_executions:
            daily_quota.is_exceeded = True
            daily_quota.save()
            return False
        
        # Check environment-specific limits
        if environment.daily_execution_limit > 0:
            env_executions_today = CodeExecution.objects.filter(
                user=user,
                environment=environment,
                created_at__date=today
            ).count()
            
            if env_executions_today >= environment.daily_execution_limit:
                return False
        
        return True
    
    def update_quota(self, user, execution: CodeExecution):
        """Update user quota after execution"""
        today = timezone.now().date()
        
        try:
            daily_quota = ExecutionQuota.objects.get(
                user=user,
                quota_type=ExecutionQuota.QuotaType.DAILY,
                reset_date=today
            )
            
            daily_quota.executions_used += 1
            daily_quota.cpu_time_used += execution.cpu_time or 0
            daily_quota.memory_used += execution.memory_used or 0
            daily_quota.save()
            
        except ExecutionQuota.DoesNotExist:
            logger.warning(f"Daily quota not found for user {user.id}")
    
    def get_quota_status(self, user) -> Dict[str, Any]:
        """Get user's current quota status"""
        today = timezone.now().date()
        
        try:
            daily_quota = ExecutionQuota.objects.get(
                user=user,
                quota_type=ExecutionQuota.QuotaType.DAILY,
                reset_date=today
            )
        except ExecutionQuota.DoesNotExist:
            daily_quota = ExecutionQuota.objects.create(
                user=user,
                quota_type=ExecutionQuota.QuotaType.DAILY,
                max_executions=self._get_user_daily_limit(user),
                max_cpu_time=3600,
                max_memory=1024,
                reset_date=today
            )
        
        return {
            'daily': {
                'executions': {
                    'used': daily_quota.executions_used,
                    'limit': daily_quota.max_executions,
                    'remaining': daily_quota.remaining_executions,
                    'percentage': daily_quota.usage_percentage
                },
                'cpu_time': {
                    'used': daily_quota.cpu_time_used,
                    'limit': daily_quota.max_cpu_time
                },
                'memory': {
                    'used': daily_quota.memory_used,
                    'limit': daily_quota.max_memory
                },
                'is_exceeded': daily_quota.is_exceeded,
                'reset_date': daily_quota.reset_date
            }
        }
    
    def _get_user_daily_limit(self, user) -> int:
        """Get daily execution limit based on user role/subscription"""
        if user.role == 'admin':
            return 1000
        elif user.role == 'instructor':
            return 500
        elif user.is_premium:
            return 200
        else:
            return 50  # Free tier


class StatisticsCollector:
    """Service for collecting execution statistics"""
    
    def collect_daily_stats(self, date: datetime.date = None):
        """Collect and store daily statistics"""
        if date is None:
            date = timezone.now().date()
        
        # Get executions for the date
        executions = CodeExecution.objects.filter(
            created_at__date=date
        )
        
        # Calculate statistics
        total_executions = executions.count()
        successful_executions = executions.filter(
            status=CodeExecution.Status.COMPLETED,
            is_successful=True
        ).count()
        failed_executions = executions.filter(
            status__in=[
                CodeExecution.Status.FAILED,
                CodeExecution.Status.ERROR,
                CodeExecution.Status.TIMEOUT
            ]
        ).count()
        timeout_executions = executions.filter(
            status=CodeExecution.Status.TIMEOUT
        ).count()
        
        # Performance metrics
        completed_executions = executions.filter(execution_time__isnull=False)
        avg_execution_time = completed_executions.aggregate(
            avg=models.Avg('execution_time')
        )['avg'] or 0
        
        total_cpu_time = completed_executions.aggregate(
            total=models.Sum('cpu_time')
        )['total'] or 0
        
        total_memory_used = completed_executions.aggregate(
            total=models.Sum('memory_used')
        )['total'] or 0
        
        # Language breakdown
        language_stats = executions.values('environment__language').annotate(
            count=Count('id')
        )
        language_dict = {
            item['environment__language']: item['count']
            for item in language_stats
        }
        
        # User metrics
        unique_users = executions.values('user').distinct().count()
        
        # Create or update statistics
        stats, created = ExecutionStatistics.objects.update_or_create(
            date=date,
            defaults={
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'timeout_executions': timeout_executions,
                'average_execution_time': avg_execution_time,
                'total_cpu_time': total_cpu_time,
                'total_memory_used': total_memory_used,
                'language_stats': language_dict,
                'unique_users': unique_users
            }
        )
        
        return stats