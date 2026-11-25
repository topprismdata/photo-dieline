
# hinged_family.py
# Pack10K Author Contract v1
#
# Class: food_container_1l
# Units: mm, Z-up.
# Dependencies: Python standard library only.
#
# Design decisions:
# - W is X dimension, D is Y dimension, H is Z dimension.
# - Front: -Y. Back: +Y.
# - Base and lid are independent closed hollow shells.
# - Nominal wall thickness: 1.5 mm.
# - External vertical corner radius: 5 mm.
# - Each rounded corner uses 48 arc segments.
# - Lid joint axis is negative X so positive joint angles
#   lift the front edge upward.
# - Hinge origin: (0, D/2, H-2).
# - Rear hinge band and front snap latches are fixed parts.
# - Hinge band is a simplified compliant living-hinge
#   envelope; deformation is not simulated.
# - Fixed attachment regions may overlap the parent shell.
# - The nominal 1 L capacity is not a calibrated fill volume.
# - Independent compile gates remain to be executed.

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


_WALL = 1.5
_CORNER_R = 5.0
_CORNER_SEGMENTS = 48
_MAX_TRIS = 40000


def _rounded_rect_ring(
    W,
    D,
    radius,
    z,
    cx=0.0,
    cy=0.0,
    arc_segments=_CORNER_SEGMENTS,
):
    """
    Generate a counterclockwise rounded rectangle.

    Each corner contains arc_segments circular intervals.
    Straight edges connect adjacent corner arcs.

    No duplicated closing vertex.
    """
    if W <= 0.0 or D <= 0.0:
        raise ValueError("Invalid rectangle dimensions")

    if not 0.0 < radius < min(W, D) / 2.0:
        raise ValueError("Invalid corner radius")

    hx = W / 2.0
    hy = D / 2.0

    corners = [
        (
            hx - radius,
            hy - radius,
            0.0,
        ),
        (
            -hx + radius,
            hy - radius,
            math.pi / 2.0,
        ),
        (
            -hx + radius,
            -hy + radius,
            math.pi,
        ),
        (
            hx - radius,
            -hy + radius,
            3.0 * math.pi / 2.0,
        ),
    ]

    ring = []

    for x0, y0, start in corners:

        for i in range(arc_segments + 1):

            angle = start + (
                math.pi / 2.0
            ) * i / arc_segments

            ring.append([
                cx + x0 + radius * math.cos(angle),
                cy + y0 + radius * math.sin(angle),
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
    Generate a closed rounded-rectangle mesh from
    an ordered axial boundary profile.

    Profile entries:
        (z, width, depth, corner_radius)

    Traversal:
        exterior bottom -> exterior upper wall
        -> rim -> inner wall -> inner floor

    Both terminal rings are capped using a single
    center vertex. For a hollow vessel, the second
    cap is the cavity floor, not the opening.

    The same function can generate ordinary solids.
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

    # Connect every adjacent pair of rings.
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

    # Bottom/exterior cap.
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

    # Final cap: upper surface or interior floor.
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


def _base_dims_at_z(z, base_h, W, D):
    """
    Mild injection-molding draft.

    Bottom footprint is smaller by 2 mm in X and Y.
    Upper footprint reaches the declared W and D.
    """
    t = max(0.0, min(1.0, z / base_h))

    shrink = 2.0 * (1.0 - t)

    return (
        W - shrink,
        D - shrink,
    )


def _build_base(H, D, W):
    """
    Open-top container base.

    Exterior:
        rounded bottom edge;
        lightly drafted walls;
        rounded upper rim.

    Interior:
        radial/planar wall offset of 1.5 mm;
        1.5 mm bottom thickness;
        rounded floor-to-wall transitions.

    The rim connects outer and inner surfaces.
    The mouth remains open.
    """
    base_h = H - 2.0

    wall = _WALL
    radius = _CORNER_R

    heel = 1.0
    rim_round = 0.25

    profile = []

    # -------------------------------------------------
    # 1. Exterior floor and rounded heel.
    # -------------------------------------------------

    for i in range(9):

        t = (
            -math.pi / 2.0
            + (math.pi / 2.0) * i / 8.0
        )

        z = heel + heel * math.sin(t)

        offset = heel * (1.0 - math.cos(t))

        w, d = _base_dims_at_z(
            z, base_h, W, D
        )

        profile.append((
            z,
            w - 2.0 * offset,
            d - 2.0 * offset,
            radius - offset,
        ))

    # -------------------------------------------------
    # 2. Main exterior wall.
    # -------------------------------------------------

    for z in (
        base_h * 0.25,
        base_h * 0.50,
        base_h * 0.75,
        base_h - rim_round,
    ):

        w, d = _base_dims_at_z(
            z, base_h, W, D
        )

        profile.append((
            z,
            w,
            d,
            radius,
        ))

    # -------------------------------------------------
    # 3. Upper rim: outer rounded edge.
    # -------------------------------------------------

    for i in range(1, 5):

        t = (math.pi / 2.0) * i / 4.0

        z = (
            base_h
            - rim_round
            + rim_round * math.sin(t)
        )

        offset = rim_round * (
            1.0 - math.cos(t)
        )

        # The outer rim is based on nominal top dimensions.
        profile.append((
            z,
            W - 2.0 * offset,
            D - 2.0 * offset,
            radius - offset,
        ))

    # -------------------------------------------------
    # 4. Flat upper rim, terminating at inner fillet.
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
    # 5. Inner rounded rim.
    # -------------------------------------------------

    for i in range(1, 5):

        t = (
            math.pi / 2.0
        ) * i / 4.0

        z = (
            base_h
            - rim_round
            + rim_round * math.cos(t)
        )

        offset = rim_round * (
            1.0 - math.sin(t)
        )

        profile.append((
            z,
            inner_W + 2.0 * offset,
            inner_D + 2.0 * offset,
            inner_r + offset,
        ))

    # -------------------------------------------------
    # 6. Main interior wall, descending.
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
            z, base_h, W, D
        )

        profile.append((
            z,
            w - 2.0 * wall,
            d - 2.0 * wall,
            inner_r,
        ))

    # -------------------------------------------------
    # 7. Rounded interior floor corner.
    # -------------------------------------------------

    for i in range(1, 9):

        t = (math.pi / 2.0) * i / 8.0

        z = (
            inner_floor
            + inner_fillet
            - inner_fillet * math.sin(t)
        )

        offset = inner_fillet * (
            1.0 - math.cos(t)
        )

        w, d = _base_dims_at_z(
            z, base_h, W, D
        )

        profile.append((
            z,
            w - 2.0 * wall - 2.0 * offset,
            d - 2.0 * wall - 2.0 * offset,
            inner_r - offset,
        ))

    # The final ring is capped at z=1.5 mm,
    # creating a real enclosed material bottom.
    verts, tris = _mesh_from_profile(profile)

    return _part("base", verts, tris)


def _build_lid(H, D, W):
    """
    Build a shallow hollow lid in local coordinates.

    Local geometry:
        open upward, floor at local z=0;
        panel thickness 1.5 mm;
        total shell depth 2.0 mm.

    Then reflect it into world coordinates so the cavity
    faces downward and the top surface reaches H.

    This gives a true recessed underside rather than
    a solid rectangular slab.
    """
    wall = _WALL
    radius = _CORNER_R

    depth = 2.0
    edge_round = 0.25

    profile = []

    # -------------------------------------------------
    # 1. Outer panel perimeter with rounded edge.
    # -------------------------------------------------

    for i in range(7):

        t = (
            -math.pi / 2.0
            + (math.pi / 2.0) * i / 6.0
        )

        z = (
            edge_round
            + edge_round * math.sin(t)
        )

        offset = edge_round * (
            1.0 - math.cos(t)
        )

        profile.append((
            z,
            W - 2.0 * offset,
            D - 2.0 * offset,
            radius - offset,
        ))

    # -------------------------------------------------
    # 2. Outer skirt wall.
    # -------------------------------------------------

    profile.append((
        depth - edge_round,
        W,
        D,
        radius,
    ))

    # -------------------------------------------------
    # 3. Rounded outer skirt edge.
    # -------------------------------------------------

    for i in range(1, 5):

        t = (math.pi / 2.0) * i / 4.0

        z = (
            depth
            - edge_round
            + edge_round * math.sin(t)
        )

        offset = edge_round * (
            1.0 - math.cos(t)
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
    # 5. Inner skirt rounded edge.
    # -------------------------------------------------

    for i in range(1, 5):

        t = (math.pi / 2.0) * i / 4.0

        z = (
            depth
            - edge_round
            + edge_round * math.cos(t)
        )

        offset = edge_round * (
            1.0 - math.sin(t)
        )

        profile.append((
            z,
            inner_W + 2.0 * offset,
            inner_D + 2.0 * offset,
            inner_r + offset,
        ))

    # -------------------------------------------------
    # 6. Recessed underside with 1.5 mm panel thickness.
    # -------------------------------------------------

    floor_fillet = 0.15

    profile.append((
        wall + floor_fillet,
        inner_W,
        inner_D,
        inner_r,
    ))

    for i in range(1, 5):

        t = (math.pi / 2.0) * i / 4.0

        z = (
            wall
            + floor_fillet
            - floor_fillet * math.sin(t)
        )

        offset = floor_fillet * (
            1.0 - math.cos(t)
        )

        profile.append((
            z,
            inner_W - 2.0 * offset,
            inner_D - 2.0 * offset,
            inner_r - offset,
        ))

    verts, tris = _mesh_from_profile(profile)

    # Reflection reverses winding, so reverse all faces.
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
            H - 2.0,
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
    """
    Closed rounded rectangular solid with upper and
    lower edge fillets.

    Used for hinge band and snap-latch components.
    Smaller parts use 12 intervals per quarter arc.
    """
    height = z_hi - z_lo

    bevel = min(
        bevel,
        height * 0.25,
        radius * 0.5,
    )

    if height <= 0.0 or bevel <= 0.0:
        raise ValueError("Invalid solid dimensions")

    profile = []

    # Lower edge.
    for i in range(5):

        t = (
            -math.pi / 2.0
            + (math.pi / 2.0) * i / 4.0
        )

        z = (
            z_lo
            + bevel
            + bevel * math.sin(t)
        )

        offset = bevel * (
            1.0 - math.cos(t)
        )

        profile.append((
            z,
            W - 2.0 * offset,
            D - 2.0 * offset,
            radius - offset,
        ))

    # Upper end of main wall.
    profile.append((
        z_hi - bevel,
        W,
        D,
        radius,
    ))

    # Upper edge.
    for i in range(1, 5):

        t = (math.pi / 2.0) * i / 4.0

        z = (
            z_hi
            - bevel
            + bevel * math.sin(t)
        )

        offset = bevel * (
            1.0 - math.cos(t)
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

    return _part(name, verts, tris)


def _build_hinge_band(H, D, W):
    """
    Rear living-hinge strip.

    Located along +Y rear edge, entirely inside the
    declared assembly envelope.

    Attachment to the shell is represented by a small
    controlled overlap, not a Boolean union.
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

    Input polygon must be counterclockwise in (Y, Z).
    End caps and lateral surfaces are triangulated.
    """
    if len(polygon_yz) < 3:
        raise ValueError("Invalid extrusion polygon")

    if width <= 0.0:
        raise ValueError("Invalid extrusion width")

    n = len(polygon_yz)

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
            0, i + 1, i,
        ])

        tris.append([
            n, n + i, n + i + 1,
        ])

    # Lateral walls.
    for i in range(n):

        j = (i + 1) % n

        tris.append([
            i, j, j + n,
        ])

        tris.append([
            i, j + n, i + n,
        ])

    return _part(name, verts, tris)


def _build_snap_latch(H, D, x_center, name):
    """
    Simplified molded snap clasp.

    The YZ section contains:
        extended lower hook;
        sloped insertion face;
        upper attachment surface.

    It remains within the overall bounding box.
    The small overlap with the front shell represents
    an attachment, not unintended penetration.
    """
    front = -D / 2.0

    polygon = [
        (front + 0.05, H - 6.0),
        (front + 0.75, H - 7.0),
        (front + 2.25, H - 7.0),
        (front + 3.0, H - 5.0),
        (front + 3.0, H - 1.0),
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


def _validate_mesh(part):
    """
    Author-side structural validation.

    Checks:
        finite vertices;
        valid triangle indices;
        non-degenerate faces;
        exactly two triangles per undirected edge;
        consistent face orientation;
        positive enclosed material volume;
        connected vertex graph.
    """
    verts = part["verts_mm"]
    tris = part["tris"]

    if not verts or not tris:
        raise ValueError("Empty mesh: " + part["name"])

    for v in verts:

        if len(v) != 3:
            raise ValueError("Invalid vertex dimension")

        if not all(math.isfinite(x) for x in v):
            raise ValueError("Non-finite vertex")

    edges = {}
    directions = {}
    adjacency = [
        set()
        for _ in verts
    ]

    volume6 = 0.0

    for tri in tris:

        if len(tri) != 3:
            raise ValueError("Non-triangle face")

        a, b, c = tri

        if len({a, b, c}) != 3:
            raise ValueError("Repeated triangle index")

        if min(a, b, c) < 0 or max(a, b, c) >= len(verts):
            raise ValueError("Triangle index out of range")

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
                "Degenerate face: " + part["name"]
            )

        volume6 += sum(
            p[i] * cross[i]
            for i in range(3)
        )

        for i, j in ((a, b), (b, c), (c, a)):

            key = (
                min(i, j),
                max(i, j),
            )

            edges[key] = edges.get(
                key, 0
            ) + 1

            directions[key] = directions.get(
                key, 0
            ) + (1 if i < j else -1)

            adjacency[i].add(j)
            adjacency[j].add(i)

    if any(x != 2 for x in edges.values()):

        raise ValueError(
            "Non-manifold mesh: " + part["name"]
        )

    if any(x != 0 for x in directions.values()):

        raise ValueError(
            "Inconsistent winding: " + part["name"]
        )

    if volume6 <= 0.0:

        raise ValueError(
            "Non-positive signed volume: " + part["name"]
        )

    visited = set()
    stack = [0]

    while stack:

        i = stack.pop()

        if i in visited:
            continue

        visited.add(i)
        stack.extend(adjacency[i] - visited)

    if len(visited) != len(verts):

        raise ValueError(
            "Disconnected mesh: " + part["name"]
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


def _validate_assembly(parts, H, D, W):

    all_verts = [
        v
        for part in parts
        for v in part["verts_mm"]
    ]

    lo, hi = _bbox(all_verts)

    if abs(lo[2]) > 1e-8:
        raise ValueError("Assembly is not grounded")

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
        raise ValueError("Duplicate part name")

    for part in parts:

        if part["material_id"] != "plastic_pp":
            raise ValueError("Invalid material")

        joint = part["joint"]

        if joint is None:
            continue

        if joint["parent"] not in by_name:
            raise ValueError("Unknown joint parent")

        if joint["parent"] == part["name"]:
            raise ValueError("Self-referencing joint")

        axis = joint["axis"]

        if abs(
            sum(x * x for x in axis) - 1.0
        ) > 1e-9:

            raise ValueError("Joint axis is not unit length")

        if sum(abs(x) > 1e-9 for x in axis) != 1:
            raise ValueError("Joint axis is not aligned")

        parent = by_name[joint["parent"]]

        p_lo, p_hi = _bbox(
            parent["verts_mm"]
        )

        for i, coordinate in enumerate(
            joint["origin"]
        ):

            # No tolerance-based bypass of parent bbox.
            if not (
                p_lo[i] - 1e-8
                <= coordinate
                <= p_hi[i] + 1e-8
            ):
                raise ValueError(
                    "Joint origin outside parent bbox"
                )

        limits = joint["limits_deg"]

        if limits[0] > limits[1]:
            raise ValueError("Invalid joint limits")


def build_parts(params: dict) -> list[dict]:
    """
    Build the closed-state food container assembly.

    Output:
        base
        lid
        hinge_band
        snap_latch_left
        snap_latch_right
    """
    config = dict(
        DEFAULTS["food_container_1l"]
    )

    config.update(params)

    H = float(config["H"])
    D = float(config["D"])
    W = float(config["W"])

    _validate_params(H, D, W)

    latch_offset = W * 0.25

    parts = [
        _build_base(H, D, W),
        _build_lid(H, D, W),
        _build_hinge_band(H, D, W),
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

    _validate_assembly(parts, H, D, W)

    return parts
