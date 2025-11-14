#!/usr/bin/env node
/**
 * JavaScript code execution script for GhostIDE
 * Executes user code with security restrictions
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

function executeCode() {
    let code = '';
    
    // Read code from stdin
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
        code += chunk;
    });
    
    process.stdin.on('end', () => {
        try {
            // Create temporary file for code
            const tempFile = path.join(os.tmpdir(), `code_${Date.now()}.js`);
            fs.writeFileSync(tempFile, code);
            
            // Execute the code with timeout
            const child = spawn('node', [tempFile], {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: '/tmp',
                timeout: 30000 // 30 second timeout
            });
            
            child.stdout.on('data', (data) => {
                process.stdout.write(data);
            });
            
            child.stderr.on('data', (data) => {
                process.stderr.write(data);
            });
            
            child.on('close', (code) => {
                // Clean up temporary file
                try {
                    fs.unlinkSync(tempFile);
                } catch (e) {
                    // Ignore cleanup errors
                }
                process.exit(code);
            });
            
            child.on('error', (error) => {
                console.error(`Error: ${error.message}`);
                process.exit(1);
            });
            
        } catch (error) {
            console.error(`Error: ${error.message}`);
            process.exit(1);
        }
    });
}

// Set timeout for the entire process
setTimeout(() => {
    console.error('Error: Code execution timed out (30 seconds)');
    process.exit(1);
}, 30000);

executeCode();