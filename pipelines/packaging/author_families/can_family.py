
# can_family.py
# Pack10K Author Contract v1
#
# Class: beverage_can_330
# Units: mm, Z-up.
# Dependencies: Python standard library only.
#
# Design decisions:
# - H includes lid, double seam and pull tab.
# - D includes the widest external surface.
# - Body wall thickness: 0.12 mm.
# - Bottom dome height: 5.0 mm.
# - Lid and double seam form one continuous closed mesh.
# - Pull tab is a separate closed mesh with two through-holes.
# - Pull tab joint parent is "lid".
# - Rivet offset: +12 mm along X.
# - Joint axis Z follows the requested contract.
# - The nominal 330 mL capacity is a class designation,
#   not a calibrated liquid fill volume.
# - Independent compile gates remain to be executed.

import math


FAMILY = "can"

CLASSES = [
    "beverage_can_330",
]

DEFAULTS = {
    "beverage_can_330": {
        "H": 115.0,
        "D": 66.0,
    },
}

PARAM_ORDER = [
    "H",
    "D",
]


_SEGMENTS = 96
_WALL = 0.12
_DOME = 5.0
_MAX_TRIS = 40000


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _linspace(a, b, intervals):
    return [
        a + (b - a) * i / intervals
        for i in range(intervals + 1)
    ]


def _append(profile, samples):
    for z, r in samples:
        p = (float(z), float(r))
        if profile:
            q = profile[-1]
            if abs(p[0] - q[0]) < 1e-9 and \
               abs(p[1] - q[1]) < 1e-9:
                continue
        profile.append(p)


def _revolve(profile):
    """
    Revolve a profile from axis to axis.

    The boundary must follow:
        underside -> exterior -> top -> interior.

    Axis endpoints use single vertices.
    All regular rings share cyclic indices.
    """
    n = _SEGMENTS

    if profile[0][1] != 0.0 or profile[-1][1] != 0.0:
        raise ValueError("Profile must terminate on axis")

    verts = []
    tris = []
    rings = []

    cs = [
        (
            math.cos(2.0 * math.pi * i / n),
            math.sin(2.0 * math.pi * i / n),
        )
        for i in range(n)
    ]

    for k, (z, r) in enumerate(profile):

        if not math.isfinite(z) or not math.isfinite(r):
            raise ValueError("Non-finite profile")

        if r < 0.0:
            raise ValueError("Negative radius")

        if r == 0.0:

            if k not in (0, len(profile) - 1):
                raise ValueError("Unexpected interior pole")

            rings.append([len(verts)])
            verts.append([0.0, 0.0, z])

        else:

            ring = []

            for c, s in cs:
                ring.append(len(verts))
                verts.append([r * c, r * s, z])

            rings.append(ring)

    for a, b in zip(rings[:-1], rings[1:]):

        for i in range(n):

            j = (i + 1) % n

            if len(a) == 1:

                tris.append([
                    a[0], b[j], b[i],
                ])

            elif len(b) == 1:

                tris.append([
                    a[i], a[j], b[0],
                ])

            else:

                tris.append([
                    a[i], a[j], b[j],
                ])

                tris.append([
                    a[i], b[j], b[i],
                ])

    return verts, tris


def _part(name, verts, tris, joint=None):

    return {
        "name": name,
        "verts_mm": verts,
        "tris": tris,
        "material_id": "metal_alu",
        "joint": joint,
    }


def _bottom_profile(R):
    """
    Exterior bottom profile, axis to cylindrical wall.

    The center is raised 5 mm above the standing ring.
    The standing ring is grounded at z=0.
    """
    foot_r = 0.79 * R
    dome_r = foot_r - 2.0
    heel_start_r = foot_r + 1.0

    profile = [
        (_DOME, 0.0),
    ]

    # Smooth inward dome.
    for r in _linspace(0.0, dome_r, 12)[1:]:

        u = r / dome_r

        z = 0.45 + (_DOME - 0.45) * (
            1.0 - _smoothstep(u)
        )

        profile.append((z, r))

    # Transition from dome to standing ring.
    _append(
        profile,
        [
            (0.25, dome_r + 0.6),
            (0.06, dome_r + 1.2),
            (0.0, foot_r),
            (0.0, heel_start_r),
        ],
    )

    # Drawn heel: smooth rise into full can diameter.
    for t in _linspace(0.0, 1.0, 10)[1:]:

        r = heel_start_r + (
            R - heel_start_r
        ) * math.sin(0.5 * math.pi * t)

        z = 8.0 * (
            1.0 - math.cos(0.5 * math.pi * t)
        )

        profile.append((z, r))

    return profile


def _offset_meridian(profile, thickness):
    """
    Offset a sampled meridional boundary toward material
    interior using averaged segment normals.

    Coordinates are (z, r).
    For traversal from bottom axis toward upper outer wall,
    the inward normal is (+dr, -dz).

    Miter lengths are bounded to avoid numerical spikes.
    """
    normals = []

    for a, b in zip(profile[:-1], profile[1:]):

        dz = b[0] - a[0]
        dr = b[1] - a[1]

        length = math.hypot(dz, dr)

        if length <= 1e-10:
            raise ValueError("Repeated profile point")

        normals.append((
            dr / length,
            -dz / length,
        ))

    result = []

    for i, (z, r) in enumerate(profile):

        if i == 0:

            nz, nr = normals[0]
            distance = thickness

        elif i == len(profile) - 1:

            nz, nr = normals[-1]
            distance = thickness

        else:

            n1 = normals[i - 1]
            n2 = normals[i]

            nz = n1[0] + n2[0]
            nr = n1[1] + n2[1]

            length = math.hypot(nz, nr)

            if length <= 1e-10:
                raise ValueError("Undefined offset normal")

            nz /= length
            nr /= length

            dot = nz * n1[0] + nr * n1[1]

            distance = thickness / max(0.5, dot)

        rz = z + distance * nz
        rr = r + distance * nr

        if i == 0 and r == 0.0:
            rr = 0.0

        if rr < 0.0:
            raise ValueError("Invalid shell offset")

        result.append((rz, rr))

    return result


def _build_body(H, D):

    R = D / 2.0

    neck_r = R - 3.1

    body_top = H - 1.0
    neck_end = H - 3.0
    neck_start = H - 12.0

    outer = _bottom_profile(R)

    # Main cylindrical wall.
    _append(
        outer,
        [
            (z, R)
            for z in _linspace(
                8.0,
                neck_start,
                8,
            )
        ],
    )

    # Smooth necked-in upper shoulder.
    _append(
        outer,
        [
            (
                z,
                R + (neck_r - R) * _smoothstep(
                    (z - neck_start) /
                    (neck_end - neck_start)
                ),
            )
            for z in _linspace(
                neck_start,
                neck_end,
                12,
            )
        ],
    )

    # Short vertical flange beneath double seam.
    _append(
        outer,
        [
            (body_top, neck_r),
        ],
    )

    inner = _offset_meridian(outer, _WALL)

    profile = list(outer)

    # Mouth annulus + reversed inner shell.
    _append(profile, reversed(inner))

    verts, tris = _revolve(profile)

    return _part("body", verts, tris)


def _build_lid(H, D):
    """
    Closed lid with:
      - recessed central panel;
      - shallow annular countersink;
      - raised external double-seam representation;
      - integral central-offset rivet added separately.

    Double-seam geometry represents its external envelope.
    The individual folded metal layers are not simulated.
    """
    R = D / 2.0

    seam_r = R - 2.0
    neck_r = R - 3.1
    panel_r = R - 6.0

    panel_z = H - 2.65
    panel_t = 0.22

    # Underside, axis to outer edge.
    profile = [
        (panel_z - panel_t, 0.0),
    ]

    for r in _linspace(0.0, panel_r, 8)[1:]:

        u = r / panel_r

        z = panel_z - panel_t + 0.35 * u ** 4

        profile.append((z, r))

    # Lower countersink and seam outer envelope.
    _append(
        profile,
        [
            (H - 2.10, panel_r + 0.9),
            (H - 1.70, panel_r + 1.7),
            (H - 1.45, neck_r - 0.25),
            (H - 1.65, neck_r + 0.20),
            (H - 1.50, seam_r - 0.30),
            (H - 1.10, seam_r),
            (H - 0.55, seam_r),
            (H - 0.18, seam_r - 0.18),
            (H, seam_r - 0.55),
        ],
    )

    # Upper seam surface, traversed inward.
    _append(
        profile,
        [
            (H, neck_r + 0.20),
            (H - 0.15, neck_r - 0.15),
            (H - 0.55, neck_r - 0.35),
            (H - 1.10, panel_r + 1.7),
            (H - 1.80, panel_r + 0.9),
            (panel_z + 0.35, panel_r),
        ],
    )

    # Upper central panel: slightly recessed.
    for r in _linspace(panel_r, 0.0, 8)[1:]:

        u = r / panel_r

        z = panel_z + 0.35 * u ** 4

        profile.append((z, r))

    verts, tris = _revolve(profile)

    return _part("lid", verts, tris)


def _ellipse(cx, cy, rx, ry, t):
    return (
        cx + rx * math.cos(t),
        cy + ry * math.sin(t),
    )


def _build_tab(H, D):
    """
    Construct a two-hole pull tab as two annular lobes
    connected by a solid central bridge.

    The mesh is generated as an extrusion of a connected
    2D cell complex, with internal faces omitted.

    Result:
        one connected closed solid;
        two through-holes;
        no coincident internal faces.
    """
    n = 48

    # Adjust lateral size for smaller can variants.
    s = min(1.0, D / 66.0)

    # Two lobes are joined along a common straight chord.
    #
    # Ring 0: lifting finger hole.
    # Ring 1: rivet hole.
    #
    # Each lobe is constructed with one outer chord
    # replacing a short arc. Both lobes reuse that chord.

    z_lo = H - 2.36
    z_hi = H - 1.48

    bridge_half = 2.8 * s

    chord_bottom = (4.0, -bridge_half)
    chord_top = (4.0, bridge_half)

    outer_left = [chord_bottom]

    # Left lobe: counterclockwise outer contour.
    # Traverse around the left side from upper chord
    # to lower chord after the shared chord.
    outer_left.append(chord_top)

    for i in range(1, n):

        t = 0.40 + (2.0 * math.pi - 0.80) * i / n

        outer_left.append(
            _ellipse(
                -3.0,
                0.0,
                8.2 * s,
                6.3 * s,
                t,
            )
        )

    outer_right = [
        chord_top,
        chord_bottom,
    ]

    # Right lobe: counterclockwise outer contour.
    for i in range(1, n):

        t = (
            math.pi + 0.50
            + (2.0 * math.pi - 1.0) * i / n
        )

        outer_right.append(
            _ellipse(
                11.0,
                0.0,
                6.8 * s,
                5.7 * s,
                t,
            )
        )

    verts2 = []
    index = {}
    faces2 = []

    def vertex(p):

        key = (
            round(p[0], 10),
            round(p[1], 10),
        )

        if key not in index:
            index[key] = len(verts2)
            verts2.append([p[0], p[1]])

        return index[key]

    def add_lobe(outer, cx, cy, rx, ry):
        """
        Construct an annulus between the outer contour
        and an interior ellipse sampled on matching rays.
        """
        outer_ids = []
        inner_ids = []

        for x, y in outer:

            dx = x - cx
            dy = y - cy

            denom = math.sqrt(
                (dx / rx) ** 2
                + (dy / ry) ** 2
            )

            if denom <= 1.0:
                raise ValueError("Pull-tab hole exceeds outline")

            inner = (
                cx + dx / denom,
                cy + dy / denom,
            )

            outer_ids.append(vertex((x, y)))
            inner_ids.append(vertex(inner))

        m = len(outer_ids)

        for i in range(m):

            j = (i + 1) % m

            faces2.append([
                outer_ids[i],
                outer_ids[j],
                inner_ids[j],
            ])

            faces2.append([
                outer_ids[i],
                inner_ids[j],
                inner_ids[i],
            ])

    add_lobe(
        outer_left,
        -3.0,
        0.0,
        5.0 * s,
        3.6 * s,
    )

    add_lobe(
        outer_right,
        12.0,
        0.0,
        2.1 * s,
        2.1 * s,
    )

    # Extrude the complete planar mesh.
    # Only boundary edges receive vertical walls.
    # The shared chord receives no internal wall.
    verts = [
        [x, y, z_lo]
        for x, y in verts2
    ] + [
        [x, y, z_hi]
        for x, y in verts2
    ]

    count = len(verts2)
    tris = []
    edges = {}

    for face in faces2:

        a, b, c = face

        tris.append([c, b, a])

        tris.append([
            a + count,
            b + count,
            c + count,
        ])

        for u, v in ((a, b), (b, c), (c, a)):

            key = (min(u, v), max(u, v))

            if key not in edges:
                edges[key] = [1, u, v]
            else:
                edges[key][0] += 1

    for edge_count, u, v in edges.values():

        if edge_count == 1:

            tris.append([
                u, v, v + count,
            ])

            tris.append([
                u, v + count, u + count,
            ])

        elif edge_count != 2:

            raise ValueError("Invalid planar tab topology")

    joint = {
        "parent": "lid",
        "axis": [0.0, 0.0, 1.0],
        "origin": [12.0, 0.0, H - 2.55],
        "limits_deg": [0.0, 165.0],
    }

    return _part("pull_tab", verts, tris, joint)


def _build_rivet(H, D):
    """
    Fixed solid rivet supporting pull-tab Z-axis motion.
    Separate metal component to preserve closed topology.
    """
    s = min(1.0, D / 66.0)

    profile = [
        (H - 2.64, 0.0),
        (H - 2.64, 1.65 * s),
        (H - 1.45, 1.65 * s),
        (H - 1.45, 2.45 * s),
        (H - 1.20, 2.55 * s),
        (H - 1.02, 2.35 * s),
        (H - 0.95, 1.80 * s),
        (H - 0.95, 0.0),
    ]

    verts, tris = _revolve(profile)

    for v in verts:
        v[0] += 12.0

    return _part("rivet", verts, tris)


def _validate_mesh(part):

    verts = part["verts_mm"]
    tris = part["tris"]

    if not verts or not tris:
        raise ValueError("Empty mesh")

    if not all(
        math.isfinite(x)
        for v in verts
        for x in v
    ):
        raise ValueError("Non-finite vertex")

    edges = {}
    directions = {}
    volume6 = 0.0

    for a, b, c in tris:

        if len({a, b, c}) != 3:
            raise ValueError("Repeated triangle index")

        if min(a, b, c) < 0 or max(a, b, c) >= len(verts):
            raise ValueError("Triangle index out of range")

        p, q, r = verts[a], verts[b], verts[c]

        u = [q[i] - p[i] for i in range(3)]
        v = [r[i] - p[i] for i in range(3)]

        cross = [
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        ]

        if sum(x * x for x in cross) <= 1e-18:
            raise ValueError(
                "Degenerate face: " + part["name"]
            )

        volume6 += sum(
            p[i] * cross[i]
            for i in range(3)
        )

        for i, j in ((a, b), (b, c), (c, a)):

            key = (min(i, j), max(i, j))

            edges[key] = edges.get(key, 0) + 1

            directions[key] = directions.get(
                key, 0
            ) + (1 if i < j else -1)

    if any(v != 2 for v in edges.values()):
        raise ValueError(
            "Non-manifold mesh: " + part["name"]
        )

    if any(v != 0 for v in directions.values()):
        raise ValueError(
            "Inconsistent winding: " + part["name"]
        )

    if volume6 <= 0.0:
        raise ValueError(
            "Non-positive signed volume: " + part["name"]
        )


def _validate_assembly(parts, H, D):

    all_verts = [
        v
        for part in parts
        for v in part["verts_mm"]
    ]

    lo = [
        min(v[i] for v in all_verts)
        for i in range(3)
    ]

    hi = [
        max(v[i] for v in all_verts)
        for i in range(3)
    ]

    if abs(lo[2]) > 1e-8:
        raise ValueError("Can is not grounded")

    for i, expected in enumerate((D, D, H)):

        actual = hi[i] - lo[i]

        if abs(actual - expected) > expected * 0.01:
            raise ValueError("Assembly dimension mismatch")

    if sum(len(p["tris"]) for p in parts) > _MAX_TRIS:
        raise ValueError("Triangle budget exceeded")

    by_name = {
        p["name"]: p
        for p in parts
    }

    for part in parts:

        joint = part["joint"]

        if joint is None:
            continue

        parent = by_name[joint["parent"]]
        axis = joint["axis"]

        if sum(abs(x) > 1e-9 for x in axis) != 1:
            raise ValueError("Joint axis is not aligned")

        if abs(sum(x*x for x in axis) - 1.0) > 1e-9:
            raise ValueError("Joint axis is not unit length")

        for i, x in enumerate(joint["origin"]):

            a = min(v[i] for v in parent["verts_mm"])
            b = max(v[i] for v in parent["verts_mm"])

            if not a - 1e-8 <= x <= b + 1e-8:
                raise ValueError("Joint origin outside parent")


def build_parts(params: dict) -> list[dict]:

    config = dict(DEFAULTS["beverage_can_330"])
    config.update(params)

    H = float(config["H"])
    D = float(config["D"])

    if not math.isfinite(H) or not math.isfinite(D):
        raise ValueError("Non-finite parameter")

    if not 90.0 <= H <= 160.0:
        raise ValueError("Unsupported can height")

    if not 58.0 <= D <= 80.0:
        raise ValueError("Unsupported can diameter")

    parts = [
        _build_body(H, D),
        _build_lid(H, D),
        _build_tab(H, D),
        _build_rivet(H, D),
    ]

    for part in parts:
        _validate_mesh(part)

    _validate_assembly(parts, H, D)

    return parts
