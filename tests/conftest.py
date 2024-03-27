import pytest


@pytest.fixture(autouse=True)
def disable_write_report(mocker):
    """
    Unit tests should not write analysis report or update any source files.
    """
    mocker.patch("codemodder.codetf.CodeTF.write_report")


@pytest.fixture(autouse=True)
def disable_update_code(mocker):
    """
    Unit tests should not write analysis report or update any source files.
    """
    mocker.patch("codemodder.codemods.libcst_transformer.update_code")


@pytest.fixture(autouse=True)
def disable_semgrep_run(mocker):
    """
    Semgrep run is slow so we mock them or pass hardcoded results when possible.
    """
    mocker.patch("codemodder.codemods.semgrep.semgrep_run")


@pytest.fixture(autouse=True)
def disable_write_dependencies(mocker):
    """
    Unit tests should not write any dependency files
    """
    mocker.patch(
        "codemodder.dependency_management.dependency_manager.DependencyManager.write",
        return_value=None,
    )


@pytest.fixture(scope="module")
def pkg_with_reqs_txt(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    req_file = base_dir / "requirements.txt"
    reqs = "# comment\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    req_file.write_text(reqs)
    return base_dir


@pytest.fixture(scope="module")
def pkg_with_reqs_r_line(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    req_file = base_dir / "requirements.txt"
    second_req_file = base_dir / "more_requirements.txt"
    second_req_file.write_text("django<5")
    reqs = "# comment\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n-r more_requirements.txt\n"
    req_file.write_text(reqs)
    return base_dir


@pytest.fixture(scope="module")
def pkg_with_reqs_txt_and_comments(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    req_file = base_dir / "requirements.txt"
    reqs = "# comment\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4 # comment\npylint>1\n"
    req_file.write_text(reqs)
    return base_dir


@pytest.fixture(scope="module")
def pkg_with_reqs_txt_utf_16(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    req_file = base_dir / "requirements.txt"
    reqs = "# comment\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    req_file.write_text(reqs)
    return base_dir


@pytest.fixture(scope="module")
def pkg_with_reqs_txt_unknown_encoding(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    req_file = base_dir / "requirements.txt"
    # invalid utf8 string
    reqs = "\xf0\x28\x8c\xbc"
    req_file.write_text(reqs)
    return base_dir


@pytest.fixture(scope="module")
def pkg_with_setup_cfg(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    req_file = base_dir / "setup.cfg"
    reqs = """\
        [metadata]
        name = my_package
        version = attr: my_package.VERSION

        # some other stuff

        [options]
        include_package_data = True
        python_requires = >=3.7
        install_requires =
            requests
            importlib-metadata; python_version<"3.8"
    """
    req_file.write_text(reqs)
    return base_dir
