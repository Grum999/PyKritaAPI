# -----------------------------------------------------------------------------
# Krita Python API documentation builder
# Copyright (C) 2024 - Grum999
#
# This script allows to build API documentation
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------

import os
import sys

# enables ansi escape characters in terminal
os.system("")


class Console:
    """A small class dedicated to display information to terminal"""

    @staticmethod
    def warning(message):
        """Display a warning message"""
        print("!!! WARNING:")

        if isinstance(message, (list, tuple)):
            message = '\n    '.join(message)

        print(f"    {message}")

    @staticmethod
    def error(message, exitCode=-1):
        """Display an error message"""
        print("!!! ERROR:")

        if isinstance(message, (list, tuple)):
            message = '\n    '.join(message)

        print(f"    {message}")

        if exitCode != 0:
            # only exit if exit code is not 0
            exit(exitCode)

    @staticmethod
    def display(message):
        """Display given message

        Can be a <str> or a <list(str)>
        """
        if isinstance(message, (list, tuple)):
            message = '\n'.join(message)

        print(message)

    @staticmethod
    def progress(text):
        """Display progress information"""
        # memorize cursor position
        sys.stdout.write('\x1b[?1048h')
        # clear line from cursor position
        sys.stdout.write('\x1b[0K')
        # display text
        sys.stdout.write(text)
        # flush content
        sys.stdout.flush()
        # restore cursor position
        sys.stdout.write('\x1b[?1048l')


