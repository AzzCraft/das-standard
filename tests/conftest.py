"""Close registered fixture scratch only after setup/call/teardown results exist."""
import importlib.util
from pathlib import Path
import pytest

_spec = importlib.util.spec_from_file_location('fixture_cleanup_' + str(Path(__file__).parent),
                                               Path(__file__).with_name('_fixture_cleanup.py'))
_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)
_cleanup = _core.FixtureCleanup(incremental=True)


def pytest_configure(config):
    global _cleanup
    try:
        _cleanup = _cleanup.configure(config)
    except OSError as exc:
        raise pytest.UsageError(str(exc)) from exc


@pytest.fixture
def tmp_path(tmp_path, tmp_path_factory, request):
    _cleanup.register(request.node, tmp_path, tmp_path_factory.getbasetemp())
    return tmp_path


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    _cleanup.observe(result.get_result())


def pytest_sessionfinish(session, exitstatus):
    _cleanup.finish(session)


def pytest_unconfigure(config):
    if not _cleanup.nested:
        import os
        os.environ.pop('DAS_FIXTURE_CLEANUP_PARENT', None)
