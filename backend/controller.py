import re
import curses
from enum import Enum
from typing import List, NamedTuple, Optional, Tuple, Union
import logging


logger = logging.getLogger()


def init_color():
    # curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_BLUE, -1)

    # HEADING1
    curses.init_pair(11, curses.COLOR_BLACK, 224)  # Light red-like
    # HEADING2
    curses.init_pair(12, curses.COLOR_BLACK, 225)  # Light magenta/pink
    # HEADING3
    curses.init_pair(13, curses.COLOR_BLACK, 229)  # Light yellow
    # HEADING4
    curses.init_pair(14, curses.COLOR_BLACK, 152)  # Light green
    # HEADING5
    curses.init_pair(15, curses.COLOR_BLACK, 153)  # Light blue
    # HEADING6
    curses.init_pair(16, curses.COLOR_BLACK, 195)
    # CODE
    curses.init_pair(17, curses.COLOR_CYAN, -1)
    # list
    curses.init_pair(18, 229, -1)

    def get_style_mapping():
        return {
            BlockType.HEADING1: curses.color_pair(11),
            BlockType.HEADING2: curses.color_pair(12),
            BlockType.HEADING3: curses.color_pair(13),
            BlockType.HEADING4: curses.color_pair(14),
            BlockType.HEADING5: curses.color_pair(15),
            BlockType.HEADING6: curses.color_pair(16),
            BlockType.CODE: curses.color_pair(17),
            InlineType.CODE: curses.color_pair(17),
            BlockType.BLOCKQUOTE: curses.color_pair(17),
            BlockType.UNORDEREDLIST: curses.color_pair(18),
            BlockType.PARAGRAPH: curses.A_NORMAL,
            InlineType.BOLD: curses.A_BOLD,
            InlineType.ITALIC: curses.A_ITALIC,
            InlineType.NORMAL: curses.A_NORMAL,
            InlineType.QUOTE: curses.color_pair(17) | curses.A_DIM,
        }

    return get_style_mapping()


class BlockType(Enum):
    HEADING1 = "HEADING1"
    HEADING2 = "HEADING2"
    HEADING3 = "HEADING3"
    HEADING4 = "HEADING4"
    HEADING5 = "HEADING5"
    HEADING6 = "HEADING6"
    BLOCKQUOTE = "BLOCKQUOTE"
    CODE = "CODE"
    UNORDEREDLIST = "UNORDEREDLIST"
    PARAGRAPH = "PARAGRAPH"


class InlineType(Enum):
    BOLD = "BOLD"
    ITALIC = "ITALIC"
    QUOTE = "QOUTE"
    CODE = "CODE"
    NORMAL = "NORMAL"


HEADER_MAP = {
    1: BlockType.HEADING1,
    2: BlockType.HEADING2,
    3: BlockType.HEADING3,
    4: BlockType.HEADING4,
    5: BlockType.HEADING5,
    6: BlockType.HEADING6,
}

# PAIR = init_color()


class TextStyles:
    def __init__(self, styles: List[Union[InlineType, BlockType]]) -> None:
        self.styles: List[Union[InlineType, BlockType]] = styles

    def __repr__(self) -> str:
        return f"styles=\n\t{self.styles}\n"


class CurseStyles:
    def __init__(self, styles) -> None:
        self.styles = styles


def split_nodes_delimiter(
    old_nodes: List[Tuple[str, TextStyles]], delimiter: str, text_type: TextStyles
) -> List[Tuple[str, TextStyles]]:
    new_nodes = []
    for node in old_nodes:
        if node[1] == BlockType.CODE:
            new_nodes.append(node)
        parts = node[0].split(delimiter)

        if (len(parts) - 1) % 2 != 0:
            raise ValueError(f"There was no closing delimiter for {delimiter=}")
        new_nodes.extend(
            [
                (sec, node[1].styles.extend(text_type.styles))
                if (idx + 1) % 2 == 0
                else (
                    f"{delimiter}{sec}{delimiter}",
                    node[1],
                )
                for idx, sec in enumerate(parts)
                if sec
            ]
        )
    return new_nodes


def block_to_block_type(block: str) -> BlockType:
    if block.startswith("#"):
        header = re.findall(r"^(#{1,6})\s+(.*)", block)
        h_tag = len(header[0][0])
        if h_tag:
            return HEADER_MAP[h_tag]
    if block.startswith("```"):
        return BlockType.CODE

    return BlockType.PARAGRAPH


def parse_block(text: str) -> List[Tuple[str, TextStyles]]:
    blocks = text.strip().split("\n\n")
    return [(block, TextStyles([block_to_block_type(block)])) for block in blocks]


def inline_parser(
    block: List[Tuple[str, TextStyles]],
) -> List[Tuple[str, TextStyles]]:
    bold_nodes = split_nodes_delimiter(
        block,
        "**",
        TextStyles([InlineType.BOLD]),
    )
    italic_nodes = split_nodes_delimiter(
        bold_nodes, "_", TextStyles([InlineType.ITALIC])
    )
    code_nodes = split_nodes_delimiter(italic_nodes, "`", TextStyles([InlineType.CODE]))

    return code_nodes


def mapper(
    blocks: List[Tuple[str, TextStyles]], pairs: dict
) -> List[Tuple[str, CurseStyles]]:
    stack = []
    for block in blocks:
        style = curses.A_NORMAL
        for st in block[1].styles:
            style |= pairs[st]
        stack.append((block[0], CurseStyles(styles=style)))
    return stack


def parse_md(text: str, pairs):
    blocks = parse_block(text)
    parsed = inline_parser(blocks)
    mapped = mapper(blocks, pairs=pairs)
    return mapped
