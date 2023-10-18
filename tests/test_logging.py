from pythonjsonlogger import jsonlogger

from codemodder.logging import OutputFormat, configure_logger


def test_json_logger(mocker):
    basic_config = mocker.patch("logging.basicConfig")
    configure_logger(False, OutputFormat.JSON, "test-project")
    assert basic_config.call_count == 1
    assert basic_config.call_args[1]["format"] == "%(message)s"
    assert isinstance(
        basic_config.call_args[1]["handlers"][0].formatter,
        jsonlogger.JsonFormatter,
    )
    assert (
        basic_config.call_args[1]["handlers"][0].formatter.project_name
        == "test-project"
    )
