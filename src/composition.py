"""Application composition root shared by desktop, API and voice entry points."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from actions.email_actions import EmailActions
from actions.news_actions import NewsActions
from actions.system_actions import SystemActions
from actions.system_actions_audio import SystemActions as AudioSystemActions
from ai.llm_client import LLMClient
from core.command_router import CommandRouter
from core.local_features import LocalCommandService, LocalStore


@dataclass(frozen=True)
class Application:
    """Shared runtime services for any JARVIS interface."""

    router: CommandRouter
    store: LocalStore
    ai: Any


def create_application(
    *,
    store: LocalStore | None = None,
    ai=None,
    email=None,
    news=None,
    system=None,
    audio=None,
) -> Application:
    """Build the application once, keeping UI and transport adapters thin.

    Optional dependencies make the composition root straightforward to test
    without starting microphones, online clients, or the real SQLite store.
    """
    local_store = store if store is not None else LocalStore()
    ai_service = ai if ai is not None else LLMClient()
    if hasattr(ai_service, "provider_preference"):
        ai_service.provider_preference = local_store.get_preferences().get("llm_provider", "auto")

    router = CommandRouter(
        ai=ai_service,
        email=email if email is not None else EmailActions(),
        news=news if news is not None else NewsActions(),
        system=system if system is not None else SystemActions(),
        audio=audio if audio is not None else AudioSystemActions(),
        local_commands=LocalCommandService(local_store),
    )
    return Application(router=router, store=local_store, ai=ai_service)


def create_command_router(**dependencies) -> CommandRouter:
    """Compatibility helper for callers that need only the shared router."""
    return create_application(**dependencies).router
