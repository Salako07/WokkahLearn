"""
Secure Python code runner with timeout and resource limits
"""

import sys
import os
import signal
import resource
import tempfile
import subprocess
import time
from contextlib import contextmanager

class SecurityError(Exception):
    pass

class TimeoutError(Exception):
    pass

# Blocked imports for security
BLOCKED_IMPORTS = {
    'os', 'sys', 'subprocess', 'multiprocessing', 'threading',
    'socket', 'urllib', 'http', 'ftplib', 'smtplib',
    'pickle', 'shelve', 'marshal', 'dill',
    'importlib', '__import__', 'eval', 'exec', 'compile',
    'open', 'file', 'input', 'raw_input'
}

# Blocked functions
BLOCKED_FUNCTIONS = {
    'open', 'file', 'input', 'raw_input', 'execfile',
    'reload', '__import__', 'eval', 'exec', 'compile',
    'exit', 'quit', 'help', 'license', 'credits', 'copyright'
}

def set_resource_limits():
    """Set resource limits for the execution"""
    # Memory limit (128MB default)
    memory_limit = int(os.getenv('MAX_MEMORY_MB', '128')) * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
    
    # CPU time limit (30 seconds default)
    cpu_limit = int(os.getenv('MAX_EXECUTION_TIME', '30'))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    
    # File size limit (10MB)
    resource.setrlimit(resource.RLIMIT_FSIZE, (10*1024*1024, 10*1024*1024))
    
    # Number of processes limit
    resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))

@contextmanager
def timeout_handler(seconds):
    """Context manager for handling timeouts"""
    def timeout_signal(signum, frame):
        raise TimeoutError(f"Execution timed out after {seconds} seconds")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_signal)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def validate_code(code):
    """Basic code validation for security"""
    # Check for blocked imports
    lines = code.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('import ') or line.startswith('from '):
            for blocked in BLOCKED_IMPORTS:
                if blocked in line:
                    raise SecurityError(f"Import '{blocked}' is not allowed")
    
    # Check for blocked functions
    for func in BLOCKED_FUNCTIONS:
        if func in code:
            raise SecurityError(f"Function '{func}' is not allowed")
    
    return True

def execute_python_code(code, stdin_input=''):
    """Execute Python code safely"""
    try:
        # Validate code
        validate_code(code)
        
        # Set resource limits
        set_resource_limits()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute with timeout
            timeout = int(os.getenv('MAX_EXECUTION_TIME', '30'))
            
            with timeout_handler(timeout):
                start_time = time.time()
                
                # Run the code
                process = subprocess.Popen(
                    [sys.executable, temp_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd='/workspace',
                    env={'PYTHONPATH': '/workspace'}
                )
                
                stdout, stderr = process.communicate(input=stdin_input, timeout=timeout)
                execution_time = time.time() - start_time
                
                return {
                    'stdout': stdout,
                    'stderr': stderr,
                    'exit_code': process.returncode,
                    'execution_time': execution_time,
                    'status': 'completed'
                }
                
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except TimeoutError as e:
        return {
            'stdout': '',
            'stderr': str(e),
            'exit_code': -1,
            'execution_time': timeout,
            'status': 'timeout'
        }
    except SecurityError as e:
        return {
            'stdout': '',
            'stderr': f"Security Error: {str(e)}",
            'exit_code': -1,
            'execution_time': 0,
            'status': 'security_error'
        }
    except Exception as e:
        return {
            'stdout': '',
            'stderr': f"Execution Error: {str(e)}",
            'exit_code': -1,
            'execution_time': 0,
            'status': 'error'
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Code provided as argument
        code = sys.argv[1]
        stdin_input = sys.argv[2] if len(sys.argv) > 2 else ''
    else:
        # Read from main.py file
        try:
            with open('/workspace/main.py', 'r') as f:
                code = f.read()
            stdin_input = ''
        except FileNotFoundError:
            print("Error: No code file found", file=sys.stderr)
            sys.exit(1)
    
    result = execute_python_code(code, stdin_input)
    
    # Output results
    print(result['stdout'], end='')
    if result['stderr']:
        print(result['stderr'], file=sys.stderr)
    
    sys.exit(result['exit_code'])