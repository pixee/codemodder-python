from core_codemods.secure_random import SecureRandom
from core_codemods.sonar.api import SonarCodemod

SonarSecureRandom = SonarCodemod.from_core_codemod(
    name="secure-random",
    other=SecureRandom,
    rule_id="python:S2245",
    rule_name="Using pseudorandom number generators (PRNGs) is security-sensitive",
)
