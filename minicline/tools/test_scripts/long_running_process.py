import sys
import time

# Simulate different behaviors based on command line arguments
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "sleep"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    if mode == "sleep":
        # Simple sleep
        print(f"Starting sleep for {duration} seconds")
        time.sleep(duration)
        print("Sleep completed")
    elif mode == "stdout":
        # Continuous stdout
        for i in range(duration):
            print(f"stdout message {i}")
            sys.stdout.flush()
            time.sleep(1)
    elif mode == "stderr":
        # Write to stderr
        for i in range(duration):
            print(f"stderr message {i}", file=sys.stderr)
            sys.stderr.flush()
            time.sleep(1)
    elif mode == "mixed":
        # Write to both stdout and stderr
        for i in range(duration):
            print(f"stdout message {i}")
            print(f"stderr message {i}", file=sys.stderr)
            sys.stdout.flush()
            sys.stderr.flush()
            time.sleep(1)
    elif mode == "exit":
        # Exit with specific code
        exit_code = int(sys.argv[2])
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
