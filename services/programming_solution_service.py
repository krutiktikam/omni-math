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
                
        # Fallback for unsupported concepts
        return [{
            "step_number": 1, 
            "explanation": f"Basic explanation for {concept} in {language}.",
            "code_example": None
        }]

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

# Create the singleton instance that gets imported by other files
programming_solution_service = ProgrammingSolutionService()