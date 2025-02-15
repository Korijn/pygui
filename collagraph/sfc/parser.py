from __future__ import annotations

from html.parser import HTMLParser
from weakref import ref


class Node:
    """Node that represents an element from a .cgx file."""

    def __init__(
        self,
        tag: str,
        attrs: dict[str, str] | None = None,
        location: tuple[int, int] | None = None,
    ):
        super().__init__()
        self.tag = tag
        self.attrs = attrs or {}
        self.location = location
        self.end: tuple[int, int] | None = None
        self.data: str | None = None
        self.children: list[Node] = []
        self.parent: ref | None = None

    def child_with_tag(self, tag):
        for child in self.children:
            if child.tag == tag:
                return child


class CGXParser(HTMLParser):
    """Parser for .cgx files.

    Creates a tree of Nodes with all encountered attributes and data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        # The tag parameter is lower-cased by the HTMLParser.
        # In order to figure out whether the tag indicates
        # an imported class, we need the original casing for
        # the tag.
        # Using the original start tag, we can figure out where
        # the tag is located using a lower-cased version. And then
        # use the index to extract the original casing for the tag.
        complete_tag = self.get_starttag_text()
        index = complete_tag.lower().index(tag)
        original_tag = complete_tag[index : index + len(tag)]
        node = Node(original_tag, attrs=dict(attrs), location=self.getpos())

        # Cast attributes that have no value to boolean (True)
        # so that they function like flags
        for key, value in node.attrs.items():
            # TODO: check if the value should actually be an integer
            if value is None:
                node.attrs[key] = True

        # Add item as child to the last on the stack
        parent = self.stack[-1]
        parent.children.append(node)
        node.parent = ref(parent)
        # Make the new node the last on the stack
        self.stack.append(node)

    def handle_endtag(self, tag: str):
        # pop it till popping the same tag in order to
        # work around unclosed tags?
        # Pop the stack until  (but not the root!)
        while len(self.stack) > 1:
            node = self.stack.pop()
            node.end = self.getpos()
            if node.tag.lower() == tag:
                break

    def handle_data(self, data: str):
        if data.strip():
            self.stack[-1].data = data.strip()
