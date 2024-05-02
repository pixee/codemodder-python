from codemodder.codemods.test import BaseCodemodTest
from core_codemods.timezone_aware_datetime import TimezoneAwareDatetime


class TestTimezoneAwareDatetimeNeedKwarg(BaseCodemodTest):
    codemod = TimezoneAwareDatetime

    def test_name(self):
        assert self.codemod.name == "timezone-aware-datetime"

    def test_no_change(self, tmpdir):
        input_code = """
        import datetime
        from zoneinfo import ZoneInfo  
        
        eastern =  ZoneInfo("America/New_York")
        datetime.datetime(2021, 12, 25, 15, 30, 0, tzinfo=eastern)
        
        datetime.datetime.now(ZoneInfo("America/New_York"))
        datetime.datetime.now(tz=eastern)
        
        datetime.datetime.fromtimestamp(time.time(), eastern)
        datetime.datetime.fromtimestamp(time.time(), tz=eastern)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_import_datetime(self, tmpdir):
        input_code = """
        import datetime
        import time
        datetime.datetime(2021, 12, 25, 15, 30, 0)
        
        datetime.datetime.now()
        
        datetime.datetime.fromtimestamp(time.time())
        """
        expected = """
        import datetime
        import time
        datetime.datetime(2021, 12, 25, 15, 30, 0, tzinfo=datetime.timezone.utc)
        
        datetime.datetime.now(tz=datetime.timezone.utc)

        datetime.datetime.fromtimestamp(time.time(), tz=datetime.timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)


class TestTimezoneAwareDatetimeReplaceFunc(BaseCodemodTest):
    codemod = TimezoneAwareDatetime

    def test_no_change(self, tmpdir):
        input_code = """
        import datetime
        
        datetime.datetime.now(tz=datetime.timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_import_datetime(self, tmpdir):
        input_code = """
        import datetime
        import time
        from zoneinfo import ZoneInfo
        
        datetime.datetime.today()
        datetime.date.today()
        datetime.datetime.utcnow()
        
        datetime.date.fromtimestamp(time.time())
        eastern =  ZoneInfo("America/New_York")
        datetime.date.fromtimestamp(time.time(), eastern)
        datetime.date.fromtimestamp(time.time(), tz=eastern)

        datetime.datetime.utcfromtimestamp(time.time())
        datetime.datetime.utcfromtimestamp(time.time(), eastern)
        datetime.datetime.utcfromtimestamp(time.time(), tz=eastern)
        """
        expected = """
        import datetime
        import time
        from zoneinfo import ZoneInfo
        
        datetime.datetime.now(tz=datetime.timezone.utc)
        datetime.datetime.now(tz=datetime.timezone.utc)
        datetime.datetime.now(tz=datetime.timezone.utc)
        
        datetime.datetime.fromtimestamp(time.time(), tz=datetime.timezone.utc).date()
        eastern =  ZoneInfo("America/New_York")
        datetime.datetime.fromtimestamp(time.time(), eastern).date()
        datetime.datetime.fromtimestamp(time.time(), tz=eastern).date()

        datetime.datetime.fromtimestamp(time.time(), tz=datetime.timezone.utc)
        datetime.datetime.fromtimestamp(time.time(), eastern)
        datetime.datetime.fromtimestamp(time.time(), tz=eastern)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=9)
