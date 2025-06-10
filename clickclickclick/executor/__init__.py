from abc import ABC, abstractmethod
from typing import List, ContextManager
import logging

logger = logging.getLogger(__name__)


class Executor(ABC):

    @abstractmethod
    def move_mouse(self, x: int, y: int, observation: str) -> bool:
        pass

    @abstractmethod
    def press_key(self, key: List[str], observation: str) -> bool:
        pass

    @abstractmethod
    def type_text(self, text: str, observation: str) -> bool:
        pass

    @abstractmethod
    def click_mouse(self, observation: str, button: str) -> bool:
        pass

    @abstractmethod
    def double_click_mouse(self, button: str, observation: str) -> bool:
        pass

    @abstractmethod
    def scroll(self, clicks: int, observation: str) -> bool:
        pass

    @abstractmethod
    def swipe_right(self, observation: str) -> bool:
        pass

    @abstractmethod
    def swipe_left(self, observation: str) -> bool:
        pass

    @abstractmethod
    def swipe_up(self, observation: str) -> bool:
        pass

    @abstractmethod
    def swipe_down(self, observation: str) -> bool:
        pass

    @abstractmethod
    def volume_up(self, observation: str) -> bool:
        pass

    @abstractmethod
    def volume_down(self, observation: str) -> bool:
        pass

    @abstractmethod
    def navigate_back(self, observation: str) -> bool:
        pass

    @abstractmethod
    def minimize_app(self, observation: str) -> bool:
        pass

    @abstractmethod
    def screenshot(self, observation: str) -> str:
        pass

    @abstractmethod
    def screenrecord(self, output_file: str) -> ContextManager:
        pass

    @abstractmethod
    def click_at_a_point(self, x: int, y: int, observation: str) -> bool:
        pass

    @abstractmethod
    def long_press_at_a_point(self, x: int, y: int, observation: str) -> bool:
        pass
