from typing import Literal

from src.events.base import Events


class UserInput(Events):
    event: Literal["user_input"] = "user_input"
    text: str
