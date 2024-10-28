# Don't evaluate type annotations at runtime
from __future__ import annotations
from typing import Literal, Optional
import platform

Point = int
DIP = float

class Region:
    """
    A singular selection region. This region has a order - ``b`` may be before
    or at ``a``.

    Also commonly used to represent an area of the text buffer, where ordering
    and ``xpos`` are generally ignored.
    """

    __slots__ = ['a', 'b', 'xpos']

    def __init__(self, a: Point, b: Optional[Point] = None, xpos: DIP = -1):
        """ """
        if b is None:
            b = a

        self.a: Point = a
        """ The first end of the region. """
        self.b: Point = b
        """
        The second end of the region. In a selection this is the location of the
        caret. May be less than ``a``.
        """
        self.xpos: DIP = xpos
        """
        In a selection this is the target horizontal position of the region.
        This affects behavior when pressing the up or down keys. Use ``-1`` if
        undefined.
        """

    def __iter__(self):
        """
        Iterate through all the points in the region.

        .. since:: 4023 3.8
        """
        return iter((self.a, self.b))

    def __str__(self) -> str:
        return "Region(" + str(self.a) + ", " + str(self.b) + ")"

    def __repr__(self) -> str:
        if self.xpos == -1:
            return f'Region({self.a}, {self.b})'
        return f'Region({self.a}, {self.b}, xpos={self.xpos})'

    def __len__(self) -> int:
        """ :returns: The size of the region. """
        return self.size()

    def __eq__(self, rhs: object) -> bool:
        """
        :returns: Whether the two regions are identical. Ignores ``xpos``.
        """
        return isinstance(rhs, Region) and self.a == rhs.a and self.b == rhs.b

    def __lt__(self, rhs: Region) -> bool:
        """
        :returns: Whether this region starts before the rhs. The end of the
                  region is used to resolve ties.
        """
        lhs_begin = self.begin()
        rhs_begin = rhs.begin()

        if lhs_begin == rhs_begin:
            return self.end() < rhs.end()
        else:
            return lhs_begin < rhs_begin

    def __contains__(self, v: Region | Point) -> bool:
        """
        :returns: Whether the provided `Region` or `Point` is entirely contained
                  within this region.

        .. since:: 4023 3.8
        """
        if isinstance(v, Region):
            return v.a in self and v.b in self
        elif isinstance(v, int):
            return v >= self.begin() and v <= self.end()
        else:
            fq_name = ""
            if v.__class__.__module__ not in {'builtins', '__builtin__'}:
                fq_name = f"{v.__class__.__module__}."
            fq_name += v.__class__.__qualname__
            raise TypeError(
                "in <Region> requires int or Region as left operand"
                f", not {fq_name}")

    def to_tuple(self) -> tuple[Point, Point]:
        """
        .. since:: 4075

        :returns: This region as a tuple ``(a, b)``.
        """
        return (self.a, self.b)

    def empty(self) -> bool:
        """ :returns: Whether the region is empty, ie. ``a == b``. """
        return self.a == self.b

    def begin(self) -> Point:
        """ :returns: The smaller of ``a`` and ``b``. """
        if self.a < self.b:
            return self.a
        else:
            return self.b

    def end(self) -> Point:
        """ :returns: The larger of ``a`` and ``b``. """
        if self.a < self.b:
            return self.b
        else:
            return self.a

    def size(self) -> int:
        """ Equivalent to `__len__`. """
        return abs(self.a - self.b)

    def contains(self, x: Point) -> bool:
        """ Equivalent to `__contains__`. """
        return x in self

    def cover(self, region: Region) -> Region:
        """ :returns: A `Region` spanning both regions. """
        a = min(self.begin(), region.begin())
        b = max(self.end(), region.end())

        if self.a < self.b:
            return Region(a, b)
        else:
            return Region(b, a)

    def intersection(self, region: Region) -> Region:
        """ :returns: A `Region` covered by both regions. """
        if self.end() <= region.begin():
            return Region(0)
        if self.begin() >= region.end():
            return Region(0)

        return Region(max(self.begin(), region.begin()), min(self.end(), region.end()))

    def intersects(self, region: Region) -> bool:
        """ :returns: Whether the provided region intersects this region. """
        lb = self.begin()
        le = self.end()
        rb = region.begin()
        re = region.end()

        return (
            (lb == rb and le == re) or
            (rb > lb and rb < le) or (re > lb and re < le) or
            (lb > rb and lb < re) or (le > rb and le < re))

class Selection:
    """
    Maintains a set of sorted non-overlapping Regions. A selection may be
    empty.

    This is primarily used to represent the textual selection.
    """

    def __init__(self, regions):
        self.regions = list(regions)

    def __iter__(self) -> Iterator[Region]:
        """
        Iterate through all the regions in the selection.

        .. since:: 4023 3.8
        """
        return iter(self.regions)

    def __len__(self) -> int:
        """ :returns: The number of regions in the selection. """
        return len(self.regions)

    def __getitem__(self, index: int) -> Region:
        """ :returns: The region at the given ``index``. """
        return self.regions(index)

    def __delitem__(self, index: int):
        """ Delete the region at the given ``index``. """
        del self.regions[index]

    def __eq__(self, rhs: object) -> bool:
        """ :returns: Whether the selections are identical. """
        return rhs is not None and isinstance(rhs, Selection) and list(self) == list(rhs)

    def __lt__(self, rhs: Optional[Selection]) -> bool:
        """ """
        return rhs is not None and list(self) < list(rhs)

    def __bool__(self) -> bool:
        """ The selection is ``True`` when not empty. """
        return len(self) > 0

    def __str__(self) -> str:
        return f"{self!r}[{', '.join(map(str, self))}]"

    def __repr__(self) -> str:
        return f'Selection'

    # def is_valid(self) -> bool:
    #     """ :returns: Whether this selection is for a valid view. """
    #     return True

    def clear(self):
        """ Remove all regions from the selection. """
        self.regions.clear()

    def add(self, x: Region):
        """
        Add a `Region` or `Point` to the selection. It will be merged with the
        existing regions if intersecting.
        """
        self.regions.append(x)

    def add_all(self, regions: Iterable[Region]):
        """ Add all the regions from the given iterable. """
        for r in regions:
            self.add(r)

    # def subtract(self, region: Region):
    #     """
    #     Subtract a region from the selection, such that the whole region is no
    #     longer contained within the selection.
    #     """
    #     sublime_api.view_selection_subtract_region(self.view_id, region.a, region.b)

    # def contains(self, region: Region) -> bool:
    #     """ :returns: Whether the provided region is contained within the selection. """
    #     return sublime_api.view_selection_contains(self.view_id, region.a, region.b)

class View:
    def __init__(self, text="", sel = None):
        self.text = text
        self.text_lines = text.split('\n')
        self._sel = Selection(sel) if sel else Selection([Region(0, 0)])

    def sel(self):
        return self._sel

    def rowcol(self, point):
        row = 0
        offset = 0
        for line in self.text_lines:
            line_len = len(line) + 1
            if offset + line_len <= point:
                row += 1
                offset += line_len
            else:
                col = point - offset
                return (row, col)
        return (row, offset)
        # lines = self.text[:point].split('\n')
        # row = len(lines) - 1
        # col = len(lines[-1]) if lines else 0
        # return (row, col)

    def substr(self, region):
        return self.text[region.begin():region.end()]

    def size(self):
        return len(self.text)

    def replace(self, edit, region, new_text):
        self.text = self.text[:region.begin()] + new_text + self.text[region.end():]
        self.text_lines = self.text.split('\n')

    def lines(self, region):
        start = 0
        res = []
        for line in self.text_lines:
            if start + len(line) >= region.begin() or start < region.end():
                res.append(Region(start, start + len(line)))
            start += len(line) + 1
        return res

platform = {'Darwin': 'osx', 'Linux': 'linux', 'Windows': 'windows'}[platform.system()]

def platform() -> Literal["osx", "linux", "windows"]:
    """
    :returns: The platform which the plugin is being run on.
    """
    return platform

def error_message(msg: str):
    """ Display an error dialog. """
    print('ERROR:', msg, file = sys.stderr, flush = True)
