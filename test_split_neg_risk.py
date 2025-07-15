import sys
import os

# Add the parent directory to the sys.path to allow importing py_safe modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from py_safe.main import main

def run_test_split_neg_risk():
    # Define the arguments for the split command
    command_args = [
        'main.py',  # Placeholder for the script name
        'split',
        '--safe-address', '',  # <<< IMPORTANT: Replace with your actual Safe wallet address
        '--condition-id', '0xeee8b80f99700f0c2ab22e0ecb2b7f156d3017cce7cc7abc61c2f9d7d4cdbaaf',
        '--amount', '1',  # Example amount, adjust as needed
        '--neg-risk' # Flag for negative risk market
    ]

    print(f"Attempting to execute: {' '.join(command_args)}")

    # Temporarily replace sys.argv to simulate command-line arguments
    original_argv = sys.argv
    sys.argv = command_args

    try:
        main()
        print("Test script finished. Check console output for transaction details.")
    except Exception as e:
        print(f"An error occurred during the test: {e}")
    finally:
        sys.argv = original_argv  # Restore original sys.argv

if __name__ == "__main__":
    print("\n--- Running Test Split Neg Risk Script ---")
    run_test_split_neg_risk()
    print("--- Test Split Neg Risk Script Finished ---\n")
