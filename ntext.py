# This file is licensed under the terms of the MIT license.
# See the LICENSE file in the root of this repository for complete details.
"""Data structure for representing string diagrams"""

from collections import namedtuple
from copy import deepcopy

__all__ = [
    'Ntext',
    'Composition',
    'NotComposable',
    'NotCompatible',
    'ncell',
    'zcell',
    'icell',
]

_Ntext = namedtuple('Ntext', [
    'cells',
    'dim',
    'source',
    'target',
    'smap',
    'tmap',
])


class Ntext(_Ntext):
    """Represents a string diagram.

    Attributes:
        cells (dict): indicates how cells connect to each other.
        dim (int): the dimension.
        source (Ntext): the source diagram.
        target (Ntext): the target diagram.
        smap (dict): indicates how the source maps to the cells.
        tmap (dict): indicates how the target maps to the cells.
    """

    __slots__ = ()

    def adapt(self, n, perm):
        """Applies a permutation to the cells of the n-source.

        This is useful to allow composition of ntexts when the target of one
        and source of the other coincide only up to permutation.

        Args:
            n: the n-source is the source (of the source) n times.
            perm: the permutation represented as a list of non repeated
                indices.
        """

        return adapt(self, n, perm)

    def compatible(self, target):
        """This diagram can be a source for the given target.

        The source and the target satisfy the globular conditions. This means
        that the source of the source is the same as source of the target and
        the target of the source is the same as the target of the target.

        Args:
            target: the target against which compatibility is checked.

        Returns:
            bool
        """

        return compatible(self, target)

    def composable(self, ntext, n):
        """This diagram can be n-composed with the given diagram."""

        return composable(self, ntext, n, None)


class Composition:
    """Composition of diagrams"""

    def __init__(self, ntext):
        self._ntext = icell(ntext.source)

    def ntext(self):
        return deepcopy(self._ntext)

    def compose(self, factor, n):
        ntext, ok = compose(self._ntext, factor, n, None)
        if not ok:
            raise NotComposable('Target of self is not source of factor.')

        self._ntext = ntext


class Error(Exception):
    """Base class for ntext exceptions."""


class NotComposable(Error):
    """Raised when trying to compose cells.

    Composing cells requires target of the first cell
    to be the same as the source of the second cell.
    """


class NotCompatible(Error):
    """Raised when trying to create a cell.

    Creating a cell with a source and target requires the source and target to
    satisfy the globular conditions. See `Ntext.compatible`.
    """


# source and target are maps.
NtextCell = namedtuple('NtextCell', ['source', 'target'])

_ref = namedtuple('_ref', ['index', 'is_new'])


def ncell(name, source, target):
    if not compatible(source, target):
        raise NotCompatible('Source and target are not compatible.')

    return _ncell(name, source, target)


def _ncell(name, source, target):
    def apply_offset(ct, o):
        for m, p in ct.items():
            ct[m] = [j+o[m] for j in p]

    # Assumes name is an unused name.
    source = deepcopy(source)
    target = deepcopy(target)
    dim = source.dim
    ntext = dict()
    smap = dict()
    tmap = dict()
    ncsource = dict()
    nctarget = dict()
    ntext[name] = [NtextCell(ncsource, nctarget)]

    if dim > 0:
        offset = dict()
        for n, cells in source.cells.items():
            ntext[n] = [deepcopy(c) for c in cells]
            smap[n] = list(range(len(cells)))
            ncsource[n] = smap[n][:]

        for n, cells in target.cells.items():
            if n not in ntext:
                ntext[n] = []

            off = len(ntext[n])
            offset[n] = off
            ntext[n].extend(deepcopy(c) for c in cells)
            tmap[n] = list(range(off, len(cells)+off))
            nctarget[n] = tmap[n][:]

        for n, cells in ntext.items():
            for i in range(offset[n], len(cells)):
                for cell in cells[i]:
                    apply_offset(cell.source, offset)
                    apply_offset(cell.target, offset)
    else:
        sn = source.cells
        ntext[sn] = 1
        smap[sn] = [0]
        ncsource[sn] = [0]
        tn = target.cells
        if tn in ntext:
            ntext[tn] += 1
            tmap[tn] = [1]
            nctarget[tn] = [1]
        else:
            ntext[tn] = 1
            tmap[tn] = [0]
            nctarget[tn] = [0]

    return Ntext(ntext, dim+1, source, target, smap, tmap)


def zcell(name):
    return Ntext(name, 0, None, None, None, None)


def icell(ntext):
    dim = ntext.dim + 1
    if ntext.dim == 0:
        cells = {ntext.cells: 1}
        smap = {ntext.cells: [0]}
    else:
        cells = deepcopy(ntext.cells)
        smap = dict()
        for n, p in cells.items():
            smap[n] = range(len(p))

    source = deepcopy(ntext)
    target = deepcopy(ntext)
    tmap = deepcopy(smap)
    return Ntext(cells, dim, source, target, smap, tmap)


def pre_stitch(dst, src, mapping):
    for name, maps in src.items():
        if isinstance(maps, int):
            length = maps
            cells = dst.get(name, 0)
            clength = cells
        else:
            length = len(maps)
            cells = dst.get(name) or []
            clength = len(cells)

        if not cells:
            dst[name] = cells

        for i in range(length):
            ni = (name, i)
            if ni not in mapping:
                mapping[ni] = _ref(clength, True)
                clength += 1

        if isinstance(maps, int):
            dst[name] = clength
        else:
            cells.extend(None for i in range(len(cells), clength))


def stitch(dst, src, mapping):
    pre_stitch(dst, src, mapping)

    # dst and src are ntext maps.
    for name, maps in src.items():
        if isinstance(maps, int):
            continue

        cells = dst[name]
        for i, cell in enumerate(maps):
            j, is_new = mapping[(name, i)]
            if is_new:
                assert cells[j] is None
                source = dict()
                target = dict()
                for t, ct  in [(source, cell.source), (target, cell.target)]:
                    for n, p in ct.items():
                        t[n] = [mapping[(n, k)].index for k in p]

                cells[j] = NtextCell(source, target)


def compatible(source, target):
    r = (source.source == target.source
         and source.target == target.target)

    if r:
        assert source.dim == target.dim

    return r


def compose(dst, src, dim, mapping):
    mapping = dict() if mapping is None else mapping
    c = composable(dst, src, dim, mapping)
    if not c:
        return None, c

    ntext = dst.cells
    stitch(ntext, src.cells, mapping)
    if dim > 0: # dim 0 is vertical composition.
        dim -= 1

        r = [None]*2
        for k, d, s, dm, sm in [
            (0, dst.source, src.source, dst.smap, src.smap),
            (1, dst.target, src.target, dst.tmap, src.tmap),
        ]:
            cm = dict()
            r[k], c = compose(d, s, dim, cm)
            assert c
            for n, p in sm:
                if n not in dm:
                    dm[n] = []

                dm[n].extend(
                    j for j, is_new in (cm[(n, i)] for i in p)
                    if is_new
                )

        source, target = r
    else:
        source = dst.source
        target = deepcopy(src.target)
        smap = dst.smap
        tmap = dict()
        for n, p in src.tmap.items():
            tmap[n] = [mapping[(n, i)].index for i in p]

    return Ntext(ntext, dst.dim, source, target, smap, tmap), True


def composable(dst, src, dim, mapping):
    if dst.dim != src.dim:
        return False

    target, tmap = get_face(dst, dim, 1)
    source, smap = get_face(src, dim, -1)
    if mapping is not None:
        for name, pos in smap.items():
            t = tmap[name]
            for i, k in enumerate(pos):
                mapping[(name, k)] = _ref(t[i], False)

    return source == target


def permute(ntext, mapping, perm):
    # perm changes ntext and mapping in place by applying itself
    # to one and its inverse to the other.
    for name, q in perm.items():
        cells = ntext[name]
        ntext[name] = [cells[i] for i in q]
        m = mapping[name]
        mapping[name] = [m[i] for i in q]


def adapt(cell, dim, perm):
    # Permute the dim-source. dim 0 is vertical composition.
    if dim > 0:
        dim -= 1
        adapt(cell.source, dim, perm)
        adapt(cell.target, dim, perm)
    else:
        permute(cell.source, cell.smap, perm)


def get_face(cell, dim, side):
    if dim > 0:
        dim -= 1
        sc, scmap = get_face(cell.source, dim, side)
        smap = dict()
        for n, p in cell.smap.items():
            smap[n] = [p[i] for i in scmap[n]]

        return sc, smap

    if side < 0:
        return cell.source, cell.smap

    return cell.target, cell.tmap
