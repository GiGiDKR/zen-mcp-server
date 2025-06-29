#!/usr/bin/env python3
"""
Health check script for Zen MCP Server Docker container
"""

import os
import subprocess
import sys


def check_process():
    """Check if the main server process is running"""
    result = subprocess.run(["pgrep", "-f", "server.py"], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        return True
    print(f"Process check failed: {result.stderr}", file=sys.stderr)
    return False


def check_python_imports():
    """Check if critical Python modules can be imported"""
    critical_modules = ["mcp", "google.genai", "openai", "pydantic", "dotenv"]

    for module in critical_modules:
        try:
            __import__(module)
        except ImportError as e:
            print(f"Critical module {module} cannot be imported: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error importing {module}: {e}", file=sys.stderr)
            return False
    return True


def check_log_directory():
    """Check if logs directory is writable"""
    log_dir = "/app/logs"
    try:
        if not os.path.exists(log_dir):
            print(f"Log directory {log_dir} does not exist", file=sys.stderr)
            return False

        test_file = os.path.join(log_dir, ".health_check")
        with open(test_file, "w") as f:
            f.write("health_check")
        os.remove(test_file)
        return True
    except Exception as e:
        print(f"Log directory check failed: {e}", file=sys.stderr)
        return False


def check_environment():
    """Check if essential environment variables are present and well-formed"""
    # At least one API key should be present
    api_key_specs = {
        "GEMINI_API_KEY": {"prefixes": ["AIza", "GEMINI", "GO"], "min_length": 32},
        "OPENAI_API_KEY": {"prefixes": ["sk-"], "min_length": 50},
        "OPENROUTER_API_KEY": {"prefixes": ["or-", "sk-or-"], "min_length": 40},
        "XAI_API_KEY": {"prefixes": ["xai-"], "min_length": 20},
        "DIAL_API_KEY": {"prefixes": ["dial-"], "min_length": 20},
    }

    has_api_key = any(os.getenv(key) for key in api_key_specs)
    if not has_api_key:
        print("No API keys found in environment", file=sys.stderr)
        return False

    # Validate API key formats (prefix and length)
    for key, spec in api_key_specs.items():
        value = os.getenv(key)
        if value:
            value = value.strip()
            if len(value) < spec["min_length"]:
                print(
                    f"API key {key} appears too short (length {len(value)}, " f"min {spec['min_length']})",
                    file=sys.stderr,
                )
                return False
            prefixes = spec["prefixes"]
            if not any(value.startswith(prefix) for prefix in prefixes):
                print(f"API key {key} does not start with expected prefix " f"{prefixes}", file=sys.stderr)
                return False

    return True


def main():
    """Main health check function"""
    checks = [
        ("Process", check_process),
        ("Python imports", check_python_imports),
        ("Log directory", check_log_directory),
        ("Environment", check_environment),
    ]

    failed_checks = []

    for check_name, check_func in checks:
        if not check_func():
            failed_checks.append(check_name)

    if failed_checks:
        print(f"Health check failed: {', '.join(failed_checks)}", file=sys.stderr)
        sys.exit(1)

    print("Health check passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
