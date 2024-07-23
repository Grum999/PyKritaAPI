#!/usr/bin/python3

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


import sys
import os
import re
import time
import json
import shutil
import hashlib
import textwrap
import argparse
import subprocess

from modules.console import Console
from modules.languagedef import LanguageDef
from modules.tokenizer import (
            Token,
            TokenType,
            Tokenizer,
            TokenizerRule
        )


__NAME__ = "Krita Python API documentation builder"
__VERSION__ = "1.2.0"
__DATE__ = "2024-07-23"


class LanguageDefCpp(LanguageDef):
    # Define token types for C++ header
    # Not a complete c++ language definition, a subset normally enough to parse headers
    # and get interesting information

    class ITokenType(TokenType):
        STRING = ('str', 'A String value')
        COMMENT = ('comment', 'A comment line')
        COMMENT_BLOCK = ('comments', 'A comment block')
        DELIMITER_SEPARATOR = ('delim_separator', 'Separator like comma')
        DELIMITER_OPERATOR = ('delim_operator', 'Operator like comma')
        DELIMITER_PARENTHESIS_OPEN = ('delim_parO', 'Parenthesis (open)')
        DELIMITER_PARENTHESIS_CLOSE = ('delim_parC', 'Parenthesis (close)')
        DELIMITER_CURLYBRACE_OPEN = ('delim_curbO', 'Curly Brace (open)')
        DELIMITER_CURLYBRACE_CLOSE = ('delim_curbC', 'Curly Brace (close)')
        IGNORED = ('ignore_operator', 'Ignored token')

        IDENTIFIER = ('identifier', 'An identifier')

    def __init__(self):
        """Initialise language & styles"""
        super(LanguageDefCpp, self).__init__([
            # ---
            TokenizerRule(LanguageDefCpp.ITokenType.STRING,
                          r'''(?:"(?:(?:.?\\"|[^"])*(?:\.(?:\\"|[^"]*))*")|(?:'(?:.?\\'|[^'])*(?:\.(?:\\'|[^']*))*'))'''),

            TokenizerRule(LanguageDefCpp.ITokenType.COMMENT_BLOCK,  r'(?:/\*(?:.|\s|\n)*?\*/)'),
            TokenizerRule(LanguageDefCpp.ITokenType.COMMENT,  r'//[^\n]*'),

            TokenizerRule(LanguageDefCpp.ITokenType.IDENTIFIER,
                          r"Qt::[A-Za-z\d_]+",
                          caseInsensitive=False),


            TokenizerRule(LanguageDefCpp.ITokenType.IDENTIFIER,
                          r"QList<[^>]+>|QMap<[^>]+>",
                          caseInsensitive=False),

            TokenizerRule(LanguageDefCpp.ITokenType.IDENTIFIER,
                          r"Q_DECL_DEPRECATED",
                          caseInsensitive=False),


            TokenizerRule(LanguageDefCpp.ITokenType.IGNORED,
                          r"^\s*~[^;]+;|^\s*explicit[^;]*;|#[^\n]*$|[\*\-&~]|const|override|Q_SLOTS"),

            TokenizerRule(LanguageDefCpp.ITokenType.IDENTIFIER,
                          r"\d+|\b(?:[a-zA-Z_][a-zA-Z0-9_]*)(?:\<(?:[a-zA-Z_][a-zA-Z0-9_]*\*?)(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*\*?)*\>)?",
                          caseInsensitive=False),

            TokenizerRule(LanguageDefCpp.ITokenType.DELIMITER_OPERATOR,
                          r"="),

            TokenizerRule(LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR,
                          r"[,:;]"),

            TokenizerRule(LanguageDefCpp.ITokenType.DELIMITER_PARENTHESIS_OPEN,
                          r"\("),

            TokenizerRule(LanguageDefCpp.ITokenType.DELIMITER_PARENTHESIS_CLOSE,
                          r"\)",
                          ignoreIndent=True),

            TokenizerRule(LanguageDefCpp.ITokenType.DELIMITER_CURLYBRACE_OPEN,
                          r"\{"),

            TokenizerRule(LanguageDefCpp.ITokenType.DELIMITER_CURLYBRACE_CLOSE,
                          r"\}",
                          ignoreIndent=True),

            TokenizerRule(LanguageDefCpp.ITokenType.SPACE,  r"(?:(?!\n)\s)+"),

            TokenizerRule(LanguageDefCpp.ITokenType.NEWLINE,  r"(?:^\s*\r?\n|\r?\n?\s*\r?\n)+")

            ],
            LanguageDefCpp.ITokenType
        )
        # print(self.tokenizer())

    def name(self):
        """Return language name"""
        return "Header C++"

    def extensions(self):
        """Return language file extension as list"""
        return ['.h']


class LanguageDefPython(LanguageDef):
    # define token types
    # ---> COPIED FROM pblanguagedef.py
    #      ImportError: attempted relative import beyond top-level package blahblahblah

    class ITokenType(TokenType):
        STRING = ('Str', 'A String value')
        FSTRING = ('Fstr', 'A F-String value')
        BSTRING = ('Bstr', 'A Binary String value')
        STRING_LONG_S = ('Str_l_s', 'A long String value (single quote)')
        STRING_LONG_D = ('Str_l_d', 'A long String value (double quotes)')
        FSTRING_LONG_S = ('Fstr_l_s', 'A long F-String value (single quote)')
        FSTRING_LONG_D = ('Fstr_l_d', 'A long F-String value (double quotes)')
        BSTRING_LONG_S = ('Bstr_l_s', 'A long Binary String value (single quote)')
        BSTRING_LONG_D = ('Bstr_l_d', 'A long Binary String value (double quotes)')

        NUMBER_INT = ('Number_int', 'An INTEGER NUMBER value')
        NUMBER_FLT = ('Number_flt', 'An FLOAT NUMBER value')

        KEYWORD = ('Kwrd', 'A keyword identifier')
        KEYWORD_SOFT = ('Kwrd_soft', 'A soft keyword identifier')
        KEYWORD_CONSTANT = ('Kwrd_const', 'A keyword constant')
        KEYWORD_OPERATOR = ('Kwrd_operator', 'A keyword operator')

        BUILTIN_FUNC = ('Builtin_fct', 'Built-in function')
        BUILTIN_EXCEPTION = ('Builtin_except', 'Built-in exception')

        OPERATOR_BINARY = ('Boperators', 'Operators like plus, minus, divide, ...')
        OPERATOR_DUAL = ('Doperators', 'Operators like "-" can be unary or binary operator ')

        DELIMITER = ('Delim', 'Miscellaneous delimiters')
        DELIMITER_OPERATOR = ('Delim_operator', 'Operators considered as delimiters in Python')
        DELIMITER_SEPARATOR = ('Delim_separator', 'Separator like comma')
        DELIMITER_PARENTHESIS_OPEN = ('Delim_parO', 'Parenthesis (open)')
        DELIMITER_PARENTHESIS_CLOSE = ('Delim_parC', 'Parenthesis (close)')
        DELIMITER_BRACKET_OPEN = ('Delim_brackO', 'Bracket (open)')
        DELIMITER_BRACKET_CLOSE = ('Delim_brackC', 'Bracket (close)')
        DELIMITER_CURLYBRACE_OPEN = ('Delim_curlbO', 'Curly brace (open)')
        DELIMITER_CURLYBRACE_CLOSE = ('Delim_curlbC', 'Curly brace (close)')

        DECL_FUNC = ('Function_decl', 'Declare a Function')
        DECL_CLASS = ('Class_decl', 'Declare a Class')

        IDENTIFIER = ('Identifier', 'An identifier')
        DECORATOR = ('Decorator', 'A decorator')

        LINE_JOIN = ('Linejoin', 'Line join')

    def __init__(self):
        """Initialise language & styles"""
        super(LanguageDefPython, self).__init__([
            # ---
            # https://docs.python.org/3.10/reference/lexical_analysis.html#string-and-bytes-literals
            #
            # Need to make distinction between all possibles string for syntax highlighting
            TokenizerRule(LanguageDefPython.ITokenType.BSTRING_LONG_S,
                          r'''(?:RB|Rb|rB|rb|BR|bR|Br|br|B|b)(?:'{3}(?:.|\s|\n)*?'{3})''',
                          multiLineStart=r"""(RB|Rb|rB|rb|BR|bR|Br|br|B|b)(?:'{3})""",
                          multiLineEnd=r"""(?:'{3})"""),
            TokenizerRule(LanguageDefPython.ITokenType.BSTRING_LONG_D,
                          r'''(?:RB|Rb|rB|rb|BR|bR|Br|br|B|b)(?:"{3}(?:.|\s|\n)*?"{3})''',
                          multiLineStart=r'''(RB|Rb|rB|rb|BR|bR|Br|br|B|b)(?:"{3})''',
                          multiLineEnd=r'''(?:"{3})'''),

            TokenizerRule(LanguageDefPython.ITokenType.FSTRING_LONG_S,
                          r'''(?:RF|Rf|rF|rf|FR|fR|Fr|fr|F|f)(?:'{3}(?:.|\s|\n)*?'{3})''',
                          multiLineStart=r"""(RF|Rf|rF|rf|FR|fR|Fr|fr|F|f)(?:'{3})""",
                          multiLineEnd=r"""(?:'{3})"""),
            TokenizerRule(LanguageDefPython.ITokenType.FSTRING_LONG_D,
                          r'''(?:RF|Rf|rF|rf|FR|fR|Fr|fr|F|f)(?:"{3}(?:.|\s|\n)*?"{3})''',
                          multiLineStart=r'''(RF|Rf|rF|rf|FR|fR|Fr|fr|F|f)(?:"{3})''',
                          multiLineEnd=r'''(?:"{3})'''),

            TokenizerRule(LanguageDefPython.ITokenType.STRING_LONG_S,
                          r'''(?:U|u|R|r)?(?:'{3}(?:.|\s|\n)*?'{3})''',
                          multiLineStart=r"""(U|u|R|r)?(?:'{3})""",
                          multiLineEnd=r"""(?:'{3})"""),
            TokenizerRule(LanguageDefPython.ITokenType.STRING_LONG_D,
                          r'''(?:U|u|R|r)?(?:"{3}(?:.|\s|\n)*?"{3})''',
                          multiLineStart=r'''(U|u|R|r)?(?:"{3})''',
                          multiLineEnd=r'''(?:"{3})'''),

            TokenizerRule(LanguageDefPython.ITokenType.BSTRING,
                          r'''(?:RB|Rb|rB|rb|BR|bR|Br|br|B|b)(?:(?:"(?:.?\\"|[^"])*(?:\.(?:\\"|[^"]*))*")|(?:'(?:.?\\'|[^'])*(?:\.(?:\\'|[^']*))*'))'''),
            TokenizerRule(LanguageDefPython.ITokenType.FSTRING,
                          r'''(?:RF|Rf|rF|rf|FR|fR|Fr|fr|F|f)(?:(?:"(?:.?\\"|[^"])*(?:\.(?:\\"|[^"]*))*")|(?:'(?:.?\\'|[^'])*(?:\.(?:\\'|[^']*))*'))'''),
            TokenizerRule(LanguageDefPython.ITokenType.STRING,
                          r'''(?:U|u|R|r)?(?:"(?:(?:.?\\"|[^"])*(?:\.(?:\\"|[^"]*))*")|(?:'(?:.?\\'|[^'])*(?:\.(?:\\'|[^']*))*'))'''),

            # ---
            #
            TokenizerRule(LanguageDefPython.ITokenType.COMMENT,  r'#[^\n]*'),

            # --
            # https://peps.python.org/pep-0318/
            TokenizerRule(LanguageDefPython.ITokenType.DECORATOR,
                          r"(?:@[a-z_][a-z0-9_]*)\b",
                          caseInsensitive=True),

            # ---
            # https://docs.python.org/3.10/reference/lexical_analysis.html#keywords
            TokenizerRule(LanguageDefPython.ITokenType.KEYWORD,
                          r"\b(?:"
                          r"yield|"
                          r"with|while|"
                          r"try|"
                          r"return|raise|"
                          r"pass|"
                          r"nonlocal|"
                          r"lambda|"
                          r"import|if|"
                          r"global|"
                          r"from|for|finally|"
                          r"except|else|elif|"
                          r"del|def|"
                          r"continue|class|"
                          r"break|"
                          r"await|async|assert|as"
                          r")\b",
                          caseInsensitive=False),
            TokenizerRule(LanguageDefPython.ITokenType.KEYWORD_OPERATOR,
                          r"\b(?:and|in|is|or|not)\b",
                          caseInsensitive=False),

            # --
            # https://docs.python.org/3.10/library/functions.html
            TokenizerRule(LanguageDefPython.ITokenType.BUILTIN_FUNC,
                          r"\b(?:"
                          r"zip|"
                          r"vars|"
                          r"type|tuple|"
                          r"super|sum|str|staticmethod|sorted|slice|setattr|set|"
                          r"round|reversed|repr|range|"
                          r"property|print|pow|"
                          r"ord|open|oct|object|"
                          r"next|"
                          r"min|memoryview|max|map|"
                          r"locals|list|len|"
                          r"iter|issubclass|isinstance|int|input|id|"
                          r"hex|help|hash|hasattr|"
                          r"globals|getattr|"
                          r"frozenset|format|float|filter|"
                          r"exec|eval|enumerate|"
                          r"divmod|dir|dict|delattr|"
                          r"complex|compile|classmethod|chr|callable|"
                          r"bytes|bytearray|breakpoint|bool|bin|"
                          r"ascii|any|anext|all|aiter|abs|"
                          r"__import__"
                          r")\b(?=\()",
                          caseInsensitive=False),

            # --
            # https://docs.python.org/3.10/library/exceptions.html
            TokenizerRule(LanguageDefPython.ITokenType.BUILTIN_EXCEPTION,
                          r"\b(?:"
                          r"ZeroDivisionError|"
                          r"Warning|"
                          r"ValueError|"
                          r"UserWarning|UnicodeWarning|UnicodeTranslateError|UnicodeError|UnicodeEncodeError|UnicodeDecodeError|UnboundLocalError|"
                          r"TypeError|TimeoutError|TabError|"
                          r"SystemExit|SystemError|SyntaxWarning|SyntaxError|StopIteration|StopAsyncIteration|"
                          r"RuntimeWarning|RuntimeError|ResourceWarning|ReferenceError|RecursionError|"
                          r"ProcessLookupError|PermissionError|PendingDeprecationWarning|"
                          r"OverflowError|OSError|"
                          r"NotImplementedError|NotADirectoryError|NameError|"
                          r"ModuleNotFoundError|MemoryError|"
                          r"LookupError|"
                          r"KeyboardInterrupt|KeyError|"
                          r"IsADirectoryError|InterruptedError|IndexError|IndentationError|ImportWarning|ImportError|"
                          r"GeneratorExit|"
                          r"FutureWarning|FloatingPointError|FileNotFoundError|FileExistsError|"
                          r"Exception|EncodingWarning|EOFError|"
                          r"DeprecationWarning|"
                          r"ConnectionResetError|ConnectionRefusedError|ConnectionError|ConnectionAbortedError|ChildProcessError|"
                          r"BytesWarning|BufferError|BrokenPipeError|BlockingIOError|BaseException|"
                          r"AttributeError|AssertionError|ArithmeticError"
                          r")\b",
                          caseInsensitive=False),

            # --
            # https://docs.python.org/3.10/library/constants.html
            TokenizerRule(LanguageDefPython.ITokenType.KEYWORD_CONSTANT,
                          r"\b(?:Ellipsis|False|None|True|NotImplemented)\b",
                          caseInsensitive=False),

            # ---
            # https://docs.python.org/3.10/reference/lexical_analysis.html#soft-keywords
            TokenizerRule(LanguageDefPython.ITokenType.KEYWORD_SOFT,
                          r"\b(?:case|match|_)\b",
                          caseInsensitive=False),

            # ---
            # https://docs.python.org/3.10/reference/lexical_analysis.html#floating-point-literals (+Imaginary literals)
            TokenizerRule(LanguageDefPython.ITokenType.NUMBER_FLT,
                          r"\b(?:(?:\d(?:_?\d)*\.|\.)(?:\d(?:_?\d)*)?(?:e[+-]?\d(?:_?\d)*)?|[1-9]\d*(?:e[+-]?\d(?:_?\d)*))j?\b",
                          caseInsensitive=True),

            # ---
            # https://docs.python.org/3.10/reference/lexical_analysis.html#integer-literals (+Imaginary literals)
            TokenizerRule(LanguageDefPython.ITokenType.NUMBER_INT,
                          r"\b(?:[1-9](?:_?\d+)*|0o(?:_?[0-7]+)*|0b(?:_?[01]+)*|0x(?:_?[0-9A-F]+)*|0+)j?\b",
                          caseInsensitive=True),

            # ---
            TokenizerRule(LanguageDefPython.ITokenType.DECL_FUNC,
                          r"(?<=def\s+)(?:[a-z_][a-z0-9_]*)(?=\s*\()",
                          caseInsensitive=True),
            TokenizerRule(LanguageDefPython.ITokenType.DECL_CLASS,
                          r"(?<=class\s+)(?:[a-zA-Z_][a-zA-Z0-9_]*)(?=\s*[\(:])",
                          caseInsensitive=True),

            # --
            # https://docs.python.org/3.10/reference/lexical_analysis.html#identifiers
            TokenizerRule(LanguageDefPython.ITokenType.IDENTIFIER,
                          r"\b(?:[a-zA-Z_][a-zA-Z0-9_]*)\b",
                          caseInsensitive=False),

            # ---
            TokenizerRule(LanguageDefPython.ITokenType.LINE_JOIN, r"\s\\$"),

            # ---
            # https://docs.python.org/3.10/reference/lexical_analysis.html#delimiters
            # => must be defined before Operators to let regex catch them properly
            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER,
                          r"->"),

            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER_OPERATOR,
                          r"(?:\+=|-=|\*\*=|\*=|//=|/=|%=|@=\@|&=|\|=|\^=|>>=|<<=|=)"),

            # ---
            # https://docs.python.org/3.10/reference/lexical_analysis.html#operators
            TokenizerRule(LanguageDefPython.ITokenType.OPERATOR_BINARY,
                          r"\+|\*\*|\*|//|/|%|<<|>>|&|\||\^|~|:=|<=|<>|<|>=|>|==|!=",
                          caseInsensitive=False,
                          ignoreIndent=True),

            TokenizerRule(LanguageDefPython.ITokenType.OPERATOR_DUAL,
                          r"-",
                          ignoreIndent=True),

            # ---
            # https://docs.python.org/3.10/reference/lexical_analysis.html#delimiters
            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER_SEPARATOR,
                          r"[,;\.:]"),

            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER_PARENTHESIS_OPEN,
                          r"\("),

            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER_PARENTHESIS_CLOSE,
                          r"\)",
                          ignoreIndent=True),

            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER_BRACKET_OPEN,
                          r"\["),

            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER_BRACKET_CLOSE,
                          r"\]",
                          ignoreIndent=True),

            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER_CURLYBRACE_OPEN,
                          r"\{"),

            TokenizerRule(LanguageDefPython.ITokenType.DELIMITER_CURLYBRACE_CLOSE,
                          r"\}",
                          ignoreIndent=True),

            # all spaces except line feed
            TokenizerRule(LanguageDefPython.ITokenType.SPACE,  r"(?:(?!\n)\s)+"),

            # line feed
            TokenizerRule(LanguageDefPython.ITokenType.NEWLINE,  r"(?:^\s*\r?\n|\r?\n?\s*\r?\n)+"),

            # Unknown --> everything else
            TokenizerRule(LanguageDefPython.ITokenType.UNKNOWN,  r"[^\s]+"),
            ],
            LanguageDefPython.ITokenType)

        self.tokenizer().setSimplifyTokenSpaces(True)
        self.tokenizer().setIndent(4)
        # print(self.tokenizer())

        tmp="""
        self.setStyles(UITheme.DARK_THEME, [
            (LanguageDefPython.ITokenType.STRING, '#98c379', False, False),
            (LanguageDefPython.ITokenType.STRING_LONG_S, '#aed095', False, False),
            (LanguageDefPython.ITokenType.STRING_LONG_D, '#aed095', False, False),

            (LanguageDefPython.ITokenType.FSTRING, '#98c379', False, True),
            (LanguageDefPython.ITokenType.FSTRING_LONG_S, '#aed095', False, True),
            (LanguageDefPython.ITokenType.FSTRING_LONG_D, '#aed095', False, True),

            (LanguageDefPython.ITokenType.BSTRING, '#56b6c2', False, False),
            (LanguageDefPython.ITokenType.BSTRING_LONG_S, '#7cc6d0', False, False),
            (LanguageDefPython.ITokenType.BSTRING_LONG_D, '#7cc6d0', False, False),

            (LanguageDefPython.ITokenType.NUMBER_INT, '#c9986a', False, False),
            (LanguageDefPython.ITokenType.NUMBER_FLT, '#c9986a', False, False),

            (LanguageDefPython.ITokenType.KEYWORD, '#c678dd', True, False),
            (LanguageDefPython.ITokenType.KEYWORD_SOFT, '#c678dd', True, False),
            (LanguageDefPython.ITokenType.KEYWORD_CONSTANT, '#dd7892', True, False),
            (LanguageDefPython.ITokenType.KEYWORD_OPERATOR, '#ff99ff', True, False),

            (LanguageDefPython.ITokenType.BUILTIN_FUNC, '#80bfff', False, False),
            (LanguageDefPython.ITokenType.BUILTIN_EXCEPTION, '#e83030', True, False),

            (LanguageDefPython.ITokenType.OPERATOR_BINARY, '#ff99ff', False, False),
            (LanguageDefPython.ITokenType.OPERATOR_DUAL, '#ff99ff', False, False),

            (LanguageDefPython.ITokenType.DELIMITER, '#ff66d9', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_OPERATOR, '#ff99ff', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_SEPARATOR, '#ff66d9', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_PARENTHESIS_OPEN, '#ff66d9', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_PARENTHESIS_CLOSE, '#ff66d9', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_BRACKET_OPEN, '#ff66d9', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_BRACKET_CLOSE, '#ff66d9', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_CURLYBRACE_OPEN, '#ff66d9', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_CURLYBRACE_CLOSE, '#ff66d9', False, False),

            (LanguageDefPython.ITokenType.LINE_JOIN, '#ff66d9', True, False, '#FDFF9E'),

            (LanguageDefPython.ITokenType.DECL_FUNC, '#ffe066', True, False),
            (LanguageDefPython.ITokenType.DECL_CLASS, '#ffe066', True, False),

            (LanguageDefPython.ITokenType.IDENTIFIER, '#e6e6e6', False, False),
            (LanguageDefPython.ITokenType.DECORATOR, '#ffffe6', True, True),

            (LanguageDefPython.ITokenType.COMMENT, '#5c6370', False, True)
        ])
        self.setStyles(UITheme.LIGHT_THEME, [
            (LanguageDefPython.ITokenType.STRING, '#238800', False, False),
            (LanguageDefPython.ITokenType.STRING_LONG_S, '#5D8C00', False, False),
            (LanguageDefPython.ITokenType.STRING_LONG_D, '#5D8C00', False, False),

            (LanguageDefPython.ITokenType.FSTRING, '#238800', False, True),
            (LanguageDefPython.ITokenType.FSTRING_LONG_S, '#5D8C00', False, True),
            (LanguageDefPython.ITokenType.FSTRING_LONG_D, '#5D8C00', False, True),

            (LanguageDefPython.ITokenType.BSTRING, '#008878', False, False),
            (LanguageDefPython.ITokenType.BSTRING_LONG_S, '#00B5A0', False, False),
            (LanguageDefPython.ITokenType.BSTRING_LONG_D, '#00B5A0', False, False),

            (LanguageDefPython.ITokenType.NUMBER_INT, '#D97814', False, False),
            (LanguageDefPython.ITokenType.NUMBER_FLT, '#D97814', False, False),

            (LanguageDefPython.ITokenType.KEYWORD, '#9B0F83', True, False),
            (LanguageDefPython.ITokenType.KEYWORD_SOFT, '#9B0F83', True, False),
            (LanguageDefPython.ITokenType.KEYWORD_CONSTANT, '#CC427B', True, False),
            (LanguageDefPython.ITokenType.KEYWORD_OPERATOR, '#DF0BEA', True, False),

            (LanguageDefPython.ITokenType.BUILTIN_FUNC, '#2677CC', True, False),
            (LanguageDefPython.ITokenType.BUILTIN_EXCEPTION, '#BF2727', True, False),

            (LanguageDefPython.ITokenType.OPERATOR_BINARY, '#DF0BEA', False, False),
            (LanguageDefPython.ITokenType.OPERATOR_DUAL, '#DF0BEA', False, False),

            (LanguageDefPython.ITokenType.DELIMITER, '#D953B5', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_OPERATOR, '#DF0BEA', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_SEPARATOR, '#D953B5', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_PARENTHESIS_OPEN, '#D953B5', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_PARENTHESIS_CLOSE, '#D953B5', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_BRACKET_OPEN, '#D953B5', False, False),
            (LanguageDefPython.ITokenType.DELIMITER_BRACKET_CLOSE, '#D953B5', False, False),

            (LanguageDefPython.ITokenType.LINE_JOIN, '#D953B5', False, False, '#FDFF9E'),

            (LanguageDefPython.ITokenType.DECL_FUNC, '#00019C', True, False),
            (LanguageDefPython.ITokenType.DECL_CLASS, '#00019C', True, False),

            (LanguageDefPython.ITokenType.IDENTIFIER, '#333333', False, True),
            (LanguageDefPython.ITokenType.DECORATOR, '#8D8D7F', True, True),

            (LanguageDefPython.ITokenType.COMMENT, '#686D9C', False, True)

        ])
        """

    def name(self):
        """Return language name"""
        return "Python"

    def extensions(self):
        """Return language file extension as list"""
        return ['.py']


class KritaApiMethod:

    @staticmethod
    def toPythonType(value):
        """Return matching python type for C++ type"""
        # normalize value
        nValue = re.sub(r"[\*\s]+", "", value)

        if nValue in ('string', 'char', 'QString'):
            return 'str'
        elif nValue in ('double', 'qreal', 'float'):
            return 'float'
        elif nValue in 'QStringList':
            return 'list[str]'
        elif matched := re.search(r'^(?:QList|QVector)<(.*)>$', nValue):
            return f"list[{KritaApiMethod.toPythonType(matched.groups()[0])}]"
        elif matched := re.search(r'^QMap<(.*),(.*)>$', nValue):
            k = KritaApiMethod.toPythonType(matched.groups()[0])
            v = KritaApiMethod.toPythonType(matched.groups()[1])
            return f"dict[{k}: {v}]"

        return value

    def __init__(self):
        self.__name = ''
        self.__returned = ''
        self.__description = ''
        self.__line = 0
        self.__access = ''
        self.__static = False
        self.__virtual = False
        self.__signal = False
        self.__deprecated = False
        self.__parameters = []

    def __repr__(self):
        returned = f"{self.__name}({', '.join([p[0] for p in self.__parameters])}) -> {self.__returned}"
        return returned

    def toDict(self):
        """Return dict for method"""
        returned = {
                'hash': '',
                'name': self.__name,
                'description': self.__description,
                'returned': self.__returned,
                'sourceCodeLine': self.__line,
                'accesType': self.__access,
                'isStatic': self.__static,
                'isVirtual': self.__virtual,
                'isSignal': self.__signal,
                'isDeprecated': self.__deprecated,
                'parameters': [],
                'tagRef': {
                        'available': [],
                        'updated': [],
                        'deprecated': []
                    }
            }

        for parameter in self.__parameters:
            returned['parameters'].append({
                    'name': parameter[0],
                    'type': parameter[1],
                    'default': parameter[2]
                })

        # calculate hash for given method
        m = hashlib.sha256()
        for property in ['name', 'description', 'returned', 'accesType', 'isStatic', 'isVirtual']:
            m.update(f"{returned[property]}".encode())
        for parameter in returned['parameters']:
            for property in ['name', 'type', 'default']:
                m.update(f"{parameter[property]}".encode())
        returned['hash'] = m.hexdigest()

        return returned

    def returned(self):
        return self.__returned

    def setReturned(self, value):
        self.__returned = KritaApiMethod.toPythonType(value)

    def name(self):
        return self.__name

    def setName(self, value):
        self.__name = value

    def line(self):
        return self.__line

    def setLine(self, value):
        self.__line = value

    def description(self):
        return self.__description

    def setDescription(self, description):
        self.__description = description

    def parameters(self):
        return self.__parameters

    def addParameter(self, name, type, default):
        if name is not None and type is not None:
            if isinstance(default, str):
                if g := re.match(r'''QString\(["'](.*)["']\)''', default):
                    default = f'"{g.groups()[0]}"'
                elif g := re.match(r'''QString\(\s*\)''', default):
                    default = f'""'
                elif default == '0':
                    if KritaApiMethod.toPythonType(type) != 'int':
                        default = 'None'
                elif default == 'true':
                    default = 'True'
                elif default == 'false':
                    default = 'False'
            self.__parameters.append((name, KritaApiMethod.toPythonType(type), default))

    def access(self):
        return self.__access

    def setAccess(self, value):
        self.__access = value

    def static(self):
        return self.__static

    def setStatic(self, value):
        self.__static = value

    def virtual(self):
        return self.__virtual

    def setVirtual(self, value):
        self.__virtual = value

    def signal(self):
        return self.__signal

    def setSignal(self, value):
        self.__signal = value

    def deprecated(self):
        return self.__deprecated

    def setDeprecated(self, value):
        self.__deprecated = value


class KritaApiClass:

    def __init__(self, fileName):
        self.__fileName = fileName
        self.__name = ""
        self.__description = ""
        self.__extend = ""
        self.__line = 0
        self.__methods = []

    def toDict(self):
        """Return dict for class"""
        returned = {
                'fileName': self.__fileName,
                'name': self.__name,
                'description': self.__description,
                'extend': self.__extend,
                'sourceCodeLine': self.__line,
                'methods': [method.toDict() for method in self.__methods],
                'tagRef': {
                        'available': [],
                        'updated': []
                    }
            }
        return returned

    def name(self):
        return self.__name

    def setName(self, name):
        self.__name = name

    def extend(self):
        return self.__extend

    def setExtend(self, extend):
        self.__extend = extend

    def description(self):
        return self.__description

    def setDescription(self, description):
        self.__description = description

    def methods(self):
        return self.__methods

    def addMethod(self, method):
        self.__methods.append(method)

    def line(self):
        return self.__line

    def setLine(self, value):
        self.__line = value


class KritaApiAnalysis:
    """Do an analysis of current source code"""

    def __init__(self, kritaSrcLibKisPath):
        self.__libkisPath = kritaSrcLibKisPath
        self.__headerFiles = sorted([fileName for fileName in os.listdir(self.__libkisPath)
                                     if re.search(r'\.h$', fileName) and fileName not in ('libkis.h', 'LibKisUtils.h')
                                     ])

        self.__languageDef = LanguageDefCpp()
        self.__classes = {}
        self.__tokens = None

        # print(self.__headerFiles)
        totalKo = 0
        for fileName in self.__headerFiles:
            nbKo = self.__processFile(fileName)
            if nbKo:
                totalKo += 1

        if totalKo > 0:
            Console.warning(f"Invalid files({totalKo}/{len(self.__headerFiles)})!")

    def __reformatDescription(self, description):
        description = re.sub(r"^\s*(/\*\*.*|\*/|\*[ \t]|\*|///?\s)", "", description, flags=re.M)
        description = re.sub(r"^\n", "", description)
        return description

    def __moveNext(self):
        """Move to next non space/newline token"""
        while not self.__tokens.eol():
            nextToken = self.__tokens.next()
            if nextToken and nextToken.type() not in (LanguageDefCpp.ITokenType.IGNORED, LanguageDefCpp.ITokenType.SPACE, LanguageDefCpp.ITokenType.NEWLINE):
                return nextToken
        return None

    def __skipStatement(self):
        """Skip current statement: ignore all token until found separator ';' """
        while not self.__tokens.eol():
            token = self.__moveNext()
            if token and token.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and token.value() == ';':
                return

    def __nextToken(self, token):
        """Return next non space/newline token from given `token` or None"""
        if nextToken := token.next():
            if nextToken.type() in (LanguageDefCpp.ITokenType.IGNORED, LanguageDefCpp.ITokenType.SPACE, LanguageDefCpp.ITokenType.NEWLINE):
                return self.__nextToken(nextToken)
            return nextToken
        return None

    def __previousToken(self, token):
        """Return previous non space/newline token from given `token` or None"""
        if previousToken := token.previous():
            if previousToken.type() in (LanguageDefCpp.ITokenType.IGNORED, LanguageDefCpp.ITokenType.SPACE, LanguageDefCpp.ITokenType.NEWLINE):
                return self.__previousToken(previousToken)
            return previousToken
        return None

    def __processClass(self, fileName):
        """Current token from given `tokens` is start of a class

        manage class
        """
        def exitClass():
            countCBraces = None
            while not self.__tokens.eol():
                token = self.__tokens.next()
                if token:
                    if token.type() == LanguageDefCpp.ITokenType.DELIMITER_CURLYBRACE_OPEN:
                        if countCBraces is None:
                            countCBraces = 0
                        countCBraces += 1
                    elif token.type() == LanguageDefCpp.ITokenType.DELIMITER_CURLYBRACE_CLOSE:
                        countCBraces -= 1
                    elif countCBraces == 0 and token.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and token.value() == ';':
                        # exit class!
                        break

            if countCBraces is None or countCBraces > 0:
                # not a normal case but nothing to do except print a warning
                Console.warning("---> W#0001: invalid class definition?")

        def defaultValue(type, value):
            if type == 'bool' and value in ('nullptr', '0'):
                return 'False'
            elif type == 'float' and value == 'nullptr':
                return '0.0'
            elif type == 'int' and value == 'nullptr':
                return '0'
            elif value == 'nullptr':
                return None

            return value

        # normally, token preceding class is a comment to describe class
        tokenDescription = self.__previousToken(self.__tokens.value())
        if not tokenDescription or not tokenDescription.type() == LanguageDefCpp.ITokenType.COMMENT_BLOCK:
            tokenDescription = None

        classLineNumber = self.__tokens.value().row()

        # get next token
        token = self.__moveNext()
        if not token:
            Console.warning("---> W#0002: invalid class definition?")
            Console.display(token)
            # can occurs!?
            return False

        if token.value() != 'KRITALIBKIS_EXPORT':
            # we're not in 'valid' class to process, continue to parse until exit class
            nextToken = self.__nextToken(token)
            if nextToken.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and nextToken.value() == ';':
                # case of class like
                #   class Xxxxx;
                #
                # nothing to do, exit
                return

            # case of class like
            #   class Xxxxx : ... { ... };
            exitClass()
            return

        # from here we can consider the class should like:
        #   class KRITALIBKIS_EXPORT Xxxxx : public XXXXX { ... };

        # this token is class name
        token = self.__moveNext()

        # start to manage krita class
        kritaClass = KritaApiClass(fileName)
        kritaClass.setName(token.value())
        kritaClass.setLine(classLineNumber)
        if tokenDescription:
            kritaClass.setDescription(self.__reformatDescription(tokenDescription.value()))

        nextToken = self.__nextToken(token)
        if nextToken.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and nextToken.value() == ':':
            token = self.__moveNext()
            token = self.__moveNext()
            if token.value() != 'public':
                # if class is not public, need to exit...
                Console.warning("---> W#0006: invalid class definition?")
                Console.display(token)
                return False

            # this token define object from which class inherits
            token = self.__moveNext()
            kritaClass.setExtend(token.value())

        # enter in class
        # only declaration in public/public Q_SLOTS managed
        #   class KRITALIBKIS_EXPORT Xxxx : public QObject
        #       {
        #           Q_OBJECT
        #
        #           public:
        #               ....
        #
        #           public Q_SLOTS:
        #               ....
        #
        #           private:
        #               ....
        #       };
        #   Note: consider to enter class if curly brace count is greater than 0
        kritaMethod = None
        methodName = None
        methodDeprecated = None
        methodComment = None
        methodReturned = None
        methodVirtual = None
        methodStatic = None
        methodAccess = None
        countCBraces = None
        asSignal = False
        while not self.__tokens.eol():
            token = self.__moveNext()
            if not token:
                break

            if token.type() == LanguageDefCpp.ITokenType.DELIMITER_CURLYBRACE_OPEN:
                if countCBraces is None:
                    countCBraces = 0
                countCBraces += 1
            elif token.type() == LanguageDefCpp.ITokenType.DELIMITER_CURLYBRACE_CLOSE:
                countCBraces -= 1
            elif countCBraces == 0 and token.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and token.value() == ';':
                # exit class!
                break
            elif token.value() in ('public', 'protected'):
                asSignal = False
                nextToken = self.__nextToken(token)
                if nextToken.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and nextToken.value() == ':':
                    nextToken = self.__nextToken(nextToken)
                    if nextToken.type() in (LanguageDefCpp.ITokenType.COMMENT, LanguageDefCpp.ITokenType.COMMENT_BLOCK) and re.search(r"\bkrita\s+api", nextToken.value(), flags=re.I):
                        methodAccess = 'private'
                        # skip comment
                        self.__moveNext()
                    else:
                        methodAccess = token.value()
                        # skip :
                        self.__moveNext()
                        if nextToken.type() in (LanguageDefCpp.ITokenType.COMMENT, LanguageDefCpp.ITokenType.COMMENT_BLOCK) and re.search(r"krita\s+api", nextToken.value(), flags=re.I):
                            self.__moveNext()

            elif token.value() == 'private':
                asSignal = False
                nextToken = self.__nextToken(token)
                if nextToken.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and nextToken.value() == ':':
                    methodAccess = 'private'
                    # skip :
                    self.__moveNext()
            elif token.value() == 'Q_SIGNALS':
                nextToken = self.__nextToken(token)
                if nextToken.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and nextToken.value() == ':':
                    asSignal = True
                    # skip :
                    self.__moveNext()
            elif methodAccess in ('public', 'protected'):
                # analyse token only if in public Q_SLOT
                # should be a method declaration maybe preceded by a comment
                # examples:
                #   QList<Node*> childNodes() const;
                #   QList<Node*> findChildNodes(const QString &name = QString(), bool recursive = false, bool partialMatch = false, const QString &type = QString(), int colorLabelIndex = 0) const;
                #   bool setPixelData(QByteArray value, int x, int y, int w, int h);
                #   virtual void canvasChanged(Canvas *canvas) = 0;
                if token.type() in (LanguageDefCpp.ITokenType.COMMENT_BLOCK, LanguageDefCpp.ITokenType.COMMENT):
                    # memorize comment
                    methodComment = self.__reformatDescription(token.value())
                else:
                    methodDeprecated = False
                    if token.value() == 'Q_DECL_DEPRECATED':
                        methodDeprecated = True
                        token = self.__moveNext()

                    methodVirtual = False
                    if token.value() == 'virtual':
                        methodVirtual = True
                        token = self.__moveNext()

                    methodStatic = False
                    if token.value() == 'static':
                        methodStatic = True
                        token = self.__moveNext()

                    nextToken = self.__nextToken(token)
                    if nextToken:
                        if nextToken.type() == LanguageDefCpp.ITokenType.DELIMITER_PARENTHESIS_OPEN:
                            # constructor
                            methodReturned = token
                            methodName = token
                        elif nextToken.value() == 'operator':
                            # something like
                            #   bool operator==(const Canvas &other) const;
                            self.__skipStatement()
                            continue
                        else:
                            methodReturned = token
                            methodName = self.__moveNext()
                    else:
                        continue

                    kritaMethod = KritaApiMethod()
                    kritaMethod.setName(methodName.value())
                    kritaMethod.setReturned(methodReturned.value())
                    kritaMethod.setAccess(methodAccess)
                    kritaMethod.setLine(methodName.row())
                    kritaMethod.setStatic(methodStatic)
                    kritaMethod.setVirtual(methodVirtual)
                    kritaMethod.setSignal(asSignal)
                    kritaMethod.setDeprecated(methodDeprecated)
                    if methodComment:
                        kritaMethod.setDescription(methodComment)

                    token = self.__moveNext()
                    if not(token and token.type() == LanguageDefCpp.ITokenType.DELIMITER_PARENTHESIS_OPEN):
                        # !!??
                        Console.warning("---> W#0003: invalid class definition?")
                        Console.display(kritaMethod)
                        Console.display(token)
                        return False

                    parametersOk = True
                    parameterType = None
                    parameterName = None
                    parameterDefault = None
                    # we are managing method parameters
                    while not self.__tokens.eol():
                        token = self.__moveNext()
                        if token:
                            if token.type() == LanguageDefCpp.ITokenType.DELIMITER_PARENTHESIS_CLOSE:
                                # no more parameters, add method to class
                                kritaMethod.addParameter(parameterName, parameterType, parameterDefault)

                                if parametersOk and re.match("^K(is|o).*", methodReturned.value()) is None:
                                    # KisXxxxx and KoXxxxx class are internal Krita classe not available in PyKrita API
                                    # then exclude it from available method
                                    kritaClass.addMethod(kritaMethod)

                                kritaMethod = None
                                methodName = None
                                methodComment = None
                                methodReturned = None
                                methodStatic = None
                                methodVirtual = None
                                parameterType = None
                                parameterName = None
                                parameterDefault = None
                            elif token.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and token.value() == ';':
                                # end of method definition
                                break
                            elif token.type() == LanguageDefCpp.ITokenType.DELIMITER_SEPARATOR and token.value() == ',':
                                # add parameter
                                kritaMethod.addParameter(parameterName, parameterType, parameterDefault)

                                parameterType = None
                                parameterName = None
                                parameterDefault = None
                            elif kritaMethod and token.type() == LanguageDefCpp.ITokenType.DELIMITER_OPERATOR and token.value() == '=':
                                # default value
                                token = self.__moveNext()
                                parameterDefault = defaultValue(parameterType, token.value())

                                pOpen = 0
                                while True:
                                    nextToken = self.__nextToken(token)

                                    if nextToken.value() == '(':
                                        pOpen += 1
                                    elif nextToken.value() == ')':
                                        if pOpen == 0:
                                            break
                                        else:
                                            pOpen -= 1
                                    elif nextToken.value() == ',':
                                        if pOpen == 0:
                                            break

                                    parameterDefault += defaultValue(parameterType, nextToken.value())
                                    token = self.__moveNext()
                            else:
                                if parameterType is None:
                                    parameterType = token.value().replace('::', '.')
                                    if re.match("^K(is|o).*", parameterType) is not None:
                                        # KisXxxxx and KoXxxxx class are internal Krita classe not available in PyKrita API
                                        # then exclude it from available method
                                        parametersOk = False
                                elif parameterName is None:
                                    parameterName = token.value()

                    if kritaMethod is not None:
                        # !!??
                        Console.warning("---> W#0004: invalid class definition?")
                        Console.display(token)
                        Console.display(kritaMethod)
                        return False

        if countCBraces is None or countCBraces > 0:
            # not a normal case but nothing to do except print a warning?
            # at least do not add class in class list...
            Console.warning("---> W#0005: invalid class definition?")
            Console.display(countCBraces)
            return False

        self.__classes[kritaClass.name()] = kritaClass

        return True

    def __processFile(self, fileName):
        fullFileName = os.path.join(self.__libkisPath, fileName)
        with open(fullFileName, 'r') as fHandle:
            content = ''.join(fHandle.readlines())

        # Console.display(content)

        self.__tokens = self.__languageDef.tokenizer().tokenize(content)

        nbKo = 0
        while token := self.__tokens.next():
            if token.value() == 'class':
                # entering a class, process it
                if self.__processClass(fileName) is False:
                    nbKo += 1
        if nbKo:
            Console.warning(f"Processed file KO: {fileName}")

        return nbKo

    def classes(self):
        """Return krita classes"""
        return self.__classes


class KritaBuildDoc:
    """Main class to build documentation"""

    GIT_REPO = "https://invent.kde.org/graphics/krita"

    HTML_NODESCPROVIDED = "<span class='noDescriptionProvided'>(no description provided)</span>"

    def __init__(self, kritaSrcLibKisPath, databaseJson, outputHtml, outputPython, showTypes):
        self.__repoMasterHash =''
        self.__showTypes = showTypes
        self.__outputPython = outputPython
        self.__outputHtml = outputHtml
        self.__kritaSrcLibKisPath = kritaSrcLibKisPath
        self.__kritaReferential = {
                'tags': {},
                'classes': {}
            }
        self.__jsonDatabase = databaseJson

        self.__loadJson()

        self.__gitUpdateRepository()
        self.__gitTags()

        self.__analyseSources()
        self.__saveJson()
        self.__buildPythonDoc()
        self.__buildHtmlDoc()
        self.__showFoundTypes()

    def __getTag(self, tagRef):
        """Return tag from given tag ref"""
        if tagRef in self.__kritaReferential['tags']:
            return self.__kritaReferential['tags'][tagRef]
        return None

    def __getTagName(self, tagRef):
        """Return normalized version of tag"""
        if tagRef == 'master':
            return tagRef

        final = ''
        if found := re.search('(?P<dev>-.*)$', re.sub('-xx$', '', tagRef, flags=re.I)):
            final = found.group('dev').lower()
        return f"{int(tagRef[0:2])}.{int(tagRef[2:4])}.{int(tagRef[4:6])}{final}"

    def __htmlFormatRefTags(self, refTags, mode='b'):
        # return ref tags: first Implemented, last updated
        # 'b': both
        # 'f': first
        # 'l': last
        # 'ld': last if different
        implementedFrom = refTags["available"][0]
        lastUpdatedFrom = refTags["updated"][-1]

        deprecatedFrom = ""
        if 'deprecated' in refTags and len(refTags["deprecated"]):
            deprecatedFrom = refTags["deprecated"][0]

            if len(refTags["updated"]) > 1:
                lastUpdatedFrom = refTags["updated"][-2]

        returned = ''

        if mode in('b', 'f'):
            returned += f"<span class='refTag' title='First implemented version'><span class='refTagSymbol'>&#65291;</span><span class='refTagTag'>Krita {self.__getTagName(implementedFrom)}</span></span>"
        if mode == 'l' or mode in ('b', 'ld') and implementedFrom != lastUpdatedFrom:
            if deprecatedFrom != lastUpdatedFrom:
                returned += f"<span class='refTag' title='Last updated version'><span class='refTagSymbol'>&#8635;</span><span class='refTagTag'>Krita {self.__getTagName(lastUpdatedFrom)}</span></span>"


        if deprecatedFrom != "":
            deprecatedFrom = refTags["deprecated"][0]
            returned += f"<span class='refTag' title='Deprecated from'><span class='refTagSymbol'>&#9888;</span><span class='refTagTag'>Krita {self.__getTagName(deprecatedFrom)}</span></span>"

        return returned

    def __htmlGetClassLink(self, className, methodName=""):
        """Return hyperlink for class name or class name if not possible to create an hyperlink"""

        if listType := re.search("^list\[([a-z0-9_]+)\]$", className, re.I):
            return f"list[{self.__htmlGetClassLink(listType.group(1))}]"
        elif dictType := re.search("^dict\[([a-z0-9_]+):\s([a-z0-9_]+)\]$", className, re.I):
            return f"dict[{self.__htmlGetClassLink(dictType.group(1))}: {self.__htmlGetClassLink(dictType.group(2))}]"

        if className not in self.__kritaReferential['classes']:
            return className

        if methodName:
            returned = f"<a href='kapi-class-{className}.html#{methodName}' target='iframeClass'>{methodName}</a>"
        else:
            returned = f"<a href='kapi-class-{className}.html' target='iframeClass'>{className}</a>"

        return returned

    def __loadJson(self):
        """Load Json documentation file"""
        if os.path.exists(self.__jsonDatabase):
            try:
                Console.display(". LOAD REFERENTIAL")
                with open(self.__jsonDatabase, 'r') as fHandle:
                    self.__kritaReferential = json.loads(fHandle.read())
            except Exception as e:
                Console.error(["Can't load referential, rebuild from scratch", str(e)])
        else:
            Console.display(". LOAD REFERENTIAL (none found)")

    def __saveJson(self):
        """Save Json documentation file"""
        try:
            Console.display(". SAVE REFERENTIAL")
            with open(self.__jsonDatabase, 'w') as fHandle:
                fHandle.write(json.dumps(self.__kritaReferential, indent=1, sort_keys=True))
        except Exception as e:
            Console.error(["ERROR: Can't save referential!", str(e)])

    def __gitTags(self):
        """Get, filter & sort git tags to process

        Build self.__tagList:
            normalised krita version;tag name;commit hash;alpha/beta/rc

            example:
                05.01.06;5.1.6;6a72b3503238bdfbc72f903b41cc2c97064da469;2023-01-01
        """
        def fixVersion(reflog):
            values = reflog.split(';')
            values[0] = values[0].replace('v', '')

            final='-XX'
            if found := re.search("(?P<dev>-(?:rc\d+|prealpha|beta\d+))", values[0], flags=re.I):
                final=found.group('dev').upper()

            values[0] = re.sub('-.*$', '', values[0])

            return ''.join([f"{int(v):02}" for v in values[0].split('.')]) + final

        def validVersion(reflog):
            if result := re.search(r"^v?(\d)\.\d+\.\d+(?:-(?:rc\d+|prealpha|beta\d+))?;", reflog, flags=re.I):
                if int(result.groups()[0]) >= 4:
                    return True
            return False

        def tagData(reflog):
            values = reflog.split(';')
            return {
                    'tag': values[1],
                    'hash': values[2],
                    'date': values[3],
                    'processed': False
                }

        Console.display(". RETRIEVE TAGS")

        try:
            cmdResult = subprocess.run(["git",
                                        "-C", self.__kritaSrcLibKisPath,
                                        "for-each-ref", '--format=%(refname:short);%(refname:short);%(objectname);%(creatordate:short)', "refs/tags"
                                        ],
                                       capture_output=True)
        except Exception as e:
            Console.error(["Unable to retrieve git tags", str(e)])
            return False

        if cmdResult.returncode != 0:
            Console.error(["Unable to retrieve git tags"] + cmdResult.stderr.decode().split('\n'))
            return False

        newTags = 0
        self.__kritaReferential['tags']['master'] = tagData(f'master;master;{self.__repoMasterHash};{time.strftime("%Y-%m-%d")}')
        for tag in cmdResult.stdout.decode().split('\n'):
            if validVersion(tag):
                fVersion = fixVersion(tag)
                if fVersion not in self.__kritaReferential['tags']:
                    self.__kritaReferential['tags'][fVersion] = tagData(tag)
                    Console.display(f"  > Found new tag: {self.__kritaReferential['tags'][fVersion]['tag']}")
                    newTags += 1

        if newTags == 0:
            Console.display("  > No new tag found")

        return True

    def __gitCheckout(self, hash):
        """Git checkout to hash
        Return True if checkout is OK, otherwise False
        """
        try:
            cmdResult = subprocess.run(["git",
                                        "-C", self.__kritaSrcLibKisPath,
                                        "checkout", hash], capture_output=True)
            # print(cmdResult)
            return True
        except Exception:
            return False

    def __gitUpdateRepository(self):
        Console.display(". UPDATE REPOSITORY")
        self.__gitCheckout('master')

        try:
            cmdResult = subprocess.run(["git",
                                        "-C", self.__kritaSrcLibKisPath,
                                        "pull",
                                        "--tags",
                                        "--all"
                                        ],
                                        capture_output=True)
            # print(cmdResult)
            cmdResult = subprocess.run(["git",
                                        "-C", self.__kritaSrcLibKisPath,
                                        "rev-parse",
                                        "HEAD",
                                        ],
                                        capture_output=True)
            self.__repoMasterHash = cmdResult.stdout.decode().strip('\n')
            return True
        except Exception:
            return False

    def __updateClasses(self, tagRef, classNfo):
        """Update self.__kritaReferential classes"""
        name = classNfo['name']
        if name not in self.__kritaReferential['classes']:
            # class doesn't exist yet in referential, add it
            self.__kritaReferential['classes'][name] = classNfo
            self.__kritaReferential['classes'][name]['tagRef']['available'].append(tagRef)
            self.__kritaReferential['classes'][name]['tagRef']['updated'].append(tagRef)
            for updateMethod in self.__kritaReferential['classes'][name]['methods']:
                updateMethod['tagRef']['available'].append(tagRef)
                updateMethod['tagRef']['updated'].append(tagRef)
            return

        # ensure to get last version
        self.__kritaReferential['classes'][name]['extend'] = classNfo['extend']
        self.__kritaReferential['classes'][name]['description'] = classNfo['description']
        self.__kritaReferential['classes'][name]['sourceCodeLine'] = classNfo['sourceCodeLine']

        isUpdated = False
        for method in classNfo['methods']:
            found = False
            # look into current class methods
            for updateMethod in self.__kritaReferential['classes'][name]['methods']:
                if updateMethod["name"] == method['name']:
                    found = True
                    if tagRef not in updateMethod['tagRef']['available']:
                        updateMethod['tagRef']['available'].append(tagRef)
                    if updateMethod["hash"] != method['hash']:
                        # method has been modified
                        # get new one
                        for property in [k for k in method.keys() if k != 'tagRef']:
                            updateMethod[property] = method[property]

                        if tagRef not in updateMethod['tagRef']['updated']:
                            updateMethod['tagRef']['updated'].append(tagRef)
                    else:
                        updateMethod['sourceCodeLine'] = method['sourceCodeLine']

                if found:
                    if method['isDeprecated'] and tagRef not in updateMethod['tagRef']['deprecated']:
                        updateMethod['tagRef']['deprecated'].append(tagRef)
                    break

            if found is False:
                self.__kritaReferential['classes'][name]['methods'].append(method)
                method['tagRef']['available'].append(tagRef)
                method['tagRef']['updated'].append(tagRef)
                isUpdated = True

        if isUpdated:
            self.__kritaReferential['classes'][name]['tagRef']['updated'].append(tagRef)

    def __analyseSources(self):
        """Loop over tags

        if tags hasn't been processed:
        - checkout tag
        - do analysis
        - store results

        Note:
        - always analyze 'master'
        - repo is on master when this method is called
        """
        Console.display(f". ANALYZE SOURCES")

        tagList = sorted(self.__kritaReferential['tags'].keys())
        if 'master' not in tagList:
            tagList = ['master'] + tagList

        for tagRef in tagList:
            tag = self.__kritaReferential['tags'][tagRef]

            if found := re.search('(?P<dev>-.*)$', tagRef):
                final = found.group('dev').upper()
                if final != '-XX':
                    if re.sub('-.*$', '-XX', tagRef) in tagList:
                        # a final version exists, do not proceed to ALPHA/BETA/RC...
                        continue

            if tag['processed'] is False:
                Console.display(f"  > TAG: {tag['tag']: <20} [{tag['hash']}]")
                if self.__gitCheckout(tag['hash']):
                    buildApiDoc = KritaApiAnalysis(kritaSrcLibKisPath)
                    for classNfo in [classNfo.toDict() for className, classNfo in buildApiDoc.classes().items()]:
                        self.__updateClasses(tagRef, classNfo)
                    tag['processed'] = True
                else:
                    Console.warning("Can't checkout!!!")

        # switch back to master branch
        self.__gitCheckout('master')

    def __showFoundTypes(self):
        if self.__showTypes:
            Console.display(". FOUND TYPES:")
            t = []
            for cName, c in self.__kritaReferential['classes'].items():
                for m in c['methods']:
                    t.append(m["returned"])
                    for p in m['parameters']:
                        t.append(p["type"])

            Console.display('- ' + "\n- ".join(sorted(set(t))))

    def __buildPythonDoc(self):

        def formatMethod(methodNfo, className=None):
            # return formatted method string
            indent = ' ' * 4

            parameters = methodNfo["parameters"]
            description = methodNfo["description"].strip('\n')
            if description:
                description += "\n"

            implementedFrom = methodNfo["tagRef"]["available"][0]
            lastUpdatedFrom = methodNfo["tagRef"]["updated"][-1]

            if methodNfo['isVirtual']:
                description += "@Virtual\n"

            description += f"@Implemented with: {self.__getTagName(implementedFrom)}"
            if implementedFrom != lastUpdatedFrom:
                description += f"\n@Last updated with: {self.__getTagName(lastUpdatedFrom)}"

            returned = []
            if methodNfo['isSignal']:
                if description:
                    description = textwrap.indent(description, '# ')
                    returned.append(description)

                sigParam = ''
                if parameters:
                    sigParam = ", ".join([parameter['type'] for parameter in parameters])

                returned.append(f'{methodNfo["name"]} = pyqtSignal({sigParam})')
            else:
                if methodNfo['isStatic']:
                    returned.append('@staticmethod')
                    fctParam = []
                else:
                    fctParam = ['self']

                if parameters:
                    for parameter in parameters:
                        param = parameter['name']
                        if parameter['type']:
                            param = f"{param}: {parameter['type']}"
                        if parameter['default']:
                            param = f"{param} = {parameter['default']}"
                        fctParam.append(param)

                returnedType = ''
                if methodNfo["returned"] != 'void' and methodNfo["returned"] != className:
                    returnedType = f" -> {methodNfo['returned']}"

                if len(description.split("\n")) > 1:
                    description += "\n"

                returned.append(f'# Source location, line {methodNfo["sourceCodeLine"]}')
                returned.append(f'def {methodNfo["name"]}({", ".join(fctParam)}){returnedType}:')
                returned.append(textwrap.indent(f'"""{description}"""', indent))
                returned.append(f"{indent}pass")

            return "\n".join(returned)

        def formatClass(classNfo):
            # return formatted class string
            className = classNfo['name']
            indent = ' ' * 4
            returned = []

            returned.append(f"# Source")
            returned.append(f"# - File: {classNfo['fileName']}")
            returned.append(f"# - Line: {classNfo['sourceCodeLine']}")

            if classNfo['extend'] and re.search("^K(is|o).*", classNfo['extend']) is None:
                # do not extend Kis* and Ko* class as their not available in Pykrita API
                returned.append(f"class {className}({classNfo['extend']}):")
            else:
                returned.append(f"class {className}:")

            if classNfo['description']:
                description = classNfo["description"]

                implementedFrom = classNfo["tagRef"]["available"][0]
                lastUpdatedFrom = classNfo["tagRef"]["updated"][-1]

                description += f"\n@Implemented with: {self.__getTagName(implementedFrom)}\n"
                if implementedFrom != lastUpdatedFrom:
                    description += f"@Updated with: {self.__getTagName(lastUpdatedFrom)}\n"

                returned.append(textwrap.indent(f'"""{description}"""', indent))

            if classNfo['methods']:
                methodsSignal = []
                methodsStatic = []
                methods = []

                for methodNfo in sorted(classNfo['methods'], key=lambda x: x['name']):
                    if methodNfo['isSignal']:
                        methodsSignal.append(formatMethod(methodNfo))
                    elif methodNfo['isStatic']:
                        methodsStatic.append(formatMethod(methodNfo))
                    else:
                        methods.append(formatMethod(methodNfo, className))

                if methodsSignal:
                    returned.append(textwrap.indent("\n\n".join(methodsSignal), indent))

                if methodsStatic:
                    returned.append(textwrap.indent("\n\n".join(methodsStatic), indent))

                if methods:
                    returned.append(textwrap.indent("\n\n".join(methods), indent))
            else:
                returned.append(textwrap.indent('pass', indent))

            return "\n".join(returned)

        if self.__outputPython is not None:
            Console.display(". BUILD PYTHON DOC")
            lastTagRef = sorted(self.__kritaReferential['tags'].keys())[-1]
            tag = self.__getTag(lastTagRef)
            fileContent = [f"# {'-' * 80}",
                           f"# File generated by {__NAME__} v{__VERSION__}",
                           "# Can be used by IDE for auto-complete",
                           "# Build from header files from Krita's libkis source code folder",
                           "# ",
                           f"# Git tag:  {tag['tag']} ({tag['date']})",
                           f"# Git hash: {tag['hash']}",
                           f"# {'-' * 80}",
                           "",
                           "from PyQt5.Qt import *"
                           "",
                           "",
                           "# Declare empty classes to avoid inter-dependencies failure",
                           ]

            for className in sorted(self.__kritaReferential['classes'].keys()):
                fileContent.append(f"class {className}: pass")
            # tweak
            fileContent.append(f"class DockPosition: pass")

            for className in sorted(self.__kritaReferential['classes'].keys()):
                fileContent.append("")
                fileContent.append("")
                fileContent.append(formatClass(self.__kritaReferential['classes'][className]))

            try:
                with open(self.__outputPython, 'w') as fHandle:
                    fHandle.write("\n".join(fileContent))
                Console.display(f"  > File saved: {self.__outputPython}")
            except Exception as e:
                Console.error(["Can't save python file!", str(e)])

    def __buildHtmlDoc(self):

        def codeToHtml(code):
            # return given code syntax highlighted
            docHtml=[]

            languageDef = LanguageDefPython()
            tokens = languageDef.tokenizer().tokenize(code)

            tokens.resetIndex()
            while not (token := tokens.next()) is None:
                if token.type() == TokenType.SPACE:
                    docHtml.append(f"<span class='py{token.type()}'>{' ' * token.length()}</span>")
                else:
                    docHtml.append(f"<span class='py{token.type()}'>{token.text()}</span>")

            return f"<div class='code'>{''.join(docHtml)}</div>"

        def docMethodsList(methodType, classNfo):
            # format method list
            methodList = []

            for method in sorted(classNfo['methods'], key=lambda x: x['name']):
                if methodType == 'static' and method['isStatic'] or \
                   methodType == 'virtual' and method['isVirtual'] or \
                   methodType == 'signals' and method['isSignal'] or \
                   methodType == '' and not (method['isSignal'] or method['isVirtual'] or method['isStatic']):
                    methodList.append(method)

            if len(methodList) == 0:
                # nothing to return
                return ""

            # build method list
            returned = []
            for method in methodList:
                parameters = []
                for parameter in method['parameters']:
                    if method['isSignal']:
                        parameters.append(f"<span class='methodParameterType'>{parameter['type']}</span>")
                    else:
                        param = f"<span class='methodParamName'>{parameter['name']}</span>"
                        if parameter['type']:
                            param = f"{param}<span class='methodSep'>: </span><span class='methodParameterType'>{parameter['type']}</span>"
                        if parameter['default']:
                            param = f"{param}<span class='methodSep'> = </span><span class='methodParameterDefault'>{parameter['default']}</span>"
                        parameters.append(param)

                returnedType = ''
                if method["returned"] != 'void' and method["returned"] != className:
                    returnedType = f"<span class='methodSep'> &#10142; </span><span class='methodParameterType'>{method['returned']}</span>"

                deprecated = ""
                if method['isDeprecated']:
                    deprecated = "<span class='rightTag isDeprecated'></span>"

                returned.append(f"""<span class='methodList'
                                          data-version-first='{method['tagRef']['available'][0]}'
                                          data-version-last='{method['tagRef']['updated'][-1]}'>
                                        <a href='#{method['name']}'>
                                            <span class='methodName'>{method['name']}</span><span class='methodSep'>(</span>{'<span class="methodSep">, </span>'.join(parameters)}<span class='methodSep'>)</span>{returnedType}
                                        </a>
                                        {deprecated}
                                    </span>""")

            returned = '\n'.join(returned)

            if methodType == 'static':
                title = "Static methods"
            elif methodType == 'virtual':
                title = "Re-implemented methods"
            elif methodType == 'signals':
                title = "Signals"
            else:
                title = "Methods"

            return f"""<h2>{title}</h2>
                <div class='methodList'>
                    {returned}
                </div>
                """

        def docMethods(classNfo):
            # format methods
            returned = []
            for method in sorted(classNfo['methods'], key=lambda x: x['name']):
                parameters = []
                for parameter in method['parameters']:
                    if method['isSignal']:
                        parameters.append(f"<span class='methodParameterType'>{parameter['type']}</span>")
                    else:
                        param = f"<span class='methodParamName'>{parameter['name']}</span>"
                        if parameter['type']:
                            param = f"{param}<span class='methodSep'>: </span><span class='methodParameterType'>{self.__htmlGetClassLink(parameter['type'])}</span>"
                        if parameter['default']:
                            param = f"{param}<span class='methodSep'> = </span><span class='methodParameterDefault'>{parameter['default']}</span>"
                        parameters.append(param)

                returnedType = ''
                if method["returned"] != 'void' and method["returned"] != className:
                    returnedType = f"<span class='methodSep'> &#10142; </span><span class='methodParameterType'>{self.__htmlGetClassLink(method['returned'])}</span>"

                isVirtual = ""
                if method['isVirtual']:
                    isVirtual = "<span class='rightTag isVirtual'></span>"
                isStatic = ""
                if method['isStatic']:
                    isStatic = "<span class='rightTag isStatic'></span>"
                isSignal = ""
                if method['isSignal']:
                    isSignal = "<span class='rightTag isSignal'></span>"
                isDeprecated = ""
                if method['isDeprecated']:
                    isDeprecated = "<span class='rightTag isDeprecated'></span>"

                methodContent = f"""<div class='methodDef'
                                         data-version-first='{method['tagRef']['available'][0]}'
                                         data-version-last='{method['tagRef']['updated'][-1]}'>
                    <div class='def'>
                        <a class='className' id="{method['name']}">{method['name']}</a><span class='methodSep'>(</span>{'<span class="methodSep">, </span>'.join(parameters)}<span class='methodSep'>)</span>{returnedType}
                        {isVirtual}{isStatic}{isSignal}{isDeprecated}
                    </div>
                    <div class='docRefTags'>{self.__htmlFormatRefTags(method["tagRef"])}</div>
                    <div class='docString'>
                        {formatDescription(classNfo, method['description'], method)}
                    </div>
                </div>
                """
                returned.append(methodContent)

            returned = '\n'.join(returned)
            return returned

        def formatDescription(classNfo, description, method=None):
            # reformat description for HTML
            # Recognized tags
            #  @brief
            #  @code - @endcode
            #  @param
            #  @return
            def fixLines(text):
                returned = re.sub(r"([^\s])\n([^\s])", r"\1 \2", text)
                returned = re.sub(r"^\n|\n$", "", returned)
                return returned

            def getCodeBlocks(text):
                returnedText = ''
                returnedBlocks = {}
                blocks = re.split("\x01", text)
                codeBlockNumber = 0
                for index in range(len(blocks)):
                    if index % 2 == 0:
                        returnedText += blocks[index]
                    else:
                        codeBlockNumber += 1
                        blockId = f"$codeBlock{codeBlockNumber}$"
                        returnedText += blockId
                        returnedBlocks[blockId] =  re.sub(r"^\n|\n$", "", blocks[index])
                return (returnedText, returnedBlocks)

            def asParagraph(text, codeBlocks):
                returned = []
                for line in text.split("\n"):
                    if blocks := re.findall(r"(\$codeBlock\d+\$)", line):
                        for block in blocks:
                            if block in codeBlocks:
                                line = line.replace(block, codeToHtml(codeBlocks[block]))

                    returned.append(f"<p>{line}</p>")
                return ''.join(returned)

            returnedNfo = {}

            if method:
                if len(method['parameters']):
                    returnedNfo['@param'] = {}
                if method['returned'] != 'void':
                    returnedNfo['@return'] = KritaBuildDoc.HTML_NODESCPROVIDED

            description = re.sub("^@@", "@", description, flags=re.I)
            description = re.sub("@code", "\x01", description, flags=re.I)
            description = re.sub("@endcode", "\x01", description, flags=re.I)
            description = re.sub(r"@[cp]\s", "", description, flags=re.I)
            while foundRef := re.search('(?P<refG>@ref\s(?P<refN>[^\s]+))', description):
                refG = foundRef.group('refG')
                refN = foundRef.group('refN')

                if re.search('::', refN):
                    description = description.replace(refG, f"<span class='decRef'>{refN}</span>")
                else:
                    methodName = re.sub("\(.*\)$", "", refN, flags=re.I)
                    if methodName in [methods['name'] for methods in classNfo['methods']]:
                        description = description.replace(refG, f"<span class='className'><a href='#{methodName}'>{methodName}</a></span><span class='className methodSep'>()</span>")
                    else:
                        description = description.replace(refG, refN)

            description, codeBlocks = getCodeBlocks(description)
            splitted = re.split(r"^(@[a-z0-9]+\s)", description, flags=re.M | re.I)

            while len(splitted) and splitted[0].strip() == '':
                splitted.pop(0)

            if len(splitted) and re.search("^@", splitted[0]) is None:
                # a description without any tag?
                splitted.insert(0, "@brief")
                if method and {method['name']}:
                    splitted[1] = f"{method['name']} {splitted[1]}"

            index = 0
            while index < len(splitted):
                if splitted[index].strip() == '':
                    # expected a @xxx tag; skip empty lines
                    index += 1
                    continue

                docTag = splitted[index].lower().strip()
                docValue = splitted[index+1]

                if found := re.findall(r"(@param\s+[^\s]+)", docValue, flags=re.I):
                    for foundItem in found:
                        paramName = re.sub(r'@param\s+', '', foundItem, flags=re.I)
                        splitted.append('@param')
                        splitted.append(f"{paramName} ")
                        docValue = docValue.replace(foundItem, paramName)

                if docTag == '@brief':
                    if method and method['name']:
                        returnedNfo['@brief'] = fixLines(re.sub(fr"^{method['name']}\s+", "", docValue))
                    else:
                        returnedNfo['@brief'] = fixLines(docValue)
                elif docTag == '@param':
                    if '@param' not in returnedNfo:
                        returnedNfo['@param'] = {}

                    if nfo := re.search(r"^([a-z0-9_]+)\s+(.*)", docValue, flags=re.S | re.I):
                        paramName = nfo.groups()[0]
                        paramDescription = nfo.groups()[1]
                        if paramName not in returnedNfo['@param']:
                            if paramDescription == '':
                                paramDescription = '<span class="noDescriptionProvided">(no description provided)</span>'
                            returnedNfo['@param'][paramName] = fixLines(paramDescription)
                        else:
                            if returnedNfo['@param'][paramName] == '' and paramDescription != '':
                                returnedNfo['@param'][paramName] = fixLines(paramDescription)

                elif docTag in ('@return', '@returns'):
                    returnedNfo['@return'] = fixLines(docValue)
                elif docTag in ('@retval'):
                    if '@return' not in returnedNfo or returnedNfo['@return'] == KritaBuildDoc.HTML_NODESCPROVIDED:
                        returnedNfo['@return'] = ''
                    else:
                        returnedNfo['@return'] += '<br>'
                    returnedNfo['@return'] += fixLines(docValue)
                elif docTag in ('@see'):
                    returnedNfo['@see'] = fixLines(docValue)
                elif docTag in ('@class'):
                    # ignore this docTag
                    pass
                elif docTag in ('@ref'):
                    # ignore this docTag
                    pass
                else:
                    if method and method['name']:
                        Console.warning(f"Unknown docTag {docTag} in function {method['name']}")
                    else:
                        Console.warning(f"WARNING: unknown docTag {docTag}")

                index += 2

            if len(codeBlocks):
                returnedNfo['@code'] = codeBlocks
            else:
                returnedNfo['@code'] = []

            # order:
            # - brief
            # - param
            # - return

            returned = []

            if '@brief' in returnedNfo:
                returned.append(asParagraph(returnedNfo['@brief'], returnedNfo['@code']))

            if '@param' in returnedNfo:
                paramTableTr = []

                if method and len(method['parameters']):
                    # manage parameters in priority, using method parameters order
                    for parameter in method['parameters']:
                        parameterName = parameter['name']
                        if parameterName in returnedNfo['@param']:
                            paramTableTr.append(f"<tr><td class='paramName'><span class='methodParamName'>{parameterName}</span></td><td>{asParagraph(returnedNfo['@param'][parameterName], returnedNfo['@code'])}</td></tr>")
                        else:
                            paramTableTr.append(f"<tr><td class='paramName'><span class='methodParamName'>{parameterName}</span></td><td><span class='noDescriptionProvided'>(no description provided)</span></td></tr>")
                else:
                    for parameterName, parameterDescription in returnedNfo['@param'].items():
                        paramTableTr.append(f"<tr><td class='paramName'><span class='methodParamName'>{parameterName}</span></td><td>{asParagraph(parameterDescription, returnedNfo['@code'])}</td></tr>")

                returned.append(f"""<h3>Parameters</h3>
                    <table class='paramList'>
                        {''.join(paramTableTr)}
                    </table>
                    """)

            if '@return' in returnedNfo:
                returned.append(f"""<h3>Return</h3>
                    <table class='paramList'>
                        <tr><td>{asParagraph(returnedNfo['@return'], returnedNfo['@code'])}</td></tr>
                    </table>
                    """)

            if '@see' in returnedNfo:
                method = re.sub("\(.*\)$", "", returnedNfo['@see'], flags=re.I)
                if method in [methods['name'] for methods in classNfo['methods']]:
                    returned.append(f"<div class='docSee'>&#129170; See <span class='className'><a href='#{method}'>{method}</a></span><span class='className methodSep'>()</span></div>")

            return "\n".join(returned)

        def buildHtmlClass(classNfo, tag):
            # build html file for given class
            className = classNfo["name"]
            fileName = f'kapi-class-{classNfo["name"]}.html'

            fileContent = f"""<!DOCTYPE HTML>
            <html>
                <head>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                    <title>Krita Python API - Class {className}</title>
                    <link rel="stylesheet" type="text/css" href="dark.css">
                    <script type="text/javascript" src="filter-classes.js"></script>
                </head>
                <body class='class'>
                    <div class='header'>
                        <div class='title'>Class <span class='className'>{className}</span></div>
                    </div>
                    <div class='content'>
                        <div class='buildFrom'>Build from <a target='_blank' href='{KritaBuildDoc.GIT_REPO}/-/blob/{tag['hash']}/libs/libkis/{classNfo["fileName"]}'>{classNfo["fileName"]}</a></div>
                        <div class='docRefTags'>{self.__htmlFormatRefTags(classNfo["tagRef"])}</div>
                        <div class='docString'>{formatDescription(classNfo, classNfo["description"])}</div>
                        {docMethodsList('static', classNfo)}
                        {docMethodsList('', classNfo)}
                        {docMethodsList('virtual', classNfo)}
                        {docMethodsList('signals', classNfo)}
                        <h1>Member documentation</h1>
                        {docMethods(classNfo)}
                    </div>
                </body>
            </html>
            """

            # dedent
            fileContent = re.sub(r"^[ ]{12}", "", fileContent, flags=re.M)
            htmlFile = os.path.join(self.__outputHtml, fileName)
            try:
                with open(htmlFile, 'w') as fHandle:
                    fHandle.write(fileContent)
                Console.display(f"  > File saved: {htmlFile}")
            except Exception as e:
                Console.error([f"Can't save html file: {fileName}", str(e)])

        def buildHtmlIndex(classNfo, lastTag):
            # build main index.html file

            tagList=[]
            for tagKey in sorted(self.__kritaReferential['tags'].keys()):
                selected=''
                if lastTag['tag'] == self.__kritaReferential['tags'][tagKey]['tag']:
                    selected=' selected'

                if tagKey != 'master' and not re.search('-XX$', tagKey):
                    if re.sub('-.*$', '-XX', tagKey) in self.__kritaReferential['tags']:
                        # final version exists, do not add RC, BETA, ALPHA, ... in tag list
                        continue

                tagList.append(f"<option value='{tagKey}'{selected}>{self.__getTagName(tagKey)}</option>")

            classList = []
            for className in sorted(classNfo.keys()):
                classList.append(f"<li data-version-first='{classNfo[className]['tagRef']['available'][0]}'"
                                 f"    data-version-last='{classNfo[className]['tagRef']['updated'][-1]}'>"
                                 f"<a href='kapi-class-{className}.html' target='iframeClass'>{className}</a>"
                                 f"</li>"
                                 )

            fileName = f'index.html'
            fileContent = f"""<!DOCTYPE HTML>
            <html>
                <head>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                    <title>Krita Python API</title>
                    <link rel="stylesheet" type="text/css" href="dark.css">
                    <script type="text/javascript" src="filter-index.js"></script>
                </head>
                <body class='index'>
                    <div class='leftMenu'>
                        <div class='menuHeader'>
                            <div class='title'>Krita Python API</div>
                            <div class='version'>
                                <select class='inputField' id="tags" name="tags">{''.join(tagList)}</select>
                                <label class='inputField' id="viewModeDeltaLbl"><input type="checkbox" id="viewModeDelta">Implemented changes only</label>
                            </div>
                        </div>
                        <div class='menuContent'>
                            <h3>Python API Indexes</h3>
                            <ul>
                                <li><a href='kapi-version.html' target='iframeClass'>Versions</a></li>
                                <li><a href='kapi-classes.html' target='iframeClass'>Classes</a></li>
                            </ul>
                            <h3>Classes</h3>
                            <ul>{''.join(classList)}</ul>
                        </div>
                    </div>
                    <iframe class='frameContent' src="kapi-classes.html" name="iframeClass" id="iframeClass"></iframe>
                    <div class='footer'>Generated at {time.strftime("%Y-%m-%d %H:%M:%S%z")} from <a target='_blank' href='{KritaBuildDoc.GIT_REPO}'>Krita</a> branch master, commit <a target='_blank' href='{KritaBuildDoc.GIT_REPO}/-/tree/{self.__repoMasterHash}'>{self.__repoMasterHash}</a></div>
                </body>
            </html>
            """

            # dedent
            fileContent = re.sub(r"^[ ]{12}", "", fileContent, flags=re.M)
            htmlFile = os.path.join(self.__outputHtml, fileName)
            try:
                with open(htmlFile, 'w') as fHandle:
                    fHandle.write(fileContent)
                Console.display(f"  > File saved: {htmlFile}")
            except Exception as e:
                Console.error([f"Can't save html file: {fileName}", str(e)])

        def buildHtmlIndexVersions():
            """Build index version"""
            tableContent =[]
            for tagKey in sorted(self.__kritaReferential['tags'].keys(), reverse=True):
                tableContent.append(f"<tr data-id='{tagKey}'>"
                                    f"<td class='tagVersion'><a target='_blank' href='{KritaBuildDoc.GIT_REPO}/-/tags/{self.__kritaReferential['tags'][tagKey]['tag']}'>{self.__getTagName(tagKey)}</a></td>"
                                    f"<td class='tagDate'>{self.__kritaReferential['tags'][tagKey]['date']}</td>"
                                    f"<td class='tagHash'><a target='_blank' href='{KritaBuildDoc.GIT_REPO}/-/tree/{self.__kritaReferential['tags'][tagKey]['hash']}'>{self.__kritaReferential['tags'][tagKey]['hash']}</a></td>"
                                    f"</tr>"
                                    )

            fileName = f'kapi-version.html'
            fileContent = f"""<!DOCTYPE HTML>
            <html>
                <head>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                    <title>Krita Python API - Versions</title>
                    <link rel="stylesheet" type="text/css" href="dark.css">
                </head>
                <body class='class'>
                    <div class='header'>
                        <div class='title'>Versions</div>
                    </div>
                    <div class='content'>
                        <table class='versions'>
                            <tr><th>Version</th><th>Date</th><th>Commit</th></tr>
                            {''.join(tableContent)}
                        </table>
                    </div>
                </body>
            </html>
            """
            # dedent
            fileContent = re.sub(r"^[ ]{12}", "", fileContent, flags=re.M)
            htmlFile = os.path.join(self.__outputHtml, fileName)
            try:
                with open(htmlFile, 'w') as fHandle:
                    fHandle.write(fileContent)
                Console.display(f"  > File saved: {htmlFile}")
            except Exception as e:
                Console.error([f"Can't save html file: {fileName}", str(e)])

        def buildHtmlIndexClasses(classNfo):
            """Build classes index"""
            tableContent = []
            for className in sorted(classNfo.keys()):
                methods = []
                methodsRef = {}
                for method in classNfo[className]['methods']:
                    classes=[]
                    if method['isSignal']:
                        classes.append('isSignal')
                    if method['isStatic']:
                        classes.append('isStatic')
                    if method['isVirtual']:
                        classes.append('isVirtual')
                    if method['isDeprecated']:
                        classes.append('isDeprecated')

                    if len(classes):
                        classes.append('inline rightTag')

                    methodsRef[method['name']]=(f"<span class='methodName {' '.join(classes)}'"
                                                f" data-version-first='{method['tagRef']['available'][0]}'"
                                                f" data-version-last='{method['tagRef']['updated'][-1]}'>"
                                                f"{self.__htmlGetClassLink(className, method['name'])}"
                                                f"</span>"
                                                )
                for index, methodName in enumerate(sorted(methodsRef.keys())):
                    if index > 0:
                        methods.append('<br>')
                    methods.append(methodsRef[methodName])

                tableContent.append(f"<tr data-id='{className}'"
                                    f" data-version-first='{classNfo[className]['tagRef']['available'][0]}'"
                                    f" data-version-last='{classNfo[className]['tagRef']['updated'][-1]}'>"
                                    f"<td class='className'>{self.__htmlGetClassLink(className)}</td>"
                                    f"<td class='version'>{self.__htmlFormatRefTags(classNfo[className]['tagRef'], 'f')}</td>"
                                    f"<td class='version'>{self.__htmlFormatRefTags(classNfo[className]['tagRef'], 'ld')}</td>"
                                    f"<td class='members'>{''.join(methods)}</td>"
                                    "</tr>"
                                    )

            fileName = f'kapi-classes.html'
            fileContent = f"""<!DOCTYPE HTML>
            <html>
                <head>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                    <title>Krita Python API - Versions</title>
                    <link rel="stylesheet" type="text/css" href="dark.css">
                    <script type="text/javascript" src="filter-classes.js"></script>
                </head>
                <body class='class'>
                    <div class='header'>
                        <div class='title'>Classes</div>
                    </div>
                    <div class='content'>
                        <table class='classes'>
                            <tr><th class='labelClass'>Class</th><th class='labelVersion'>Implemented</th><th class='labelVersion'>Updated</th><th>Members</th></tr>
                            {''.join(tableContent)}
                        </table>
                    </div>
                </body>
            </html>
            """
            # dedent
            fileContent = re.sub(r"^[ ]{12}", "", fileContent, flags=re.M)
            htmlFile = os.path.join(self.__outputHtml, fileName)
            try:
                with open(htmlFile, 'w') as fHandle:
                    fHandle.write(fileContent)
                Console.display(f"  > File saved: {htmlFile}")
            except Exception as e:
                Console.error([f"Can't save html file: {fileName}", str(e)])

        if self.__outputHtml is not None:
            Console.display(". BUILD HTML DOC")

            lastTagRef = sorted(self.__kritaReferential['tags'].keys())[-1]
            tag = self.__getTag(lastTagRef)
            tag['nTagName'] = self.__getTagName(lastTagRef)

            for className in sorted(self.__kritaReferential['classes'].keys()):
                buildHtmlClass(self.__kritaReferential['classes'][className], tag)

            buildHtmlIndexVersions()
            buildHtmlIndexClasses(self.__kritaReferential['classes'])
            buildHtmlIndex(self.__kritaReferential['classes'], tag)

            cssSource = os.path.join(os.path.dirname(__file__), "res", "dark.css")
            cssTarget = os.path.join(self.__outputHtml, "dark.css")
            try:
                shutil.copy2(cssSource, cssTarget)
            except Exception as e:
                Console.warning(["Can't copy CSS file:",
                                 f". From: {cssSource}",
                                 f". To:   {cssTarget}",
                                 f"{e}"
                                 ])

            jsSource = os.path.join(os.path.dirname(__file__), "res", "filter-index.js")
            jsTarget = os.path.join(self.__outputHtml, "filter-index.js")
            try:
                shutil.copy2(jsSource, jsTarget)
            except Exception as e:
                Console.warning(["Can't copy JS file:",
                                 f". From: {jsSource}",
                                 f". To:   {jsTarget}",
                                 f"{e}"
                                 ])

            jsSource = os.path.join(os.path.dirname(__file__), "res", "filter-classes.js")
            jsTarget = os.path.join(self.__outputHtml, "filter-classes.js")
            try:
                shutil.copy2(jsSource, jsTarget)
            except Exception as e:
                Console.warning(["Can't copy JS file:",
                                 f". From: {jsSource}",
                                 f". To:   {jsTarget}",
                                 f"{e}"
                                 ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build krita documentation')
    parser.add_argument('-k', '--kritaSrc',
                        dest='KRITA_SOURCE_PATH',
                        metavar='PATH',
                        action='store',
                        help='Krita source code path'
                        )

    parser.add_argument('--output-html',
                        dest='OUTPUT_HTML',
                        metavar='PATH',
                        action='store',
                        help='\n'.join(['Html output path',
                                        'When provided, HTML documentation will be built'
                                        ])
                        )

    parser.add_argument('--output-python',
                        dest='OUTPUT_PYTHON',
                        metavar='PATH',
                        action='store',
                        help='\n'.join(['Python output path',
                                        'When provided, a krita.py file will be built',
                                        'This file can be used by IDE to understand PyKrita API class'
                                        ])
                        )

    parser.add_argument('--database-json',
                        dest='DATABASE_JSON',
                        metavar='FILE',
                        action='store',
                        help='\n'.join(['Json database path',
                                        'When provided, use given file as JSON database',
                                        'Otherwise will use default JSON database file'
                                        ])
                        )

    parser.add_argument('-r', '--reset',
                        dest='DATABASE_RESET',
                        action='store_true',
                        help='Rebuild from scratch'
                        )

    parser.add_argument('-t', '--show-types',
                        dest='SHOW_TYPES',
                        action='store_true',
                        help='List found types'
                        )

    args = parser.parse_args()
    argsVar = vars(args)

    if argsVar['KRITA_SOURCE_PATH'] is None:
        parser.print_help()
        exit(-1)

    kritaSrcPath = os.path.expanduser(os.path.abspath(argsVar['KRITA_SOURCE_PATH']))
    if not os.path.exists(kritaSrcPath):
        Console.error([f"Given Krita source path seems to not be a valid Krita source repository: {kritaSrcPath}",
                       "--> Path not found"
                       ])

    kritaSrcLibKisPath = os.path.join(kritaSrcPath, 'libs', 'libkis')
    if not os.path.exists(kritaSrcLibKisPath):
        Console.error([f"Given Krita source path seems to not be a valid Krita source repository: {kritaSrcPath}",
                       "--> Unable to find libs/libkis"
                       ])

    try:
        cmdResult = subprocess.run(["git", "--version"], capture_output=True)
    except Exception:
        Console.error(["Git is not installed on your system",
                       "Git is required"
                       ])

    outputHtml = None
    outputPython = None
    databaseJson = os.path.join(os.path.dirname(__file__), 'krita-apisrc.json')

    if argsVar['OUTPUT_HTML'] is not None:
        outputHtml = os.path.abspath(argsVar['OUTPUT_HTML'])
        os.makedirs(outputHtml, exist_ok=True)

    if argsVar['OUTPUT_PYTHON'] is not None:
        outputPython = os.path.abspath(argsVar['OUTPUT_PYTHON'])
        if not re.search("\.py$", os.path.basename(outputPython)):
            outputPython = os.path.join(outputPython, 'krita.py')
        os.makedirs(os.path.dirname(outputPython), exist_ok=True)

    if argsVar['DATABASE_JSON'] is not None:
        databaseJson = os.path.abspath(argsVar['DATABASE_JSON'])
        if not re.search("\.json", os.path.basename(databaseJson)):
            databaseJson = os.path.join(databaseJson, 'krita-apisrc.json')
        os.makedirs(os.path.dirname(databaseJson), exist_ok=True)

    if argsVar['DATABASE_RESET'] and os.path.exists(databaseJson):
        Console.display('. RESET DATABASE')
        os.remove(databaseJson)

    KritaBuildDoc(kritaSrcLibKisPath,
                  databaseJson,
                  outputHtml,
                  outputPython,
                  argsVar['SHOW_TYPES'])
