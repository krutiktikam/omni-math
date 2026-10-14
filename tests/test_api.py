import urllib.request
import json

url = "http://localhost:8000/inference/reason"
headers = {"Content-Type": "application/json"}

def run_test(name, payload):
    print(f"=== {name} ===")
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    print("\n")

# 1. Mathematical Query
run_test("MATH TEST", {
    "prompt": "Find derivative of x^3", 
    "step_by_step": True
})

# 2. Programming Explanation
run_test("PROGRAMMING EXPLANATION TEST", {
    "prompt": "Explain Python decorators", 
    "step_by_step": True, 
    "include_programming": True
})

# 3. Code Verification
run_test("CODE VERIFICATION TEST", {
    "prompt": "Write a Python function to add two numbers", 
    "include_programming": True
})