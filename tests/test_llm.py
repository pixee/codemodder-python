import os

import pytest

from codemodder.llm import MODELS


class TestModels:
    def test_get_model_name(self):
        assert MODELS.gpt_4_turbo_2024_04_09 == "gpt-4-turbo-2024-04-09"

    @pytest.mark.parametrize("model", ["gpt-4-turbo-2024-04-09", "gpt-4o-2024-05-13"])
    def test_model_get_name_from_env(self, mocker, model):
        name = "my-awesome-deployment"
        mocker.patch.dict(
            os.environ,
            {
                f"CODEMODDER_AZURE_OPENAI_{model.upper()}_DEPLOYMENT": name,
            },
        )
        assert getattr(MODELS, model.replace("-", "_")) == name
