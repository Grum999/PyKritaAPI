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

# -----------------------------------------------------------------------------
# The languagedef module provides base class used to defined a language
# (that can be tokenized and parsed --> tokenizer + parser modules)
#
# Main class from this module
#
# - LanguageDef:
#       Base class to use to define language
#
# -----------------------------------------------------------------------------

import re

from .tokenizer import (
            Token,
            TokenType,
            Tokenizer,
            TokenizerRule
        )

class LanguageDef:

    SEP_PRIMARY_VALUE = '\x01'              # define bounds for <value> and cursor position
    SEP_SECONDARY_VALUE = '\x02'            # define bounds for other values

    def __init__(self, rules=[], tokenType=None):
        """Initialise language & styles"""
        if tokenType is not None:
            self.__tokenType = tokenType
            self.__tokenTypeVars = [tt for tt in [getattr(self.__tokenType, tt) for tt in dir(self.__tokenType)] if isinstance(tt, self.__tokenType) and not callable(tt.value)]
        else:
            self.__tokenType = None
            self.__tokenTypeVars = []
        self.__tokenizer = Tokenizer(rules)

    def __repr__(self):
        return f"<{self.__class__.name}({self.name()}, {self.extensions()})>"

    def name(self):
        """Return language name"""
        return "None"

    def extensions(self):
        """Return language file extension as list

        For example:
            ['.htm', '.html']

        """
        return []

    def tokenizer(self):
        """Return tokenizer for language"""
        return self.__tokenizer

