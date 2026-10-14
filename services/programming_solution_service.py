from typing import List, Dict, Any

class ProgrammingSolutionService:
    def explain_concept(self, concept: str, language: str) -> List[Dict[str, Any]]:
        """Main routing method to fetch step-by-step explanations for programming concepts."""
        concept_lower = concept.lower()
        
        if language.lower() == 'python':
            if 'decorator' in concept_lower:
                return self._explain_python_decorators()
            elif 'async' in concept_lower:
                return self._explain_python_async()
        elif language.lower() in ['javascript', 'js']:
            if 'promise' in concept_lower or 'async' in concept_lower:
                return self._explain_javascript_promises()

        # Fallback for unsupported concepts
        return [
            {
                "step_number": 1,
                "explanation": f"Core concept introduction: understanding {concept} in {language}.",
                "code_example": None
            },
            {
                "step_number": 2,
                "explanation": f"Implementation guidelines and standard practices for {concept} in {language}.",
                "code_example": None
            }
        ]

    def _explain_python_decorators(self) -> List[Dict[str, Any]]:
        """Explain Python decorators step-by-step"""
        return [
            {
                "step_number": 1,
                "explanation": "A decorator is a function that takes another function and extends its behavior without modifying it.",
                "code_example": {
                    "language": "python",
                    "code": "def my_decorator(func):\n    def wrapper():\n        print('Before function')\n        func()\n        print('After function')\n    return wrapper",
                    "explanation": "The decorator wraps the original function with new behavior."
                }
            },
            {
                "step_number": 2,
                "explanation": "Apply the decorator using the @ symbol above your function definition.",
                "code_example": {
                    "language": "python",
                    "code": "@my_decorator\ndef say_hello():\n    print('Hello!')\n\nsay_hello()",
                    "explanation": "This syntactic sugar is equivalent to: say_hello = my_decorator(say_hello)"
                }
            }
        ]

    def _explain_python_async(self) -> List[Dict[str, Any]]:
        """Explain Python async/await step-by-step"""
        return [
            {
                "step_number": 1,
                "explanation": "Understand that async/await enables concurrent programming in Python",
                "code_example": {
                    "language": "python",
                    "code": "import asyncio\n\nasync def fetch_data():\n    await asyncio.sleep(1)\n    return {'data': 42}",
                    "explanation": "Async function that simulates fetching data with a delay"
                }
            },
            {
                "step_number": 2,
                "explanation": "Learn how to run async functions concurrently using asyncio.gather",
                "code_example": {
                    "language": "python",
                    "code": "async def main():\n    results = await asyncio.gather(\n        fetch_data(),\n        fetch_data(),\n        fetch_data()\n    )\n    print(results)",
                    "explanation": "Three operations run concurrently, taking ~1 second total instead of 3"
                }
            },
            {
                "step_number": 3,
                "explanation": "See how to run the async main function",
                "code_example": {
                    "language": "python",
                    "code": "if __name__ == '__main__':\n    asyncio.run(main())",
                    "explanation": "Entry point that runs the async main function"
                }
            }
        ]

    def _explain_javascript_promises(self) -> List[Dict[str, Any]]:
        """Explain JavaScript Promises and async/await step-by-step"""
        return [
            {
                "step_number": 1,
                "explanation": "A Promise in JavaScript represents an asynchronous operation that will produce a value in the future.",
                "code_example": {
                    "language": "javascript",
                    "code": "const fetchData = () => {\n  return new Promise((resolve) => {\n    setTimeout(() => resolve({ data: 42 }), 1000);\n  });\n};",
                    "explanation": "Creates a new Promise that resolves with data after 1 second"
                }
            },
            {
                "step_number": 2,
                "explanation": "Handle promises using modern async/await syntax or the .then() method.",
                "code_example": {
                    "language": "javascript",
                    "code": "async function handleData() {\n  const res = await fetchData();\n  console.log(res.data);\n}\nhandleData();",
                    "explanation": "Awaits the promise resolution cleanly without callback nesting"
                }
            }
        ]

# Create the singleton instance that gets imported by other files
programming_solution_service = ProgrammingSolutionService()