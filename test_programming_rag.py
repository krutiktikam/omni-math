#!/usr/bin/env python3
"""
Test script for the Programming Concepts RAG System
Tests the core components: parsing, verification, and basic API functionality
"""

import sys
import os
from pathlib import Path

# Add the current directory and services directory to Python path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "services"))

def test_parsing_service():
    """Test the enhanced parsing service with code and markdown"""
    print("Testing Parsing Service...")

    try:
        from parsing_service import parsing_service

        # Test Python code parsing
        python_code = '''
def fibonacci(n):
    """Calculate Fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def add(self, a, b):
        return a + b
'''
        chunks = parsing_service.chunk_python_code(python_code, "test_fib.py")
        print(f"  Python code parsed into {len(chunks)} chunks")
        assert len(chunks) >= 2, "Should have at least function and class chunks"
        assert chunks[0]['metadata']['type'] == 'code_example'
        assert chunks[0]['metadata']['language'] == 'python'

        # Test Markdown with code blocks
        markdown = '''
# Python Decorators

Here's how to use decorators:

```python
def my_decorator(func):
    def wrapper():
        print("Before")
        result = func()
        print("After")
        return result
    return wrapper

@my_decorator
def greet():
    return "Hello"
```
'''
        chunks = parsing_service.chunk_markdown(markdown, "decorators.md")
        print(f"  Markdown parsed into {len(chunks)} chunks")
        # Should have explanation chunks and code example chunks
        code_chunks = [c for c in chunks if c['metadata']['type'] == 'code_example']
        explanation_chunks = [c for c in chunks if c['metadata']['type'] == 'explanation']
        assert len(code_chunks) >= 1, "Should have at least one code chunk"
        assert len(explanation_chunks) >= 1, "Should have at least one explanation chunk"

        print("  Parsing Service tests passed!")
        return True

    except Exception as e:
        print(f"  Parsing Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_verification_service():
    """Test the code verification service"""
    print("Testing Verification Service...")

    try:
        from verification_service import verification_service

        # Test valid Python code
        valid_code = '''
def greet(name: str) -> str:
    return f"Hello, {name}!"

result = greet("World")
print(result)
'''
        result = verification_service.verify_code(valid_code, "python", run_ruff=True, execute=False)
        print(f"  Valid Python code verification: {result['overall_verified']}")
        assert result['overall_verified'] == True, "Valid code should pass verification"
        assert result['syntax_check']['valid'] == True

        # Test invalid Python code
        invalid_code = '''
def broken_function(
    print("This is broken")
'''
        result = verification_service.verify_code(invalid_code, "python", run_ruff=False, execute=False)
        print(f"  Invalid Python code verification: {result['overall_verified']}")
        assert result['overall_verified'] == False, "Invalid code should fail verification"
        assert result['syntax_check']['valid'] == False

        # Test JavaScript (basic validation since parser might not be available)
        js_code = '''
function add(a, b) {
    return a + b;
}
const result = add(2, 3);
console.log(result);
'''
        result = verification_service.verify_code(js_code, "javascript", run_ruff=False, execute=False)
        print(f"  JavaScript code verification: {result['overall_verified']}")
        # Should at least not crash

        print("  Verification Service tests passed!")
        return True

    except Exception as e:
        print(f"  Verification Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_programming_solution_service():
    """Test the programming solution service"""
    print("Testing Programming Solution Service...")

    try:
        from programming_solution_service import programming_solution_service

        # Test Python decorators explanation
        steps = programming_solution_service.explain_concept("decorators", "python")
        print(f"  Python decorators explanation: {len(steps)} steps")
        assert len(steps) >= 2, "Should have multiple steps"
        assert steps[0]['step_number'] == 1
        assert "decorator" in steps[0]['explanation'].lower()

        # Test JavaScript promises explanation
        steps = programming_solution_service.explain_concept("promises", "javascript")
        print(f"  JavaScript promises explanation: {len(steps)} steps")
        assert len(steps) >= 2
        assert "promise" in steps[0]['explanation'].lower() or "async" in steps[0]['explanation'].lower()

        # Test general concept explanation
        steps = programming_solution_service.explain_concept("unknown concept", "python")
        print(f"  Generic concept explanation: {len(steps)} steps")
        assert len(steps) >= 2

        print("  Programming Solution Service tests passed!")
        return True

    except Exception as e:
        print(f"  Programming Solution Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schemas():
    """Test that the schemas are properly defined"""
    print("Testing Schemas...")

    try:
        from schemas import (
            InferenceRequest,
            InferenceResponse,
            ProgrammingExplanation,
            ProgrammingStep,
            CodeExample
        )

        # Test InferenceRequest with new fields
        request = InferenceRequest(
            prompt="Explain Python decorators",
            step_by_step=True,
            include_programming=True
        )
        assert request.prompt == "Explain Python decorators"
        assert request.step_by_step == True
        assert request.include_programming == True
        print("  InferenceRequest schema works")

        # Test ProgrammingExplanation
        explanation = ProgrammingExplanation(
            concept="Decorators",
            language="python",
            steps=[
                ProgrammingStep(
                    step_number=1,
                    explanation="Introduction to decorators",
                    code_example=CodeExample(
                        language="python",
                        code="@my_decorator\ndef func(): pass",
                        explanation="Basic decorator syntax"
                    )
                )
            ]
        )
        assert explanation.concept == "Decorators"
        assert explanation.language == "python"
        assert len(explanation.steps) == 1
        print("  ProgrammingExplanation schema works")

        print("  Schemas tests passed!")
        return True

    except Exception as e:
        print(f"  Schemas test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting Programming Concepts RAG System Tests\n")

    tests = [
        test_schemas,
        test_parsing_service,
        test_verification_service,
        test_programming_solution_service
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()  # Empty line between tests

    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed! The Programming Concepts RAG System is ready.")
        return 0
    else:
        print("Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())