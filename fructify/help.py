import contextlib
import traceback
from inspect import cleandoc


@contextlib.contextmanager
def stdout_tb():
    try:
        yield
    except Exception:
        traceback.print_exc()
        raise


def unwrap_heredoc(heredoc):
    """
    Reformat text written with three quote multi line strings.

    This allows you to write long strings as blocks without worrying about the
    indenting. All lines separated by a single new line will be joined with spaces, so
    you can wrap long lines when writing. Runs of more than one new line will be
    preserved.
    """
    return "\n\n".join(
        para.replace("\n", " ") for para in cleandoc(heredoc).split("\n\n")
    )
