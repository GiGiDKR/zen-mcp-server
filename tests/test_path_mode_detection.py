"""
Test for file path mode detection (MCP_FILE_PATH_MODE).

This test verifies that the zen MCP server correctly detects
whether it is running in Docker or local mode according to the configuration.
"""

import os
from unittest.mock import patch

from utils.path_detector import PathModeDetector


class TestPathModeDetection:
    """Tests for automatic and forced path mode detection."""

    def teardown_method(self):
        """Cleans up the singleton cache after each test."""
        self._reset_detector()

    def _reset_detector(self):
        """Fully resets the detector for tests."""
        PathModeDetector._instance = None
        PathModeDetector._cached_mode = None

    def test_auto_detection_current_environment(self):
        """Tests automatic detection in the current environment."""
        self._reset_detector()

        with patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "auto"}, clear=False):
            detector = PathModeDetector()
            mode = detector.get_path_mode()

            # In a normal local environment, should detect 'local'
            assert mode in ["local", "docker"], f"Invalid detected mode: {mode}"
            print(f"Auto-detected mode: {mode}")

    def test_forced_local_mode(self):
        """Tests forced local mode."""
        self._reset_detector()

        with patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "local"}, clear=False):
            detector = PathModeDetector()
            mode = detector.get_path_mode()

            assert mode == "local", f"Forced mode 'local' but detected: {mode}"

    def test_forced_docker_mode(self):
        """Tests forced Docker mode."""
        self._reset_detector()

        with patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "docker"}, clear=False):
            detector = PathModeDetector()
            mode = detector.get_path_mode()

            assert mode == "docker", f"Forced mode 'docker' but detected: {mode}"

    def test_path_conversion_local_mode(self):
        """Tests path conversion in local mode."""
        self._reset_detector()

        with patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "local"}, clear=False):
            detector = PathModeDetector()
            mode = detector.get_path_mode()
            assert mode == "local", f"Forced mode 'local' but detected: {mode}"
            test_path = r"C:\Users\Test\zen-mcp-server\src\main.py"
            converted = detector.convert_path(test_path)

            # In local mode, the path should not be modified
            assert converted == test_path

    def test_path_conversion_docker_mode(self):
        """Tests path conversion in Docker mode."""
        self._reset_detector()

        with patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "docker"}, clear=False):
            detector = PathModeDetector()

            test_path = r"C:\Users\Test\zen-mcp-server\src\main.py"
            converted = detector.convert_path(test_path)

            # In Docker mode, should be converted to a Linux path
            assert converted.startswith("/app/project/")
            assert converted.endswith("src/main.py")
            assert "\\" not in converted  # No Windows backslashes

    def test_singleton_behavior(self):
        """Tests that the detector works as a singleton."""
        self._reset_detector()

        detector1 = PathModeDetector()
        detector2 = PathModeDetector()

        assert detector1 is detector2, "The detector should be a singleton"

    def test_debug_mode_output(self):
        """Tests enabling debug mode for detection."""
        self._reset_detector()

        env_vars = {
            "MCP_FILE_PATH_MODE": "auto",
            "MCP_DEBUG_PATH_DETECTION": "true",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            detector = PathModeDetector()
            mode = detector.get_path_mode()

            # Debug mode does not change detection, only verbosity
            assert mode in ["local", "docker"]

    def test_invalid_mode_fallback(self):
        """Tests behavior with an invalid mode."""
        self._reset_detector()

        with patch.dict(os.environ, {"MCP_FILE_PATH_MODE": "invalid"}, clear=False):
            detector = PathModeDetector()
            mode = detector.get_path_mode()

            # Should fallback to automatic detection
            assert mode in ["local", "docker"]


if __name__ == "__main__":
    # Direct execution for quick tests
    test = TestPathModeDetection()

    print("MCP path mode detection tests")
    print("=" * 50)

    try:
        test.test_auto_detection_current_environment()
        print("Test auto detection: PASS")

        test.test_forced_local_mode()
        print("Test forced local mode: PASS")

        test.test_forced_docker_mode()
        print("Test forced Docker mode: PASS")

        test.test_path_conversion_local_mode()
        print("Test local path conversion: PASS")

        test.test_path_conversion_docker_mode()
        print("Test Docker path conversion: PASS")

        test.test_singleton_behavior()
        print("Test singleton behavior: PASS")

        print("\nAll tests passed!")

    except Exception as e:
        print(f"Test error: {e}")
        raise
