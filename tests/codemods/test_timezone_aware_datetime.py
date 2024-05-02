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

    def test_import(self, tmpdir):
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

    def test_import_alias(self, tmpdir):
        input_code = """
        import datetime as mydate
        import time
        mydate.datetime(2021, 12, 25, 15, 30, 0)

        mydate.datetime.now()

        mydate.datetime.fromtimestamp(time.time())
        """
        expected = """
        import datetime as mydate
        import time
        mydate.datetime(2021, 12, 25, 15, 30, 0, tzinfo=mydate.timezone.utc)

        mydate.datetime.now(tz=mydate.timezone.utc)

        mydate.datetime.fromtimestamp(time.time(), tz=mydate.timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)

    def test_import_from(self, tmpdir):
        input_code = """
        from datetime import datetime
        import time
        datetime(2021, 12, 25, 15, 30, 0)

        datetime.now()

        datetime.fromtimestamp(time.time())
        """
        expected = """
        from datetime import timezone, datetime
        import time
        datetime(2021, 12, 25, 15, 30, 0, tzinfo=timezone.utc)

        datetime.now(tz=timezone.utc)

        datetime.fromtimestamp(time.time(), tz=timezone.utc)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)

    def test_import_from_alias(self, tmpdir):
        input_code = """
        from datetime import datetime as mydate
        import time
        mydate(2021, 12, 25, 15, 30, 0)

        mydate.now()

        mydate.fromtimestamp(time.time())
        """
        expected = """
        from datetime import timezone, datetime as mydate
        import time
        mydate(2021, 12, 25, 15, 30, 0, tzinfo=timezone.utc)

        mydate.now(tz=timezone.utc)

        mydate.fromtimestamp(time.time(), tz=timezone.utc)
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

    def test_import(self, tmpdir):
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
        datetime.datetime.now(tz=datetime.timezone.utc).date()
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

    def test_import_alias(self, tmpdir):
        input_code = """
        import datetime as mydate
        import time
        from zoneinfo import ZoneInfo

        mydate.datetime.today()
        mydate.date.today()
        mydate.datetime.utcnow()

        mydate.date.fromtimestamp(time.time())
        eastern =  ZoneInfo("America/New_York")
        mydate.date.fromtimestamp(time.time(), eastern)
        mydate.date.fromtimestamp(time.time(), tz=eastern)

        mydate.datetime.utcfromtimestamp(time.time())
        mydate.datetime.utcfromtimestamp(time.time(), eastern)
        mydate.datetime.utcfromtimestamp(time.time(), tz=eastern)
        """
        expected = """
        import datetime as mydate
        import time
        from zoneinfo import ZoneInfo

        mydate.datetime.now(tz=mydate.timezone.utc)
        mydate.datetime.now(tz=mydate.timezone.utc).date()
        mydate.datetime.now(tz=mydate.timezone.utc)

        mydate.datetime.fromtimestamp(time.time(), tz=mydate.timezone.utc).date()
        eastern =  ZoneInfo("America/New_York")
        mydate.datetime.fromtimestamp(time.time(), eastern).date()
        mydate.datetime.fromtimestamp(time.time(), tz=eastern).date()

        mydate.datetime.fromtimestamp(time.time(), tz=mydate.timezone.utc)
        mydate.datetime.fromtimestamp(time.time(), eastern)
        mydate.datetime.fromtimestamp(time.time(), tz=eastern)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=9)

    def test_import_from(self, tmpdir):
        input_code = """
        from datetime import date, datetime
        import time
        from zoneinfo import ZoneInfo

        datetime.today()
        date.today()
        datetime.utcnow()

        date.fromtimestamp(time.time())
        eastern =  ZoneInfo("America/New_York")
        date.fromtimestamp(time.time(), eastern)
        date.fromtimestamp(time.time(), tz=eastern)

        datetime.utcfromtimestamp(time.time())
        datetime.utcfromtimestamp(time.time(), eastern)
        datetime.utcfromtimestamp(time.time(), tz=eastern)
        """
        expected = """
        from datetime import timezone, date, datetime
        import time
        from zoneinfo import ZoneInfo

        datetime.now(tz=timezone.utc)
        datetime.now(tz=timezone.utc).date()
        datetime.now(tz=timezone.utc)

        datetime.fromtimestamp(time.time(), tz=timezone.utc).date()
        eastern =  ZoneInfo("America/New_York")
        datetime.fromtimestamp(time.time(), eastern).date()
        datetime.fromtimestamp(time.time(), tz=eastern).date()

        datetime.fromtimestamp(time.time(), tz=timezone.utc)
        datetime.fromtimestamp(time.time(), eastern)
        datetime.fromtimestamp(time.time(), tz=eastern)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=9)

    def test_import_from_alias(self, tmpdir):
        input_code = """
        from datetime import date, datetime as mydate
        import time
        from zoneinfo import ZoneInfo

        mydate.today()
        date.today()
        mydate.utcnow()

        date.fromtimestamp(time.time())
        eastern =  ZoneInfo("America/New_York")
        date.fromtimestamp(time.time(), eastern)
        date.fromtimestamp(time.time(), tz=eastern)

        mydate.utcfromtimestamp(time.time())
        mydate.utcfromtimestamp(time.time(), eastern)
        mydate.utcfromtimestamp(time.time(), tz=eastern)
        """
        expected = """
        from datetime import timezone, date, datetime as mydate
        import time
        from zoneinfo import ZoneInfo

        mydate.now(tz=timezone.utc)
        mydate.now(tz=timezone.utc).date()
        mydate.now(tz=timezone.utc)

        mydate.fromtimestamp(time.time(), tz=timezone.utc).date()
        eastern =  ZoneInfo("America/New_York")
        mydate.fromtimestamp(time.time(), eastern).date()
        mydate.fromtimestamp(time.time(), tz=eastern).date()

        mydate.fromtimestamp(time.time(), tz=timezone.utc)
        mydate.fromtimestamp(time.time(), eastern)
        mydate.fromtimestamp(time.time(), tz=eastern)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=9)

    # def test_import_date(self, tmpdir):
    #     input_code = """
    #     from datetime import date
    #     date.today()
    #     """
    #     # need to handle original node being "date", import from, alias, etc
