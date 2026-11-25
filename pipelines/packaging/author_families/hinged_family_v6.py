
# hinged_family.py
# Pack10K Author Contract v1
# Revision: V6 — Material Semantic Correction
# Class: food_container_1l
# Units: mm, Z-up.
# Dependencies: Python standard library only.
#
# ============================================================
# V6 CHANGE RECORD
# ============================================================
#
# Material-only revision based on V5.
#
# 1. base:
#       plastic_pp -> plastic_pp_translucent
#
# 2. snap_latch_left / snap_latch_right:
#       plastic_pp -> plastic_hdpe
#
# 3. lid / hinge_band:
#       plastic_pp unchanged
#
# 4. G-F5 author-side validation:
#       exact per-component material mapping.
#       No generic material whitelist bypass.
#
# 5. All V5 geometry is frozen.
#       No vertex changes.
#       No triangle changes.
#       No part order changes.
#       No articulation changes.
#
# 6. External compiler must register:
#       plastic_pp_translucent
#       plastic_hdpe
#
# Optical properties are owned by the external material
# library and are not embedded in this author module.
#
# ============================================================
# INHERITED V5 CONTRACT DECISIONS
# ============================================================
#
# Nominal shell thickness: 0.9 mm
# Nominal plan-view corner radius: 5 mm
#
# Lid annular recess:
#       in-plane width = 3.0 mm
#       vertical depth = 0.6 mm
#       top exterior edge radius = 1.0 mm
#       lower skirt edge radius = 0.25 mm
#
# Snap latches:
#       vertical extent increased by 2.0 mm
#       edge bevel = 0.5 mm
#       outward protrusion capped at 0.95 mm
#
# Hinge band:
#       X span = 18 mm
#       Y thickness = 2 mm
#       original Z attachment interval retained
#
# Default assembly nominal dimensions:
#       W = 130 mm
#       D = 100 mm
#       H = 90 mm
#
# V5/V6 assembly depth including latch protrusion:
#       100.95 mm
#
# Hinge origin:
#       (0, 50, 88)
#
# Joint axis:
#       (-1, 0, 0)
#
# Joint limits:
#       0 to 180 degrees
#
# CLOSED pose retained.
#
# External G-F1..F7 / USDC / PhysX validation must be rerun.
# Author topology checks do not prove full-angle collision
# clearance or absence of all geometric self-intersections.

import math


FAMILY = "hinged_box"

CLASSES = [
    "food_container_1l",
]

DEFAULTS = {
    "food_container_1l": {
        "H": 90.0,
        "D": 100.0,
        "W": 130.0,
    },
}

PARAM_ORDER = [
    "H",
    "D",
    "W",
]


# ============================================================
# V6 MATERIAL SEMANTIC CONTRACT
# ============================================================

_PART_MATERIAL_IDS = {
    "base": "plastic_pp_translucent",
    "lid": "plastic_pp",
    "hinge_band": "plastic_pp",
    "snap_latch_left": "plastic_hdpe",
    "snap_latch_right": "plastic_hdpe",
}


# ============================================================
# FROZEN V5 GEOMETRY CONTRACT
# ============================================================

_WALL = 0.9
_CORNER_R = 5.0
_CORNER_SEGMENTS = 48
_LID_DEPTH = 2.0

_BASE_GROOVE_Z = 40.0
_BASE_GROOVE_WIDTH = 5.0
_BASE_GROOVE_DEPTH = 0.8
_BASE_GROOVE_RAMP = 2.0


# ------------------------------------------------------------
# Frozen V5 lid geometry
# ------------------------------------------------------------

_LID_GROOVE_WIDTH = 3.0
_LID_GROOVE_OUTER_INSET = 1.55
_LID_GROOVE_DEPTH = 0.6
_LID_GROOVE_RAMP = 0.9

_LID_TOP_ROUND = 1.0
_LID_SKIRT_ROUND = 0.25


# ------------------------------------------------------------
# Frozen V5 functional details
# ------------------------------------------------------------

_LATCH_WIDTH = 14.0
_LATCH_EXTRA_HEIGHT = 2.0
_LATCH_BEVEL = 0.5
_LATCH_MAX_PROTRUSION = 0.95

_HINGE_WIDTH = 18.0
_HINGE_THICKNESS = 2.0

_MAX_TRIS = 40000
_EPS = 1e-8


def _rounded_rect_ring(
    W,
    D,
    radius,
    z,
    cx=0.0,
    cy=0.0,
    arc_segments=_CORNER_SEGMENTS,
):
    """Generate a counterclockwise rounded rectangle."""

    if W <= 0.0 or D <= 0.0:
        raise ValueError("Invalid rectangle dimensions")

    if not 0.0 < radius < min(W, D) / 2.0:
        raise ValueError("Invalid corner radius")

    hx = W / 2.0
    hy = D / 2.0

    corners = [
        (hx - radius, hy - radius, 0.0),
        (-hx + radius, hy - radius, math.pi / 2.0),
        (-hx + radius, -hy + radius, math.pi),
        (hx - radius, -hy + radius, 3.0 * math.pi / 2.0),
    ]

    ring = []

    for x0, y0, start in corners:

        for i in range(arc_segments + 1):

            angle = (
                start
                + math.pi * i / (2.0 * arc_segments)
            )

            c = math.cos(angle)
            s = math.sin(angle)

            # Preserve exact nominal bbox extrema.
            if abs(c) < 1e-14:
                c = 0.0

            if abs(s) < 1e-14:
                s = 0.0

            if abs(abs(c) - 1.0) < 1e-14:
                c = math.copysign(1.0, c)

            if abs(abs(s) - 1.0) < 1e-14:
                s = math.copysign(1.0, s)

            ring.append([
                cx + x0 + radius * c,
                cy + y0 + radius * s,
                float(z),
            ])

    return ring


def _mesh_from_profile(
    profile,
    cx=0.0,
    cy=0.0,
    arc_segments=_CORNER_SEGMENTS,
):
    """
    Sweep rounded rectangular rings along a profile.

    Entry format:
        (z, width, depth, corner_radius)

    Terminal rings are capped independently.
    Hollow shell openings remain open.
    """

    if len(profile) < 2:
        raise ValueError("Insufficient profile rings")

    verts = []
    tris = []
    rings = []

    previous = None

    for z, W, D, radius in profile:

        values = (z, W, D, radius)

        if not all(math.isfinite(x) for x in values):
            raise ValueError("Non-finite profile")

        if previous is not None:

            if all(
                abs(a - b) < 1e-10
                for a, b in zip(values, previous)
            ):
                continue

        ring = _rounded_rect_ring(
            W,
            D,
            radius,
            z,
            cx=cx,
            cy=cy,
            arc_segments=arc_segments,
        )

        ids = list(
            range(len(verts), len(verts) + len(ring))
        )

        verts.extend(ring)
        rings.append(ids)

        previous = values

    if len(rings) < 2:
        raise ValueError("Insufficient distinct rings")

    n = len(rings[0])

    for a, b in zip(rings[:-1], rings[1:]):

        if len(a) != n or len(b) != n:
            raise ValueError("Ring resolution mismatch")

        for i in range(n):

            j = (i + 1) % n

            tris.append([
                a[i], a[j], b[j],
            ])

            tris.append([
                a[i], b[j], b[i],
            ])

    # Exterior terminal cap.
    first = rings[0]

    p0 = len(verts)

    verts.append([
        cx,
        cy,
        verts[first[0]][2],
    ])

    for i in range(n):

        j = (i + 1) % n

        tris.append([
            p0,
            first[j],
            first[i],
        ])

    # Interior terminal cap.
    last = rings[-1]

    p1 = len(verts)

    verts.append([
        cx,
        cy,
        verts[last[0]][2],
    ])

    for i in range(n):

        j = (i + 1) % n

        tris.append([
            last[i],
            last[j],
            p1,
        ])

    return verts, tris


# ============================================================
# V6 MATERIAL BINDING
# ============================================================


def _part(name, verts, tris, joint=None):
    """
    Build the original Author Contract part record.

    V6:
    Resolve material_id from an exact per-part mapping.

    Geometry and articulation fields are unchanged.
    Unknown part names fail closed.
    """

    if name not in _PART_MATERIAL_IDS:
        raise ValueError(
            "Unknown part material mapping: " + name
        )

    return {
        "name": name,
        "verts_mm": verts,
        "tris": tris,
        "material_id": _PART_MATERIAL_IDS[name],
        "joint": joint,
    }


# ============================================================
# FROZEN V5 BASE GEOMETRY
# ============================================================


def _base_dims_at_z(z, full_width_z, W, D):

    if full_width_z <= 0.0:
        raise ValueError("Invalid draft height")

    t = max(
        0.0,
        min(1.0, z / full_width_z),
    )

    shrink = 2.0 * (1.0 - t)

    return (
        W - shrink,
        D - shrink,
    )


def _offset_graph(
    points,
    thickness,
    before_slope=0.0,
    after_slope=0.0,
):
    """
    Miter-offset a piecewise-linear graph toward +v.

    Each offset segment remains parallel to its source
    segment at the specified normal distance.
    """

    slopes = [before_slope] + [
        (b[1] - a[1]) / (b[0] - a[0])
        for a, b in zip(points[:-1], points[1:])
    ] + [after_slope]

    result = []

    for i, (u, v) in enumerate(points):

        m0, m1 = slopes[i:i + 2]

        c0 = thickness * math.hypot(1.0, m0)
        c1 = thickness * math.hypot(1.0, m1)

        if abs(m0 - m1) < _EPS:

            du = (
                -thickness * m0
                / math.hypot(1.0, m0)
            )

            dv = (
                thickness
                / math.hypot(1.0, m0)
            )

        else:

            du = (c1 - c0) / (m0 - m1)
            dv = c0 + m0 * du

        result.append((
            u + du,
            v + dv,
        ))

    if any(
        b[0] <= a[0]
        for a, b in zip(result[:-1], result[1:])
    ):
        raise ValueError("Offset groove folds back")

    return result


def _base_groove_profiles(full_width_z, W, D):
    """
    Frozen horizontal groove.

    Center Z = 40 mm
    Width = 5 mm
    Depth = 0.8 mm

    Inner wall follows the offset outer profile.
    """

    lo = (
        _BASE_GROOVE_Z
        - _BASE_GROOVE_WIDTH / 2.0
    )

    hi = (
        _BASE_GROOVE_Z
        + _BASE_GROOVE_WIDTH / 2.0
    )

    slope = -1.0 / full_width_z

    points = [
        (
            lo,
            1.0 - lo / full_width_z,
        ),
        (
            lo + _BASE_GROOVE_RAMP,
            1.0
            - (lo + _BASE_GROOVE_RAMP) / full_width_z
            + _BASE_GROOVE_DEPTH,
        ),
        (
            hi - _BASE_GROOVE_RAMP,
            1.0
            - (hi - _BASE_GROOVE_RAMP) / full_width_z
            + _BASE_GROOVE_DEPTH,
        ),
        (
            hi,
            1.0 - hi / full_width_z,
        ),
    ]

    inner = _offset_graph(
        points,
        _WALL,
        slope,
        slope,
    )

    if inner[-1][0] >= full_width_z:
        raise ValueError("Base groove intersects upper rim")

    def rings(graph):

        return [
            (
                z,
                W - 2.0 * inset,
                D - 2.0 * inset,
                _CORNER_R - (
                    inset
                    - (1.0 - z / full_width_z)
                ),
            )
            for z, inset in graph
        ]

    return rings(points), rings(inner)


def _build_base(H, D, W):
    """
    Frozen V5 base geometry.

    V6 material assignment is resolved by _part().
    """

    base_h = H - _LID_DEPTH

    wall = _WALL
    radius = _CORNER_R

    heel = 1.0
    rim_round = 0.25

    full_width_z = base_h - rim_round

    profile = []

    # 1. Exterior floor and rounded heel.

    for i in range(9):

        angle = (
            -math.pi / 2.0
            + math.pi * i / 16.0
        )

        z = heel + heel * math.sin(angle)

        offset = heel * (
            1.0 - math.cos(angle)
        )

        w, d = _base_dims_at_z(
            z,
            full_width_z,
            W,
            D,
        )

        profile.append((
            z,
            w - 2.0 * offset,
            d - 2.0 * offset,
            radius - offset,
        ))

    # 2. Drafted exterior wall with frozen groove.

    outer_groove, inner_groove = (
        _base_groove_profiles(
            full_width_z,
            W,
            D,
        )
    )

    outer_wall = list(outer_groove)

    for z in (
        base_h * 0.25,
        base_h * 0.50,
        base_h * 0.75,
    ):

        if (
            outer_groove[0][0]
            <= z
            <= outer_groove[-1][0]
        ):
            continue

        w, d = _base_dims_at_z(
            z,
            full_width_z,
            W,
            D,
        )

        outer_wall.append((
            z,
            w,
            d,
            radius,
        ))

    profile.extend(
        sorted(outer_wall)
    )

    # 3. Exact nominal footprint.

    profile.append((
        full_width_z,
        W,
        D,
        radius,
    ))

    # 4. Rounded outer rim.

    for i in range(1, 5):

        angle = math.pi * i / 8.0

        z = (
            full_width_z
            + rim_round * math.sin(angle)
        )

        offset = rim_round * (
            1.0 - math.cos(angle)
        )

        profile.append((
            z,
            W - 2.0 * offset,
            D - 2.0 * offset,
            radius - offset,
        ))

    # 5. Upper rim annulus.

    inner_W = W - 2.0 * wall
    inner_D = D - 2.0 * wall
    inner_r = radius - wall

    profile.append((
        base_h,
        inner_W + 2.0 * rim_round,
        inner_D + 2.0 * rim_round,
        inner_r + rim_round,
    ))

    # 6. Rounded inner rim.

    for i in range(1, 5):

        angle = math.pi * i / 8.0

        z = (
            full_width_z
            + rim_round * math.cos(angle)
        )

        offset = rim_round * (
            1.0 - math.sin(angle)
        )

        profile.append((
            z,
            inner_W + 2.0 * offset,
            inner_D + 2.0 * offset,
            inner_r + offset,
        ))

    # 7. Descending interior wall.

    inner_floor = wall
    inner_fillet = 1.0

    inner_wall = list(inner_groove)

    for z in (
        base_h * 0.75,
        base_h * 0.50,
        base_h * 0.25,
        inner_floor + inner_fillet,
    ):

        if (
            inner_groove[0][0]
            <= z
            <= inner_groove[-1][0]
        ):
            continue

        w, d = _base_dims_at_z(
            z,
            full_width_z,
            W,
            D,
        )

        inner_wall.append((
            z,
            w - 2.0 * wall,
            d - 2.0 * wall,
            inner_r,
        ))

    profile.extend(
        sorted(inner_wall, reverse=True)
    )

    # 8. Interior floor fillet.

    for i in range(1, 9):

        angle = math.pi * i / 16.0

        z = (
            inner_floor
            + inner_fillet
            - inner_fillet * math.sin(angle)
        )

        offset = inner_fillet * (
            1.0 - math.cos(angle)
        )

        w, d = _base_dims_at_z(
            z,
            full_width_z,
            W,
            D,
        )

        profile.append((
            z,
            w - 2.0 * wall - 2.0 * offset,
            d - 2.0 * wall - 2.0 * offset,
            inner_r - offset,
        ))

    verts, tris = _mesh_from_profile(profile)

    return _part(
        "base",
        verts,
        tris,
    )


# ============================================================
# FROZEN V5 LID
# ============================================================


def _lid_groove_profiles(W, D):
    """
    Frozen V5 annular formed recess.

    Width: 3.0 mm
    Vertical depth: 0.6 mm

    The matching underside follows a normal-offset
    profile to preserve nominal shell thickness.

    No Boolean subtraction.
    """

    a = _LID_GROOVE_OUTER_INSET

    b = (
        a + _LID_GROOVE_WIDTH
    )

    r = _LID_GROOVE_RAMP

    points = [
        (a, 0.0),
        (
            a + r,
            _LID_GROOVE_DEPTH,
        ),
        (
            b - r,
            _LID_GROOVE_DEPTH,
        ),
        (b, 0.0),
    ]

    inner = _offset_graph(
        points,
        _WALL,
    )

    def rings(graph):

        return [
            (
                z,
                W - 2.0 * inset,
                D - 2.0 * inset,
                _CORNER_R - inset,
            )
            for inset, z in graph
        ]

    return rings(points), rings(inner)


def _build_lid(H, D, W):
    """
    Frozen V5 lid in CLOSED assembly pose.

    Frozen bbox:
        X = [-W/2, +W/2]
        Y = [-D/2, +D/2]
        Z = [H-2, H]

    Frozen geometry:
        formed annular recess
        R1.0 exterior upper edge
        original lower skirt geometry

    Material remains plastic_pp.
    """

    wall = _WALL
    radius = _CORNER_R

    depth = _LID_DEPTH

    top_round = _LID_TOP_ROUND
    edge_round = _LID_SKIRT_ROUND

    top_groove, underside_groove = (
        _lid_groove_profiles(W, D)
    )

    # Start at central top panel, then traverse
    # outward through the annular recess.

    profile = list(
        reversed(top_groove)
    )

    # 1. Exterior upper edge R1.0.

    for i in range(7):

        angle = (
            -math.pi / 2.0
            + math.pi * i / 12.0
        )

        z = (
            top_round
            + top_round * math.sin(angle)
        )

        offset = top_round * (
            1.0 - math.cos(angle)
        )

        profile.append((
            z,
            W - 2.0 * offset,
            D - 2.0 * offset,
            radius - offset,
        ))

    # 2. Preserve exact nominal bbox extrema.

    profile.append((
        depth - edge_round,
        W,
        D,
        radius,
    ))

    # 3. Lower skirt edge.

    for i in range(1, 5):

        angle = math.pi * i / 8.0

        z = (
            depth
            - edge_round
            + edge_round * math.sin(angle)
        )

        offset = edge_round * (
            1.0 - math.cos(angle)
        )

        profile.append((
            z,
            W - 2.0 * offset,
            D - 2.0 * offset,
            radius - offset,
        ))

    # 4. Skirt rim annulus.

    inner_W = W - 2.0 * wall
    inner_D = D - 2.0 * wall
    inner_r = radius - wall

    profile.append((
        depth,
        inner_W + 2.0 * edge_round,
        inner_D + 2.0 * edge_round,
        inner_r + edge_round,
    ))

    # 5. Inner skirt edge.

    for i in range(1, 5):

        angle = math.pi * i / 8.0

        z = (
            depth
            - edge_round
            + edge_round * math.cos(angle)
        )

        offset = edge_round * (
            1.0 - math.sin(angle)
        )

        profile.append((
            z,
            inner_W + 2.0 * offset,
            inner_D + 2.0 * offset,
            inner_r + offset,
        ))

    # 6. Underside corner transition.

    floor_fillet = 0.15

    profile.append((
        wall + floor_fillet,
        inner_W,
        inner_D,
        inner_r,
    ))

    for i in range(1, 5):

        angle = math.pi * i / 8.0

        z = (
            wall
            + floor_fillet
            - floor_fillet * math.sin(angle)
        )

        offset = floor_fillet * (
            1.0 - math.cos(angle)
        )

        profile.append((
            z,
            inner_W - 2.0 * offset,
            inner_D - 2.0 * offset,
            inner_r - offset,
        ))

    # 7. Matching underside groove.

    profile.extend(
        underside_groove
    )

    verts, tris = _mesh_from_profile(profile)

    # Reflect into closed world-space lid pose.
    # Reflection reverses orientation.

    for v in verts:

        v[2] = H - v[2]

    tris = [
        [a, c, b]
        for a, b, c in tris
    ]

    # Frozen articulation contract.

    joint = {
        "parent": "base",
        "axis": [
            -1.0,
            0.0,
            0.0,
        ],
        "origin": [
            0.0,
            D / 2.0,
            H - depth,
        ],
        "limits_deg": [
            0.0,
            180.0,
        ],
    }

    return _part(
        "lid",
        verts,
        tris,
        joint,
    )


# ============================================================
# FROZEN CLOSED SOLID GENERATORS
# ============================================================


def _rounded_solid(
    name,
    W,
    D,
    z_lo,
    z_hi,
    radius,
    cx=0.0,
    cy=0.0,
    bevel=0.2,
):
    """Generate a closed rounded rectangular solid."""

    height = z_hi - z_lo

    bevel = min(
        bevel,
        height * 0.25,
        radius * 0.5,
    )

    if height <= 0.0 or bevel <= 0.0:
        raise ValueError("Invalid solid dimensions")

    profile = []

    # Rounded lower edge.

    for i in range(5):

        angle = (
            -math.pi / 2.0
            + math.pi * i / 8.0
        )

        z = (
            z_lo
            + bevel
            + bevel * math.sin(angle)
        )

        offset = bevel * (
            1.0 - math.cos(angle)
        )

        profile.append((
            z,
            W - 2.0 * offset,
            D - 2.0 * offset,
            radius - offset,
        ))

    # Vertical wall.

    profile.append((
        z_hi - bevel,
        W,
        D,
        radius,
    ))

    # Rounded upper edge.

    for i in range(1, 5):

        angle = math.pi * i / 8.0

        z = (
            z_hi
            - bevel
            + bevel * math.sin(angle)
        )

        offset = bevel * (
            1.0 - math.cos(angle)
        )

        profile.append((
            z,
            W - 2.0 * offset,
            D - 2.0 * offset,
            radius - offset,
        ))

    verts, tris = _mesh_from_profile(
        profile,
        cx=cx,
        cy=cy,
        arc_segments=12,
    )

    return _part(
        name,
        verts,
        tris,
    )


# ============================================================
# FROZEN V5 HINGE BAND
# ============================================================


def _build_hinge_band(H, D, W):
    """
    Fixed rear hinge envelope.

    Frozen X span: 18 mm
    Frozen Y thickness: 2 mm

    Rear surface remains exactly at +D/2.
    The original hinge origin remains in its bbox.

    Material remains plastic_pp.

    This is a simplified fixed hinge envelope, not a
    deformable living-hinge simulation.
    """

    return _rounded_solid(
        name="hinge_band",
        W=_HINGE_WIDTH,
        D=_HINGE_THICKNESS,
        z_lo=H - 5.5,
        z_hi=H - 0.5,
        radius=0.65,
        cx=0.0,
        cy=(
            D / 2.0
            - _HINGE_THICKNESS / 2.0
        ),
        bevel=0.25,
    )


# ============================================================
# LEGACY EXTRUSION HELPER
# Retained for compatibility.
# ============================================================


def _extrude_x_polygon(
    name,
    polygon_yz,
    x_center,
    width,
):
    """Extrude a convex CCW YZ polygon along X."""

    if len(polygon_yz) < 3:
        raise ValueError("Invalid extrusion polygon")

    if width <= 0.0:
        raise ValueError("Invalid extrusion width")

    n = len(polygon_yz)

    area2 = 0.0

    for i in range(n):

        j = (i + 1) % n

        y0, z0 = polygon_yz[i]
        y1, z1 = polygon_yz[j]

        area2 += y0 * z1 - y1 * z0

    if area2 <= 0.0:
        raise ValueError("Invalid polygon winding")

    x0 = x_center - width / 2.0
    x1 = x_center + width / 2.0

    verts = [
        [x0, y, z]
        for y, z in polygon_yz
    ] + [
        [x1, y, z]
        for y, z in polygon_yz
    ]

    tris = []

    for i in range(1, n - 1):

        tris.append([
            0,
            i + 1,
            i,
        ])

        tris.append([
            n,
            n + i,
            n + i + 1,
        ])

    for i in range(n):

        j = (i + 1) % n

        tris.append([
            i,
            j,
            j + n,
        ])

        tris.append([
            i,
            j + n,
            i + n,
        ])

    return _part(
        name,
        verts,
        tris,
    )


# ============================================================
# FROZEN V5 FRONT SNAP LATCHES
# ============================================================


def _build_snap_latch(H, D, x_center, name):
    """
    Frozen V5 front latch geometry.

    Vertical extent:
        V4 + 2 mm

    Edge bevel:
        0.5 mm

    Outward projection bounded by both:
        fixed cap = 0.95 mm
        relative cap = 0.95% of nominal depth

    Default assembled depth:
        100.95 mm

    V6:
        Material changes to plastic_hdpe via _part().

    Actual snap-fit mechanics remain outside
    the scope of this mesh author.
    """

    front = -D / 2.0

    protrusion = min(
        _LATCH_MAX_PROTRUSION,
        D * 0.0095,
    )

    y_lo = (
        front - protrusion
    )

    y_hi = (
        front + 3.0
    )

    latch_depth = (
        y_hi - y_lo
    )

    latch_cy = (
        y_lo + y_hi
    ) / 2.0

    return _rounded_solid(
        name=name,
        W=_LATCH_WIDTH,
        D=latch_depth,
        z_lo=(
            H
            - 7.0
            - _LATCH_EXTRA_HEIGHT
        ),
        z_hi=H - 0.45,
        radius=1.0,
        cx=x_center,
        cy=latch_cy,
        bevel=_LATCH_BEVEL,
    )


# ============================================================
# AUTHOR VALIDATION
# Original geometry checks retained.
# ============================================================


def _validate_params(H, D, W):

    if not all(
        math.isfinite(x)
        for x in (H, D, W)
    ):
        raise ValueError("Non-finite dimensions")

    if not 45.0 <= H <= 150.0:
        raise ValueError("Unsupported container height")

    if not 75.0 <= D <= 180.0:
        raise ValueError("Unsupported container depth")

    if not 90.0 <= W <= 220.0:
        raise ValueError("Unsupported container width")

    if W < D * 0.75:
        raise ValueError("Unsupported footprint ratio")

    if _CORNER_R - _WALL <= 1.0:
        raise ValueError("Insufficient inner corner radius")

    if _LID_DEPTH <= _WALL:
        raise ValueError("Insufficient lid cavity depth")


def _validate_mesh(part):
    """
    Author-side topology checks.

    Checks:
        finite coordinates
        valid indices
        non-degenerate triangles
        two faces per undirected edge
        consistent winding
        positive signed volume
        connected vertex graph
    """

    name = part["name"]

    verts = part["verts_mm"]
    tris = part["tris"]

    if not verts or not tris:
        raise ValueError("Empty mesh: " + name)

    for v in verts:

        if len(v) != 3:
            raise ValueError(
                "Invalid vertex dimension: " + name
            )

        if not all(
            math.isfinite(x)
            for x in v
        ):
            raise ValueError(
                "Non-finite vertex: " + name
            )

    edges = {}
    directions = {}

    adjacency = [
        set()
        for _ in verts
    ]

    volume6 = 0.0

    for tri in tris:

        if len(tri) != 3:
            raise ValueError(
                "Non-triangle face: " + name
            )

        a, b, c = tri

        if len({a, b, c}) != 3:
            raise ValueError(
                "Repeated triangle index: " + name
            )

        if min(a, b, c) < 0:
            raise ValueError(
                "Negative triangle index: " + name
            )

        if max(a, b, c) >= len(verts):
            raise ValueError(
                "Triangle index out of range: " + name
            )

        p, q, r = (
            verts[a],
            verts[b],
            verts[c],
        )

        u = [
            q[i] - p[i]
            for i in range(3)
        ]

        v = [
            r[i] - p[i]
            for i in range(3)
        ]

        cross = [
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        ]

        if sum(
            x * x
            for x in cross
        ) <= 1e-18:

            raise ValueError(
                "Degenerate face: " + name
            )

        volume6 += sum(
            p[i] * cross[i]
            for i in range(3)
        )

        for i, j in (
            (a, b),
            (b, c),
            (c, a),
        ):

            key = (
                min(i, j),
                max(i, j),
            )

            edges[key] = (
                edges.get(key, 0) + 1
            )

            directions[key] = (
                directions.get(key, 0)
                + (1 if i < j else -1)
            )

            adjacency[i].add(j)
            adjacency[j].add(i)

    if any(
        x != 2
        for x in edges.values()
    ):
        raise ValueError(
            "Non-manifold mesh: " + name
        )

    if any(
        x != 0
        for x in directions.values()
    ):
        raise ValueError(
            "Inconsistent winding: " + name
        )

    if volume6 <= 0.0:
        raise ValueError(
            "Non-positive signed volume: " + name
        )

    visited = set()
    stack = [0]

    while stack:

        i = stack.pop()

        if i in visited:
            continue

        visited.add(i)

        stack.extend(
            adjacency[i] - visited
        )

    if len(visited) != len(verts):
        raise ValueError(
            "Disconnected mesh: " + name
        )


def _bbox(verts):

    lo = [
        min(v[i] for v in verts)
        for i in range(3)
    ]

    hi = [
        max(v[i] for v in verts)
        for i in range(3)
    ]

    return lo, hi


def _assert_point_in_bbox(
    point,
    part,
    role,
):
    """
    Validate point against actual mesh bbox.

    Original numerical epsilon retained.
    """

    lo, hi = _bbox(
        part["verts_mm"]
    )

    for i, coordinate in enumerate(point):

        if not (
            lo[i] - _EPS
            <= coordinate
            <= hi[i] + _EPS
        ):

            raise ValueError(
                "Joint origin outside "
                + role
                + " bbox: part="
                + part["name"]
                + ", axis="
                + str(i)
                + ", origin="
                + str(coordinate)
                + ", bbox=["
                + str(lo[i])
                + ", "
                + str(hi[i])
                + "]"
            )


def _validate_closed_pose(parts, H, D, W):
    """
    Validate frozen closed-pose base/lid bboxes
    and the original rear hinge contract.
    """

    by_name = {
        p["name"]: p
        for p in parts
    }

    base = by_name["base"]
    lid = by_name["lid"]
    hinge = by_name["hinge_band"]

    base_lo, base_hi = _bbox(
        base["verts_mm"]
    )

    lid_lo, lid_hi = _bbox(
        lid["verts_mm"]
    )

    expected_base_lo = [
        -W / 2.0,
        -D / 2.0,
        0.0,
    ]

    expected_base_hi = [
        W / 2.0,
        D / 2.0,
        H - _LID_DEPTH,
    ]

    expected_lid_lo = [
        -W / 2.0,
        -D / 2.0,
        H - _LID_DEPTH,
    ]

    expected_lid_hi = [
        W / 2.0,
        D / 2.0,
        H,
    ]

    for actual, expected, label in (
        (
            base_lo,
            expected_base_lo,
            "base bbox minimum",
        ),
        (
            base_hi,
            expected_base_hi,
            "base bbox maximum",
        ),
        (
            lid_lo,
            expected_lid_lo,
            "lid bbox minimum",
        ),
        (
            lid_hi,
            expected_lid_hi,
            "lid bbox maximum",
        ),
    ):

        if any(
            abs(a - b) > _EPS
            for a, b in zip(actual, expected)
        ):

            raise ValueError(
                "Closed-pose bbox mismatch: "
                + label
                + ", actual="
                + str(actual)
                + ", expected="
                + str(expected)
            )

    if abs(lid_lo[2] - base_hi[2]) > _EPS:
        raise ValueError(
            "Lid is not in closed assembly pose"
        )

    origin = lid["joint"]["origin"]

    expected_origin = [
        0.0,
        D / 2.0,
        H - _LID_DEPTH,
    ]

    if any(
        abs(a - b) > _EPS
        for a, b in zip(origin, expected_origin)
    ):
        raise ValueError(
            "Incorrect rear hinge origin"
        )

    # Original dual-bbox requirement.

    _assert_point_in_bbox(
        origin,
        base,
        "parent",
    )

    _assert_point_in_bbox(
        origin,
        lid,
        "moving component",
    )

    _assert_point_in_bbox(
        origin,
        hinge,
        "hinge band",
    )

    if abs(origin[1] - base_hi[1]) > _EPS:
        raise ValueError(
            "Hinge is not on base rear boundary"
        )

    if abs(origin[1] - lid_hi[1]) > _EPS:
        raise ValueError(
            "Hinge is not on lid rear boundary"
        )

    axis_x = lid["joint"]["axis"][0]

    front_relative_y = -D

    upward_velocity = (
        axis_x * front_relative_y
    )

    if upward_velocity <= 0.0:
        raise ValueError(
            "Positive joint angle does not lift lid"
        )


def _validate_assembly(parts, H, D, W):

    all_verts = [
        v
        for part in parts
        for v in part["verts_mm"]
    ]

    lo, hi = _bbox(all_verts)

    # G-F3: grounded.

    if abs(lo[2]) > _EPS:
        raise ValueError(
            "Assembly is not grounded"
        )

    # G-F4: original ±1% dimension tolerance.

    expected = (
        W,
        D,
        H,
    )

    for i, target in enumerate(expected):

        actual = hi[i] - lo[i]

        if abs(actual - target) > target * 0.01:
            raise ValueError(
                "Dimension mismatch on axis "
                + str(i)
            )

    total_tris = sum(
        len(p["tris"])
        for p in parts
    )

    if total_tris > _MAX_TRIS:
        raise ValueError(
            "Triangle budget exceeded: "
            + str(total_tris)
        )

    by_name = {
        p["name"]: p
        for p in parts
    }

    if len(by_name) != len(parts):
        raise ValueError(
            "Duplicate part name"
        )

    expected_names = {
        "base",
        "lid",
        "hinge_band",
        "snap_latch_left",
        "snap_latch_right",
    }

    if set(by_name) != expected_names:
        raise ValueError(
            "Unexpected family part set"
        )

    # V6: material mapping must cover exactly the
    # five original family components.

    if set(_PART_MATERIAL_IDS) != expected_names:
        raise ValueError(
            "Incomplete or unexpected material mapping"
        )

    movable_parts = []

    for part in parts:

        # ----------------------------------------------------
        # G-F5: V6 exact per-component material semantics.
        #
        # This replaces the V5 uniform plastic_pp assertion.
        # It is NOT a relaxation to arbitrary material IDs.
        # ----------------------------------------------------

        expected_material_id = (
            _PART_MATERIAL_IDS[part["name"]]
        )

        actual_material_id = part["material_id"]

        if actual_material_id != expected_material_id:

            raise ValueError(
                "Invalid material assignment: part="
                + part["name"]
                + ", expected="
                + expected_material_id
                + ", actual="
                + str(actual_material_id)
            )

        joint = part["joint"]

        if joint is None:
            continue

        movable_parts.append(
            part["name"]
        )

        # G-F6: joint parent.

        if joint["parent"] not in by_name:
            raise ValueError(
                "Unknown joint parent"
            )

        if joint["parent"] == part["name"]:
            raise ValueError(
                "Self-referencing joint"
            )

        axis = joint["axis"]

        if len(axis) != 3:
            raise ValueError(
                "Invalid joint axis dimension"
            )

        if not all(
            math.isfinite(x)
            for x in axis
        ):
            raise ValueError(
                "Non-finite joint axis"
            )

        if abs(
            sum(x * x for x in axis) - 1.0
        ) > _EPS:
            raise ValueError(
                "Joint axis is not unit length"
            )

        if sum(
            abs(x) > _EPS
            for x in axis
        ) != 1:
            raise ValueError(
                "Joint axis is not aligned"
            )

        origin = joint["origin"]

        if len(origin) != 3:
            raise ValueError(
                "Invalid joint origin dimension"
            )

        if not all(
            math.isfinite(x)
            for x in origin
        ):
            raise ValueError(
                "Non-finite joint origin"
            )

        parent = by_name[
            joint["parent"]
        ]

        _assert_point_in_bbox(
            origin,
            parent,
            "parent",
        )

        _assert_point_in_bbox(
            origin,
            part,
            "moving component",
        )

        limits = joint["limits_deg"]

        if len(limits) != 2:
            raise ValueError(
                "Invalid joint limits"
            )

        if not all(
            math.isfinite(x)
            for x in limits
        ):
            raise ValueError(
                "Non-finite joint limits"
            )

        if limits[0] > limits[1]:
            raise ValueError(
                "Reversed joint limits"
            )

    # G-F7: frozen family articulation semantics.

    if movable_parts != ["lid"]:
        raise ValueError(
            "Only lid may be articulated"
        )

    lid_joint = by_name["lid"]["joint"]

    if lid_joint["parent"] != "base":
        raise ValueError(
            "Lid must be attached to base"
        )

    if lid_joint["axis"] != [-1.0, 0.0, 0.0]:
        raise ValueError(
            "Incorrect lid revolute axis"
        )

    if lid_joint["limits_deg"] != [0.0, 180.0]:
        raise ValueError(
            "Incorrect lid revolute limits"
        )

    _validate_closed_pose(
        parts,
        H,
        D,
        W,
    )


# ============================================================
# PUBLIC AUTHOR ENTRY POINT
# ============================================================


def build_parts(params: dict) -> list[dict]:
    """
    Build V6 food_container_1l in CLOSED pose.

    Returns exactly five independent mesh components:

        base
        lid
        hinge_band
        snap_latch_left
        snap_latch_right

    Only lid carries an articulated joint.

    All geometry generators remain frozen from V5.

    V6 material assignments:
        base               plastic_pp_translucent
        lid                plastic_pp
        hinge_band         plastic_pp
        snap_latch_left    plastic_hdpe
        snap_latch_right   plastic_hdpe

    No external dependencies.
    No file I/O.
    No render configuration side effects.
    """

    config = dict(
        DEFAULTS["food_container_1l"]
    )

    config.update(params)

    H = float(config["H"])
    D = float(config["D"])
    W = float(config["W"])

    _validate_params(
        H,
        D,
        W,
    )

    latch_offset = W * 0.25

    parts = [
        _build_base(
            H,
            D,
            W,
        ),
        _build_lid(
            H,
            D,
            W,
        ),
        _build_hinge_band(
            H,
            D,
            W,
        ),
        _build_snap_latch(
            H,
            D,
            -latch_offset,
            "snap_latch_left",
        ),
        _build_snap_latch(
            H,
            D,
            latch_offset,
            "snap_latch_right",
        ),
    ]

    for part in parts:

        _validate_mesh(part)

    _validate_assembly(
        parts,
        H,
        D,
        W,
    )

    return parts


# ============================================================
# STANDALONE AUTHOR SMOKE TEST
# ============================================================


if __name__ == "__main__":

    parts = build_parts(
        DEFAULTS["food_container_1l"]
    )

    print("Revision: V6")
    print("Author structural checks: PASS")
    print("Material semantic checks: PASS")

    for part in parts:

        lo, hi = _bbox(
            part["verts_mm"]
        )

        print(
            part["name"],
            "material_id=",
            part["material_id"],
            "verts=",
            len(part["verts_mm"]),
            "tris=",
            len(part["tris"]),
            "bbox=",
            (lo, hi),
        )

        if part["joint"] is not None:

            print(
                "  joint=",
                part["joint"],
            )

    all_verts = [
        v
        for part in parts
        for v in part["verts_mm"]
    ]

    lo, hi = _bbox(all_verts)

    dims = [
        hi[i] - lo[i]
        for i in range(3)
    ]

    print(
        "Assembly dimensions:",
        dims,
    )

    print(
        "Total triangles:",
        sum(
            len(p["tris"])
            for p in parts
        ),
    )
