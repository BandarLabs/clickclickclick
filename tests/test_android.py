import unittest
from unittest.mock import patch, MagicMock
from subprocess import CompletedProcess
from clickclickclick.executor.android import (
    AndroidExecutor,
    run_adb_command,
    sanitize_for_adb,
)
from clickclickclick.executor import logger
import io
from PIL import Image
import base64
import tempfile
import os


class TestAndroidExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = AndroidExecutor()
        # mock the logger
        self.logger = MagicMock()
        self.executor.logger = self.logger
        logger.logger = self.logger

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_move_mouse(self, mock_run_adb_command):
        self.assertTrue(self.executor.move_mouse(100, 200, "observation"))
        mock_run_adb_command.assert_called_once_with(["shell", "input", "tap", "100", "200"])
        self.logger.debug.assert_called_with("move mouse x y 100 200")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_move_mouse_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.move_mouse(100, 200, "observation"))
        self.logger.exception.assert_called_with("Error in move_mouse")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_press_key(self, mock_run_adb_command):
        self.assertTrue(self.executor.press_key(["Ctrl", "A"], "observation"))
        mock_run_adb_command.assert_any_call(["shell", "input", "keyevent", "CTRL"])
        mock_run_adb_command.assert_any_call(["shell", "input", "keyevent", "A"])
        self.logger.debug.assert_called_with("press keys ['Ctrl', 'A']")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_press_key_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.press_key(["Ctrl", "A"], "observation"))
        self.logger.exception.assert_called_with("Error in press_key")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_type_text(self, mock_run_adb_command):
        self.assertTrue(self.executor.type_text("hello", "observation"))
        mock_run_adb_command.assert_called_with(["shell", "input", "text", "'hello'"])
        self.logger.debug.assert_called_with("type text hello")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_type_text_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.type_text("hello", "observation"))
        self.logger.exception.assert_called_with("Error in type_text")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_type_text_multiline(self, mock_run_adb_command):
        self.assertTrue(self.executor.type_text("hello\nworld\n", "observation"))
        mock_run_adb_command.assert_any_call(["shell", "input", "text", "'hello'"])
        mock_run_adb_command.assert_any_call(["shell", "input", "keyevent", "66"])
        mock_run_adb_command.assert_any_call(["shell", "input", "text", "'world'"])
        mock_run_adb_command.assert_any_call(["shell", "input", "keyevent", "66"])
        mock_run_adb_command.assert_any_call(["shell", "input", "keyevent", "66"])

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_scroll_up(self, mock_run_adb_command):
        self.assertTrue(self.executor.scroll(10, "observation"))
        # Calculate expected coordinates based on executor properties
        start_y = self.executor.screen_center_y + self.executor.scroll_distance // 2
        end_y = self.executor.screen_center_y - self.executor.scroll_distance // 2
        expected_call = [
            "shell",
            "input",
            "swipe",
            str(self.executor.screen_center_x),
            str(start_y),
            str(self.executor.screen_center_x),
            str(end_y),
        ]
        mock_run_adb_command.assert_called_once_with(expected_call)
        self.logger.debug.assert_called_with("scroll 10")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_scroll_down(self, mock_run_adb_command):
        self.assertTrue(self.executor.scroll(-10, "observation"))
        # Calculate expected coordinates based on executor properties
        start_y = self.executor.screen_center_y - self.executor.scroll_distance // 2
        end_y = self.executor.screen_center_y + self.executor.scroll_distance // 2
        expected_call = [
            "shell",
            "input",
            "swipe",
            str(self.executor.screen_center_x),
            str(start_y),
            str(self.executor.screen_center_x),
            str(end_y),
        ]
        mock_run_adb_command.assert_called_once_with(expected_call)
        self.logger.debug.assert_called_with("scroll -10")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_scroll_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.scroll(10, "observation"))
        self.logger.exception.assert_called_with("Error in scroll")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_swipe_left(self, mock_run_adb_command):
        self.assertTrue(self.executor.swipe_left("observation"))
        # Calculate expected coordinates based on executor properties
        start_x = self.executor.screen_center_x + self.executor.swipe_distance // 2
        end_x = self.executor.screen_center_x - self.executor.swipe_distance // 2
        expected_call = [
            "shell",
            "input",
            "swipe",
            str(start_x),
            str(self.executor.screen_center_y),
            str(end_x),
            str(self.executor.screen_center_y),
        ]
        mock_run_adb_command.assert_called_once_with(expected_call)
        self.logger.debug.assert_called_with("swipe left")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_swipe_left_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.swipe_left("observation"))
        self.logger.exception.assert_called_with("Error in swipe_left")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_swipe_right(self, mock_run_adb_command):
        self.assertTrue(self.executor.swipe_right("observation"))
        # Calculate expected coordinates based on executor properties
        start_x = self.executor.screen_center_x - self.executor.swipe_distance // 2
        end_x = self.executor.screen_center_x + self.executor.swipe_distance // 2
        expected_call = [
            "shell",
            "input",
            "swipe",
            str(start_x),
            str(self.executor.screen_center_y),
            str(end_x),
            str(self.executor.screen_center_y),
        ]
        mock_run_adb_command.assert_called_once_with(expected_call)
        self.logger.debug.assert_called_with("swipe right")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_swipe_right_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.swipe_right("observation"))
        self.logger.exception.assert_called_with("Error in swipe_right")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_swipe_up(self, mock_run_adb_command):
        self.assertTrue(self.executor.swipe_up("observation"))
        # Calculate expected coordinates based on executor properties
        start_y = self.executor.screen_center_y + self.executor.scroll_distance // 2
        end_y = self.executor.screen_center_y - self.executor.scroll_distance // 2
        expected_call = [
            "shell",
            "input",
            "swipe",
            str(self.executor.screen_center_x),
            str(start_y),
            str(self.executor.screen_center_x),
            str(end_y),
        ]
        mock_run_adb_command.assert_called_once_with(expected_call)
        self.logger.debug.assert_called_with("swipe up")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_swipe_up_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.swipe_up("observation"))
        self.logger.exception.assert_called_with("Error in swipe_up")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_swipe_down(self, mock_run_adb_command):
        self.assertTrue(self.executor.swipe_down("observation"))
        # Calculate expected coordinates based on executor properties
        start_y = self.executor.screen_center_y - self.executor.scroll_distance // 2
        end_y = self.executor.screen_center_y + self.executor.scroll_distance // 2
        expected_call = [
            "shell",
            "input",
            "swipe",
            str(self.executor.screen_center_x),
            str(start_y),
            str(self.executor.screen_center_x),
            str(end_y),
        ]
        mock_run_adb_command.assert_called_once_with(expected_call)
        self.logger.debug.assert_called_with("swipe down")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_swipe_down_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.swipe_down("observation"))
        self.logger.exception.assert_called_with("Error in swipe_down")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_volume_up(self, mock_run_adb_command):
        self.assertTrue(self.executor.volume_up("observation"))
        mock_run_adb_command.assert_called_once_with(
            ["shell", "input", "keyevent", "KEYCODE_VOLUME_UP"]
        )
        self.logger.debug.assert_called_with("volume up")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_volume_up_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.volume_up("observation"))
        self.logger.exception.assert_called_with("Error in volume_up")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_volume_down(self, mock_run_adb_command):
        self.assertTrue(self.executor.volume_down("observation"))
        mock_run_adb_command.assert_called_once_with(
            ["shell", "input", "keyevent", "KEYCODE_VOLUME_DOWN"]
        )
        self.logger.debug.assert_called_with("volume down")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_volume_down_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.volume_down("observation"))
        self.logger.exception.assert_called_with("Error in volume_down")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_navigate_back(self, mock_run_adb_command):
        self.assertTrue(self.executor.navigate_back("observation"))
        mock_run_adb_command.assert_called_once_with(["shell", "input", "keyevent", "KEYCODE_BACK"])
        self.logger.debug.assert_called_with("navigate back")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_navigate_back_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.navigate_back("observation"))
        self.logger.exception.assert_called_with("Error in navigate_back")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_minimize_app(self, mock_run_adb_command):
        self.assertTrue(self.executor.minimize_app("observation"))
        mock_run_adb_command.assert_called_once_with(["shell", "input", "keyevent", "KEYCODE_HOME"])
        self.logger.debug.assert_called_with("minimize app")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_minimize_app_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.minimize_app("observation"))
        self.logger.exception.assert_called_with("Error in minimize_app")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_click_at_a_point(self, mock_run_adb_command):
        self.assertTrue(self.executor.click_at_a_point(100, 200, "observation"))
        mock_run_adb_command.assert_called_once_with(["shell", "input", "tap", "100", "200"])
        self.logger.debug.assert_called_with("click at a point x y 100 200")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_click_at_a_point_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.click_at_a_point(100, 200, "observation"))
        self.logger.exception.assert_called_with("Error in click_at_a_point")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_long_press_at_a_point(self, mock_run_adb_command):
        self.assertTrue(self.executor.long_press_at_a_point(100, 200, "observation", duration=500))
        mock_run_adb_command.assert_called_once_with(
            ["shell", "input", "swipe", "100", "200", "100", "200", "500"]
        )
        self.logger.debug.assert_called_with("Long press at a point x y 100 200 for duration 500")

    @patch(
        "clickclickclick.executor.android.run_adb_command",
        side_effect=Exception("Test Exception"),
    )
    def test_long_press_at_a_point_exception(self, mock_run_adb_command):
        self.assertFalse(self.executor.long_press_at_a_point(100, 200, "observation", duration=500))
        self.logger.exception.assert_called_with("Error in long_press_at_a_point")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_screenshot_default(self, mock_run_adb_command):
        mock_process = MagicMock(spec=CompletedProcess)
        mock_process.returncode = 0
        mock_process.stdout = b"PNG data"  # Dummy PNG data
        mock_run_adb_command.return_value = mock_process
        result = self.executor.screenshot("observation")
        self.assertIsInstance(result, Image.Image)
        self.logger.debug.assert_called_with("Take a screenshot use_tempfile=False")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_screenshot_as_base64(self, mock_run_adb_command):
        mock_process = MagicMock(spec=CompletedProcess)
        mock_process.returncode = 0
        mock_process.stdout = b"PNG data"  # Dummy PNG data
        mock_run_adb_command.return_value = mock_process
        result = self.executor.screenshot("observation", as_base64=True)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.logger.debug.assert_called_with("Take a screenshot use_tempfile=False")

    @patch("clickclickclick.executor.android.run_adb_command")
    def test_screenshot_as_tempfile(self, mock_run_adb_command):
        mock_process = MagicMock(spec=CompletedProcess)
        mock_process.returncode = 0
        mock_process.stdout = b"PNG data"  # Dummy PNG data
        mock_run_adb_command.return_value = mock_process
        result = self.executor.screenshot("observation", use_tempfile=True)
        self.assertTrue(os.path.exists(result))
        self.logger.debug.assert_called_with("Take a screenshot use_tempfile=True")
        os.remove(result)
