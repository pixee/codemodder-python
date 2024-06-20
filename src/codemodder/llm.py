from __future__ import annotations

import os
from typing import TYPE_CHECKING

try:
    from openai import AzureOpenAI, OpenAI
except ImportError:
    OpenAI = None
    AzureOpenAI = None


if TYPE_CHECKING:
    from openai import OpenAI

from codemodder.logging import logger

__all__ = [
    "MODELS",
    "setup_llm_client",
    "MisconfiguredAIClient",
]

models = ["gpt-4-turbo-2024-04-09", "gpt-4o-2024-05-13", "gpt-35-turbo-0125"]
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


def setup_llm_client() -> OpenAI | None:
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


class MisconfiguredAIClient(ValueError):
    pass
