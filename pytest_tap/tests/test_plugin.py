# Copyright (c) 2018, Matt Layman

import pytest


@pytest.fixture
def sample_test_file(testdir):
    testdir.makepyfile(
        """
        import pytest

        def test_ok():
            assert True

        def test_not_ok():
            assert False

        @pytest.mark.skip(reason='some reason')
        def test_skipped():
            assert False

        @pytest.mark.xfail(reason='a reason')
        def test_broken():
            assert False
    """
    )


def test_includes_options(testdir):
    """All options are present in the help."""
    result = testdir.runpytest("--help")

    expected_option_flags = [
        "*--tap-stream*",
        "*--tap-files*",
        "*--tap-combined*",
        "*--tap-outdir=path*",
    ]
    result.stdout.fnmatch_lines(expected_option_flags)


def test_stream(testdir, sample_test_file):
    """Results are streamed to stdout."""
    result = testdir.runpytest_subprocess("--tap-stream")

    result.stdout.fnmatch_lines(
        [
            "ok 1 test_stream.py::test_ok",
            "not ok 2 test_stream.py::test_not_ok",
            "ok 3 test_stream.py::test_skipped # SKIP some reason",
            "ok 4 test_stream.py::test_broken # TODO expected failure: a reason",
            "1..4",
        ]
    )


def test_combined(testdir, sample_test_file):
    """Tests are combined into a single output file."""
    testdir.runpytest_subprocess("--tap-combined")

    testresults = testdir.tmpdir.join("testresults.tap")
    assert testresults.check()


def test_files(testdir, sample_test_file):
    """Tests are split into separate files."""
    testdir.makepyfile(
        test_other_file="""
        def test_other_ok():
            assert True
    """
    )

    testdir.runpytest_subprocess("--tap-files")

    sample_tap = testdir.tmpdir.join("test_files.py.tap")
    assert sample_tap.check()
    other_tap = testdir.tmpdir.join("test_other_file.py.tap")
    assert other_tap.check()


def test_outdir(testdir, sample_test_file):
    """Tests are put in the output directory."""
    testdir.runpytest_subprocess("--tap-outdir", "results", "--tap-combined")

    outdir = testdir.tmpdir.join("results")
    testresults = outdir.join("testresults.tap")
    assert testresults.check()


def test_xfail_strict_function(testdir):
    """An xfail with strict on will fail when it unexpectedly passes.

    The xfail should look like an xfail by including the TODO directive.
    """
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.xfail(reason='a reason')
        def test_unexpected_pass():
            assert True

        @pytest.mark.xfail(reason='a reason', strict=True)
        def test_broken():
            assert True
    """
    )
    result = testdir.runpytest_subprocess("--tap-stream")

    result.stdout.fnmatch_lines(
        [
            (
                "ok 1 test_xfail_strict_function.py::test_unexpected_pass "
                "# TODO unexpected success: a reason"
            ),
            "not ok 2 test_xfail_strict_function.py::test_broken # TODO",
            "# [XPASS(strict)] a reason",
        ]
    )
