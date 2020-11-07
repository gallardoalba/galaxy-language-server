""" This code is based on the Eclipse/Lemminx XML language server implementation:
https://github.com/eclipse/lemminx/tree/master/org.eclipse.lemminx/src/main/java/org/eclipse/lemminx/dom

Only the minimum subset of the XML dialect used by Galaxy tool wrappers is supported.
"""

from typing import Callable, List

from .constants import _LAN, WHITESPACE_CHARS


class MultiLineStream:
    """Represents a multi-line stream of characters."""

    def __init__(self, source: str, position: int = 0) -> None:
        self._source = source
        self._position = position
        self._len = len(source)

    def eos(self) -> bool:
        """Indicates that the stream is at the end position."""
        return self._len <= self._position

    def get_source(self) -> str:
        """Gets the source text."""
        return self._source

    def pos(self) -> int:
        """Gets the current stream position."""
        return self._position

    def advance(self, n: int) -> None:
        """Advances the stream given number of positions."""
        self._position = self._position + n

    def go_to_end(self) -> None:
        """Sets the stream position to the end of the stream."""
        self._position = self._len

    def peek_char(self, n: int = 0) -> int:
        """Gets the value of the next position in the stream without advancing it."""
        try:
            return ord(self._source[self._position + n])
        except IndexError:
            return -1

    def advance_if_char(self, ch: int) -> bool:
        """If the next character in the stream matches the given character, the stream advances one position."""
        if ch == self.peek_char():
            self._position = self._position + 1
            return True
        return False

    def advance_if_chars(self, ch: List[int]) -> bool:
        """If the next characters in the stream matches the given sequence of characters, the stream advances the length of the sequence."""
        if self._position + len(ch) > self._len:
            return False
        i = 0
        for i in range(len(ch)):
            if self._source[self._position + i] != chr(ch[i]):
                return False
        self.advance(i)
        return True

    def advance_until_char(self, ch: int) -> bool:
        """Advances the stream until it founds a character matching the given."""
        while self._position < self._len:
            if ord(self._source[self._position]) == ch:
                return True
            self.advance(1)
        return False

    def advance_until_chars(self, ch: List[int]) -> bool:
        """Advances the stream until it founds a list of character matching the given."""
        while self._position + len(ch) <= self._len:
            i = 0
            while i < len(ch) and self._source[self._position + i] == chr(ch[i]):
                i = i + 1
            if i == len(ch):
                return True
            self.advance(i or 1)
        self.go_to_end()
        return False

    def advance_while_char_in(self, list: List[int]) -> int:
        """Advances the stream if the characters are like any of the characters in the given list."""
        pos_now = self._position
        while self._position < self._len and ord(self._source[self._position]) in list:
            self._position = self._position + 1
        return self._position - pos_now

    def advance_until_char_or_new_tag(self, ch: int) -> bool:
        """Advances the stream until it finds the given character or the '<' (new tag character)."""
        while self._position < self._len:
            if self.peek_char() == ch or self.peek_char() == _LAN:
                return True
            self.advance(1)
        return False

    def advance_until_chars_or_new_tag(self, ch: List[int]) -> bool:
        """Advances the stream until it finds the given sequence of characters or the '<' (new tag character)."""
        while self._position + len(ch) <= self._len:
            i = 0
            if self.peek_char() == _LAN:
                return True
            while i < len(ch) and self._source[self._position + i] == chr(ch[i]):
                i = i + 1
            if i == len(ch):
                return True
            self.advance(i or 1)
        self.go_to_end()
        return False

    def advance_while_char(self, predicate: Callable[[str], bool]) -> int:
        """Advances the stream while the given condition is True."""
        pos_now = self._position
        while self._position < self._len and predicate(self._source[self._position]):
            self._position = self._position + 1
        return self._position - pos_now

    def skip_whitespace(self) -> bool:
        """Advances the stream while any kind of white space character is found."""
        n = self.advance_while_char_in(WHITESPACE_CHARS)
        return n > 0
