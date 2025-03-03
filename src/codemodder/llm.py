from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import Self

try:
    from openai import AzureOpenAI, OpenAI
except ImportError:
    OpenAI = None
    AzureOpenAI = None

try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
except ImportError:
    ChatCompletionsClient = None
    AzureKeyCredential = None

if TYPE_CHECKING:
    from openai import OpenAI
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential

from codemodder.logging import logger

__all__ = [
    "MODELS",
    "setup_openai_llm_client",
    "setup_azure_llama_llm_client",
    "MisconfiguredAIClient",
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
DEFAULT_AZURE_OPENAI_API_VERSION = "2024-02-01"


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


def setup_openai_llm_client() -> OpenAI | None:
    """Configure either the Azure OpenAI LLM client or the OpenAI client, in that order."""
    if not AzureOpenAI:
        logger.info("Azure OpenAI API client not available")
        return None

    azure_openapi_key = os.getenv("CODEMODDER_AZURE_OPENAI_API_KEY")
    azure_openapi_endpoint = os.getenv("CODEMODDER_AZURE_OPENAI_ENDPOINT")
    if bool(azure_openapi_key) ^ bool(azure_openapi_endpoint):
        raise MisconfiguredAIClient(
            "Azure OpenAI API key and endpoint must both be set or unset"
        )

    if azure_openapi_key and azure_openapi_endpoint:
        logger.info("Using Azure OpenAI API client")
        return AzureOpenAI(
            api_key=azure_openapi_key,
            api_version=os.getenv(
                "CODEMODDER_AZURE_OPENAI_API_VERSION",
                DEFAULT_AZURE_OPENAI_API_VERSION,
            ),
            azure_endpoint=azure_openapi_endpoint,
        )

    if not OpenAI:
        logger.info("OpenAI API client not available")
        return None

    if not (api_key := os.getenv("CODEMODDER_OPENAI_API_KEY")):
        logger.info("OpenAI API key not found")
        return None

    logger.info("Using OpenAI API client")
    return OpenAI(api_key=api_key)


def setup_azure_llama_llm_client() -> ChatCompletionsClient | None:
    """Configure the Azure Llama LLM client."""
    if not ChatCompletionsClient:
        logger.info("Azure Llama client not available")
        return None

    azure_llama_key = os.getenv("CODEMODDER_AZURE_LLAMA_API_KEY")
    azure_llama_endpoint = os.getenv("CODEMODDER_AZURE_LLAMA_ENDPOINT")
    if bool(azure_llama_key) ^ bool(azure_llama_endpoint):
        raise MisconfiguredAIClient(
            "Azure Llama API key and endpoint must both be set or unset"
        )

    if azure_llama_key and azure_llama_endpoint:
        logger.info("Using Azure Llama API client")
        return ChatCompletionsClient(
            credential=AzureKeyCredential(azure_llama_key),
            endpoint=azure_llama_endpoint,
        )
    return None


class MisconfiguredAIClient(ValueError):
    pass


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
