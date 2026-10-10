import requests
import json

response = requests.post(
    'http://localhost:8000/inference/reason',
    json={
        'prompt': 'How do Python decorators work?',
        'step_by_step': True,
        'include_programming': True
    }
)
print('Status:', response.status_code)
print('Response:')
print(json.dumps(response.json(), indent=2))