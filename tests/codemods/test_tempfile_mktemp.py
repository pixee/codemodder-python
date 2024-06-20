import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.tempfile_mktemp import TempfileMktemp


class TestTempfileMktemp(BaseCodemodTest):
    codemod = TempfileMktemp

    def test_name(self):
        assert self.codemod.name == "secure-tempfile"

    def test_no_change(self, tmpdir):
        input_code = """
        import tempfile
        tempfile.mktemp()
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_import(self, tmpdir):
        input_code = """
        import tempfile

        name = tempfile.mktemp()
        var = "hello"
        """
        expected_output = """
        import tempfile
        
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            name = tf.name
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_as_sink(self, tmpdir):
        input_code = """
        import tempfile

        print(tempfile.mktemp())
        var = "hello"
        bool(tempfile.mktemp())
        """
        expected_output = """
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            print(tf.name)
        var = "hello"
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            bool(tf.name)
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

    def test_import_with_arg(self, tmpdir):
        input_code = """
        import tempfile

        filename = tempfile.mktemp('suffix')
        print(tempfile.mktemp('suffix', 'prefix'))
        filename = tempfile.mktemp('suffix', 'prefix', 'dir')
        filename = tempfile.mktemp('suffix', prefix='prefix')
        filename = tempfile.mktemp(suffix='suffix', prefix='prefix', dir='dir')
        var = "hello"
        """
        expected_output = """
        import tempfile

        with tempfile.NamedTemporaryFile(suffix="suffix", delete=False) as tf:
            filename = tf.name
        with tempfile.NamedTemporaryFile(suffix="suffix", prefix="prefix", delete=False) as tf:
            print(tf.name)
        with tempfile.NamedTemporaryFile(suffix="suffix", prefix="prefix", dir="dir", delete=False) as tf:
            filename = tf.name
        with tempfile.NamedTemporaryFile(suffix="suffix", prefix="prefix", delete=False) as tf:
            filename = tf.name
        with tempfile.NamedTemporaryFile(suffix="suffix", prefix="prefix", dir="dir", delete=False) as tf:
            filename = tf.name
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected_output, 5)

    def test_from_import(self, tmpdir):
        input_code = """
        from tempfile import mktemp

        filename = mktemp()
        print(filename)
        """
        expected_output = """
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            filename = tf.name
        print(filename)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_import_alias(self, tmpdir):
        input_code = """
        import tempfile as _tempfile

        filename = _tempfile.mktemp()
        var = "hello"
        _tempfile.template
        """
        expected_output = """
        import tempfile as _tempfile
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            filename = tf.name
        var = "hello"
        _tempfile.template
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_import_method_alias(self, tmpdir):
        input_code = """
        from tempfile import mktemp as get_temp_file

        filename = get_temp_file()
        var = "hello"
        """
        expected_output = """
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            filename = tf.name
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_random_multifunctions(self, tmpdir):
        input_code = """
        from tempfile import mktemp, TemporaryFile

        filename = mktemp()
        TemporaryFile()
        var = "hello"
        """
        expected_output = """
        from tempfile import TemporaryFile
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            filename = tf.name
        TemporaryFile()
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_open_and_write_no_change(self, tmpdir):
        input_code = """
        import tempfile

        tmp_file = open(tempfile.mktemp(), "w+")
        tmp_file.write("text")
        print(tmp_file.name)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        import tempfile
        name = tempfile.mktemp()
        """
        lines_to_exclude = [3]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )

    def test_in_func_scope(self, tmpdir):
        input_code = """
        import tempfile

        def make_file():
            filename = tempfile.mktemp()
        """
        expected_output = """
        import tempfile

        def make_file():
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                filename = tf.name
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.xfail(reason="Not currently supported")
    def test_as_str_concat(self, tmpdir):
        input_code = """
        import tempfile

        var = "hello"
        filename = tempfile.mktemp() + var
        """
        expected_output = """
        import tempfile

        var = "hello"

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            filename = tf.name + var
        """
        self.run_and_assert(tmpdir, input_code, expected_output)


@pytest.mark.xfail(reason="Not currently supported")
class TestOpenTempfileMktemp(BaseCodemodTest):
    codemod = TempfileMktemp

    def test_open_and_write(self, tmpdir):
        input_code = """
        import tempfile

        tmp_file = open(tempfile.mktemp(), "w+")
        tmp_file.write("text")
        """
        expected_output = """
        import tempfile

        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write("text")
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_open_write_close(self, tmpdir):
        input_code = """
        import tempfile

        tmp_file = open(tempfile.mktemp(), "w+")
        tmp_file.write("text")
        print(tmp_file.name)
        tmp_file.close()
        """
        expected_output = """
        import tempfile

        with tempfile.NamedTemporaryFile("w+") as tf:
            tf.write("text")
            print(tmp_file.name)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_make_name_then_open(self, tmpdir):
        input_code = """
        import tempfile

        filename = tempfile.mktemp()
        print(filename)
        tmp_file = open(filename, "w+")
        tmp_file.write("text")
        print("hello")
        """
        expected_output = """
        import tempfile

        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            filename = tf.name
            print(filename)
            tf.write("text")
        print("hello")
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_open_context_manager(self, tmpdir):
        input_code = """
        import tempfile

        filename = tempfile.mktemp()
        with open(filename, "w+") as tmp:
            tmp.write("text")
        """
        expected_output = """
        import tempfile

        with tempfile.NamedTemporaryFile("w+") as tf:
            tf.write("text")
        """
        self.run_and_assert(tmpdir, input_code, expected_output)
