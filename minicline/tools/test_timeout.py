import os
import psutil
import time
from execute_command import execute_command

def get_python_processes():
    """Get list of python processes running our test script"""
    current_pid = os.getpid()
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python' and proc.pid != current_pid:
                cmdline = proc.info['cmdline']
                if cmdline and 'long_running_process.py' in ' '.join(cmdline):
                    python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return python_processes

def verify_process_terminated(initial_processes):
    """Verify that any new python processes have been terminated"""
    time.sleep(0.5)  # Give process time to clean up
    current_processes = get_python_processes()
    new_processes = [p for p in current_processes if p not in initial_processes]
    if new_processes:
        pids = [str(p.pid) for p in new_processes]
        raise AssertionError(f"Process(es) still running with PIDs: {', '.join(pids)}")

def run_test(name: str, command: str, timeout: int, expected_timeout: bool = False):
    print(f"\n=== Test: {name} ===")
    print(f"Command: {command}")
    print(f"Timeout: {timeout}s")

    # Track python processes before test
    initial_processes = get_python_processes()

    start_time = time.time()
    summary, result = execute_command(
        command=command,
        requires_approval=False,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        auto=True,
        approve_all_commands=True,
        timeout=timeout
    )
    end_time = time.time()

    duration = end_time - start_time
    print(f"Duration: {duration:.2f}s")
    print("Result:")
    print(result)

    # Verify timeout behavior
    if expected_timeout:
        assert "timed out" in result.lower(), "Expected timeout but process completed"
        assert duration < timeout + 1, f"Process ran longer than timeout: {duration:.2f}s vs {timeout}s timeout"
        # Also verify that we capture output when timing out
        if "stdout" in command or "mixed" in command:
            assert "STDOUT (partial):" in result, "Expected partial stdout in timeout result"
        if "mixed" in command:
            assert "STDERR (partial):" in result, "Expected partial stderr in timeout result"
    else:
        assert "timed out" not in result.lower(), "Unexpected timeout"

    # Verify process termination
    verify_process_terminated(initial_processes)

    print("Test passed!")
    return duration, result

def main():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "test_scripts", "long_running_process.py")

    # Test 1: Normal completion (no timeout)
    run_test(
        "Normal completion",
        f"python {script_path} sleep 2",
        timeout=5
    )

    # Test 2: Timeout triggered - short timeout
    run_test(
        "Timeout triggered (2s timeout)",
        f"python {script_path} sleep 10",
        timeout=2,
        expected_timeout=True
    )

    # Test 3: Stdout until timeout
    run_test(
        "Stdout with timeout",
        f"python {script_path} stdout 10",
        timeout=2,
        expected_timeout=True
    )

    # Test 4: Mixed stdout/stderr until timeout
    run_test(
        "Mixed stdout/stderr with timeout",
        f"python {script_path} mixed 10",
        timeout=2,
        expected_timeout=True
    )

    # Test 5: Normal stdout capture
    run_test(
        "Stdout capture",
        f"python {script_path} stdout 2",
        timeout=5
    )

    # Test 6: Exit code verification
    run_test(
        "Exit code 1",
        f"python {script_path} exit 1",
        timeout=5
    )

    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    main()
