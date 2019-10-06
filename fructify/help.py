import contextlib
import traceback


@contextlib.contextmanager
def stdout_tb():
    try:
        yield
    except Exception:
        traceback.print_exc()
        raise
