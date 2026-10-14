import requests
import json
import sys
import time
import re

def clear_line():
    sys.stdout.write("\033[K")

def print_help():
    """Print available commands"""
    help_text = """
Available commands:
  /setlang [language]  - Set programming language context (python, javascript, etc.)
  /explain [concept]   - Get step-by-step explanation of a programming concept
  /example [task]      - Generate code example for a programming task
  /exit or /quit       - Exit the program
  Just type your question for general reasoning (math or programming)
"""
    print(help_text)

def format_code_example(language, code, explanation=None):
    """Format a code example with syntax highlighting hint"""
    result = f"\n\033[1;36m{language.upper()} Example:\033[0m\n"
    result += f"```{language.lower()}\n{code}\n```\n"
    if explanation:
        result += f"\033[1;33mExplanation:\033[0m {explanation}\n"
    return result

def format_explanation_steps(steps):
    """Format step-by-step explanation"""
    if not steps:
        return ""

    result = "\n\033[1;35mStep-by-Step Explanation:\033[0m\n"
    for step in steps:
        step_num = step.get('step_number', '?')
        explanation = step.get('explanation', '')
        code_example = step.get('code_example')

        result += f"\n{step_num}. \033[1;32m{explanation}\033[0m"

        if code_example:
            lang = code_example.get('language', 'unknown')
            code = code_example.get('code', '')
            expl = code_example.get('explanation', '')
            result += format_code_example(lang, code, expl)

    return result

def main():
    url = "http://localhost:8000/inference/reason"
    current_language = "python"  # Default language

    print("\n" + "="*50)
    print("  OMNIMATH-LOCAL: INTERACTIVE REASONING ENGINE")
    print("  Now with Programming Concepts Support!")
    print("="*50)
    print(f"Default language: {current_language}")
    print("Type your question below. Type 'help' for commands, 'exit' to quit.\n")

    while True:
        try:
            prompt = input("\033[1;32mUser > \033[0m").strip()

            if not prompt:
                continue

            # Handle special commands
            if prompt.lower() in ['exit', 'quit']:
                print("\n\033[1;33mGoodbye!\033[0m")
                break

            if prompt.lower() == 'help':
                print_help()
                continue

            # Handle /setlang command
            if prompt.lower().startswith('/setlang'):
                parts = prompt.split()
                if len(parts) >= 2:
                    lang = parts[1].lower()
                    # Validate language
                    if lang in ['python', 'javascript', 'js', 'typescript', 'ts']:
                        current_language = lang
                        print(f"\n\033[1;32mLanguage set to: {current_language}\033[0m\n")
                    else:
                        print(f"\n\033[1;31mUnsupported language: {lang}\033[0m")
                        print(f"Supported languages: python, javascript/js, typescript/ts\n")
                else:
                    print(f"\n\033[1;33mCurrent language: {current_language}\033[0m\n")
                continue

            # Handle /explain command
            if prompt.lower().startswith('/explain'):
                concept = prompt[8:].strip()  # Remove '/explain' prefix
                if not concept:
                    print("\n\033[1;31mPlease specify a concept to explain (e.g., /explain decorators)\033[0m\n")
                    continue

                print(f"\n\033[1;34mExplaining {concept} in {current_language}...\033[0m", end="\r")

                try:
                    payload = {
                        "prompt": f"Explain the concept of {concept} in {current_language}",
                        "step_by_step": True,
                        "include_programming": True
                    }

                    response = requests.post(url, json=payload, timeout=30)
                    response.raise_for_status()
                    data = response.json()

                    clear_line()  # Clear the "Thinking..." message

                    if data.get("type") == "programming_explanation":
                        result = data.get("result", {})
                        explanation_text = f"\n\033[1;35mConcept: {result.get('concept', concept)}\033[0m"
                        explanation_text += f"\n\033[1;32mLanguage: {result.get('language', current_language)}\033[0m"

                        steps = result.get("steps", [])
                        if steps:
                            explanation_text += format_explanation_steps(steps)

                        related = result.get("related_concepts", [])
                        if related:
                            explanation_text += f"\n\n\033[1;34mRelated Concepts:\033[0m {', '.join(related)}"

                        complexity = result.get("complexity_analysis")
                        if complexity:
                            explanation_text += f"\n\n\033[1;34mComplexity Analysis:\033[0m {json.dumps(complexity, indent=2)}"

                        print(explanation_text + "\n")

                    elif data.get("type") == "programming_code":
                        # Handle code verification/results
                        result = data.get("result", {})
                        code = result.get("code", "")
                        explanation = result.get("explanation", "")
                        lang = result.get("language", current_language)

                        print(f"\n\033[1;35mCode Example for {concept}:\033[0m")
                        print(format_code_example(lang, code, explanation))

                    else:
                        # Fallback to general output
                        print(f"\n\033[1;36mReasoning:\033[0m\n{data.get('reasoning_steps', 'No reasoning steps returned.')}\n")

                        if data.get("core_formula"):
                            print(f"\033[1;33mCore Formula:\033[0m {data.get('core_formula')}")

                        if data.get("final_answer"):
                            print(f"\033[1;32mFinal Answer:\033[0m {data.get('final_answer')}")

                        verification = data.get("verification")
                        if verification and verification.get("verified"):
                            print(f"\033[1;42m[VERIFIED]\033[0m {verification.get('simplified', '')}")
                        elif verification and verification.get("error"):
                            print(f"\033[1;43m[CHECK FAILED]\033[0m {verification.get('error', '')}")

                    print()  # Extra newline for spacing

                except requests.exceptions.RequestException as e:
                    clear_line()
                    print(f"\n\033[1;31mError: Could not connect to backend. Is main.py running?\033[0m\n")
                except Exception as e:
                    clear_line()
                    print(f"\n\033[1;31mAn error occurred: {e}\033[0m\n")
                continue

            # Handle /example command
            if prompt.lower().startswith('/example'):
                task = prompt[8:].strip()  # Remove '/example' prefix
                if not task:
                    print("\n\033[1;31mPlease specify a task (e.g., /example fibonacci function)\033[0m\n")
                    continue

                print(f"\n\033[1;34mGenerating example for: {task} in {current_language}...\033[0m", end="\r")

                try:
                    payload = {
                        "prompt": f"Write a {current_language} code example for: {task}",
                        "step_by_step": False,
                        "include_programming": True
                    }

                    response = requests.post(url, json=payload, timeout=30)
                    response.raise_for_status()
                    data = response.json()

                    clear_line()  # Clear the "Thinking..." message

                    if data.get("type") == "programming_code":
                        result = data.get("result", {})
                        code = result.get("code", "")
                        explanation = result.get("explanation", "")
                        lang = result.get("language", current_language)

                        print(f"\n\033[1;35mCode Example for {task}:\033[0m")
                        print(format_code_example(lang, code, explanation))

                    elif data.get("type") == "programming_explanation":
                        # If we got an explanation instead, show it
                        result = data.get("result", {})
                        explanation_text = f"\n\033[1;35mExplanation for {task}:\033[0m"
                        explanation_text += f"\n\033[1;32mLanguage: {result.get('language', current_language)}\033[0m"

                        steps = result.get("steps", [])
                        if steps:
                            explanation_text += format_explanation_steps(steps)

                        print(explanation_text + "\n")

                    else:
                        # Fallback
                        print(f"\n\033[1;36mReasoning:\033[0m\n{data.get('reasoning_steps', 'No reasoning steps returned.')}\n")

                    print()  # Extra newline for spacing

                except requests.exceptions.RequestException as e:
                    clear_line()
                    print(f"\n\033[1;31mError: Could not connect to backend. Is main.py running?\033[0m\n")
                except Exception as e:
                    clear_line()
                    print(f"\n\033[1;31mAn error occurred: {e}\033[0m\n")
                continue

            # Handle general queries (math or programming)
            print(f"\n\033[1;34mProcessing your request...\033[0m", end="\r")

            try:
                # Determine if this is likely a programming query based on keywords
                programming_keywords = ['code', 'function', 'class', 'variable', 'loop', 'array', 'list',
                                      'dictionary', 'python', 'javascript', 'java', 'cpp', 'algorithm',
                                      'data structure', 'api', 'framework', 'library', 'syntax',
                                      'debug', 'error', 'exception', 'compile', 'runtime', 'script',
                                      'program', 'software', 'development', 'coding', 'programming',
                                      'developer']

                is_likely_programming = any(keyword in prompt.lower() for keyword in programming_keywords)

                payload = {
                    "prompt": prompt,
                    "step_by_step": False,
                    "include_programming": is_likely_programming
                }

                response = requests.post(url, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()

                clear_line()  # Clear the "Thinking..." message

                # Handle different response types
                if data.get("type") == "programming_explanation":
                    result = data.get("result", {})
                    explanation_text = f"\n\033[1;35mProgramming Explanation:\033[0m"
                    explanation_text += f"\n\033[1;32mLanguage: {result.get('language', 'unknown')}\033[0m"

                    steps = result.get("steps", [])
                    if steps:
                        explanation_text += format_explanation_steps(steps)

                    related = result.get("related_concepts", [])
                    if related:
                        explanation_text += f"\n\n\033[1;34mRelated Concepts:\033[0m {', '.join(related)}"

                    print(explanation_text + "\n")

                elif data.get("type") == "programming_code":
                    result = data.get("result", {})
                    code = result.get("code", "")
                    explanation = result.get("explanation", "")
                    lang = result.get("language", "unknown")

                    print(f"\n\033[1;35mCode Result:\033[0m")
                    print(format_code_example(lang, code, explanation))

                else:
                    # Mathematical or general response
                    print(f"\n\033[1;36mReasoning:\033[0m\n{data.get('reasoning_steps', 'No reasoning steps returned.')}\n")

                    if data.get("core_formula"):
                        print(f"\033[1;33mCore Formula:\033[0m {data.get('core_formula')}")

                    if data.get("final_answer"):
                        print(f"\033[1;32mFinal Answer:\033[0m {data.get('final_answer')}")

                    verification = data.get("verification")
                    if verification and verification.get("verified"):
                        print(f"\033[1;42m[VERIFIED]\033[0m {verification.get('simplified', '')}")
                    elif verification and verification.get("error"):
                        print(f"\033[1;43m[CHECK FAILED]\033[0m {verification.get('error', '')}")

                print()  # Extra newline for spacing

            except requests.exceptions.RequestException as e:
                clear_line()
                print(f"\n\033[1;31mError: Could not connect to backend. Is main.py running?\033[0m\n")
            except Exception as e:
                clear_line()
                print(f"\n\033[1;31mAn error occurred: {e}\033[0m\n")

        except KeyboardInterrupt:
            print("\n\n\033[1;33mInterrupted. Type 'exit' to quit.\033[0m")
            continue
        except EOFError:
            print("\n\033[1;33mGoodbye!\033[0m")
            break

if __name__ == "__main__":
    main()