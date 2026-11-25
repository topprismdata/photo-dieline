
# hinged_family.py
# Pack10K Author Contract v1
# Revision: R2 — G-F6 joint-origin bbox correction.
#
# Class: food_container_1l
# Units: mm, Z-up.
# Dependencies: Python standard library only.
#
# R2 ROOT CAUSE:
# The R1 base used drafted dimensions followed by a rounded
# upper rim. No exterior ring reached the exact nominal
# rear boundary y=+D/2.
#
# Consequently, the prescribed hinge origin was marginally
# outside the actual parent mesh bbox.
#
# R2 CORRECTION:
# 1. Base reaches exact W and D before the upper rim fillet.
# 2. Lid reaches exact W and D along its exterior skirt.
# 3. Lid remains in the CLOSED assembly pose.
# 4. Joint origin remains exactly (0, D/2, H-2).
# 5. Joint parent remains "base", following Author Contract.
# 6. Author validation checks the joint origin against BOTH
#    the parent bbox and the moving lid's own bbox.
# 7. No bbox tolerance enlargement or origin displacement.
#
# Default assembly:
#   W = 130 mm
#   D = 100 mm
#   H = 90 mm
#   hinge origin = (0, 50, 88)
#
# Lid joint axis is -X so positive rotation lifts the
# front edge upward. Opening is expressed only by the joint.
#
# Base and lid are closed, hollow PP shells.
# Nominal wall thickness: 0.9 mm (v4).
# Plan-view corner radius: 5 mm.
# Angular resolution: 48 intervals per rounded corner.
#
# Fixed hinge band represents a simplified living hinge.
# Fixed attachment regions may intentionally overlap.
# Full-angle collision and flexible-hinge deformation
# are outside the scope of this mesh author.
#
# External compile gates have not yet been re-executed.

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


_WALL = 0.9  # v4: 1.5 → 0.9 (评审: 减过实感)
_CORNER_R = 5.0
_CORNER_SEGMENTS = 48
_LID_DEPTH = 2.0
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

            # Snap cardinal directions to exact values.
            # This avoids tiny floating-point differences
            # at nominal bounding-box extrema.
            c = math.cos(angle)
            s = math.sin(angle)

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
    Sweep rounded rectangular rings along an axial profile.

    Profile entries:
        (z, width, depth, corner_radius)

    For hollow parts, traversal follows:
        outer floor -> outer wall -> rim
        -> inner wall -> inner floor.

    Terminal rings are capped independently.
    The opening itself is not capped.
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

    # Ring-to-ring strips.
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

    # Exterior floor cap.
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

    # Interior floor or solid top cap.
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


def _part(name, verts, tris, joint=None):

    return {
        "name": name,
        "verts_mm": verts,
        "tris": tris,
        "material_id": "plastic_pp",
        "joint": joint,
    }


def _base_dims_at_z(z, full_width_z, W, D):
    """
    Mild injection-molding draft.

    R2:
    Reach the exact nominal footprint BEFORE the rim fillet,
    not at the highest point of the rounded rim.

    For z >= full_width_z:
        width = W
        depth = D
    """

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


def _build_base(H, D, W):
    """
    Closed material shell representing the open-top base.

    R2 bbox guarantee:
        x_min = -W/2
        x_max = +W/2
        y_min = -D/2
        y_max = +D/2
        z_min = 0
        z_max = H-2

    The rear hinge point is inside this exact bbox.
    """

    base_h = H - _LID_DEPTH

    wall = _WALL
    radius = _CORNER_R

    heel = 1.0
    rim_round = 0.25

    # R2: full footprint is reached before rounding.
    full_width_z = base_h - rim_round

    profile = []

    # -------------------------------------------------
    # 1. Exterior floor and rounded lower heel.
    # -------------------------------------------------

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

    # -------------------------------------------------
    # 2. Drafted exterior wall.
    # -------------------------------------------------

    for z in (
        base_h * 0.25,
        base_h * 0.50,
        base_h * 0.75,
    ):

        w, d = _base_dims_at_z(
            z,
            full_width_z,
            W,
            D,
        )

        profile.append((
            z,
            w,
            d,
            radius,
        ))

    # -------------------------------------------------
    # 3. Exact full-width ring.
    #
    # This ring fixes the R1 joint bbox failure.
    # At default dimensions:
    #     z = 87.75
    #     x extrema = +/-65
    #     y extrema = +/-50
    # -------------------------------------------------

    profile.append((
        full_width_z,
        W,
        D,
        radius,
    ))

    # -------------------------------------------------
    # 4. Rounded outer rim.
    # -------------------------------------------------

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

    # -------------------------------------------------
    # 5. Upper rim annulus.
    # -------------------------------------------------

    inner_W = W - 2.0 * wall
    inner_D = D - 2.0 * wall
    inner_r = radius - wall

    profile.append((
        base_h,
        inner_W + 2.0 * rim_round,
        inner_D + 2.0 * rim_round,
        inner_r + rim_round,
    ))

    # -------------------------------------------------
    # 6. Rounded inner rim.
    # -------------------------------------------------

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

    # -------------------------------------------------
    # 7. Descending interior wall.
    # -------------------------------------------------

    inner_floor = wall
    inner_fillet = 1.0

    for z in (
        base_h * 0.75,
        base_h * 0.50,
        base_h * 0.25,
        inner_floor + inner_fillet,
    ):

        w, d = _base_dims_at_z(
            z,
            full_width_z,
            W,
            D,
        )

        profile.append((
            z,
            w - 2.0 * wall,
            d - 2.0 * wall,
            inner_r,
        ))

    # -------------------------------------------------
    # 8. Interior floor fillet.
    # -------------------------------------------------

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


def _build_lid(H, D, W):
    """
    Build a closed hollow lid in CLOSED assembly pose.

    Construct a shallow tray in local coordinates, then
    reflect it vertically to face the cavity downward.

    World-space lid bbox:
        x = [-W/2, W/2]
        y = [-D/2, D/2]
        z = [H-2, H]

    At default parameters:
        x = [-65, 65]
        y = [-50, 50]
        z = [88, 90]

    Hinge origin:
        (0, 50, 88)

    The hinge origin lies in both the base and lid bboxes.
    No mesh rotation is applied during construction.
    """

    wall = _WALL
    radius = _CORNER_R

    depth = _LID_DEPTH
    edge_round = 0.25

    profile = []

    # -------------------------------------------------
    # 1. Exterior panel edge fillet.
    # -------------------------------------------------

    for i in range(7):

        angle = (
            -math.pi / 2.0
            + math.pi * i / 12.0
        )

        z = (
            edge_round
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

    # -------------------------------------------------
    # 2. Exact nominal skirt dimensions.
    #
    # Preserve explicit full-size rings so the moving
    # component bbox includes the rear hinge origin.
    # -------------------------------------------------

    profile.append((
        depth - edge_round,
        W,
        D,
        radius,
    ))

    # -------------------------------------------------
    # 3. Outer skirt edge fillet.
    # -------------------------------------------------

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

    # -------------------------------------------------
    # 4. Skirt rim.
    # -------------------------------------------------

    inner_W = W - 2.0 * wall
    inner_D = D - 2.0 * wall
    inner_r = radius - wall

    profile.append((
        depth,
        inner_W + 2.0 * edge_round,
        inner_D + 2.0 * edge_round,
        inner_r + edge_round,
    ))

    # -------------------------------------------------
    # 5. Inner skirt edge fillet.
    # -------------------------------------------------

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

    # -------------------------------------------------
    # 6. Recessed underside.
    #
    # Panel thickness = 1.5 mm.
    # Skirt depth = 2.0 mm.
    # -------------------------------------------------

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

    verts, tris = _mesh_from_profile(profile)

    # Reflect the shallow tray into the closed lid pose.
    # Reflection reverses orientation, so reverse winding.
    for v in verts:

        v[2] = H - v[2]

    tris = [
        [a, c, b]
        for a, b, c in tris
    ]

    joint = {
        "parent": "base",
        "axis": [-1.0, 0.0, 0.0],
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


def _build_hinge_band(H, D, W):
    """
    Fixed rear living-hinge envelope.

    Located along +Y.
    Contains the nominal hinge origin within its bbox.
    Remains within the declared assembly dimensions.

    Intentional attachment overlap with base/lid is allowed.
    """

    return _rounded_solid(
        name="hinge_band",
        W=W * 0.70,
        D=2.0,
        z_lo=H - 5.5,
        z_hi=H - 0.5,
        radius=0.65,
        cx=0.0,
        cy=D / 2.0 - 1.0,
        bevel=0.25,
    )


def _extrude_x_polygon(
    name,
    polygon_yz,
    x_center,
    width,
):
    """
    Extrude a convex YZ polygon along X.

    Positive signed polygon area is required.
    Both ends and all lateral faces are triangulated.
    """

    if len(polygon_yz) < 3:
        raise ValueError("Invalid extrusion polygon")

    if width <= 0.0:
        raise ValueError("Invalid extrusion width")

    n = len(polygon_yz)

    # Verify polygon winding.
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

    # End caps.
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

    # Lateral faces.
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


def _build_snap_latch(H, D, x_center, name):
    """
    Independent fixed molded front snap clasp.

    Front direction: -Y.
    Includes sloped lower insertion face and upper
    attachment surface.

    The complete part remains inside the assembly bbox.
    """

    front = -D / 2.0

    polygon = [
        (front + 0.05, H - 6.0),
        (front + 0.75, H - 7.0),
        (front + 2.25, H - 7.0),
        (front + 3.00, H - 5.0),
        (front + 3.00, H - 1.0),
        (front + 2.30, H - 0.45),
        (front + 0.75, H - 0.45),
        (front + 0.05, H - 1.20),
    ]

    return _extrude_x_polygon(
        name=name,
        polygon_yz=polygon,
        x_center=x_center,
        width=14.0,
    )


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
    Author-side topology checks:

    - finite vertex coordinates;
    - valid triangle indices;
    - non-degenerate triangles;
    - exactly two faces per undirected edge;
    - consistent winding;
    - positive signed volume;
    - connected vertex graph.
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

        if not all(math.isfinite(x) for x in v):
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

        p, q, r = verts[a], verts[b], verts[c]

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

        if sum(x * x for x in cross) <= 1e-18:
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

    if any(x != 2 for x in edges.values()):
        raise ValueError(
            "Non-manifold mesh: " + name
        )

    if any(x != 0 for x in directions.values()):
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
    Validate a point against an actual mesh bbox.

    Only a numerical epsilon is permitted.
    No geometric tolerance is added to bypass G-F6.
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
    R2-specific assembly checks.

    Explicitly ensure the lid is not authored in an
    already-open pose and the hinge lies at the rear
    boundary of both parts.
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

    # Closed lid rests on the upper base rim.
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

    # R2 dual-bbox requirement.
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

    # The physical hinge band must also cover the origin.
    _assert_point_in_bbox(
        origin,
        hinge,
        "hinge band",
    )

    # Check that the pivot is at the rear boundary
    # of both mesh bboxes.
    if abs(origin[1] - base_hi[1]) > _EPS:
        raise ValueError(
            "Hinge is not on base rear boundary"
        )

    if abs(origin[1] - lid_hi[1]) > _EPS:
        raise ValueError(
            "Hinge is not on lid rear boundary"
        )

    # Check positive-angle opening direction analytically.
    # For a front point relative to the rear hinge:
    #     r_y = -D
    #     omega_x = -1
    #     (omega cross r)_z = +D
    #
    # The front edge must initially move upward.
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

    # G-F4: dimensions.
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

    movable_parts = []

    for part in parts:

        # G-F5: material.
        if part["material_id"] != "plastic_pp":
            raise ValueError(
                "Invalid material: "
                + part["name"]
            )

        joint = part["joint"]

        if joint is None:
            continue

        movable_parts.append(
            part["name"]
        )

        # G-F6: parent existence.
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

        # Original contract: validate parent bbox.
        _assert_point_in_bbox(
            origin,
            parent,
            "parent",
        )

        # R2 compile requirement: also validate the
        # moving component's own bbox.
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

    # G-F7: family-specific semantics.
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


def build_parts(params: dict) -> list[dict]:
    """
    Build a grounded food container in CLOSED pose.

    Default assembly dimensions:
        X = 130 mm
        Y = 100 mm
        Z = 90 mm

    Returns five independent closed components:
        base
        lid
        hinge_band
        snap_latch_left
        snap_latch_right

    Only lid carries a revolute joint.

    The joint's origin must satisfy both parent-bbox
    and moving-component-bbox requirements.
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


if __name__ == "__main__":
    # Optional standalone author-side smoke test.
    # No output or side effects during normal import.

    parts = build_parts(
        DEFAULTS["food_container_1l"]
    )

    print("Author structural checks: PASS")

    for part in parts:

        lo, hi = _bbox(
            part["verts_mm"]
        )

        print(
            part["name"],
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

    print(
        "Total triangles:",
        sum(
            len(p["tris"])
            for p in parts
        ),
    )
