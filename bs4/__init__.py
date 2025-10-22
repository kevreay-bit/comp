"""Lightweight subset of BeautifulSoup for offline environments."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional
import re

__all__ = ["BeautifulSoup", "Tag"]


class Tag:
    def __init__(self, name: str, attrs: Optional[Dict[str, str]] = None, parent: Optional["Tag"] = None) -> None:
        self.name = name.lower()
        self.attrs: Dict[str, str] = {k.lower(): v for k, v in (attrs or {}).items()}
        self.children: List[Tag] = []
        self.parent = parent
        self._text_parts: List[str] = []

    def append_child(self, child: "Tag") -> None:
        self.children.append(child)
        child.parent = self

    def append_text(self, text: str) -> None:
        if text:
            self._text_parts.append(text)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.attrs.get(key.lower(), default)

    def has_attr(self, key: str) -> bool:
        return key.lower() in self.attrs

    def __getitem__(self, key: str) -> str:
        return self.attrs[key.lower()]

    def get_text(self, separator: str = "", strip: bool = False) -> str:
        parts: List[str] = []

        def _gather(node: "Tag") -> None:
            if node._text_parts:
                parts.append("".join(node._text_parts))
            for child in node.children:
                _gather(child)

        _gather(self)
        text = separator.join(parts)
        return text.strip() if strip else text

    def select(self, selector: str) -> List["Tag"]:
        results: List[Tag] = []
        for token in selector.split(","):
            token = token.strip()
            if not token:
                continue
            results.extend(self._select_single(token))
        return results

    def select_one(self, selector: str) -> Optional["Tag"]:
        matches = self.select(selector)
        return matches[0] if matches else None

    # Internal helpers -------------------------------------------------
    def _select_single(self, selector: str) -> List["Tag"]:
        tag_name, classes, attributes = _parse_selector(selector)
        results: List[Tag] = []
        for node in self._descendants():
            if tag_name and node.name != tag_name:
                continue
            if classes and not _has_all_classes(node, classes):
                continue
            if attributes and not _match_attributes(node, attributes):
                continue
            results.append(node)
        return results

    def _descendants(self) -> Iterable["Tag"]:
        for child in self.children:
            yield child
            yield from child._descendants()


class _SoupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Tag("[document]", {})
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        attr_dict = {k: (v or "") for k, v in attrs}
        node = Tag(tag, attr_dict)
        self.current.append_child(node)
        self.current = node

    def handle_startendtag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        node = self.current
        while node is not None and node.name != tag.lower():
            node = node.parent
        if node is None:
            return
        self.current = node.parent or self.root

    def handle_data(self, data: str) -> None:
        self.current.append_text(data)


class BeautifulSoup(Tag):
    def __init__(self, markup: str, parser: str = "html.parser") -> None:
        if parser != "html.parser":  # pragma: no cover - unsupported parser
            raise ValueError("Only html.parser is supported in the lightweight soup")
        parser_obj = _SoupParser()
        parser_obj.feed(markup)
        super().__init__(parser_obj.root.name, parser_obj.root.attrs)
        self.children = parser_obj.root.children


def _parse_selector(selector: str) -> tuple[Optional[str], List[str], List[tuple[str, Optional[str], bool]]]:
    tag_name: Optional[str] = None
    classes: List[str] = []
    attrs: List[tuple[str, Optional[str], bool]] = []
    remainder = selector
    match = re.match(r"^[a-zA-Z0-9_-]+", remainder)
    if match:
        tag_name = match.group(0).lower()
        remainder = remainder[match.end():]
    while remainder:
        if remainder.startswith('.'):
            remainder = remainder[1:]
            cls_match = re.match(r"[a-zA-Z0-9_-]+", remainder)
            if not cls_match:
                break
            classes.append(cls_match.group(0))
            remainder = remainder[cls_match.end():]
        elif remainder.startswith('['):
            end_idx = remainder.find(']')
            if end_idx == -1:
                break
            content = remainder[1:end_idx]
            remainder = remainder[end_idx + 1:]
            if '=' in content:
                attr, value = content.split('=', 1)
                value = value.strip().strip("\"'")
                attrs.append((attr.strip().lower(), value, True))
            else:
                attrs.append((content.strip().lower(), None, False))
        else:
            break
    return tag_name, classes, attrs


def _has_all_classes(tag: Tag, classes: List[str]) -> bool:
    class_attr = tag.get("class")
    if not class_attr:
        return False
    values = set(class_attr.split())
    return all(cls in values for cls in classes)


def _match_attributes(tag: Tag, attributes: List[tuple[str, Optional[str], bool]]) -> bool:
    for name, value, must_equal in attributes:
        if not tag.has_attr(name):
            return False
        if must_equal and tag.get(name) != value:
            return False
    return True
