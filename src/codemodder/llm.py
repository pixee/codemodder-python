from __future__ import annotations

import os
from dataclasses import dataclass

from typing_extensions import Self

from codemodder.logging import logger

__all__ = [
    "MODELS",
    "TokenUsage",
    "log_token_usage",
]

models = [
    "gpt-4-turbo-2024-04-09",
    "gpt-4o-2024-05-13",
    "gpt-35-turbo-0125",
    "o1-mini",
    "o1",
]


class ModelRegistry(dict):
    def __init__(self, models):
        super().__init__()
        self.models = models
        for model in models:
            attribute_name = model.replace("-", "_")
            self[attribute_name] = model

    def __getattr__(self, name):
        if name in self:
            return os.getenv(
                f"CODEMODDER_AZURE_OPENAI_{name.upper()}_DEPLOYMENT", self[name]
            )
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


MODELS = ModelRegistry(models)


@dataclass
class TokenUsage:
    completion_tokens: int = 0
    prompt_tokens: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            completion_tokens=self.completion_tokens + other.completion_tokens,
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
        )

    def __iadd__(self, other: TokenUsage) -> Self:
        self.completion_tokens += other.completion_tokens
        self.prompt_tokens += other.prompt_tokens
        return self

    @property
    def total(self):
        return self.completion_tokens + self.prompt_tokens


def log_token_usage(header: str, token_usage: TokenUsage):
    logger.info(
        "%s token usage\n\tcompletion_tokens = %s\n\tprompt_tokens = %s",
        header,
        token_usage.completion_tokens,
        token_usage.prompt_tokens,
    )
