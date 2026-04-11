from __future__ import annotations

from raygame.encounters.defs import SexpNode


def parse_sexp(text: str) -> list[SexpNode]:
    tokens = _tokenize(text)
    index = 0
    forms: list[SexpNode] = []
    while index < len(tokens):
        form, index = _parse_form(tokens, index)
        forms.append(form)
    return forms


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in " \t\r\n":
            i += 1
            continue
        if ch == ";":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if ch in "()":
            tokens.append(ch)
            i += 1
            continue
        if ch == '"':
            i += 1
            chars: list[str] = []
            while i < len(text):
                cur = text[i]
                if cur == "\\":
                    i += 1
                    assert i < len(text), "Unterminated string escape."
                    escaped = text[i]
                    chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
                    i += 1
                    continue
                if cur == '"':
                    i += 1
                    break
                chars.append(cur)
                i += 1
            else:
                raise AssertionError("Unterminated string literal.")
            tokens.append(f'"{"".join(chars)}"')
            continue
        start = i
        while i < len(text) and text[i] not in '()"; \t\r\n':
            i += 1
        tokens.append(text[start:i])
    return tokens


def _parse_form(tokens: list[str], index: int) -> tuple[SexpNode, int]:
    token = tokens[index]
    if token == "(":
        items: list[SexpNode] = []
        index += 1
        while index < len(tokens) and tokens[index] != ")":
            item, index = _parse_form(tokens, index)
            items.append(item)
        assert index < len(tokens) and tokens[index] == ")", "Missing closing parenthesis."
        return items, index + 1
    assert token != ")", "Unexpected closing parenthesis."
    return _parse_atom(token), index + 1


def _parse_atom(token: str) -> SexpNode:
    if token.startswith('"'):
        return token[1:-1]
    if token == "true":
        return True
    if token == "false":
        return False
    if token.lstrip("-").isdigit():
        return int(token)
    return token
