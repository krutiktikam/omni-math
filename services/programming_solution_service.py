from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger("omnimath.programming_solution")

class ProgrammingSolutionService:
    def explain_concept(self, concept: str, language: str) -> List[Dict[str, Any]]:
        """Main routing method to fetch step-by-step explanations for programming concepts."""
        concept_lower = concept.lower()
        
        # 1. Specialized Python Concepts
        if language.lower() == 'python':
            if 'decorator' in concept_lower:
                return self._explain_python_decorators()
            elif 'async' in concept_lower:
                return self._explain_python_async()
            elif 'binary search' in concept_lower:
                return self._explain_binary_search()
            elif 'quick sort' in concept_lower or 'quicksort' in concept_lower:
                return self._explain_quick_sort()
            elif 'linked list' in concept_lower:
                return self._explain_linked_list()
            elif 'observer' in concept_lower:
                return self._explain_observer_pattern()
            elif 'singleton' in concept_lower:
                return self._explain_singleton_pattern()

        # 2. Specialized JavaScript Concepts
        elif language.lower() in ['javascript', 'js']:
            if 'promise' in concept_lower or 'async' in concept_lower:
                return self._explain_javascript_promises()

        # 3. Dynamic RAG Retrieval from ChromaDB
        rag_steps = self._explain_from_rag(concept, language)
        if rag_steps:
            return rag_steps

        # 4. Standard Fallback for unsupported concepts
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

    def _explain_from_rag(self, concept: str, language: str) -> Optional[List[Dict[str, Any]]]:
        """Queries local ChromaDB to pull real matching code examples."""
        try:
            from vector_service import vector_service
            results = vector_service.query(f"{concept} {language}", n_results=1)
            if results and results.get("documents") and results["documents"][0]:
                doc = results["documents"][0][0]
                
                # Extract code block if markdown format
                code_text = ""
                if "```" in doc:
                    parts = doc.split("```")
                    if len(parts) >= 3:
                        code_lines = parts[1].strip().splitlines()
                        if code_lines and code_lines[0].lower() in ["python", "py", "javascript", "js", "ts"]:
                            code_text = "\n".join(code_lines[1:]).strip()
                        else:
                            code_text = parts[1].strip()
                elif "def " in doc or "class " in doc or "function " in doc:
                    code_text = doc.strip()

                if code_text:
                    return [
                        {
                            "step_number": 1,
                            "explanation": f"Definition and architectural role of {concept} in {language}.",
                            "code_example": None
                        },
                        {
                            "step_number": 2,
                            "explanation": f"Working implementation of {concept} retrieved from offline knowledge base.",
                            "code_example": {
                                "language": language,
                                "code": code_text[:800],
                                "explanation": f"Implementation example for {concept}."
                            }
                        }
                    ]
        except Exception as e:
            logger.warning(f"RAG concept retrieval failed: {e}")
        return None

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

    def _explain_binary_search(self) -> List[Dict[str, Any]]:
        """Explain Binary Search algorithm step-by-step"""
        return [
            {
                "step_number": 1,
                "explanation": "Binary Search operates on a sorted array by dividing the search interval in half at each step (O(log n) time complexity).",
                "code_example": None
            },
            {
                "step_number": 2,
                "explanation": "Maintain two pointers (low and high) and inspect the midpoint element until the target is found.",
                "code_example": {
                    "language": "python",
                    "code": "def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1",
                    "explanation": "Returns the index of target if found, else -1."
                }
            }
        ]

    def _explain_quick_sort(self) -> List[Dict[str, Any]]:
        """Explain Quick Sort algorithm step-by-step"""
        return [
            {
                "step_number": 1,
                "explanation": "Quick Sort is a divide-and-conquer algorithm that selects a 'pivot' element and partitions array elements into smaller and greater subsets.",
                "code_example": None
            },
            {
                "step_number": 2,
                "explanation": "Recursively sort the partitions and concatenate results.",
                "code_example": {
                    "language": "python",
                    "code": "def quick_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + middle + quick_sort(right)",
                    "explanation": "Clean and idiomatic Python implementation of Quick Sort (Average O(n log n))."
                }
            }
        ]

    def _explain_linked_list(self) -> List[Dict[str, Any]]:
        """Explain Singly Linked List step-by-step"""
        return [
            {
                "step_number": 1,
                "explanation": "A Linked List is a linear data structure where elements (nodes) contain data and a reference pointer to the next node.",
                "code_example": {
                    "language": "python",
                    "code": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None",
                    "explanation": "Basic node containing data and a reference to the next node."
                }
            },
            {
                "step_number": 2,
                "explanation": "Implement append and traversal operations.",
                "code_example": {
                    "language": "python",
                    "code": "class LinkedList:\n    def __init__(self):\n        self.head = None\n    def append(self, data):\n        if not self.head:\n            self.head = Node(data)\n            return\n        curr = self.head\n        while curr.next:\n            curr = curr.next\n        curr.next = Node(data)",
                    "explanation": "Singly linked list appending new elements at the tail."
                }
            }
        ]

    def _explain_observer_pattern(self) -> List[Dict[str, Any]]:
        """Explain Observer Design Pattern step-by-step"""
        return [
            {
                "step_number": 1,
                "explanation": "The Observer pattern defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified automatically.",
                "code_example": None
            },
            {
                "step_number": 2,
                "explanation": "Create a Subject with attach/notify methods and Observer listeners.",
                "code_example": {
                    "language": "python",
                    "code": "class Subject:\n    def __init__(self):\n        self._observers = []\n    def attach(self, observer):\n        self._observers.append(observer)\n    def notify(self, message):\n        for obs in self._observers:\n            obs.update(message)\n\nclass Observer:\n    def update(self, message):\n        print(f'Received update: {message}')",
                    "explanation": "Decoupled publisher/subscriber architecture in pure Python."
                }
            }
        ]

    def _explain_singleton_pattern(self) -> List[Dict[str, Any]]:
        """Explain Singleton / Borg Pattern step-by-step"""
        return [
            {
                "step_number": 1,
                "explanation": "The Singleton pattern ensures a class has only one instance, providing a global point of access to it.",
                "code_example": None
            },
            {
                "step_number": 2,
                "explanation": "Implement in Python using __new__ or the Borg shared state pattern.",
                "code_example": {
                    "language": "python",
                    "code": "class Singleton:\n    _instance = None\n    def __new__(cls, *args, **kwargs):\n        if not cls._instance:\n            cls._instance = super().__new__(cls)\n        return cls._instance",
                    "explanation": "Guarantees only one object instance is ever instantiated in memory."
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
