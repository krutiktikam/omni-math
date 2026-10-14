import subprocess
import time
import threading
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
API_URL = "http://localhost:8000/inference/reason"
LIGHT_LOAD_REQUESTS = 5
LIGHT_LOAD_CONCURRENCY = 1
MEDIUM_LOAD_REQUESTS = 10
MEDIUM_LOAD_CONCURRENCY = 2
VRAM_LIMIT_MB = 3584  # 3.5 GB
RESPONSE_TIME_LIMIT_S = 3.0  # 3 seconds

def get_vram_usage():
    """Get VRAM usage in MB for the first GPU."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, check=True
        )
        # Take the first line (first GPU)
        vram_str = result.stdout.strip().split('\n')[0]
        return int(vram_str)
    except Exception as e:
        print(f"Warning: Could not get VRAM usage: {e}")
        return 0

def make_request(prompt, step_by_step=True, include_programming=True):
    """Make a single request to the API and return (success, response_time, response_json)."""
    start_time = time.time()
    try:
        response = requests.post(
            API_URL,
            json={
                "prompt": prompt,
                "step_by_step": step_by_step,
                "include_programming": include_programming
            },
            timeout=10
        )
        elapsed = time.time() - start_time
        if response.status_code == 200:
            return True, elapsed, response.json()
        else:
            return False, elapsed, {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        elapsed = time.time() - start_time
        return False, elapsed, {"error": str(e)}

def vram_monitor(stop_event, max_vram):
    """Background thread to monitor VRAM usage."""
    while not stop_event.is_set():
        vram = get_vram_usage()
        with max_vram['lock']:
            if vram > max_vram['value']:
                max_vram['value'] = vram
        time.sleep(0.5)  # Sample every 0.5 seconds

def run_load_test(num_requests, concurrency, prompt, test_name):
    """Run a load test with the given parameters."""
    print(f"\n=== {test_name} ({num_requests} requests, {concurrency} concurrent) ===")

    # Shared variable for max VRAM observed during the test
    max_vram = {'value': 0, 'lock': threading.Lock()}
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=vram_monitor, args=(stop_event, max_vram))
    monitor_thread.start()

    start_time = time.time()

    # We'll collect results for each request
    results = []

    if concurrency == 1:
        # Sequential requests
        for i in range(num_requests):
            success, elapsed, resp = make_request(prompt)
            results.append((success, elapsed, resp))
            # Small delay between requests to avoid overwhelming
            time.sleep(0.1)
    else:
        # Concurrent requests using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request, prompt) for _ in range(num_requests)]
            for future in as_completed(futures):
                results.append(future.result())

    end_time = time.time()
    total_elapsed = end_time - start_time

    # Stop the VRAM monitor
    stop_event.set()
    monitor_thread.join()

    # Process results
    successful_requests = [r for r in results if r[0]]
    failed_requests = [r for r in results if not r[0]]

    if successful_requests:
        response_times = [r[1] for r in successful_requests]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
    else:
        avg_response_time = max_response_time = min_response_time = 0

    # Get the max VRAM observed during the test
    with max_vram['lock']:
        observed_max_vram = max_vram['value']

    # Get VRAM before and after for reference
    vram_before = get_vram_usage()
    # Small delay to let any pending operations finish
    time.sleep(1)
    vram_after = get_vram_usage()

    # Print results
    print(f"Total time: {total_elapsed:.2f}s")
    print(f"Successful requests: {len(successful_requests)}/{num_requests}")
    if failed_requests:
        print(f"Failed requests: {len(failed_requests)}")
        for i, (success, elapsed, resp) in enumerate(failed_requests[:3]):  # Show first 3 failures
            print(f"  Failure {i+1}: {resp.get('error', 'Unknown error')} (took {elapsed:.2f}s)")

    if successful_requests:
        print(f"Response times: avg={avg_response_time:.2f}s, min={min_response_time:.2f}s, max={max_response_time:.2f}s")

    print(f"VRAM usage: before={vram_before} MB, after={vram_after} MB, max observed during test={observed_max_vram} MB")

    # Check constraints
    vram_ok = observed_max_vram <= VRAM_LIMIT_MB
    time_ok = avg_response_time <= RESPONSE_TIME_LIMIT_S if successful_requests else False

    print(f"VRAM constraint (<={VRAM_LIMIT_MB} MB): {'PASS' if vram_ok else 'FAIL'}")
    print(f"Response time constraint (<={RESPONSE_TIME_LIMIT_S}s avg): {'PASS' if time_ok else 'FAIL'}")

    return {
        'total_time': total_elapsed,
        'successful_requests': len(successful_requests),
        'failed_requests': len(failed_requests),
        'avg_response_time': avg_response_time if successful_requests else None,
        'max_vram_observed': observed_max_vram,
        'vram_before': vram_before,
        'vram_after': vram_after,
        'vram_ok': vram_ok,
        'time_ok': time_ok
    }

def main():
    print("Performance and Constraint Testing for Programming Concepts RAG System")
    print(f"API URL: {API_URL}")
    print(f"VRAM limit: {VRAM_LIMIT_MB} MB")
    print(f"Response time limit: {RESPONSE_TIME_LIMIT_S} seconds\n")

    # Test prompts
    math_prompt = "Find the derivative of x^3 + 2*x^2 - 5*x + 7"
    programming_prompt = "Explain Python decorators with examples"

    # First, check if the server is reachable
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code != 200:
            raise Exception("Server not responding correctly")
        print("Server is reachable.")
    except Exception as e:
        print(f"Error: Cannot connect to server at {API_URL}. Please make sure the server is running.")
        print(f"Details: {e}")
        return

    # Run light load test with programming prompt
    light_result = run_load_test(
        LIGHT_LOAD_REQUESTS,
        LIGHT_LOAD_CONCURRENCY,
        programming_prompt,
        "Light Load Test"
    )

    # Run medium load test with programming prompt
    medium_result = run_load_test(
        MEDIUM_LOAD_REQUESTS,
        MEDIUM_LOAD_CONCURRENCY,
        programming_prompt,
        "Medium Load Test"
    )

    # Also test with math prompt to ensure we didn't break existing functionality
    print("\n=== Math Prompt Light Load Test (5 requests, 1 concurrent) ===")
    math_light_result = run_load_test(
        5,
        1,
        math_prompt,
        "Math Prompt Light Load Test"
    )

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    all_passed = True
    for test_name, result in [("Light Load", light_result), ("Medium Load", medium_result), ("Math Light Load", math_light_result)]:
        passed = result['vram_ok'] and result['time_ok'] and result['failed_requests'] == 0
        all_passed = all_passed and passed
        print(f"{test_name}: {'PASS' if passed else 'FAIL'} "
              f"(VRAM: {result['max_vram_observed']} MB, "
              f"Avg Time: {result['avg_response_time']:.2f}s if success else N/A, "
              f"Failures: {result['failed_requests']})")

    if all_passed:
        print("\n*** All tests passed! The system meets the performance and constraint requirements. ***")
    else:
        print("\n!!! Some tests failed. Please review the results above. !!!")

    return all_passed

if __name__ == "__main__":
    main()