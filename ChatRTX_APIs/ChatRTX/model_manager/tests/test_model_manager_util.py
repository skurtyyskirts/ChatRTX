# ruff: noqa: E402
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys

# Mock missing dependencies
sys.modules['ngcsdk'] = MagicMock()
sys.modules['tqdm'] = MagicMock()
sys.modules['requests'] = MagicMock()

from ChatRTX.model_manager.model_manager_util import execute_command

class TestModelManagerUtil(unittest.TestCase):

    @patch('subprocess.run')
    @patch('builtins.print')
    def test_execute_command_success(self, mock_print, mock_subprocess_run):
        # Setup mock for successful command execution
        mock_process = MagicMock()
        mock_process.stdout.decode.return_value = "Mocked stdout output"
        mock_process.stderr.decode.return_value = "Mocked stderr output"
        mock_subprocess_run.return_value = mock_process

        # Call the function
        execute_command("echo test")

        # Verify subprocess.run was called correctly
        mock_subprocess_run.assert_called_once_with("echo test", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Verify print was called correctly
        self.assertEqual(mock_print.call_count, 2)
        mock_print.assert_any_call("Mocked stdout output")
        mock_print.assert_any_call("Mocked stderr output")

    @patch('subprocess.run')
    @patch('builtins.print')
    def test_execute_command_called_process_error(self, mock_print, mock_subprocess_run):
        # Setup mock to raise CalledProcessError
        error = subprocess.CalledProcessError(returncode=1, cmd="bad_command")
        error.stdout = b"Error stdout output"
        error.stderr = b"Error stderr output"
        mock_subprocess_run.side_effect = error

        # Call the function
        execute_command("bad_command")

        # Verify subprocess.run was called correctly
        mock_subprocess_run.assert_called_once_with("bad_command", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Verify print was called correctly with error information
        self.assertEqual(mock_print.call_count, 3)
        mock_print.assert_any_call(f"An error occurred while executing the command: {error}")
        mock_print.assert_any_call("Error stdout output")
        mock_print.assert_any_call("Error stderr output")

if __name__ == '__main__':
    unittest.main()
