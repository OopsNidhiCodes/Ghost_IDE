"""
Unit tests for Language Manager Service
"""

import pytest
from app.services.language_manager import LanguageManager, LanguageType


class TestLanguageManager:
    """Test cases for LanguageManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.language_manager = LanguageManager()
    
    def test_get_supported_languages(self):
        """Test getting list of supported languages"""
        languages = self.language_manager.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert LanguageType.PYTHON in languages
        assert LanguageType.JAVASCRIPT in languages
        assert LanguageType.JAVA in languages
        assert LanguageType.CPP in languages
    
    def test_get_language_config_valid(self):
        """Test getting configuration for valid language"""
        config = self.language_manager.get_language_config(LanguageType.PYTHON)
        
        assert config is not None
        assert config.name == "Python"
        assert config.extension == ".py"
        assert config.monaco_language == "python"
        assert config.icon == "🐍"
        assert config.docker_image == "ghostide-python"
        assert len(config.validation_rules) > 0
        assert len(config.examples) > 0
    
    def test_get_language_config_invalid(self):
        """Test getting configuration for invalid language"""
        config = self.language_manager.get_language_config("invalid_language")
        assert config is None
    
    def test_detect_language_from_filename(self):
        """Test language detection from filename"""
        # Test Python files
        assert self.language_manager.detect_language_from_filename("test.py") == LanguageType.PYTHON
        assert self.language_manager.detect_language_from_filename("script.pyw") == LanguageType.PYTHON
        
        # Test JavaScript files
        assert self.language_manager.detect_language_from_filename("app.js") == LanguageType.JAVASCRIPT
        assert self.language_manager.detect_language_from_filename("module.mjs") == LanguageType.JAVASCRIPT
        
        # Test Java files
        assert self.language_manager.detect_language_from_filename("Main.java") == LanguageType.JAVA
        
        # Test C++ files
        assert self.language_manager.detect_language_from_filename("program.cpp") == LanguageType.CPP
        assert self.language_manager.detect_language_from_filename("code.cxx") == LanguageType.CPP
        
        # Test unknown files
        assert self.language_manager.detect_language_from_filename("unknown.xyz") is None
        assert self.language_manager.detect_language_from_filename("") is None
    
    def test_detect_language_from_content_python(self):
        """Test Python language detection from content"""
        python_code = """
def hello_world():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
"""
        assert self.language_manager.detect_language_from_content(python_code) == LanguageType.PYTHON
        
        # Test with imports
        python_import = "import os\nfrom datetime import datetime"
        assert self.language_manager.detect_language_from_content(python_import) == LanguageType.PYTHON
    
    def test_detect_language_from_content_javascript(self):
        """Test JavaScript language detection from content"""
        js_code = """
function helloWorld() {
    console.log("Hello, World!");
}

const message = "Hello";
let count = 0;
"""
        assert self.language_manager.detect_language_from_content(js_code) == LanguageType.JAVASCRIPT
    
    def test_detect_language_from_content_java(self):
        """Test Java language detection from content"""
        java_code = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
        assert self.language_manager.detect_language_from_content(java_code) == LanguageType.JAVA
    
    def test_detect_language_from_content_cpp(self):
        """Test C++ language detection from content"""
        cpp_code = """
#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}
"""
        assert self.language_manager.detect_language_from_content(cpp_code) == LanguageType.CPP
    
    def test_detect_language_from_content_unknown(self):
        """Test unknown language detection from content"""
        unknown_code = "This is just plain text with no programming patterns."
        assert self.language_manager.detect_language_from_content(unknown_code) is None
    
    def test_validate_code_python_valid(self):
        """Test Python code validation - valid code"""
        valid_code = """
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
"""
        is_valid, issues = self.language_manager.validate_code(valid_code, LanguageType.PYTHON)
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_code_python_security_issues(self):
        """Test Python code validation - security issues"""
        dangerous_code = """
import os
import subprocess
eval("print('dangerous')")
exec("print('also dangerous')")
"""
        is_valid, issues = self.language_manager.validate_code(dangerous_code, LanguageType.PYTHON)
        assert is_valid is False
        assert len(issues) > 0
        
        # Check that all issues are errors
        error_issues = [issue for issue in issues if issue["severity"] == "error"]
        assert len(error_issues) > 0
    
    def test_validate_code_python_warnings(self):
        """Test Python code validation - warnings"""
        warning_code = """
with open("file.txt", "r") as f:
    content = f.read()

name = input("Enter your name: ")
print(f"Hello, {name}!")
"""
        is_valid, issues = self.language_manager.validate_code(warning_code, LanguageType.PYTHON)
        assert is_valid is True  # Should be valid despite warnings
        assert len(issues) > 0
        
        # Check that issues are warnings
        warning_issues = [issue for issue in issues if issue["severity"] == "warning"]
        assert len(warning_issues) > 0
    
    def test_validate_code_java_valid(self):
        """Test Java code validation - valid code"""
        valid_code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
        is_valid, issues = self.language_manager.validate_code(valid_code, LanguageType.JAVA)
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_code_java_missing_main_class(self):
        """Test Java code validation - missing Main class"""
        invalid_code = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
        is_valid, issues = self.language_manager.validate_code(invalid_code, LanguageType.JAVA)
        assert is_valid is False
        assert len(issues) > 0
        
        # Check for Main class error
        main_class_errors = [issue for issue in issues if "Main" in issue["message"]]
        assert len(main_class_errors) > 0
    
    def test_validate_code_empty(self):
        """Test validation of empty code"""
        is_valid, issues = self.language_manager.validate_code("", LanguageType.PYTHON)
        assert is_valid is False
        assert len(issues) > 0
        assert "empty" in issues[0]["message"].lower()
    
    def test_validate_code_too_large(self):
        """Test validation of code that's too large"""
        large_code = "# " + "x" * (100 * 1024 + 1)  # Over 100KB
        is_valid, issues = self.language_manager.validate_code(large_code, LanguageType.PYTHON)
        assert is_valid is False
        assert len(issues) > 0
        assert "too large" in issues[0]["message"].lower()
    
    def test_validate_code_unsupported_language(self):
        """Test validation of unsupported language"""
        is_valid, issues = self.language_manager.validate_code("print('hello')", "unsupported")
        assert is_valid is False
        assert len(issues) > 0
        assert "unsupported" in issues[0]["message"].lower()
    
    def test_parse_error_message_python(self):
        """Test Python error message parsing"""
        python_error = '''File "/tmp/code.py", line 5, in <module>
    print(undefined_variable)
NameError: name 'undefined_variable' is not defined'''
        
        parsed = self.language_manager.parse_error_message(python_error, LanguageType.PYTHON)
        assert parsed["line"] == 5
        assert "NameError" in parsed["type"]
        assert "undefined_variable" in parsed["message"]
        assert "Line 5" in parsed["formatted"]
    
    def test_parse_error_message_java(self):
        """Test Java error message parsing"""
        java_error = "Main.java:3: error: cannot find symbol"
        
        parsed = self.language_manager.parse_error_message(java_error, LanguageType.JAVA)
        assert parsed["line"] == 3
        assert "cannot find symbol" in parsed["message"]
    
    def test_parse_error_message_cpp(self):
        """Test C++ error message parsing"""
        cpp_error = "code.cpp:5:10: error: 'undefined' was not declared in this scope"
        
        parsed = self.language_manager.parse_error_message(cpp_error, LanguageType.CPP)
        assert parsed["line"] == 5
        assert "undefined" in parsed["message"]
    
    def test_parse_error_message_unknown_format(self):
        """Test parsing of unknown error format"""
        unknown_error = "Some unknown error format"
        
        parsed = self.language_manager.parse_error_message(unknown_error, LanguageType.PYTHON)
        assert parsed["line"] is None
        assert parsed["message"] == unknown_error.strip()
        assert parsed["type"] == "Error"
    
    def test_get_language_template(self):
        """Test getting language template"""
        template = self.language_manager.get_language_template(LanguageType.PYTHON)
        assert template is not None
        assert isinstance(template, str)
        assert len(template) > 0
        assert "python" in template.lower() or "print" in template.lower()
        
        # Test invalid language
        assert self.language_manager.get_language_template("invalid") is None
    
    def test_get_language_examples(self):
        """Test getting language examples"""
        examples = self.language_manager.get_language_examples(LanguageType.PYTHON)
        assert isinstance(examples, list)
        assert len(examples) > 0
        
        # Check example structure
        for example in examples:
            assert "name" in example
            assert "description" in example
            assert "code" in example
            assert isinstance(example["name"], str)
            assert isinstance(example["description"], str)
            assert isinstance(example["code"], str)
        
        # Test invalid language
        assert self.language_manager.get_language_examples("invalid") == []
    
    def test_get_all_language_configs(self):
        """Test getting all language configurations"""
        configs = self.language_manager.get_all_language_configs()
        assert isinstance(configs, dict)
        assert len(configs) > 0
        
        # Check that all supported languages are included
        supported_languages = self.language_manager.get_supported_languages()
        for lang in supported_languages:
            assert lang in configs
            assert configs[lang] is not None


class TestLanguageManagerIntegration:
    """Integration tests for LanguageManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.language_manager = LanguageManager()
    
    def test_full_workflow_python(self):
        """Test complete workflow for Python"""
        # 1. Detect language from filename
        detected = self.language_manager.detect_language_from_filename("test.py")
        assert detected == LanguageType.PYTHON
        
        # 2. Get language config
        config = self.language_manager.get_language_config(detected)
        assert config is not None
        assert config.name == "Python"
        
        # 3. Get template
        template = self.language_manager.get_language_template(detected)
        assert template is not None
        
        # 4. Validate template code
        is_valid, issues = self.language_manager.validate_code(template, detected)
        assert is_valid is True
        
        # 5. Get examples
        examples = self.language_manager.get_language_examples(detected)
        assert len(examples) > 0
        
        # 6. Validate example code
        for example in examples:
            is_valid, issues = self.language_manager.validate_code(example["code"], detected)
            # Examples should be valid (may have warnings but no errors)
            error_issues = [issue for issue in issues if issue["severity"] == "error"]
            assert len(error_issues) == 0
    
    def test_file_upload_simulation(self):
        """Test simulating file upload with language detection"""
        test_files = [
            ("hello.py", "print('Hello, World!')"),
            ("app.js", "console.log('Hello, World!');"),
            ("Main.java", "public class Main { public static void main(String[] args) { System.out.println(\"Hello\"); } }"),
            ("program.cpp", "#include <iostream>\nint main() { std::cout << \"Hello\"; return 0; }")
        ]
        
        for filename, content in test_files:
            # Detect from filename
            lang_from_name = self.language_manager.detect_language_from_filename(filename)
            assert lang_from_name is not None
            
            # Detect from content
            lang_from_content = self.language_manager.detect_language_from_content(content)
            
            # Should match or content detection should work
            assert lang_from_name == lang_from_content or lang_from_content is not None
            
            # Use filename detection as primary
            detected_lang = lang_from_name
            
            # Validate the content
            is_valid, issues = self.language_manager.validate_code(content, detected_lang)
            # Simple hello world examples should be valid
            error_issues = [issue for issue in issues if issue["severity"] == "error"]
            assert len(error_issues) == 0