"""Mask obvious variable tokens before clustering, to cut noise."""
from __future__ import annotations
import re

# order matters: most specific first
_RULES = [
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<UUID>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b"), "<IP>"),
    (re.compile(r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b"), "<MAC>"),
    (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"), "<TS>"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "<EMAIL>"),
    (re.compile(r"/[\w./-]+"), "<PATH>"),
    (re.compile(r"\b\d+\.\d+\b"), "<NUM>"),   # floats (e.g. 3.14 ms) before plain ints
    (re.compile(r"\b\d+\b"), "<NUM>"),
]


def mask_variables(line: str) -> str:
    for rx, repl in _RULES:
        line = rx.sub(repl, line)
    return line
