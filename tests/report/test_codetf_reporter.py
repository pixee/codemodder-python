import json

import mock
import pytest

from codemodder.report.codetf_reporter import CodeTF


@pytest.fixture(autouse=True, scope="module")
def disable_write_report():
    """Disable write_report mocking so it can be properlly tested"""
    patch_open = mock.patch("builtins.open")
    patch_open.start()
    yield
    patch_open.stop()


class TestCodeTfReporter:
    @mock.patch("json.dump")
    def test_write_report(self, mock_dump):
        reporter = CodeTF()
        res = reporter.write_report("any/file")
        assert res == 0
        mock_dump.assert_called()

    @mock.patch("json.dump", side_effect=json.JSONDecodeError)
    def test_write_report_fails(self, mock_dump):
        reporter = CodeTF()
        res = reporter.write_report("any/file")
        assert res == 2
        mock_dump.assert_called()
