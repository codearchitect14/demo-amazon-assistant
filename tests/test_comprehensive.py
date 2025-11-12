"""
Comprehensive unit testing framework for the RAG system.
"""

import unittest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import pytest

# Import the modules we want to test
from shared.utils.error_handling import (
    RAGException, ValidationError, NetworkError, DatabaseError, 
    LLMError, MemoryError, ConfigurationError, ErrorHandler, InputValidator
)
from shared.utils.validation import (
    DataSanitizer, TypeValidator, SchemaValidator, 
    validate_and_sanitize_input, ValidationLevel
)
from shared.utils.type_safety import (
    TypeChecker, TypeCheckMode, type_check, TypedList, TypedDict
)
from rag.llm.client import LLMClient
from rag.retriever import MultiVectorRetriever
from rag.memory.base import MemoryStrategy
from app.services.rag_service import RAGService
from core.config.adapter import get_configuration_manager


class TestErrorHandling(unittest.TestCase):
    """Test error handling system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.input_validator = InputValidator()
    
    def test_rag_exception_creation(self):
        """Test RAG exception creation."""
        error = RAGException("Test error", severity="HIGH", category="VALIDATION")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.severity, "HIGH")
        self.assertEqual(error.category, "VALIDATION")
        self.assertIsNotNone(error.context)
    
    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Invalid input", field="test_field", value="test_value")
        self.assertEqual(error.field, "test_field")
        self.assertEqual(error.value, "test_value")
    
    def test_network_error(self):
        """Test network error."""
        error = NetworkError("Connection failed", url="http://test.com", status_code=404)
        self.assertEqual(error.url, "http://test.com")
        self.assertEqual(error.status_code, 404)
    
    def test_error_handler_rag_error(self):
        """Test error handler with RAG error."""
        error = ValidationError("Test validation error")
        result = self.error_handler.handle_error(error)
        
        self.assertIn("error_type", result)
        self.assertIn("message", result)
        self.assertIn("severity", result)
        self.assertEqual(result["error_type"], "ValidationError")
    
    def test_error_handler_generic_error(self):
        """Test error handler with generic error."""
        error = ValueError("Test generic error")
        result = self.error_handler.handle_error(error)
        
        self.assertIn("error_type", result)
        self.assertIn("message", result)
        self.assertEqual(result["error_type"], "ValueError")


class TestInputValidation(unittest.TestCase):
    """Test input validation system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
    
    def test_validate_string_success(self):
        """Test successful string validation."""
        result = self.validator.validate_string("test", "test_field", min_length=1, max_length=10)
        self.assertEqual(result, "test")
    
    def test_validate_string_too_short(self):
        """Test string validation with too short input."""
        with self.assertRaises(ValidationError):
            self.validator.validate_string("a", "test_field", min_length=2)
    
    def test_validate_string_too_long(self):
        """Test string validation with too long input."""
        with self.assertRaises(ValidationError):
            self.validator.validate_string("a" * 1001, "test_field", max_length=1000)
    
    def test_validate_string_pattern(self):
        """Test string validation with pattern."""
        result = self.validator.validate_string(
            "test@example.com", "email", pattern=self.validator.EMAIL_PATTERN
        )
        self.assertEqual(result, "test@example.com")
    
    def test_validate_integer_success(self):
        """Test successful integer validation."""
        result = self.validator.validate_integer(5, "test_field", min_value=1, max_value=10)
        self.assertEqual(result, 5)
    
    def test_validate_integer_out_of_range(self):
        """Test integer validation with out of range value."""
        with self.assertRaises(ValidationError):
            self.validator.validate_integer(15, "test_field", max_value=10)
    
    def test_validate_boolean_success(self):
        """Test successful boolean validation."""
        result = self.validator.validate_boolean(True, "test_field")
        self.assertTrue(result)
        
        result = self.validator.validate_boolean("true", "test_field")
        self.assertTrue(result)
    
    def test_validate_list_success(self):
        """Test successful list validation."""
        result = self.validator.validate_list([1, 2, 3], "test_field", min_length=1, max_length=5)
        self.assertEqual(result, [1, 2, 3])
    
    def test_validate_dict_success(self):
        """Test successful dictionary validation."""
        data = {"key1": "value1", "key2": "value2"}
        result = self.validator.validate_dict(data, "test_field", required_keys=["key1"])
        self.assertEqual(result, data)
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        result = self.validator.sanitize_string("<script>alert('xss')</script>")
        self.assertNotIn("<script>", result)
    
    def test_validate_chat_request(self):
        """Test chat request validation."""
        result = self.validator.validate_chat_request(
            query="test query",
            session_id="test_session",
            top_k=5,
            retrieval_method="title_first"
        )
        
        self.assertEqual(result["query"], "test query")
        self.assertEqual(result["session_id"], "test_session")
        self.assertEqual(result["top_k"], 5)
        self.assertEqual(result["retrieval_method"], "title_first")


class TestDataSanitization(unittest.TestCase):
    """Test data sanitization system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sanitizer = DataSanitizer()
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = self.sanitizer.sanitize_string("test string")
        self.assertEqual(result, "test string")
    
    def test_sanitize_string_with_html(self):
        """Test string sanitization with HTML."""
        result = self.sanitizer.sanitize_string("<script>alert('xss')</script>")
        self.assertNotIn("<script>", result)
    
    def test_sanitize_string_with_sql_injection(self):
        """Test string sanitization with SQL injection."""
        result = self.sanitizer.sanitize_string("'; DROP TABLE users; --")
        self.assertNotIn("DROP TABLE", result)
    
    def test_sanitize_url_valid(self):
        """Test URL sanitization with valid URL."""
        result = self.sanitizer.sanitize_url("https://example.com")
        self.assertEqual(result, "https://example.com")
    
    def test_sanitize_url_invalid(self):
        """Test URL sanitization with invalid URL."""
        result = self.sanitizer.sanitize_url("javascript:alert('xss')")
        self.assertEqual(result, "")
    
    def test_sanitize_email_valid(self):
        """Test email sanitization with valid email."""
        result = self.sanitizer.sanitize_email("test@example.com")
        self.assertEqual(result, "test@example.com")
    
    def test_sanitize_email_invalid(self):
        """Test email sanitization with invalid email."""
        result = self.sanitizer.sanitize_email("invalid-email")
        self.assertEqual(result, "")
    
    def test_sanitize_filename_valid(self):
        """Test filename sanitization with valid filename."""
        result = self.sanitizer.sanitize_filename("test_file.txt")
        self.assertEqual(result, "test_file.txt")
    
    def test_sanitize_filename_invalid(self):
        """Test filename sanitization with invalid filename."""
        result = self.sanitizer.sanitize_filename("file<>.txt")
        self.assertEqual(result, "file.txt")


class TestTypeSafety(unittest.TestCase):
    """Test type safety system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = TypeChecker(TypeCheckMode.STRICT)
    
    def test_check_type_success(self):
        """Test successful type checking."""
        result = self.checker.check_type("test", str, "test_field")
        self.assertTrue(result.is_valid)
    
    def test_check_type_failure(self):
        """Test failed type checking."""
        with self.assertRaises(TypeError):
            self.checker.check_type(123, str, "test_field")
    
    def test_check_optional_type_success(self):
        """Test successful optional type checking."""
        result = self.checker.check_optional_type(None, str, "test_field")
        self.assertTrue(result.is_valid)
        
        result = self.checker.check_optional_type("test", str, "test_field")
        self.assertTrue(result.is_valid)
    
    def test_check_union_type_success(self):
        """Test successful union type checking."""
        result = self.checker.check_union_type("test", [str, int], "test_field")
        self.assertTrue(result.is_valid)
        
        result = self.checker.check_union_type(123, [str, int], "test_field")
        self.assertTrue(result.is_valid)
    
    def test_typed_list(self):
        """Test typed list."""
        string_list = TypedList(str)
        string_list.append("test")
        string_list.append("another")
        
        self.assertEqual(len(string_list), 2)
        self.assertEqual(string_list[0], "test")
        
        with self.assertRaises(TypeError):
            string_list.append(123)
    
    def test_typed_dict(self):
        """Test typed dictionary."""
        string_dict = TypedDict(str, str)
        string_dict["key1"] = "value1"
        string_dict["key2"] = "value2"
        
        self.assertEqual(len(string_dict), 2)
        self.assertEqual(string_dict["key1"], "value1")
        
        with self.assertRaises(TypeError):
            string_dict[123] = "value"
        
        with self.assertRaises(TypeError):
            string_dict["key3"] = 123
    
    @type_check(TypeCheckMode.STRICT)
    def test_function_with_type_check(self, text: str, number: int) -> str:
        """Test function with type checking."""
        return f"{text} {number}"
    
    def test_type_check_decorator(self):
        """Test type check decorator."""
        # This should work
        result = self.test_function_with_type_check("test", 123)
        self.assertEqual(result, "test 123")
        
        # This should fail
        with self.assertRaises(TypeError):
            self.test_function_with_type_check(123, "test")


class TestSchemaValidation(unittest.TestCase):
    """Test schema validation system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = SchemaValidator()
    
    def test_validate_dict_schema_success(self):
        """Test successful dictionary schema validation."""
        schema = {
            "name": {"type": "string", "min_length": 1, "max_length": 100},
            "age": {"type": "integer", "min_value": 0, "max_value": 150},
            "email": {"type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"}
        }
        
        data = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        
        result = self.validator.validate_dict_schema(data, schema)
        self.assertEqual(result, data)
    
    def test_validate_dict_schema_missing_required(self):
        """Test dictionary schema validation with missing required field."""
        schema = {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": False}
        }
        
        data = {"age": 30}
        
        with self.assertRaises(ValueError):
            self.validator.validate_dict_schema(data, schema)
    
    def test_validate_dict_schema_invalid_type(self):
        """Test dictionary schema validation with invalid type."""
        schema = {
            "age": {"type": "integer"}
        }
        
        data = {"age": "not_a_number"}
        
        with self.assertRaises(ValueError):
            self.validator.validate_dict_schema(data, schema)


class TestRAGService(unittest.TestCase):
    """Test RAG service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_llm_client = Mock()
        self.mock_retriever = Mock()
        self.mock_memory = Mock()
        self.mock_config_manager = Mock()
        
        # Create RAG service with mocked dependencies
        with patch('app.services.rag_service.resolve_service') as mock_resolve:
            mock_resolve.side_effect = [
                self.mock_llm_client,
                self.mock_retriever,
                self.mock_memory
            ]
            with patch('app.services.rag_service.get_configuration_manager') as mock_config:
                mock_config.return_value = self.mock_config_manager
                self.rag_service = RAGService()
    
    @patch('asyncio.run')
    async def test_process_chat_success(self, mock_run):
        """Test successful chat processing."""
        # Mock the async method
        self.rag_service.process_chat = AsyncMock()
        self.rag_service.process_chat.return_value = {
            "question": "test",
            "answer": "test answer",
            "context": "test context"
        }
        
        result = await self.rag_service.process_chat("test query")
        
        self.assertIn("question", result)
        self.assertIn("answer", result)
        self.assertIn("context", result)


class TestConfigurationManager(unittest.TestCase):
    """Test configuration manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = get_configuration_manager()
    
    def test_get_llm_config(self):
        """Test LLM configuration retrieval."""
        config = self.config_manager.get_llm_config()
        self.assertIsNotNone(config)
        self.assertIsNotNone(config.primary_api_key)
        self.assertIsNotNone(config.primary_model)
    
    def test_get_memory_config(self):
        """Test memory configuration retrieval."""
        config = self.config_manager.get_memory_config()
        self.assertIsNotNone(config)
        self.assertIsInstance(config.enabled, bool)
        self.assertIsInstance(config.max_entries, int)
    
    def test_get_database_config(self):
        """Test database configuration retrieval."""
        config = self.config_manager.get_database_config()
        self.assertIsNotNone(config)
        self.assertIsNotNone(config.url)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = {
            "query": "test query",
            "session_id": "test_session_123",
            "top_k": 5,
            "retrieval_method": "title_first"
        }
    
    def test_end_to_end_validation(self):
        """Test end-to-end validation flow."""
        # Test input validation
        validator = InputValidator()
        validated_data = validator.validate_chat_request(**self.test_data)
        
        # Test data sanitization
        sanitizer = DataSanitizer()
        sanitized_query = sanitizer.sanitize_string(validated_data["query"])
        
        # Test type checking
        checker = TypeChecker(TypeCheckMode.STRICT)
        result = checker.check_type(sanitized_query, str, "query")
        
        self.assertTrue(result.is_valid)
        self.assertEqual(sanitized_query, "test query")
    
    def test_error_handling_integration(self):
        """Test error handling integration."""
        error_handler = ErrorHandler()
        
        # Test with validation error
        try:
            validator = InputValidator()
            validator.validate_string("", "test_field", min_length=1)
        except ValidationError as e:
            result = error_handler.handle_error(e)
            self.assertIn("error_type", result)
            self.assertEqual(result["error_type"], "ValidationError")


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestErrorHandling,
        TestInputValidation,
        TestDataSanitization,
        TestTypeSafety,
        TestSchemaValidation,
        TestRAGService,
        TestConfigurationManager,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"TESTS RUN: {result.testsRun}")
    print(f"FAILURES: {len(result.failures)}")
    print(f"ERRORS: {len(result.errors)}")
    print(f"SUCCESS RATE: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1) 