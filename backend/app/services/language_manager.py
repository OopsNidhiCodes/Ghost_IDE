"""
Language Manager Service for GhostIDE
Handles language configurations, templates, validation, and Docker container management
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LanguageType(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"


@dataclass
class CompilerConfig:
    """Configuration for language compiler/interpreter"""
    command: str
    args: List[str]
    compile_command: Optional[str] = None
    compile_args: Optional[List[str]] = None
    timeout: int = 30
    memory_limit: str = "128m"
    cpu_quota: int = 50000


@dataclass
class ValidationRule:
    """Validation rule for code"""
    pattern: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ErrorPattern:
    """Pattern for parsing language-specific errors"""
    pattern: str
    line_group: int
    message_group: int
    type_group: Optional[int] = None


@dataclass
class LanguageConfig:
    """Complete language configuration"""
    name: str
    extension: str
    monaco_language: str
    icon: str
    color: str
    docker_image: str
    dockerfile: str
    compiler_config: CompilerConfig
    validation_rules: List[ValidationRule]
    error_patterns: List[ErrorPattern]
    template: str
    examples: List[Dict[str, str]]
    file_patterns: List[str]  # For file detection
    mime_types: List[str]  # For file detection


class LanguageManager:
    """Service for managing programming language configurations and operations"""
    
    def __init__(self):
        self._languages = self._initialize_languages()
    
    def _initialize_languages(self) -> Dict[str, LanguageConfig]:
        """Initialize all supported language configurations"""
        return {
            LanguageType.PYTHON: LanguageConfig(
                name="Python",
                extension=".py",
                monaco_language="python",
                icon="🐍",
                color="#3776ab",
                docker_image="ghostide-python",
                dockerfile="python.Dockerfile",
                compiler_config=CompilerConfig(
                    command="python3",
                    args=["-u", "/tmp/code.py"],
                    timeout=30,
                    memory_limit="128m",
                    cpu_quota=50000
                ),
                validation_rules=[
                    # Docker containers provide isolation, only block code injection
                    ValidationRule(
                        pattern=r'eval\s*\(',
                        message="eval() function is dangerous and not allowed",
                        severity="error"
                    ),
                    ValidationRule(
                        pattern=r'\bexec\s*\(',
                        message="exec() function is dangerous and not allowed",
                        severity="error"
                    )
                ],
                error_patterns=[
                    ErrorPattern(
                        pattern=r'File ".*", line (\d+).*\n.*\n(\w+Error: .+)',
                        line_group=1,
                        message_group=2,
                        type_group=2
                    ),
                    ErrorPattern(
                        pattern=r'line (\d+).*\n.*\n(SyntaxError: .+)',
                        line_group=1,
                        message_group=2,
                        type_group=2
                    )
                ],
                template="""# Welcome to the haunted Python realm 👻
print("Hello, mortal! The spirits are watching...")

# The ghosts whisper: "Write your spooky code here"
def summon_spirits():
    spirits = ["Casper", "Boo", "Phantom"]
    for spirit in spirits:
        print(f"👻 {spirit} has been summoned!")

# Invoke the supernatural
summon_spirits()
""",
                examples=[
                    {
                        "name": "Hello World",
                        "description": "A simple greeting from the spirit world",
                        "code": 'print("Greetings from the ghostly realm! 👻")'
                    },
                    {
                        "name": "Spooky Calculator",
                        "description": "A calculator with supernatural powers",
                        "code": """# Supernatural Calculator 🔮
def ghostly_add(a, b):
    result = a + b
    print(f"The spirits calculate: {a} + {b} = {result}")
    return result

def phantom_multiply(a, b):
    result = a * b
    print(f"The phantoms multiply: {a} × {b} = {result}")
    return result

# Test the supernatural math
ghostly_add(13, 7)
phantom_multiply(6, 7)
"""
                    },
                    {
                        "name": "Haunted List",
                        "description": "A list that manages ghostly entities",
                        "code": """# Haunted Entity Manager 👻
class GhostlyList:
    def __init__(self):
        self.spirits = []
    
    def summon(self, spirit_name):
        self.spirits.append(spirit_name)
        print(f"👻 {spirit_name} has been summoned!")
    
    def banish(self, spirit_name):
        if spirit_name in self.spirits:
            self.spirits.remove(spirit_name)
            print(f"💨 {spirit_name} has been banished!")
        else:
            print(f"🔍 {spirit_name} is not in this realm...")
    
    def list_spirits(self):
        if self.spirits:
            print("Current spirits in the realm:")
            for i, spirit in enumerate(self.spirits, 1):
                print(f"  {i}. 👻 {spirit}")
        else:
            print("The realm is empty... for now.")

# Create a haunted realm
realm = GhostlyList()
realm.summon("Casper")
realm.summon("Boo")
realm.list_spirits()
realm.banish("Casper")
realm.list_spirits()
"""
                    }
                ],
                file_patterns=["*.py", "*.pyw"],
                mime_types=["text/x-python", "application/x-python-code"]
            ),
            
            LanguageType.JAVASCRIPT: LanguageConfig(
                name="JavaScript",
                extension=".js",
                monaco_language="javascript",
                icon="⚡",
                color="#f7df1e",
                docker_image="ghostide-javascript",
                dockerfile="javascript.Dockerfile",
                compiler_config=CompilerConfig(
                    command="node",
                    args=["/tmp/code.js"],
                    timeout=30,
                    memory_limit="128m",
                    cpu_quota=50000
                ),
                validation_rules=[
                    # Docker containers provide isolation, only block truly dangerous operations
                    ValidationRule(
                        pattern=r'eval\s*\(',
                        message="eval() function is dangerous and not allowed",
                        severity="error"
                    )
                ],
                error_patterns=[
                    ErrorPattern(
                        pattern=r'(\w+Error): (.+)\n.*at.*:(\d+):',
                        line_group=3,
                        message_group=2,
                        type_group=1
                    ),
                    ErrorPattern(
                        pattern=r'SyntaxError: (.+)\n.*at.*:(\d+):',
                        line_group=2,
                        message_group=1,
                        type_group=None
                    )
                ],
                template="""// The ghostly JavaScript realm awaits ⚡
console.log("Welcome to the spectral console... 👻");

// The spirits whisper JavaScript secrets
function summonSpectralFunction() {
    const ghosts = ["Phantom", "Wraith", "Specter"];
    
    ghosts.forEach((ghost, index) => {
        setTimeout(() => {
            console.log(`👻 ${ghost} materializes from the void...`);
        }, (index + 1) * 1000);
    });
}

// Invoke the supernatural
summonSpectralFunction();
console.log("The ritual has begun... ⚡");
""",
                examples=[
                    {
                        "name": "Spectral Greeting",
                        "description": "A haunting hello from the JavaScript realm",
                        "code": 'console.log("Greetings from the JavaScript netherworld! ⚡👻");'
                    },
                    {
                        "name": "Phantom Array",
                        "description": "An array that holds ghostly entities",
                        "code": """// Phantom Array Manager 👻
const phantomArray = [];

function materialize(entity) {
    phantomArray.push(entity);
    console.log(`👻 ${entity} has materialized! Current spirits: ${phantomArray.length}`);
}

function vanish(entity) {
    const index = phantomArray.indexOf(entity);
    if (index > -1) {
        phantomArray.splice(index, 1);
        console.log(`💨 ${entity} has vanished! Remaining spirits: ${phantomArray.length}`);
    } else {
        console.log(`🔍 ${entity} was never here...`);
    }
}

function listSpirits() {
    if (phantomArray.length > 0) {
        console.log("Current phantoms in the array:");
        phantomArray.forEach((spirit, index) => {
            console.log(`  ${index + 1}. 👻 ${spirit}`);
        });
    } else {
        console.log("The array is empty... eerily quiet.");
    }
}

// Test the phantom array
materialize("Casper");
materialize("Boo");
listSpirits();
vanish("Casper");
listSpirits();
"""
                    }
                ],
                file_patterns=["*.js", "*.mjs"],
                mime_types=["application/javascript", "text/javascript"]
            ),
            
            LanguageType.JAVA: LanguageConfig(
                name="Java",
                extension=".java",
                monaco_language="java",
                icon="☕",
                color="#ed8b00",
                docker_image="ghostide-java",
                dockerfile="java.Dockerfile",
                compiler_config=CompilerConfig(
                    command="java",
                    args=["Main"],
                    compile_command="javac",
                    compile_args=["/tmp/Main.java"],
                    timeout=45,  # Java needs more time for compilation
                    memory_limit="256m",  # Java needs more memory
                    cpu_quota=75000
                ),
                validation_rules=[
                    ValidationRule(
                        pattern=r'import\s+java\.io\.File',
                        message="File I/O operations are restricted for security reasons",
                        severity="warning"
                    ),
                    ValidationRule(
                        pattern=r'import\s+java\.lang\.Runtime',
                        message="Runtime operations are not allowed for security reasons",
                        severity="error"
                    ),
                    ValidationRule(
                        pattern=r'import\s+java\.lang\.ProcessBuilder',
                        message="Process operations are not allowed for security reasons",
                        severity="error"
                    ),
                    ValidationRule(
                        pattern=r'System\.exit\s*\(',
                        message="System.exit() is not allowed in this environment",
                        severity="error"
                    ),
                    ValidationRule(
                        pattern=r'class\s+(?!Main\b)\w+\s*\{',
                        message="Please use 'Main' as your class name for proper execution",
                        severity="warning"
                    )
                ],
                error_patterns=[
                    ErrorPattern(
                        pattern=r'Main\.java:(\d+): error: (.+)',
                        line_group=1,
                        message_group=2,
                        type_group=None
                    ),
                    ErrorPattern(
                        pattern=r'Exception in thread "main" (\w+): (.+)\n\s+at Main\.main\(Main\.java:(\d+)\)',
                        line_group=3,
                        message_group=2,
                        type_group=1
                    )
                ],
                template="""// Enter the haunted halls of Java ☕
public class Main {
    public static void main(String[] args) {
        System.out.println("The ancient Java spirits have awakened... ☕👻");
        
        // The ghostly compiler whispers: "Write your cursed code here"
        summonJavaSpirits();
    }
    
    public static void summonJavaSpirits() {
        String[] spirits = {"Phantom", "Wraith", "Specter"};
        
        System.out.println("Summoning Java spirits:");
        for (int i = 0; i < spirits.length; i++) {
            System.out.println("👻 " + spirits[i] + " has been invoked!");
        }
    }
}
""",
                examples=[
                    {
                        "name": "Haunted Hello",
                        "description": "A spectral greeting in Java",
                        "code": """public class Main {
    public static void main(String[] args) {
        System.out.println("Greetings from the Java underworld! ☕👻");
    }
}"""
                    },
                    {
                        "name": "Ghostly Calculator",
                        "description": "A calculator possessed by Java spirits",
                        "code": """public class Main {
    public static void main(String[] args) {
        GhostlyCalculator calc = new GhostlyCalculator();
        
        calc.hauntedAdd(13, 7);
        calc.spectralMultiply(6, 7);
        calc.phantomDivide(42, 6);
    }
    
    static class GhostlyCalculator {
        public void hauntedAdd(int a, int b) {
            int result = a + b;
            System.out.println("👻 The spirits calculate: " + a + " + " + b + " = " + result);
        }
        
        public void spectralMultiply(int a, int b) {
            int result = a * b;
            System.out.println("🔮 The phantoms multiply: " + a + " × " + b + " = " + result);
        }
        
        public void phantomDivide(int a, int b) {
            if (b != 0) {
                double result = (double) a / b;
                System.out.println("⚡ The wraiths divide: " + a + " ÷ " + b + " = " + result);
            } else {
                System.out.println("💀 Division by zero summons the void!");
            }
        }
    }
}"""
                    }
                ],
                file_patterns=["*.java"],
                mime_types=["text/x-java-source"]
            ),
            
            LanguageType.CPP: LanguageConfig(
                name="C++",
                extension=".cpp",
                monaco_language="cpp",
                icon="⚙️",
                color="#00599c",
                docker_image="ghostide-cpp",
                dockerfile="cpp.Dockerfile",
                compiler_config=CompilerConfig(
                    command="./program",
                    args=[],
                    compile_command="g++",
                    compile_args=["-o", "/tmp/program", "/tmp/code.cpp", "-std=c++17"],
                    timeout=45,
                    memory_limit="256m",
                    cpu_quota=75000
                ),
                validation_rules=[
                    # Docker containers provide isolation, only block actual system calls
                    ValidationRule(
                        pattern=r'\bsystem\s*\(',
                        message="System calls are not allowed for security reasons",
                        severity="error"
                    ),
                    ValidationRule(
                        pattern=r'exit\s*\(',
                        message="exit() function is not recommended in this environment",
                        severity="warning"
                    )
                ],
                error_patterns=[
                    ErrorPattern(
                        pattern=r'code\.cpp:(\d+):.*error: (.+)',
                        line_group=1,
                        message_group=2,
                        type_group=None
                    ),
                    ErrorPattern(
                        pattern=r'code\.cpp:(\d+):.*warning: (.+)',
                        line_group=1,
                        message_group=2,
                        type_group=None
                    )
                ],
                template="""// Welcome to the haunted C++ catacombs ⚙️
#include <iostream>
#include <vector>
#include <string>

using namespace std;

int main() {
    cout << "The ancient C++ spirits stir... ⚙️👻" << endl;
    
    // The ghostly compiler whispers: "Write your spectral code here"
    vector<string> spirits = {"Phantom", "Wraith", "Specter"};
    
    cout << "Summoning C++ spirits:" << endl;
    for (const auto& spirit : spirits) {
        cout << "👻 " << spirit << " has been compiled into existence!" << endl;
    }
    
    return 0;
}
""",
                examples=[
                    {
                        "name": "Spectral Greeting",
                        "description": "A haunting hello from the C++ realm",
                        "code": """#include <iostream>
using namespace std;

int main() {
    cout << "Greetings from the C++ underworld! ⚙️👻" << endl;
    return 0;
}"""
                    },
                    {
                        "name": "Haunted Vector",
                        "description": "A vector container possessed by C++ spirits",
                        "code": """#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

using namespace std;

class HauntedVector {
private:
    vector<string> spirits;
    
public:
    void summon(const string& spirit) {
        spirits.push_back(spirit);
        cout << "👻 " << spirit << " has been summoned! Total spirits: " << spirits.size() << endl;
    }
    
    void banish(const string& spirit) {
        auto it = find(spirits.begin(), spirits.end(), spirit);
        if (it != spirits.end()) {
            spirits.erase(it);
            cout << "💨 " << spirit << " has been banished! Remaining: " << spirits.size() << endl;
        } else {
            cout << "🔍 " << spirit << " was never here..." << endl;
        }
    }
    
    void listSpirits() {
        if (spirits.empty()) {
            cout << "The vector is empty... eerily quiet." << endl;
        } else {
            cout << "Current spirits in the haunted vector:" << endl;
            for (size_t i = 0; i < spirits.size(); ++i) {
                cout << "  " << (i + 1) << ". 👻 " << spirits[i] << endl;
            }
        }
    }
};

int main() {
    HauntedVector hauntedVec;
    
    hauntedVec.summon("Casper");
    hauntedVec.summon("Boo");
    hauntedVec.listSpirits();
    hauntedVec.banish("Casper");
    hauntedVec.listSpirits();
    
    return 0;
}"""
                    }
                ],
                file_patterns=["*.cpp", "*.cxx", "*.cc", "*.C"],
                mime_types=["text/x-c++src", "text/x-c++"]
            )
        }
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages"""
        return list(self._languages.keys())
    
    def get_language_config(self, language: str) -> Optional[LanguageConfig]:
        """Get configuration for a specific language"""
        return self._languages.get(language)
    
    def get_all_language_configs(self) -> Dict[str, LanguageConfig]:
        """Get all language configurations"""
        return self._languages.copy()
    
    def detect_language_from_filename(self, filename: str) -> Optional[str]:
        """Detect programming language from filename"""
        filename_lower = filename.lower()
        
        for lang_key, config in self._languages.items():
            # Check extension
            if filename_lower.endswith(config.extension):
                return lang_key
            
            # Check file patterns
            for pattern in config.file_patterns:
                if self._match_pattern(filename_lower, pattern.lower()):
                    return lang_key
        
        return None
    
    def detect_language_from_content(self, content: str) -> Optional[str]:
        """Detect programming language from code content"""
        content_lines = content.strip().split('\n')[:10]  # Check first 10 lines
        content_sample = '\n'.join(content_lines)
        
        # Language-specific patterns
        patterns = {
            LanguageType.PYTHON: [
                r'^\s*def\s+\w+\s*\(',
                r'^\s*import\s+\w+',
                r'^\s*from\s+\w+\s+import',
                r'^\s*print\s*\(',
                r'^\s*if\s+__name__\s*==\s*[\'"]__main__[\'"]',
            ],
            LanguageType.JAVASCRIPT: [
                r'^\s*function\s+\w+\s*\(',
                r'^\s*const\s+\w+\s*=',
                r'^\s*let\s+\w+\s*=',
                r'^\s*var\s+\w+\s*=',
                r'console\.log\s*\(',
                r'^\s*\/\/.*',
            ],
            LanguageType.JAVA: [
                r'^\s*public\s+class\s+\w+',
                r'^\s*public\s+static\s+void\s+main',
                r'^\s*import\s+java\.',
                r'System\.out\.print',
                r'^\s*\/\*\*.*\*\/',
            ],
            LanguageType.CPP: [
                r'^\s*#include\s*<.*>',
                r'^\s*using\s+namespace\s+std',
                r'^\s*int\s+main\s*\(',
                r'std::cout',
                r'cout\s*<<',
                r'^\s*\/\/.*',
            ]
        }
        
        scores = {}
        for lang, lang_patterns in patterns.items():
            score = 0
            for pattern in lang_patterns:
                if re.search(pattern, content_sample, re.MULTILINE | re.IGNORECASE):
                    score += 1
            scores[lang] = score
        
        # Return language with highest score, if any
        if scores:
            best_lang = max(scores, key=scores.get)
            if scores[best_lang] > 0:
                return best_lang
        
        return None
    
    def validate_code(self, code: str, language: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate code against language-specific rules
        Returns (is_valid, list_of_issues)
        """
        config = self.get_language_config(language)
        if not config:
            return False, [{"severity": "error", "message": f"Unsupported language: {language}"}]
        
        if not code or not code.strip():
            return False, [{"severity": "error", "message": "Code cannot be empty"}]
        
        # Check code length (max 100KB)
        if len(code.encode('utf-8')) > 100 * 1024:
            return False, [{"severity": "error", "message": "Code is too large (max 100KB)"}]
        
        issues = []
        
        # Apply validation rules
        for rule in config.validation_rules:
            matches = re.finditer(rule.pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append({
                    "severity": rule.severity,
                    "message": rule.message,
                    "line": line_num,
                    "pattern": rule.pattern
                })
        
        # Language-specific validation
        if language == LanguageType.JAVA:
            if 'class Main' not in code and 'public class Main' not in code:
                issues.append({
                    "severity": "error",
                    "message": "Java code must contain a 'public class Main' with a main method",
                    "line": 1
                })
        
        # Check if there are any errors
        has_errors = any(issue["severity"] == "error" for issue in issues)
        return not has_errors, issues
    
    def parse_error_message(self, error_output: str, language: str) -> Dict[str, Any]:
        """Parse language-specific error messages to extract line numbers and details"""
        config = self.get_language_config(language)
        if not config:
            return {"message": error_output, "line": None, "type": "unknown"}
        
        for pattern in config.error_patterns:
            match = re.search(pattern.pattern, error_output, re.MULTILINE | re.DOTALL)
            if match:
                try:
                    line_num = int(match.group(pattern.line_group)) if pattern.line_group else None
                    message = match.group(pattern.message_group) if pattern.message_group else error_output
                    error_type = match.group(pattern.type_group) if pattern.type_group else "Error"
                    
                    return {
                        "message": message.strip(),
                        "line": line_num,
                        "type": error_type,
                        "formatted": f"Line {line_num}: {error_type}: {message.strip()}" if line_num else f"{error_type}: {message.strip()}"
                    }
                except (ValueError, IndexError):
                    continue
        
        # Fallback: return original error
        return {
            "message": error_output.strip(),
            "line": None,
            "type": "Error",
            "formatted": error_output.strip()
        }
    
    def get_language_template(self, language: str) -> Optional[str]:
        """Get template code for a specific language"""
        config = self.get_language_config(language)
        return config.template if config else None
    
    def get_language_examples(self, language: str) -> List[Dict[str, str]]:
        """Get example code snippets for a specific language"""
        config = self.get_language_config(language)
        return config.examples if config else []
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Match text against a glob-like pattern"""
        # Convert glob pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.match(f'^{regex_pattern}$', text))


# Global instance
language_manager = LanguageManager()