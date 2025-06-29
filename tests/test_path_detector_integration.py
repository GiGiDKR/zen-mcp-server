"""
Integration tests for PathModeDetector

End-to-end tests validating the complete system behavior in different
execution environments (Docker vs local).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_integration_local_environment():
    """Integration test in LOCAL environment"""
    print("=== Integration test LOCAL ENVIRONMENT ===")

    # Force local mode
    env = os.environ.copy()
    env["MCP_FILE_PATH_MODE"] = "local"
    env["MCP_DEBUG_PATH_DETECTION"] = "true"

    # Simple test script
    test_script = """
import sys
sys.path.insert(0, '.')
from utils.path_detector import get_path_detector

detector = get_path_detector()
mode = detector.get_path_mode()
test_path = r'C:\\Projects\\test_file.py'
converted = detector.convert_path(test_path)

print(f'MODE:{mode}')
print(f'ORIGINAL:{test_path}')
print(f'CONVERTED:{converted}')
"""

    result = subprocess.run(
        [sys.executable, "-c", test_script], env=env, cwd=project_root, capture_output=True, text=True, timeout=30
    )

    assert result.returncode == 0, f"LOCAL test failed - Error: {result.stderr}"

    output = result.stdout
    expected_path = "CONVERTED:C:\\Projects\\test_file.py"

    assert "MODE:local" in output, f"Local mode not detected in: {output}"
    assert expected_path in output, f"Expected path not found in: {output}"

    print("Test LOCAL integration passed")
    print(f"Output: {output.strip()}")


def test_integration_docker_environment():
    """Integration test in forced Docker mode"""
    print("\n=== Integration test DOCKER ENVIRONMENT ===")

    # Force docker mode
    env = os.environ.copy()
    env["MCP_FILE_PATH_MODE"] = "docker"
    env["MCP_DEBUG_PATH_DETECTION"] = "true"

    # Simple test script
    test_script = """
import sys
sys.path.insert(0, '.')
from utils.path_detector import get_path_detector

detector = get_path_detector()
mode = detector.get_path_mode()
test_path = r'C:\\Projects\\zen-mcp-server\\server.py'
converted = detector.convert_path(test_path)

print(f'MODE:{mode}')
print(f'ORIGINAL:{test_path}')
print(f'CONVERTED:{converted}')
"""

    result = subprocess.run(
        [sys.executable, "-c", test_script], env=env, cwd=project_root, capture_output=True, text=True, timeout=30
    )

    assert result.returncode == 0, f"DOCKER test failed - Error: {result.stderr}"

    output = result.stdout
    expected_docker_path = "CONVERTED:/app/project/server.py"

    assert "MODE:docker" in output, f"Docker mode not detected in: {output}"
    assert expected_docker_path in output, f"Expected Docker path not found in: {output}"

    print("Test DOCKER integration passed")
    print(f"Output: {output.strip()}")


def test_integration_auto_detection():
    """Test automatic detection without override"""
    print("\n=== Integration test AUTO DETECTION ===")

    # Auto mode (no MCP_FILE_PATH_MODE variable)
    env = os.environ.copy()
    env.pop("MCP_FILE_PATH_MODE", None)  # Remove if exists
    env["MCP_DEBUG_PATH_DETECTION"] = "true"

    # Simple test script
    test_script = """
import sys
sys.path.insert(0, '.')
from utils.path_detector import get_path_detector

detector = get_path_detector()
mode = detector.get_path_mode()
is_docker = detector.is_docker_mode()

print(f'MODE:{mode}')
print(f'IS_DOCKER:{is_docker}')
"""

    result = subprocess.run(
        [sys.executable, "-c", test_script], env=env, cwd=project_root, capture_output=True, text=True, timeout=30
    )

    assert result.returncode == 0, f"AUTO test failed - Error: {result.stderr}"

    output = result.stdout

    assert "MODE:" in output, f"Mode not detected in: {output}"
    assert "local" in output or "docker" in output, f"Valid mode not found in: {output}"

    print("Test AUTO integration passed")
    print(f"Output: {output.strip()}")


def test_integration_env_file():
    """Test reading variables from .env file"""
    print("\n=== Integration test .ENV file ===")

    # Create temporary .env file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("MCP_FILE_PATH_MODE=docker\n")
        f.write("MCP_DEBUG_PATH_DETECTION=true\n")
        temp_env_file = f.name

    # Test script with dotenv
    test_script = f"""
import sys
sys.path.insert(0, '.')
import os
from dotenv import load_dotenv
load_dotenv(r'{temp_env_file}')

from utils.path_detector import get_path_detector

detector = get_path_detector()
mode = detector.get_path_mode()
env_mode = os.getenv('MCP_FILE_PATH_MODE')

print(f'ENV_VAR:{{env_mode}}')
print(f'DETECTED_MODE:{{mode}}')
"""

    try:
        result = subprocess.run(
            [sys.executable, "-c", test_script], cwd=project_root, capture_output=True, text=True, timeout=30
        )

        # Clean up temporary file
        os.unlink(temp_env_file)

        assert result.returncode == 0, f".ENV test failed - Error: {result.stderr}"

        output = result.stdout

        assert "ENV_VAR:docker" in output, f"ENV variable not detected: {output}"
        assert "DETECTED_MODE:docker" in output, f"Docker mode not detected in: {output}"

        print(".ENV integration test passed")
        print(f"Output: {output.strip()}")

    except Exception as e:
        try:
            os.unlink(temp_env_file)
        except Exception:
            pass
        raise AssertionError(f".ENV test failed - Exception: {e}") from e


def test_performance_benchmark():
    """Basic performance test"""
    print("\n=== PERFORMANCE TEST ===")

    test_script = """
import sys
import time
sys.path.insert(0, '.')
from utils.path_detector import get_path_detector

# Performance detection test
start = time.time()
detector = get_path_detector()

# First detection (with cache)
for i in range(100):
    mode = detector.get_path_mode()

first_100 = time.time() - start

# Path conversion test
start = time.time()
test_paths = [
    r'C:\\Projects\\test_file1.py',
    r'C:\\Projects\\test_file2.py',
    r'C:\\Projects\\test_file3.py',
    'relative/file.py',
    '/already/docker/path.py'
] * 20  # 100 conversions

for path in test_paths:
    detector.convert_path(path)

conversions_100 = time.time() - start

print(f'DETECTIONS_100:{{first_100:.4f}}s')
print(f'CONVERSIONS_100:{{conversions_100:.4f}}s')
"""

    result = subprocess.run(
        [sys.executable, "-c", test_script], cwd=project_root, capture_output=True, text=True, timeout=30
    )

    assert result.returncode == 0, f"PERFORMANCE test failed - Error: {result.stderr}"

    output = result.stdout
    print("PERFORMANCE test passed")
    print(f"Output: {output.strip()}")


def main():
    """Run all PathModeDetector integration tests"""
    print("Integration tests for PathModeDetector")
    print("=" * 50)

    tests = [
        test_integration_local_environment,
        test_integration_docker_environment,
        test_integration_auto_detection,
        test_integration_env_file,
        test_performance_benchmark,
    ]

    results = []

    for test_func in tests:
        try:
            test_func()
            results.append(True)
        except (AssertionError, Exception) as e:
            print(f"Error in {test_func.__name__}: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    successful = sum(results)
    total = len(results)

    print(f"Tests passed: {successful}/{total}")

    if successful == total:
        print("All integration tests passed!")
        return True
    else:
        print("Some integration tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
