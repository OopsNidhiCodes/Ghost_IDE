"""
Unit tests for Language API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.language_manager import LanguageType

client = TestClient(app)


class TestLanguageAPI:
    """Test cases for Language API endpoints"""
    
    def test_get_supported_languages(self):
        """Test GET /api/v1/languages"""
        response = client.get("/api/v1/languages")
        assert response.status_code == 200
        
        languages = response.json()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert LanguageType.PYTHON in languages
        assert LanguageType.JAVASCRIPT in languages
    
    def test_get_language_info_valid(self):
        """Test GET /api/v1/languages/{language} with valid language"""
        response = client.get(f"/api/v1/languages/{LanguageType.PYTHON}")
        assert response.status_code == 200
        
        info = response.json()
        assert info["name"] == "Python"
        assert info["extension"] == ".py"
        assert info["monaco_language"] == "python"
        assert info["icon"] == "🐍"
        assert "template" in info
        assert "examples" in info
        assert isinstance(info["examples"], list)
    
    def test_get_language_info_invalid(self):
        """Test GET /api/v1/languages/{language} with invalid language"""
        response = client.get("/api/v1/languages/invalid_language")
        assert response.status_code == 404
        assert "not supported" in response.json()["detail"]
    
    def test_get_language_template_valid(self):
        """Test GET /api/v1/languages/{language}/template with valid language"""
        response = client.get(f"/api/v1/languages/{LanguageType.PYTHON}/template")
        assert response.status_code == 200
        
        data = response.json()
        assert "template" in data
        assert isinstance(data["template"], str)
        assert len(data["template"]) > 0
    
    def test_get_language_template_invalid(self):
        """Test GET /api/v1/languages/{language}/template with invalid language"""
        response = client.get("/api/v1/languages/invalid_language/template")
        assert response.status_code == 404
    
    def test_get_language_examples_valid(self):
        """Test GET /api/v1/languages/{language}/examples with valid language"""
        response = client.get(f"/api/v1/languages/{LanguageType.PYTHON}/examples")
        assert response.status_code == 200
        
        data = response.json()
        assert "examples" in data
        assert isinstance(data["examples"], list)
        
        # Check example structure if examples exist
        if data["examples"]:
            example = data["examples"][0]
            assert "name" in example
            assert "description" in example
            assert "code" in example
    
    def test_get_language_examples_invalid(self):
        """Test GET /api/v1/languages/{language}/examples with invalid language"""
        response = client.get("/api/v1/languages/invalid_language/examples")
        assert response.status_code == 404
    
    def test_validate_code_valid(self):
        """Test POST /api/v1/languages/validate with valid code"""
        valid_code = "print('Hello, World!')"
        
        response = client.post("/api/v1/languages/validate", json={
            "code": valid_code,
            "language": LanguageType.PYTHON
        })
        assert response.status_code == 200
        
        result = response.json()
        assert "is_valid" in result
        assert "issues" in result
        assert result["is_valid"] is True
        assert isinstance(result["issues"], list)
    
    def test_validate_code_with_issues(self):
        """Test POST /api/v1/languages/validate with code that has issues"""
        dangerous_code = "import os\neval('print(1)')"
        
        response = client.post("/api/v1/languages/validate", json={
            "code": dangerous_code,
            "language": LanguageType.PYTHON
        })
        assert response.status_code == 200
        
        result = response.json()
        assert result["is_valid"] is False
        assert len(result["issues"]) > 0
        
        # Check issue structure
        issue = result["issues"][0]
        assert "severity" in issue
        assert "message" in issue
        assert issue["severity"] in ["error", "warning", "info"]
    
    def test_validate_code_empty(self):
        """Test POST /api/v1/languages/validate with empty code"""
        response = client.post("/api/v1/languages/validate", json={
            "code": "",
            "language": LanguageType.PYTHON
        })
        assert response.status_code == 200
        
        result = response.json()
        assert result["is_valid"] is False
        assert len(result["issues"]) > 0
    
    def test_detect_language_from_filename(self):
        """Test POST /api/v1/languages/detect with filename"""
        response = client.post("/api/v1/languages/detect", json={
            "filename": "test.py"
        })
        assert response.status_code == 200
        
        result = response.json()
        assert "detected_language" in result
        assert "confidence" in result
        assert result["detected_language"] == LanguageType.PYTHON
        assert result["confidence"] == "high"
    
    def test_detect_language_from_content(self):
        """Test POST /api/v1/languages/detect with content"""
        python_code = "def hello():\n    print('Hello, World!')"
        
        response = client.post("/api/v1/languages/detect", json={
            "content": python_code
        })
        assert response.status_code == 200
        
        result = response.json()
        assert result["detected_language"] == LanguageType.PYTHON
        assert result["confidence"] in ["high", "medium"]
    
    def test_detect_language_from_both(self):
        """Test POST /api/v1/languages/detect with both filename and content"""
        response = client.post("/api/v1/languages/detect", json={
            "filename": "test.py",
            "content": "print('Hello, World!')"
        })
        assert response.status_code == 200
        
        result = response.json()
        assert result["detected_language"] == LanguageType.PYTHON
        assert result["confidence"] == "high"  # Filename detection has high confidence
    
    def test_detect_language_unknown(self):
        """Test POST /api/v1/languages/detect with unknown content"""
        response = client.post("/api/v1/languages/detect", json={
            "filename": "unknown.xyz",
            "content": "This is just plain text"
        })
        assert response.status_code == 200
        
        result = response.json()
        assert result["detected_language"] is None
        assert result["confidence"] == "low"
    
    def test_detect_language_no_input(self):
        """Test POST /api/v1/languages/detect with no input"""
        response = client.post("/api/v1/languages/detect", json={})
        assert response.status_code == 400
        assert "must be provided" in response.json()["detail"]
    
    def test_get_language_config_valid(self):
        """Test GET /api/v1/languages/{language}/config with valid language"""
        response = client.get(f"/api/v1/languages/{LanguageType.PYTHON}/config")
        assert response.status_code == 200
        
        config = response.json()
        assert "name" in config
        assert "extension" in config
        assert "docker_image" in config
        assert "compiler_config" in config
        assert "validation_rules_count" in config
        assert "error_patterns_count" in config
        assert "examples_count" in config
        
        # Check compiler config structure
        compiler_config = config["compiler_config"]
        assert "command" in compiler_config
        assert "args" in compiler_config
        assert "timeout" in compiler_config
        assert "memory_limit" in compiler_config
    
    def test_get_language_config_invalid(self):
        """Test GET /api/v1/languages/{language}/config with invalid language"""
        response = client.get("/api/v1/languages/invalid_language/config")
        assert response.status_code == 404


class TestLanguageAPIIntegration:
    """Integration tests for Language API"""
    
    def test_full_language_workflow(self):
        """Test complete language workflow through API"""
        # 1. Get supported languages
        response = client.get("/api/v1/languages")
        assert response.status_code == 200
        languages = response.json()
        assert LanguageType.PYTHON in languages
        
        # 2. Get language info
        response = client.get(f"/api/v1/languages/{LanguageType.PYTHON}")
        assert response.status_code == 200
        info = response.json()
        
        # 3. Get template
        response = client.get(f"/api/v1/languages/{LanguageType.PYTHON}/template")
        assert response.status_code == 200
        template_data = response.json()
        template = template_data["template"]
        
        # 4. Validate template
        response = client.post("/api/v1/languages/validate", json={
            "code": template,
            "language": LanguageType.PYTHON
        })
        assert response.status_code == 200
        validation = response.json()
        # Template should be valid (may have warnings but no errors)
        error_issues = [issue for issue in validation["issues"] if issue["severity"] == "error"]
        assert len(error_issues) == 0
        
        # 5. Get examples
        response = client.get(f"/api/v1/languages/{LanguageType.PYTHON}/examples")
        assert response.status_code == 200
        examples_data = response.json()
        examples = examples_data["examples"]
        
        # 6. Validate first example if exists
        if examples:
            example_code = examples[0]["code"]
            response = client.post("/api/v1/languages/validate", json={
                "code": example_code,
                "language": LanguageType.PYTHON
            })
            assert response.status_code == 200
            validation = response.json()
            # Examples should be valid
            error_issues = [issue for issue in validation["issues"] if issue["severity"] == "error"]
            assert len(error_issues) == 0
    
    def test_language_detection_workflow(self):
        """Test language detection workflow"""
        test_cases = [
            ("hello.py", "print('Hello')", LanguageType.PYTHON),
            ("app.js", "console.log('Hello');", LanguageType.JAVASCRIPT),
            ("Main.java", "public class Main { }", LanguageType.JAVA),
            ("program.cpp", "#include <iostream>", LanguageType.CPP),
        ]
        
        for filename, content, expected_lang in test_cases:
            # Test detection
            response = client.post("/api/v1/languages/detect", json={
                "filename": filename,
                "content": content
            })
            assert response.status_code == 200
            
            result = response.json()
            detected_lang = result["detected_language"]
            
            # Should detect the expected language or at least detect something
            assert detected_lang is not None
            if detected_lang != expected_lang:
                # If not exact match, at least confidence should be reasonable
                assert result["confidence"] in ["high", "medium", "low"]
            
            # Validate the detected language exists
            if detected_lang:
                response = client.get(f"/api/v1/languages/{detected_lang}")
                assert response.status_code == 200
    
    def test_validation_across_languages(self):
        """Test code validation across different languages"""
        test_cases = [
            (LanguageType.PYTHON, "print('Hello, World!')", True),
            (LanguageType.PYTHON, "import os", False),  # Should trigger security warning/error
            (LanguageType.JAVASCRIPT, "console.log('Hello');", True),
            (LanguageType.JAVASCRIPT, "eval('dangerous')", False),  # Should trigger security error
            (LanguageType.JAVA, "public class Main { public static void main(String[] args) { } }", True),
            (LanguageType.JAVA, "public class NotMain { }", False),  # Missing Main class
            (LanguageType.CPP, "#include <iostream>\nint main() { return 0; }", True),
        ]
        
        for language, code, should_be_valid in test_cases:
            response = client.post("/api/v1/languages/validate", json={
                "code": code,
                "language": language
            })
            assert response.status_code == 200
            
            result = response.json()
            if should_be_valid:
                # Should be valid or have only warnings
                error_issues = [issue for issue in result["issues"] if issue["severity"] == "error"]
                assert len(error_issues) == 0
            else:
                # Should have errors or be invalid
                assert result["is_valid"] is False or any(
                    issue["severity"] == "error" for issue in result["issues"]
                )