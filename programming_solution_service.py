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
                    "code": "async def main():\n    # Run multiple async operations concurrently\n    results = await asyncio.gather(\n        fetch_data(),\n        fetch_data(),\n        fetch_data()\n    )\n    print(results)",
                    "explanation": "Three fetch_data operations run concurrently, taking ~1 second total instead of 3"
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
            ]
        ]