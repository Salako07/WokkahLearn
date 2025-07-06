#!/usr/bin/env node

/**
 * Secure Node.js code runner with timeout and resource limits
 */

const fs = require('fs');
const vm = require('vm');
const path = require('path');

// Security configuration
const BLOCKED_MODULES = [
    'fs', 'child_process', 'cluster', 'dgram', 'dns', 'http', 'https',
    'net', 'os', 'process', 'repl', 'tls', 'worker_threads'
];

const MAX_EXECUTION_TIME = parseInt(process.env.MAX_EXECUTION_TIME || '30') * 1000;
const MAX_MEMORY_MB = parseInt(process.env.MAX_MEMORY_MB || '128');

class SecurityError extends Error {
    constructor(message) {
        super(message);
        this.name = 'SecurityError';
    }
}

class TimeoutError extends Error {
    constructor(message) {
        super(message);
        this.name = 'TimeoutError';
    }
}

function validateCode(code) {
    // Check for blocked modules
    for (const module of BLOCKED_MODULES) {
        const patterns = [
            `require('${module}')`,
            `require("${module}")`,
            `import.*from.*['"]${module}['"]`,
            `import.*${module}.*from`
        ];
        
        for (const pattern of patterns) {
            if (new RegExp(pattern).test(code)) {
                throw new SecurityError(`Module '${module}' is not allowed`);
            }
        }
    }
    
    // Check for dangerous functions
    const dangerousPatterns = [
        /eval\s*\(/,
        /Function\s*\(/,
        /setTimeout\s*\(/,
        /setInterval\s*\(/,
        /process\./,
        /global\./,
        /__dirname/,
        /__filename/
    ];
    
    for (const pattern of dangerousPatterns) {
        if (pattern.test(code)) {
            throw new SecurityError(`Dangerous pattern detected: ${pattern}`);
        }
    }
    
    return true;
}

function createSandbox() {
    // Create safe console object
    const safeConsole = {
        log: (...args) => console.log(...args),
        error: (...args) => console.error(...args),
        warn: (...args) => console.warn(...args),
        info: (...args) => console.info(...args)
    };
    
    // Create safe Math object
    const safeMath = Object.freeze({ ...Math });
    
    // Create safe Date object
    const safeDate = Date;
    
    // Create safe JSON object
    const safeJSON = Object.freeze({ ...JSON });
    
    // Create sandbox context
    return {
        console: safeConsole,
        Math: safeMath,
        Date: safeDate,
        JSON: safeJSON,
        parseInt,
        parseFloat,
        isNaN,
        isFinite,
        encodeURIComponent,
        decodeURIComponent,
        encodeURI,
        decodeURI,
        Array,
        Object,
        String,
        Number,
        Boolean,
        RegExp,
        Error,
        TypeError,
        RangeError,
        SyntaxError,
        ReferenceError,
        // Safe require function
        require: (moduleName) => {
            if (BLOCKED_MODULES.includes(moduleName)) {
                throw new SecurityError(`Module '${moduleName}' is not allowed`);
            }
            try {
                return require(moduleName);
            } catch (err) {
                throw new Error(`Module '${moduleName}' not found or not allowed`);
            }
        }
    };
}

function executeNodeCode(code, stdinInput = '') {
    try {
        // Validate code
        validateCode(code);
        
        // Create sandbox
        const sandbox = createSandbox();
        
        // Set up stdin simulation
        if (stdinInput) {
            const lines = stdinInput.split('\n');
            let lineIndex = 0;
            
            // Mock readline functionality
            sandbox.readline = () => {
                return lineIndex < lines.length ? lines[lineIndex++] : null;
            };
        }
        
        // Track execution
        const startTime = Date.now();
        let output = '';
        let errorOutput = '';
        
        // Capture console output
        const originalConsoleLog = sandbox.console.log;
        const originalConsoleError = sandbox.console.error;
        
        sandbox.console.log = (...args) => {
            output += args.join(' ') + '\n';
        };
        
        sandbox.console.error = (...args) => {
            errorOutput += args.join(' ') + '\n';
        };
        
        // Execute with timeout
        const script = new vm.Script(code, {
            filename: 'user_code.js',
            timeout: MAX_EXECUTION_TIME
        });
        
        const context = vm.createContext(sandbox);
        script.runInContext(context, {
            timeout: MAX_EXECUTION_TIME
        });
        
        const executionTime = (Date.now() - startTime) / 1000;
        
        return {
            stdout: output,
            stderr: errorOutput,
            exit_code: 0,
            execution_time: executionTime,
            status: 'completed'
        };
        
    } catch (error) {
        const executionTime = (Date.now() - startTime) / 1000;
        
        if (error.name === 'TimeoutError' || error.code === 'ERR_SCRIPT_EXECUTION_TIMEOUT') {
            return {
                stdout: '',
                stderr: `Execution timed out after ${MAX_EXECUTION_TIME/1000} seconds`,
                exit_code: -1,
                execution_time: MAX_EXECUTION_TIME/1000,
                status: 'timeout'
            };
        } else if (error.name === 'SecurityError') {
            return {
                stdout: '',
                stderr: `Security Error: ${error.message}`,
                exit_code: -1,
                execution_time: executionTime,
                status: 'security_error'
            };
        } else {
            return {
                stdout: '',
                stderr: `Error: ${error.message}`,
                exit_code: -1,
                execution_time: executionTime,
                status: 'error'
            };
        }
    }
}

// Main execution
if (require.main === module) {
    let code, stdinInput;
    
    if (process.argv.length > 2) {
        // Code provided as argument
        code = process.argv[2];
        stdinInput = process.argv[3] || '';
    } else {
        // Read from main.js file
        try {
            code = fs.readFileSync('/workspace/main.js', 'utf8');
            stdinInput = '';
        } catch (err) {
            console.error('Error: No code file found');
            process.exit(1);
        }
    }
    
    const result = executeNodeCode(code, stdinInput);
    
    // Output results
    process.stdout.write(result.stdout);
    if (result.stderr) {
        process.stderr.write(result.stderr);
    }
    
    process.exit(result.exit_code);
}

module.exports = { executeNodeCode, validateCode };