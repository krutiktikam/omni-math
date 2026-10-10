import requests
import json

# Test code verification with valid code
print("=== Testing valid code verification ===")
response = requests.post(
    'http://localhost:8000/inference/reason',
    json={
        'prompt': 'Write a Python function to add two numbers',
        'step_by_step': False,
        'include_programming': True
    }
)
print('Status:', response.status_code)
print('Response:')
print(json.dumps(response.json(), indent=2))

print("\n" + "="*50 + "\n")

# Test code verification with invalid code (by asking for something that might generate invalid code)
print("=== Testing code that should trigger verification ===")
response = requests.post(
    'http://localhost:8000/inference/reason',
    json={
        'prompt': 'Create a Python function with a syntax error',
        'step_by_step': False,
        'include_programming': True
    }
)
print('Status:', response.status_code)
print('Response:')
print(json.dumps(response.json(), indent=2))