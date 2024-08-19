from codemodder.codemods.test import BaseCodemodTest
from core_codemods.timezone_aware_datetime import TimezoneAwareDatetime


class TestTimezoneAwareDatetimeNeedKwarg(BaseCodemodTest):
    codemod = TimezoneAwareDatetime

    def test_name(self):
        assert self.codemod.name == "timezone-aware-datetime"

    def test_import(self, tmpdir):
        input_code = """
        import datetime
        import time
        
        datetime.datetime.utcnow()
        datetime.datetime.utcfromtimestamp(time.time())
        """
        expected = """
        import datetime
        import time
        
        datetime.datetime.now(tz=datetime.timezone.utc)
        datetime.datetime.fromtimestamp(time.time(), tz=datetime.timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)

    def test_import_alias(self, tmpdir):
        input_code = """
        import datetime as mydate
        import time

        mydate.datetime.utcnow()
        mydate.datetime.utcfromtimestamp(time.time())
        """
        expected = """
        import datetime as mydate
        import time

        mydate.datetime.now(tz=mydate.timezone.utc)
        mydate.datetime.fromtimestamp(time.time(), tz=mydate.timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)

    def test_import_from(self, tmpdir):
        input_code = """
        from datetime import datetime
        import time

        datetime.utcnow()
        datetime.utcfromtimestamp(time.time())
        """
        expected = """
        from datetime import timezone, datetime
        import time

        datetime.now(tz=timezone.utc)
        datetime.fromtimestamp(time.time(), tz=timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)

    def test_import_from_alias(self, tmpdir):
        input_code = """
        from datetime import datetime as mydate
        import time

        mydate.utcnow()
        mydate.utcfromtimestamp(time.time())
        """
        expected = """
        from datetime import timezone, datetime as mydate
        import time

        mydate.now(tz=timezone.utc)
        mydate.fromtimestamp(time.time(), tz=timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)
