import requests
import json
import sys
import time

def clear_line():
    sys.stdout.write("\033[K")

def main():
    url = "http://localhost:8000/inference/reason"
    print("\n" + "="*50)
    print("  OMNIMATH-LOCAL: INTERACTIVE REASONING ENGINE")
    print("="*50)
    print("Type your math question below. Type 'exit' to quit.\n")

    while True:
        try:
            prompt = input("\033[1;32mUser > \033[0m")
            
            if prompt.lower() in ['exit', 'quit']:
                break
            
            if not prompt.strip():
                continue

            print("\n\033[1;34mThinking and searching textbooks...\033[0m", end="\r")
            
            payload = {"prompt": prompt}
            start_time = time.time()
            
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            
            data = response.json()
            elapsed = time.time() - start_time
            
            clear_line()
            print(f"\r\033[1;36mReasoning ({data.get('model_used', 'LLM')} - {elapsed:.2f}s):\033[0m")
            print("-" * 30)
            print(data.get("reasoning_steps", "No reasoning steps returned."))
            
            print(f"\n\033[1;33mCore Formula:\033[0m {data.get('core_formula', 'N/A')}")
            print(f"\033[1;32mFinal Answer:\033[0m {data.get('final_answer', 'N/A')}")
            
            v = data.get("verification_details", {})
            if v and v.get("verified"):
                print(f"\033[1;42m[VERIFIED]\033[0m Symbolic check passed: {v.get('simplified')}")
            elif v and v.get("error"):
                print(f"\033[1;43m[CHECK FAILED]\033[0m SymPy Error: {v.get('error')}")
            
            print("-" * 50 + "\n")

        except requests.exceptions.ConnectionError:
            print("\n\033[1;31mError: Backend server is not running. Please start main.py first.\033[0m\n")
            break
        except Exception as e:
            print(f"\n\033[1;31mAn error occurred: {e}\033[0m\n")

if __name__ == "__main__":
    main()
