import os

import pytest

from codemodder.llm import MODELS, TokenUsage, models


class TestModels:
    def test_get_model_name(self):
        assert MODELS.gpt_4_turbo_2024_04_09 == "gpt-4-turbo-2024-04-09"

    @pytest.mark.parametrize("model", models)
    def test_model_get_name_from_env(self, mocker, model):
        name = "my-awesome-deployment"
        attr_name = model.replace("-", "_")
        mocker.patch.dict(
            os.environ,
            {
                f"CODEMODDER_AZURE_OPENAI_{attr_name.upper()}_DEPLOYMENT": name,
            },
        )
        assert getattr(MODELS, attr_name) == name


def test_token_usage():
    token_usage = TokenUsage()
    token_usage += TokenUsage(10, 5)
    assert token_usage.completion_tokens == 10
    assert token_usage.prompt_tokens == 5
    assert token_usage.total == 15
