from core_codemods.sonar.api import SonarCodemod
from core_codemods.timezone_aware_datetime import TimezoneAwareDatetime

SonarTimezoneAwareDatetime = SonarCodemod.from_core_codemod(
    name="timezone-aware-datetime",
    other=TimezoneAwareDatetime,
    rule_id="python:S6903",
    rule_name='Using timezone-aware "datetime" objects should be preferred over using "datetime.datetime.utcnow" and "datetime.datetime.utcfromtimestamp"',
)
