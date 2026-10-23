"""Composition root for the GUI's application services."""

from actions.email_actions import EmailActions
from actions.news_actions import NewsActions
from actions.system_actions import SystemActions
from actions.system_actions_audio import SystemActions as AudioSystemActions
from ai.llm_client import LLMClient
from core.command_router import CommandRouter


def create_command_router() -> CommandRouter:
    return CommandRouter(
        ai=LLMClient(),
        email=EmailActions(),
        news=NewsActions(),
        system=SystemActions(),
        audio=AudioSystemActions(),
    )
