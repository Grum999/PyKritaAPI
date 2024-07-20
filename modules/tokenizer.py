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
# The tokenizer module provides a generic tokenizer and tools needed to
# define grammar
# (Works with languagedef + tokenizer modules)
# (that can be tokenized and parsed --> tokenizer + parser modules)
# Main class from this module
#
# - Tokenizer:
#       The tokenizer (need rules to tokenize)
#       Usually, language definition instanciate tokenizer and provides rules
#
# - Token:
#       A token built from given text and language definition
#
# - TokenizerRule:
#       A class that define a basic rule to produce a Token from text
#       Language definition are built with TokenizerRule items
#
# -----------------------------------------------------------------------------

import hashlib
import re
import time

from .elist import EList

from .extendableenum import ExtendableEnum


class TokenType(ExtendableEnum):
    # some default token type
    UNKNOWN = ('Unknown', 'This value is not know in grammar and might not be interpreted')
    NEWLINE = ('NewLine', 'A line feed')
    SPACE = ('Space', 'Space(s) character(s)')
    INDENT = ('Indent', 'An indented block start')
    DEDENT = ('Dedent', 'An indented block finished')
    WRONG_INDENT = ('WrongIndent', 'An indent is found but doesn\'t match expected indentation value')
    WRONG_DEDENT = ('WrongDedent', 'An dedent is found but doesn\'t match expected indentation value')
    COMMENT = ('Comment', 'A comment text')

    def id(self, **param):
        """Return token Id value"""
        if isinstance(param, dict):
            return self.value[0].format(**param)
        else:
            return self.value[0]

    def description(self, **param):
        """Return token description"""
        if isinstance(param, dict):
            return self.value[1].format(**param)
        else:
            return self.value[1]

    def __format__(self, spec):
        return f"{self.value[0]:{spec}}"


class Token(object):
    """A token

    Once created, can't be changed

    A token have the following properties:
    - a type
    - a value
    - position (column and row) from original text
    """
    __LINE_NUMBER = 0
    __LINE_POSSTART = 0

    @staticmethod
    def resetTokenizer():
        Token.__LINE_NUMBER = 1
        Token.__LINE_POSSTART = 0

    def __init__(self, text, rule, positionStart, positionEnd, length, simplifySpaces=False):
        self.__text = text.lstrip()
        self.__rule = rule
        self.__positionStart = positionStart
        self.__positionEnd = positionEnd
        self.__length = length
        self.__lineNumber = Token.__LINE_NUMBER
        self.__linePositionStart = (positionStart - Token.__LINE_POSSTART) + 1
        self.__linePositionEnd = self.__linePositionStart + length
        self.__next = None
        self.__previous = None
        self.__simplifySpaces = simplifySpaces

        self.__type = rule.type()

        Token.__LINE_NUMBER += text.count('\n')
        if self.__type == TokenType.NEWLINE:
            self.__indent = 0
            Token.__LINE_POSSTART = positionEnd
        else:
            self.__indent = len(text) - len(self.__text)

        if simplifySpaces and self.__type != TokenType.COMMENT:
            # do not simplify COMMENT token
            self.__text = re.sub(r"\s+", " ", self.__text)

        self.__caseInsensitive = self.__rule.caseInsensitive()
        self.__iText = self.__text.lower()

        self.__value = self.__text

    def __repr__(self):
        if self.__type == TokenType.NEWLINE:
            txt = ''
        else:
            txt = self.__text
        return (f"<Token({self.__indent}, '{txt}', Type[{self.__type}]"
                f"Length: {self.__length}, "
                f"Global[Start: {self.__positionStart}, End: {self.__positionEnd}], "
                f"Line[Start: {self.__linePositionStart}, End: {self.__linePositionEnd}, Number: {self.__lineNumber}])>")

    def __str__(self):
        return f'| {self.__linePositionStart:>5} | {self.__lineNumber:>5} | {self.__indent:>2} | {self.__type:<50} | {self.__length:>2} | `{self.__text}`'

    def type(self):
        """return token type"""
        return self.__type

    def positionStart(self):
        """Return position (start) in text"""
        return self.__positionStart

    def positionEnd(self):
        """Return position (end) in text"""
        return self.__positionEnd

    def length(self):
        """Return text length"""
        return self.__length

    def indent(self):
        """Return token indentation"""
        return self.__indent

    def text(self):
        """Return token text"""
        return self.__text

    def value(self):
        """Return token value

        Value can differ from text:
        - text is raw text, provided as string value
        - value is a pre-processed text
        """
        return self.__value

    def rule(self):
        """Return token rule"""
        return self.__rule

    def setNext(self, token=None):
        """Set next token"""
        self.__next = token

    def setPrevious(self, token=None):
        """Set previous token"""
        self.__previous = token

    def next(self):
        """Return next token, or None if current token is the last one"""
        return self.__next

    def previous(self):
        """Return previous token, or None if current token is the last one"""
        return self.__previous

    def column(self):
        """Return column number for token"""
        return self.__linePositionStart

    def row(self):
        """Return row number for token"""
        return self.__lineNumber

    def isUnknown(self):
        """return if it's an unknown token"""
        return (self.__rule.type() == TokenType.UNKNOWN)

    def simplifySpaces(self):
        """Return if spaces are simplified or not"""
        return self.__simplifySpaces

    def equal(self, value, doLower=False, caseInsensitive=None):
        """Check if given text `value` equals or not text value from token

        If given `value` is a list, check if token text is in given list

        If `doLower` is True, equal() will lowercase value before comparison (if case insensitive)
        If False, consider that when equal function is called, value are already provided as lowercase
        (avoid to lowercase on each call can improve performance)

        This method take in account if the rule is case sensitive or not
        If `caseInsensitive` is provided (True or False) it will overrides the rule defined by tokenizerule
        Otherwise (None value) comparison will use the rule defined by tokenizerule
        """
        if caseInsensitive is None:
            checkCaseInsensitive = self.__caseInsensitive
        else:
            checkCaseInsensitive = (caseInsensitive is True)

        if isinstance(value, str):
            if checkCaseInsensitive:
                if doLower:
                    value = value.lower()

                return (self.__iText == value)
            else:
                return (self.__text == value)
        elif isinstance(value, list) or isinstance(value, tuple):
            if checkCaseInsensitive:
                if doLower:
                    lValue = [v.lower() for v in value]
                    return (self.__iText in lValue)
                return (self.__iText in value)
            else:
                return (self.__text in value)


class TokenizerRule(object):
    """Define a rule used by tokenizer to build a token

    A tokenizer rule is defined by:
    - A regular expression
    - A token type
    - An optional flag to set rule case insensitive (by default=True) or case sensitive
    """

    def __init__(self,
                 type,
                 regex,
                 caseInsensitive=True,
                 ignoreIndent=False,
                 multiLineStart=None,
                 multiLineEnd=None):
        """Initialise a tokenizer rule

        Given `type` determinate which type of token will be generated by rule
        Given `regex` is a regular expression that will define token
        Given `caseInsensitive` allows to define if token is case sensitive or case insensitive (default)
        Given `ignoreIndent` allows to define if token ignore or not indent (default False)
            For example, no INDENT/DEDENT token is produced before a token with `ignoreIndent` set to True
        Given `multiLineStart` and `multiLineEnd` allows to define regular exspression to define multiline token like python long string of C comments
            Used only for syntax highlighting (managed line by line)
            The main regex provided should be able to manage properly the tokenization within a multiline full source code
            If multiLineStart is provided, multiLineEnd must be provided too
            Can be list; is this case
                multiLineStart[0] is used with multiLineEnd[0]
                multiLineStart[1] is used with multiLineEnd[1]
                ...
                multiLineStart[n] is used with multiLineEnd[n]
        """
        self.__type = None
        self.__regEx = None

        # put in cache a regex with '^....$' to match single values (improve speed!)
        self.__regExSingle = None

        # lookahead and lookbehind are removed from __regExSingle
        # store them if any
        self.__regExLookAhead = None
        self.__regExLookAheadIsNeg = False
        self.__regExLookbehind = None
        self.__regExLookbehindIsNeg = False

        # list of errors for rule
        self.__error = []

        self.__caseInsensitive = caseInsensitive
        self.__ignoreIndent = ignoreIndent

        # if token can be on multiple line (python long string or C comment)
        # these are defined with regular expression designed to find start and end of
        # multine topken
        # --> this is mostly used for syntax highlighting
        self.__multiLineRegExStart = []
        self.__multiLineRegExEnd = []

        self.__setRegEx(regex)
        self.__setType(type)
        self.__setRegExMulLineStartEnd(multiLineStart, multiLineEnd)

        if len(self.__error) > 0:
            NL = "\n"
            raise Exception(f'Token rule ({regex}) for "{type}" is not valid!{NL}{NL.join(self.__error)}')

    def __str__(self):
        if self.isValid():
            return f'{self.__type}: {self.__regEx.pattern}'
        elif self.__regEx is None:
            return f'{self.__type} / None / {self.__error}'
        else:
            return f"{self.__type} / '{self.__regEx.pattern}' / {self.__error}"

    def __repr__(self):
        if self.__regEx is None:
            return f"<TokenizerRule({self.__type}, None)>"
        return f"<TokenizerRule({self.__type}, '{self.__regEx.pattern}')>"

    def __setRegEx(self, regEx):
        """Set current regular expression for rule

        Given `regEx` must be string

        If invalid, doesn't raise error: just define rule as 'in error' with a message
        """
        if not isinstance(regEx, str):
            self.__error.append("Given regular expression must be a <str>")
            return

        # build single regEx, use to check token type
        pattern = regEx

        # check if regex starts with a lookbehind
        #    Negative lookbehind: not preceded by xxx
        #    (?<!xxx)...
        #
        #    Positive lookbehind: preceded by xxx
        #    (?<=xxx)...
        #
        #   Note: lookahead & lookbehind normally don't accept unfixed patterns; here we accept them :-)
        if found := re.search(r"^\(\?<([!=])(.*?)\)", regEx):
            # store lookbehind pattern
            self.__regExLookbehind = re.compile(f"{found.groups()[1]}$")
            self.__regExLookbehindIsNeg = (found.groups()[0] == '!')

            # remove lookbehind from pattern
            regEx = re.sub(r"^(\(\?<[!=].*?\))", "", regEx)

        # check if regex ends with a lookahead
        #    Negative lookahead: not followed by xxx
        #    ...(?!xxx)
        #
        #    Positive lookahead: followed by xxx
        #    ...(?=xxx)
        #
        #   Note: lookahead & lookbehind normally don't accept unfixed patterns; here we accept them :-)
        if found := re.search(r"\(\?([!=])(.*?)\)$", regEx):
            # store lookahead pattern
            self.__regExLookAhead = re.compile(f"^{found.groups()[1]}")
            self.__regExLookAheadIsNeg = (found.groups()[0] == '!')

            # remove lookahead from pattern
            regEx = re.sub(r"(\(\?[!=].*?\))$", "", regEx)

        # full regEx, use to split tokens
        self.__regEx = re.compile(regEx)

        # single regEx, use to determinate tokens type
        if regEx != '' and regEx[0] == '^':
            regEx += '$'
        else:
            regEx = f'^{regEx}$'

        if self.__caseInsensitive:
            self.__regExSingle = re.compile(regEx, re.IGNORECASE)
        else:
            self.__regExSingle = re.compile(regEx)

    def __setRegExMulLineStartEnd(self, regExStart, regExEnd):
        """Set current regular expression for syntax highlighting of multine block

        Given `regExStart` and `regExEnd` can be:
            - A string
            - A list
            - None

        Both `regExStart` and `regExEnd` must be:
            - None
            or
            - A valid regular expression

        If invalid, doesn't raise error: just define rule as 'in error' with a message
        """
        if regExStart is not None:
            if isinstance(regExStart, str):
                if self.__caseInsensitive:
                    regExStart = re.compile(regExStart, re.IGNORECASE)
                else:
                    regExStart = re.compile(regExStart)
            elif isinstance(regExStart, (tuple, list)) and isinstance(regExEnd, (tuple, list)):
                if len(regExStart) == len(regExEnd):
                    for index in range(len(regExStart)):
                        self.__setRegExMulLineStartEnd(regExStart[index], regExEnd[index])
                    return
                else:
                    self.__error.append("Given regular expression `multiLineStart` is not a valid")
                    return
            else:
                self.__error.append("Given regular expression `multiLineStart` must be a <str> type")
                return

        if regExEnd is not None:
            if isinstance(regExEnd, str):
                if self.__caseInsensitive:
                    regExEnd = re.compile(regExEnd, re.IGNORECASE)
                else:
                    regExEnd = re.compile(regExEnd)
            else:
                self.__error.append("Given regular expression `multiLineEnd` must be a <str> type")
                return

        if regExStart is None and regExEnd is not None or regExStart is not None and regExEnd is None:
            self.__error.append("None or both regular expression `multiLineStart` and `multiLineEnd` must be provided")

        if regExStart is not None and regExEnd is not None:
            self.__multiLineRegExStart.append(regExStart)
            self.__multiLineRegExEnd.append(regExEnd)

    def __setType(self, value):
        """Set current type for rule"""
        if isinstance(value, TokenType):
            self.__type = value
        else:
            self.__error.append("Given type must be a valid <TokenType>")

    def regEx(self, single=False):
        """Return regular expression"""
        if single:
            return self.__regExSingle
        return self.__regEx

    def regExLookAhead(self):
        """Return regular expression lookahead (as str) if any, otherwise return None"""
        if self.__regExLookAhead is None:
            return None
        return (self.__regExLookAhead, self.__regExLookAheadIsNeg)

    def regExLookBehind(self):
        """Return regular expression lookbehind (as str) if any, otherwise return None"""
        if self.__regExLookbehind is None:
            return None
        return (self.__regExLookbehind, self.__regExLookbehindIsNeg)

    def multiLineRegEx(self):
        """Return a list of tuple (multiLineStart, multiLineEnd) if defined, otherwise return None"""
        return [(self.__multiLineRegExStart[index], self.__multiLineRegExEnd[index]) for index in range(len(self.__multiLineRegExStart))]

    def type(self):
        """Return current type for rule"""
        return self.__type

    def isValid(self):
        """Return True is token rule is valid"""
        return (len(self.__error) == 0 and self.__regEx is not None)

    def errors(self):
        """Return errors list"""
        return self.__error

    def caseInsensitive(self):
        """Return true if rule is case case insensitive"""
        return self.__caseInsensitive

    def ignoreIndent(self):
        """Return if token ignore or not indent/dedent"""
        return self.__ignoreIndent


class Tokenizer(object):
    """A tokenizer will 'split' a text into tokens, according to given rules


    note: the tokenizer doesn't verify the validity of tokenized text (this is
          made in a second time by a parser)
    """
    RULES_ALL = None
    RULES_MULTILINE = 'multiline'

    ADD_RULE_LAST = 0
    ADD_RULE_TYPE_BEFORE_FIRST = 1
    ADD_RULE_TYPE_AFTER_FIRST = 2
    ADD_RULE_TYPE_BEFORE_LAST = 3
    ADD_RULE_TYPE_AFTER_LAST = 4

    POP_RULE_LAST = 0
    POP_RULE_FIRST = 1
    POP_RULE_ALL = 2

    __TOKEN_INDENT_RULE = TokenizerRule(TokenType.INDENT, '')
    __TOKEN_DEDENT_RULE = TokenizerRule(TokenType.DEDENT, '')
    __TOKEN_WRONGINDENT_RULE = TokenizerRule(TokenType.WRONG_INDENT, '')
    __TOKEN_WRONGDEDENT_RULE = TokenizerRule(TokenType.WRONG_DEDENT, '')

    def __init__(self, rules=None):
        # internal storage for rules (list of TokenizerRule)
        self.__rules = []

        self.__invalidRules = []

        # a global regEx with all rules
        self.__regEx = None

        # list of rules with multiline management
        # None if not initialised, otherwise a list
        self.__multilineRules = None

        # a flag to determinate if regular expression&cache need to be updated
        self.__needUpdate = True

        # a cache to store tokenized code
        self.__cache = {}
        self.__cacheOrdered = []
        self.__cacheLastCleared = time.time()

        self.__massUpdate = False

        # when True, for token including spaces, reduce consecutive spaces to 1
        # example: 'set    value'
        #       => 'set value'
        self.__simplifyTokenSpaces = False

        # indent value
        #   When
        #       -1: indent value is defined automatically on first found indent,
        #           and then is used
        #       0:  ignore indent
        #       N:  indent value is defined by given positive number
        self.__indent = 0

        if rules is not None:
            self.setRules(rules)

    def __repr__(self):
        NL = '\n'
        return f"<Tokenizer(Cache={len(self.__cache)}, Rules={len(self.__rules)}{NL}{NL.join([f'{rule}' for rule in self.__rules])}{NL}RegEx={self.regEx()})>"

    def __searchAddIndex(self, mode, type):
        """Search index for given `type` according to defined search `mode`"""
        foundLastPStart = -1
        foundLastPEnd = -1
        reset = True
        for index in range(len(self.__rules)):
            if self.__rules[index].type() == type:
                if reset:
                    if mode == Tokenizer.ADD_RULE_TYPE_BEFORE_FIRST:
                        return index
                    foundLastPStart = index
                    reset = False

                foundLastPEnd = index

            elif foundLastPEnd != -1 and mode == Tokenizer.ADD_RULE_TYPE_AFTER_FIRST:
                return index
            else:
                reset = True

        if mode == Tokenizer.ADD_RULE_TYPE_BEFORE_LAST:
            return foundLastPStart
        elif mode == Tokenizer.ADD_RULE_TYPE_AFTER_LAST:
            return foundLastPEnd

        return len(self.__rules)

    def __searchRemoveIndex(self, mode, type):
        """Search index for given `type` according to defined search `mode`"""
        if mode == Tokenizer.POP_RULE_LAST:
            rng = range(len(self.__rules), -1, -1)
        else:
            rng = range(len(self.__rules))

        for index in rng:
            if self.__rules[index].type() == type:
                return index

        return None

    def __setCache(self, hashValue, tokens=None):
        """Update cache content

        If no tokens is provided, consider to update existing hashValue
        If in self.__massUpdate, do not maintain oredered cache as it's useless '
        """
        if tokens is True:
            # update cache timestamp
            # ==> assume that hashvalue exists in cache!!
            self.__cache[hashValue][0] = time.time()
            if not self.__massUpdate:
                self.__cache[hashValue][1].resetIndex()
                index = self.__cacheOrdered.index(hashValue)
                self.__cacheOrdered.pop(self.__cacheOrdered.index(hashValue))
                self.__cacheOrdered.append(hashValue)
        elif tokens is False:
            # remove from cache
            # ==> assume that hashvalue exists in cache!!
            if not self.__massUpdate:
                index = self.__cacheOrdered.index(hashValue)
                self.__cacheOrdered.pop(self.__cacheOrdered.index(hashValue))
                self.__cache.pop(hashValue)
        else:
            # add to cache
            if not self.__massUpdate:
                self.__cache[hashValue] = [time.time(), tokens, len(self.__cacheOrdered)]
                self.__cache[hashValue][1].resetIndex()
                self.__cacheOrdered.append(hashValue)
            else:
                self.__cache[hashValue] = [time.time(), tokens, 0]

    def indent(self):
        """Return current indent value used to generate INDENT/DEDENT tokens"""
        return self.__indent

    def setIndent(self, value):
        """Set indent value used to generate INDENT/DEDENT tokens"""
        if not isinstance(value, int):
            raise Exception("Given `value` must be <int>")

        if value < 0 and self.__indent != -1:
            self.__indent = -1
            self.__needUpdate = True
        elif self.__indent != value:
            self.__indent = value
            self.__needUpdate = True

    def addRule(self, rules, mode=None):
        """Add tokenizer rule(s)

        Given `rule` must be a <TokenizerRule> or a list of <TokenizerRule>
        """
        if mode is None:
            mode = Tokenizer.ADD_RULE_LAST

        if isinstance(rules, list):
            for rule in rules:
                self.addRule(rule, mode)
        elif isinstance(rules, TokenizerRule):
            if rules.type() is not None:
                if mode == Tokenizer.ADD_RULE_LAST:
                    self.__rules.append(rules)
                else:
                    self.__rules.insert(self.__searchAddIndex(mode, rules.type()), rules)

                self.__needUpdate = True

                if rules.multiLineRegEx():
                    # contains a multiline rule; need to rebuild list
                    self.__multilineRules = None
            else:
                self.__invalidRules.append((rules, "The rule type is set to NONE: the NONE type is reserved"))
        else:
            raise Exception("Given `rule` must be a <TokenizerRule>")

    def removeRule(self, rules, mode=None):
        """Remove tokenizer rule(s)

        Given `rule` must be a <TokenizerRule> or a list of <TokenizerRule>
        """
        if mode is None:
            mode = Tokenizer.POP_RULE_LAST

        if isinstance(rules, list):
            for rule in rules:
                self.removeRule(rule)
        elif isinstance(rules, TokenizerRule):
            if rules.type() is not None:
                if mode == Tokenizer.POP_RULE_ALL:
                    while index := self.__searchRemoveIndex(Tokenizer.POP_RULE_LAST, rules.type()):
                        self.__rules.pop(index)
                elif index := self.__searchRemoveIndex(mode, rules.type()):
                    self.__rules.pop(index)

                self.__needUpdate = True

                if rules.multiLineRegEx():
                    # contains a multiline rule; need to rebuild list
                    self.__multilineRules = None
            else:
                self.__invalidRules.append((rules, "The rule type is set to NONE: the NONE type is reserved"))
        else:
            raise Exception("Given `rule` must be a <TokenizerRule>")

    def rules(self, filter=None):
        """return list of given (and valid) rules

        If given `filter` equals Tokenizer.RULES_MULTILINE, return multilines rules only
        """
        if filter == Tokenizer.RULES_MULTILINE:
            if self.__multilineRules is None:
                # rebuild list of multilines
                self.__multilineRules = [rule for rule in self.__rules if rule.multiLineRegEx()]
            return self.__multilineRules
        return self.__rules

    def setRules(self, rules):
        """Define tokenizer rules"""
        if isinstance(rules, list):
            self.__rules = []
            self.__invalidRules = []

            self.addRule(rules)
        else:
            raise Exception("Given `rules` must be a list of <TokenizerRule>")

    def invalidRules(self):
        """Return list of invalid given rules"""
        return self.__invalidRules

    def regEx(self):
        """Return current built regular expression used for lexer"""
        def ruleInsensitive(rule):
            if rule.caseInsensitive():
                return f"(?i:{rule.regEx().pattern})"
            else:
                return rule.regEx().pattern

        if self.__needUpdate:
            self.clearCache(True)
            self.__needUpdate = False

            self.__regEx = re.compile("(" + '|'.join([ruleInsensitive(rule) for rule in self.__rules]) + ")", re.MULTILINE)

        return self.__regEx

    def clearCache(self, full=True):
        """Clear cache content

        If `full`, clear everything

        Otherwise clear oldest values
        - At least 5 items are kept in cache
        - At most, 500 items are kept in cache
        """
        currentTime = time.time()
        if full:
            self.__cache = {}
            self.__cacheOrdered = []
            self.__cacheLastCleared = currentTime
        elif self.__massUpdate is False and currentTime - self.__cacheLastCleared > 120:
            # keep at least, five items
            for key in self.__cacheOrdered[:-5]:
                if (currentTime - self.__cache[key][0]) > 120:
                    # older than than 2minutes, clear it
                    self.__setCache(key, False)

            if len(self.__cacheOrdered) > 500:
                keys = self.__cacheOrdered[:-500]
                for key in keys:
                    self.__setCache(key, False)
            self.__cacheLastCleared = currentTime

    def simplifyTokenSpaces(self):
        """Return if option 'simplify token spaces' is active or not"""
        return self.__simplifyTokenSpaces

    def setSimplifyTokenSpaces(self, value):
        """Set if option 'simplify token spaces' is active or not"""
        if not isinstance(value, bool):
            raise Exception("Given ` value` must be a <bool>")

        if value != self.__simplifyTokenSpaces:
            self.__simplifyTokenSpaces = value
            self.__needUpdate = True

    def massUpdate(self):
        """Return if tokenizer is in a mass udpate state or not"""
        return self.__massUpdate

    def setMassUpdate(self, value):
        """Set if tokenizer is in a mass udpate state or not

        It could be usefull to set the massupdate to True when tokenize() method is called many times in a very short time (tokenize all lines of a file for example)
        to reduce tokenization time
        In this situation, ordered cache + automatic cleanup is disabled during operation

        Whe nset to true, cache is automatically ordered and cleanup applied
        """
        if value != self.__massUpdate and isinstance(value, bool):
            self.__massUpdate = value
            if self.__massUpdate is False:
                # item[1][0] ==> 1-> item value; 0 -> value time
                self.__cacheOrdered = [item[0] for item in sorted(self.__cache.items(), key=lambda item: item[1][0])]
                self.clearCache(False)
                # reset idnex for all tokens item
                for item in self.__cache.values():
                    item[1].resetIndex()

    def tokenize(self, text):
        """Tokenize given text

        If ` stripSpaces` is True, token spaces are simplified

        Example:
            token 'set   value'
            is returned as 'set value'


        Return a EList object
        """
        if not isinstance(text, str):
            raise Exception("Given `text` must be a <str>")

        returned = []

        if self.__needUpdate:
            # rules has been modified, cleanup cache
            self.clearCache(True)

        if text == "" or len(self.__rules) == 0:
            # nothing to process (empty string and/or no rules?)
            return EList(returned)

        hashValue = hashlib.blake2b(text.encode(), digest_size=64).digest()

        if hashValue in self.__cache:
            # update
            self.__setCache(hashValue, True)
            # need to clear unused items in cache
            self.clearCache(False)
            return self.__cache[hashValue][1]

        matches = self.regEx().split(text)
        Token.resetTokenizer()

        indent = self.__indent
        previousIndent = 0
        previousToken = None
        # iterate all found tokens
        for tokenText in matches:
            if tokenText == '':
                # empty string!?
                # no need to check rules for a token
                continue

            position = 0
            for rule in self.__rules:
                # We've got a token, we need to determinate token type
                # ==> loop on rules, check one by one if token match rule
                #     if yes, then token type is known

                if rule.regEx(True).search(tokenText):
                    if regex := rule.regExLookBehind():
                        # need to check if not preceded by
                        if regex[0].search(text[0:position]):
                            if regex[1]: # isNegative
                                # there's a match and we have a negative look behind, search next rule
                                continue
                        else:
                            if not regex[1]: #.isNegative:
                                # there's no match and we have a positive behind, search next rule
                                continue

                    if regex := rule.regExLookAhead():
                        # need to check if not followed by
                        if regex[0].search(text[position + len(tokenText):]):
                            if regex[1]: # isNegative
                                # there's a match and we have a negative look behind, search next rule
                                continue
                        else:
                            if not regex[1]: #.isNegative:
                                # there's no match and we have a positive behind, search next rule
                                continue

                    token = Token(tokenText, rule,
                                    position,
                                    position + len(tokenText),
                                    len(tokenText),
                                    self.__simplifyTokenSpaces)

                    # ---- manage indent/dedent ----
                    if not rule.ignoreIndent() and indent != 0 and (re.search(r'^\s*$', tokenText) is None) and token.column() == 1:
                        # indent value is not zero => means that indent are managed
                        # token is not empty string (only spaces and/or newline)
                        if indent < 0 and token.indent() > 0:
                            # if indent is negative, define indent value with first indented token
                            indent = token.indent()

                        if indent > 0:
                            if previousIndent < token.indent():
                                # token indent is greater than previous indent value
                                # need to add INDENT token
                                nbIndent, nbWrongIndent = divmod(token.indent() - previousIndent, indent)

                                for numIndent in range(nbIndent):
                                    pStart = token.positionStart() + indent * numIndent
                                    pEnd = token.positionStart() + indent * (numIndent + 1)
                                    length = pEnd-pStart

                                    tokenIndent = Token(' ' * indent, Tokenizer.__TOKEN_INDENT_RULE, pStart, pEnd, length)
                                    tokenIndent.setPrevious(previousToken)
                                    returned.append(tokenIndent)
                                    previousToken = tokenIndent

                                if nbWrongIndent > 0:
                                    pStart = token.positionStart() + indent * (numIndent + 1)
                                    pEnd = pStart+nbWrongIndent

                                    tokenIndent = Token(' ' * nbWrongIndent, Tokenizer.__TOKEN_WRONGINDENT_RULE, pStart, pEnd, nbWrongIndent)
                                    tokenIndent.setPrevious(previousToken)
                                    returned.append(tokenIndent)
                                    previousToken = tokenIndent

                            elif previousIndent > token.indent():
                                # token indent is lower than previous indent value
                                # need to add DEDENT token
                                nbIndent, nbWrongIndent = divmod(previousIndent - token.indent(), indent)

                                for numIndent in range(nbIndent):
                                    pStart = token.positionStart() + indent * numIndent
                                    pEnd = token.positionStart() + indent * (numIndent + 1)
                                    length = pEnd-pStart

                                    tokenIndent = Token(' ' * indent, Tokenizer.__TOKEN_DEDENT_RULE, pStart, pEnd, length)
                                    tokenIndent.setPrevious(previousToken)
                                    returned.append(tokenIndent)
                                    previousToken = tokenIndent

                                if nbWrongIndent > 0:
                                    pStart = token.positionStart() + indent * (numIndent + 1)
                                    pEnd = pStart+nbWrongIndent

                                    tokenIndent = Token(' ' * nbWrongIndent, Tokenizer.__TOKEN_WRONGDEDENT_RULE, pStart, pEnd, nbWrongIndent)
                                    tokenIndent.setPrevious(previousToken)
                                    returned.append(tokenIndent)
                                    previousToken = tokenIndent

                            previousIndent = token.indent()

                    token.setPrevious(previousToken)
                    if previousToken is not None:
                        previousToken.setNext(token)
                    returned.append(token)
                    previousToken = token

                    # token type is found:
                    # => do not need to continue to check for an another token type
                    break
                position + len(tokenText)

        # add
        self.__setCache(hashValue, EList(returned))

        # need to clear unused items in cache
        self.clearCache(False)

        return self.__cache[hashValue][1]
