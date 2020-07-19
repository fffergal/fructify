import unittest

from fructify import help


class HelpTestCase(unittest.TestCase):
    def test_unwrap_heredoc(self):
        self.assertEqual(
            help.unwrap_heredoc(
                """
                This is one paragraph. It is not too long, but long enough to wrap over
                a couple of lines in the code.

                This is another paragraph.
                """
            ),
            (
                "This is one paragraph. It is not too long, but long enough to wrap "
                "over a couple of lines in the code.\n"
                "\n"
                "This is another paragraph."
            ),
        )
