import unittest
from unittest.mock import patch, MagicMock
import pyautogui
from clickclickclick.executor.osx import MacExecutor
from clickclickclick.executor import logger
import io
from PIL import Image
import base64
import tempfile
import os


class TestMacExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = MacExecutor()
        # mock the logger
        self.logger = MagicMock()
        self.executor.logger = self.logger
        logger.logger = self.logger

    @patch("pyautogui.moveTo")
    def test_move_mouse(self, mock_move_to):
        self.assertTrue(self.executor.move_mouse(100, 200, "observation"))
        mock_move_to.assert_called_once_with(200, 100, 1)
        self.logger.debug.assert_called_with("move mouse x y 100 200")

    @patch("pyautogui.moveTo", side_effect=Exception("Test Exception"))
    def test_move_mouse_exception(self, mock_move_to):
        self.assertFalse(self.executor.move_mouse(100, 200, "observation"))
        self.logger.exception.assert_called_with("Error in move_mouse")

    @patch("pyautogui.hotkey")
    def test_press_key(self, mock_hotkey):
        self.assertTrue(self.executor.press_key(["Ctrl", "A"], "observation"))
        mock_hotkey.assert_called_once_with("ctrl", "a")
        self.logger.debug.assert_called_with("press keys ['Ctrl', 'A']")

    @patch("pyautogui.hotkey", side_effect=Exception("Test Exception"))
    def test_press_key_exception(self, mock_hotkey):
        self.assertFalse(self.executor.press_key(["Ctrl", "A"], "observation"))
        self.logger.exception.assert_called_with("Error in press_key")

    @patch("pyautogui.write")
    def test_type_text(self, mock_write):
        self.assertTrue(self.executor.type_text("hello", "observation"))
        mock_write.assert_called_once_with("hello")
        self.logger.debug.assert_called_with("type text hello")

    @patch("pyautogui.write", side_effect=Exception("Test Exception"))
    def test_type_text_exception(self, mock_write):
        self.assertFalse(self.executor.type_text("hello", "observation"))
        self.logger.exception.assert_called_with("Error in type_text")

    @patch("pyautogui.click")
    def test_click_mouse(self, mock_click):
        self.assertTrue(self.executor.click_mouse("observation"))
        mock_click.assert_called_once_with(button="left")
        self.logger.debug.assert_called_with("click mouse left")

    @patch("pyautogui.click", side_effect=Exception("Test Exception"))
    def test_click_mouse_exception(self, mock_click):
        self.assertFalse(self.executor.click_mouse("observation"))
        self.logger.exception.assert_called_with("Error in click_mouse")

    @patch("pyautogui.doubleClick")
    def test_double_click_mouse(self, mock_double_click):
        self.assertTrue(self.executor.double_click_mouse("left", "observation"))
        mock_double_click.assert_called_once_with(button="left")
        self.logger.debug.assert_called_with("doubleclick mouse left")

    @patch("pyautogui.doubleClick", side_effect=Exception("Test Exception"))
    def test_double_click_mouse_exception(self, mock_double_click):
        self.assertFalse(self.executor.double_click_mouse("left", "observation"))
        self.logger.exception.assert_called_with("Error in double_click_mouse")

    @patch("pyautogui.scroll")
    def test_scroll(self, mock_scroll):
        self.assertTrue(self.executor.scroll(10, "observation"))
        mock_scroll.assert_called_once_with(10)
        self.logger.debug.assert_called_with("scroll 10")

    @patch("pyautogui.scroll", side_effect=Exception("Test Exception"))
    def test_scroll_exception(self, mock_scroll):
        self.assertFalse(self.executor.scroll(10, "observation"))
        self.logger.exception.assert_called_with("Error in scroll")

    @patch("pyautogui.click")
    def test_click_at_a_point(self, mock_click):
        self.assertTrue(self.executor.click_at_a_point(100, 200, "observation"))
        mock_click.assert_called_once_with(x=200, y=100, duration=1)
        self.logger.debug.assert_called_with("click at a point x y 100 200")

    @patch("pyautogui.click", side_effect=Exception("Test Exception"))
    def test_click_at_a_point_exception(self, mock_click):
        self.assertFalse(self.executor.click_at_a_point(100, 200, "observation"))
        self.logger.exception.assert_called_with("Error in click_at_a_point")

    def test_swipe_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.executor.swipe_left("observation")
        with self.assertRaises(NotImplementedError):
            self.executor.swipe_right("observation")
        with self.assertRaises(NotImplementedError):
            self.executor.swipe_up("observation")
        with self.assertRaises(NotImplementedError):
            self.executor.swipe_down("observation")

    def test_volume_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.executor.volume_up("observation")
        with self.assertRaises(NotImplementedError):
            self.executor.volume_down("observation")

    def test_navigate_back_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.executor.navigate_back("observation")

    def test_minimize_app_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.executor.minimize_app("observation")

    @patch("pyautogui.screenshot")
    def test_screenshot_default(self, mock_screenshot):
        mock_image = MagicMock(spec=Image.Image)
        mock_screenshot.return_value = mock_image
        result = self.executor.screenshot("observation")
        self.assertEqual(result, mock_image)
        self.logger.debug.assert_called_with("Take a screenshot use_tempfile=False")

    @patch("pyautogui.screenshot")
    def test_screenshot_as_base64(self, mock_screenshot):
        mock_image = MagicMock(spec=Image.Image)
        mock_image.save = MagicMock()
        mock_screenshot.return_value = mock_image
        result = self.executor.screenshot("observation", as_base64=True)
        mock_image.save.assert_called_once()
        self.assertIsInstance(result, str)

    @patch("pyautogui.screenshot")
    def test_screenshot_as_tempfile(self, mock_screenshot):
        mock_image = MagicMock(spec=Image.Image)
        mock_image.save = MagicMock()
        mock_screenshot.return_value = mock_image
        result = self.executor.screenshot("observation", use_tempfile=True)
        mock_image.save.assert_called_once()
        self.assertTrue(os.path.exists(result))
        os.remove(result)  # Clean up the temp file

    @patch("pyautogui.screenshot")
    def test_screenshot_exception(self, mock_screenshot):
        mock_screenshot.side_effect = Exception("Test exception")
        result = self.executor.screenshot("observation", as_base64=True)
        self.assertEqual(result, "")
        self.logger.exception.assert_called_with("Error in screenshot")

    @patch("pyautogui.screenshot")
    def test_screenshot_as_tempfile_exception(self, mock_screenshot):
        mock_screenshot.side_effect = Exception("Test exception")
        result = self.executor.screenshot("observation", use_tempfile=True)
        self.assertEqual(result, "")
        self.logger.exception.assert_called_with("Error in screenshot")

    @patch("applescript.AppleScript")
    def test_apple_script(self, mock_applescript):
        mock_script = MagicMock()
        mock_applescript.return_value = mock_script
        mock_script.run.return_value = "Test Result"

        self.assertTrue(self.executor.apple_script('tell application "Finder"', "observation"))
        self.logger.info.assert_called_with("Test Result")
        self.logger.debug.assert_called_with('Run apple script tell application "Finder"')

    @patch("applescript.AppleScript")
    def test_apple_script_exception(self, mock_applescript):
        mock_script = MagicMock()
        mock_applescript.return_value = mock_script
        mock_script.run.side_effect = Exception("Test exception")

        self.assertFalse(self.executor.apple_script('tell application "Finder"', "observation"))
        self.logger.exception.assert_called_with("Error in apple_script Test exception")
