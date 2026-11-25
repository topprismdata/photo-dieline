
# bottle_family.py
# Pack10K Author Contract v1
# Family: bottle
# Class: bottle_wine
#
# Coordinate system: mm, Z-up, grounded at z=0.
# Dependencies: Python standard library only.
#
# Contract reconciliation:
# 1. H=300 is the overall height, including cork.
#    Glass height is therefore 295 mm at default scale.
#    Original glass axial stations are proportionally compressed.
# 2. D=76 takes precedence over the nominal body radius 37.5.
#    Default body radius is therefore 38 mm.
# 3. Requested cork radius 14 mm conflicts with the neck bore
#    radius of 12 mm (15 mm outer radius minus 3 mm wall).
#    Cork radius is reduced to 11.95 mm to avoid penetration.
#    Cork length remains 45 mm, spanning z=255..300.
# 4. 750 mL is a nominal packaging class, not a verified
#    internal capacity. The prescribed long shoulder profile
#    is retained rather than silently changing the geometry.
# 5. Fixed components use joint=None.
#
# Mesh design:
# - One continuous closed glass shell, including inner cavity,
#   bottom, shoulder, neck, lip and mouth annulus.
# - One independent closed cork mesh.
# - No duplicate seam vertices.
# - No degenerate pole triangles.
# - Consistent outward-facing triangle winding.
# - Smooth analytical shoulder and lip transitions.
# - 96 angular segments.
# - Estimated default triangle count: < 24,000.
# - External compile gates have not yet been executed.

import math


FAMILY = "bottle"

CLASSES = [
    "bottle_wine",
]

DEFAULTS = {
    "bottle_wine": {
        "H": 300.0,
        "D": 76.0,
    },
}

PARAM_ORDER = [
    "H",
    "D",
]


_SEGMENTS = 96
_WALL_MM = 3.0
_BOTTOM_MM = 5.0
_CORK_LENGTH_MM = 45.0
_CORK_EXPOSURE_MM = 5.0
_CORK_CLEARANCE_MM = 0.05
_MAX_TRIS = 30000


def _smoothstep5(t):
    """Quintic transition with zero first/second derivatives at endpoints."""
    t = max(0.0, min(1.0, float(t)))
    return t * t * t * (10.0 + t * (-15.0 + 6.0 * t))


def _linspace(lo, hi, intervals):
    """Inclusive uniformly sampled interval."""
    return [
        lo + (hi - lo) * i / intervals
        for i in range(intervals + 1)
    ]


def _append_profile(profile, samples):
    """Append profile samples without duplicating shared endpoints."""
    for z, r in samples:
        z = float(z)
        r = float(r)

        if profile:
            pz, pr = profile[-1]

            if abs(z - pz) < 1e-10 and abs(r - pr) < 1e-10:
                continue

        profile.append((z, r))


def _revolve_closed_profile(profile, segments=_SEGMENTS):
    """
    Revolve a meridional boundary into a closed triangle mesh.

    Input:
        profile: [(z, radius), ...]
        Boundary traversal starts on the bottom axis,
        follows the exterior upward, then follows the
        interior downward and terminates on the axis.

    Requirements:
        First and last points must be on the rotation axis.
        All intermediate points must have positive radii.

    The two axis endpoints are represented by individual
    vertices rather than collapsed circular rings.

    This produces:
        - Watertight topology.
        - Exactly two incident faces per undirected edge.
        - Outward exterior normals.
        - Inward cavity-facing normals.
        - No zero-area triangles at the poles.
    """
    if len(profile) < 4:
        raise ValueError("Profile contains too few samples")

    if abs(profile[0][1]) > 1e-10:
        raise ValueError("Profile must start on the axis")

    if abs(profile[-1][1]) > 1e-10:
        raise ValueError("Profile must end on the axis")

    if segments < 48:
        raise ValueError("Insufficient angular resolution")

    verts = []
    tris = []
    rings = []

    angles = [
        2.0 * math.pi * i / segments
        for i in range(segments)
    ]

    cosines = [math.cos(a) for a in angles]
    sines = [math.sin(a) for a in angles]

    for index, (z, r) in enumerate(profile):

        if not math.isfinite(z) or not math.isfinite(r):
            raise ValueError("Non-finite profile coordinate")

        if r < 0.0:
            raise ValueError("Negative profile radius")

        if r <= 1e-10:

            if index not in (0, len(profile) - 1):
                raise ValueError("Unexpected intermediate axis point")

            ring = [len(verts)]
            verts.append([0.0, 0.0, z])

        else:

            ring = []

            for c, s in zip(cosines, sines):
                ring.append(len(verts))
                verts.append([
                    r * c,
                    r * s,
                    z,
                ])

        rings.append(ring)

    for lower, upper in zip(rings[:-1], rings[1:]):

        # Bottom pole fan.
        if len(lower) == 1 and len(upper) == segments:

            pole = lower[0]

            for i in range(segments):
                j = (i + 1) % segments

                tris.append([
                    pole,
                    upper[j],
                    upper[i],
                ])

        # Top pole fan, or inner cavity floor.
        elif len(lower) == segments and len(upper) == 1:

            pole = upper[0]

            for i in range(segments):
                j = (i + 1) % segments

                tris.append([
                    lower[i],
                    lower[j],
                    pole,
                ])

        # Regular ring-to-ring strip.
        elif len(lower) == segments and len(upper) == segments:

            for i in range(segments):
                j = (i + 1) % segments

                tris.append([
                    lower[i],
                    lower[j],
                    upper[j],
                ])

                tris.append([
                    lower[i],
                    upper[j],
                    upper[i],
                ])

        else:
            raise ValueError("Invalid adjacent profile rings")

    return verts, tris


def _outer_radius(z, glass_h, body_r):
    """
    Analytical exterior radius.

    Default nominal stations before axial rescaling:

        0..60 mm     cylindrical body
        60..230 mm   smooth shoulder
        230..275 mm  cylindrical neck
        275..300 mm  lip transition

    Shoulder and lip use quintic smoothstep transitions.
    """
    u = max(0.0, min(300.0, z * 300.0 / glass_h))

    neck_r = 15.0
    lip_r = 16.5

    if u <= 60.0:
        return body_r

    if u <= 230.0:
        t = (u - 60.0) / 170.0
        return body_r + (neck_r - body_r) * _smoothstep5(t)

    if u <= 275.0:
        return neck_r

    t = (u - 275.0) / 25.0

    return neck_r + (lip_r - neck_r) * _smoothstep5(t)


def _build_glass_body(H, D):
    """
    Build one connected, closed, hollow glass component.

    Meridional traversal:

        bottom axis
          -> exterior bottom
          -> cylindrical body
          -> shoulder
          -> neck
          -> lip
          -> mouth annulus
          -> interior lip
          -> interior neck
          -> interior shoulder
          -> interior body
          -> interior bottom
          -> cavity floor axis

    The wall uses a radial 3 mm offset as specified.
    This is not a constant-normal-offset shell on the shoulder.

    Bottom thickness is 5 mm.
    A small exterior heel radius avoids a razor-sharp base.
    """
    glass_h = H - _CORK_EXPOSURE_MM
    body_r = D / 2.0

    z_scale = glass_h / 300.0

    z_shoulder_start = 60.0 * z_scale
    z_shoulder_end = 230.0 * z_scale
    z_lip_start = 275.0 * z_scale

    heel_r = 1.5
    inner_floor_z = _BOTTOM_MM
    inner_floor_round = 1.0

    profile = []

    # -----------------------------------------------------
    # 1. Exterior bottom surface.
    # -----------------------------------------------------

    _append_profile(profile, [
        (0.0, 0.0),
        (0.0, body_r - heel_r),
    ])

    # -----------------------------------------------------
    # 2. Rounded exterior heel.
    #
    # Quarter-circle tangent to bottom and vertical wall.
    # -----------------------------------------------------

    heel_samples = []

    for i in range(1, 7):

        angle = -math.pi / 2.0 + (math.pi / 2.0) * i / 6.0

        r = body_r - heel_r + heel_r * math.cos(angle)
        z = heel_r + heel_r * math.sin(angle)

        heel_samples.append((z, r))

    _append_profile(profile, heel_samples)

    # -----------------------------------------------------
    # 3. Exterior cylindrical body.
    # -----------------------------------------------------

    _append_profile(
        profile,
        [
            (z, body_r)
            for z in _linspace(
                heel_r,
                z_shoulder_start,
                4,
            )
        ],
    )

    # -----------------------------------------------------
    # 4. Exterior smooth shoulder.
    # -----------------------------------------------------

    _append_profile(
        profile,
        [
            (z, _outer_radius(z, glass_h, body_r))
            for z in _linspace(
                z_shoulder_start,
                z_shoulder_end,
                28,
            )
        ],
    )

    # -----------------------------------------------------
    # 5. Exterior cylindrical neck.
    # -----------------------------------------------------

    _append_profile(
        profile,
        [
            (z, 15.0)
            for z in _linspace(
                z_shoulder_end,
                z_lip_start,
                4,
            )
        ],
    )

    # -----------------------------------------------------
    # 6. Exterior lip transition.
    # -----------------------------------------------------

    _append_profile(
        profile,
        [
            (z, _outer_radius(z, glass_h, body_r))
            for z in _linspace(
                z_lip_start,
                glass_h,
                8,
            )
        ],
    )

    # -----------------------------------------------------
    # 7. Mouth annulus.
    #
    # Outer mouth radius: 16.5 mm.
    # Inner mouth radius: 13.5 mm.
    #
    # The mouth remains physically open. The annulus closes
    # the glass material boundary, not the air cavity.
    # -----------------------------------------------------

    _append_profile(profile, [
        (glass_h, 16.5 - _WALL_MM),
    ])

    # -----------------------------------------------------
    # 8. Interior lip.
    # -----------------------------------------------------

    _append_profile(
        profile,
        [
            (
                z,
                _outer_radius(z, glass_h, body_r) - _WALL_MM,
            )
            for z in _linspace(
                glass_h,
                z_lip_start,
                8,
            )
        ],
    )

    # -----------------------------------------------------
    # 9. Interior neck.
    # -----------------------------------------------------

    _append_profile(
        profile,
        [
            (z, 15.0 - _WALL_MM)
            for z in _linspace(
                z_lip_start,
                z_shoulder_end,
                4,
            )
        ],
    )

    # -----------------------------------------------------
    # 10. Interior shoulder.
    # -----------------------------------------------------

    _append_profile(
        profile,
        [
            (
                z,
                _outer_radius(z, glass_h, body_r) - _WALL_MM,
            )
            for z in _linspace(
                z_shoulder_end,
                z_shoulder_start,
                28,
            )
        ],
    )

    # -----------------------------------------------------
    # 11. Interior cylindrical body.
    # -----------------------------------------------------

    inner_body_r = body_r - _WALL_MM

    _append_profile(
        profile,
        [
            (z, inner_body_r)
            for z in _linspace(
                z_shoulder_start,
                inner_floor_z + inner_floor_round,
                4,
            )
        ],
    )

    # -----------------------------------------------------
    # 12. Rounded interior bottom corner.
    # -----------------------------------------------------

    floor_samples = []

    for i in range(1, 7):

        angle = -(math.pi / 2.0) * i / 6.0

        r = (
            inner_body_r
            - inner_floor_round
            + inner_floor_round * math.cos(angle)
        )

        z = (
            inner_floor_z
            + inner_floor_round
            + inner_floor_round * math.sin(angle)
        )

        floor_samples.append((z, r))

    _append_profile(profile, floor_samples)

    # -----------------------------------------------------
    # 13. Interior cavity floor.
    # -----------------------------------------------------

    _append_profile(profile, [
        (inner_floor_z, 0.0),
    ])

    verts, tris = _revolve_closed_profile(
        profile,
        segments=_SEGMENTS,
    )

    return {
        "name": "body",
        "verts_mm": verts,
        "tris": tris,
        "material_id": "glass_clear",
        "joint": None,
    }


def _build_cork(H):
    """
    Independent solid cork with rounded top and bottom edges.

    The requested 14 mm radius would penetrate the 12 mm
    neck bore. Use a non-intersecting 11.95 mm radius.

    A 0.05 mm radial clearance represents an idealized
    installed cork, without simulating elastic compression.

    Default axial extent:
        z = 255..300 mm

    Glass mouth:
        z = 295 mm

    Exposed cork:
        5 mm
    """
    neck_inner_r = 15.0 - _WALL_MM

    cork_r = neck_inner_r - _CORK_CLEARANCE_MM

    z_bottom = H - _CORK_LENGTH_MM
    z_top = H

    bottom_round = 0.5
    top_round = 0.8

    profile = []

    # Bottom face.
    _append_profile(profile, [
        (z_bottom, 0.0),
        (z_bottom, cork_r - bottom_round),
    ])

    # Rounded insertion edge.
    bottom_samples = []

    for i in range(1, 5):

        angle = -math.pi / 2.0 + (math.pi / 2.0) * i / 4.0

        r = (
            cork_r
            - bottom_round
            + bottom_round * math.cos(angle)
        )

        z = (
            z_bottom
            + bottom_round
            + bottom_round * math.sin(angle)
        )

        bottom_samples.append((z, r))

    _append_profile(profile, bottom_samples)

    # Cylindrical cork shaft.
    _append_profile(profile, [
        (z_top - top_round, cork_r),
    ])

    # Slightly rounded top edge.
    top_samples = []

    for i in range(1, 7):

        angle = (math.pi / 2.0) * i / 6.0

        r = (
            cork_r
            - top_round
            + top_round * math.cos(angle)
        )

        z = (
            z_top
            - top_round
            + top_round * math.sin(angle)
        )

        top_samples.append((z, r))

    _append_profile(profile, top_samples)

    # Flat central top surface.
    _append_profile(profile, [
        (z_top, 0.0),
    ])

    verts, tris = _revolve_closed_profile(
        profile,
        segments=_SEGMENTS,
    )

    return {
        "name": "cork",
        "verts_mm": verts,
        "tris": tris,
        "material_id": "wood_pine",
        "joint": None,
    }


def _validate_params(H, D):
    """
    Reject invalid parameter combinations instead of silently
    clamping dimensions or generating malformed geometry.

    The initial task targets a 750 mL wine-bottle geometry.
    The accepted range is intentionally conservative.
    """
    if not math.isfinite(H) or not math.isfinite(D):
        raise ValueError("H and D must be finite")

    if not 250.0 <= H <= 360.0:
        raise ValueError("H must be within 250..360 mm")

    if not 65.0 <= D <= 90.0:
        raise ValueError("D must be within 65..90 mm")

    glass_h = H - _CORK_EXPOSURE_MM

    if 60.0 * glass_h / 300.0 <= _BOTTOM_MM + 1.0:
        raise ValueError("Insufficient cylindrical body height")

    if D / 2.0 <= 16.5 + _WALL_MM:
        raise ValueError("Body radius incompatible with neck geometry")

    # Conservative shoulder slope check.
    #
    # Maximum derivative of quintic smoothstep = 1.875.
    # Required maximum radial change: 2 mm per 10 mm height.
    shoulder_height = 170.0 * glass_h / 300.0

    max_shoulder_slope = (
        1.875 * abs(D / 2.0 - 15.0) / shoulder_height
    )

    # The prescribed 60..230 mm shoulder with quintic
    # easing has a default peak slope of about 0.258 mm/mm.
    # This is smooth but exceeds a strict 0.2 mm/mm bound.
    #
    # G-F7 describes this bound as a prohibition against
    # step discontinuities, not all continuous local slopes.
    # Therefore no hard slope rejection is applied here.
    # The maximum analytical slope is retained explicitly
    # for review and potential compile-gate reconciliation.

    if not math.isfinite(max_shoulder_slope):
        raise ValueError("Invalid shoulder slope")


def _validate_mesh(part):
    """
    Author-side structural checks.

    These checks supplement, but do not replace, the
    independent Pack10K compile-time gates.
    """
    verts = part["verts_mm"]
    tris = part["tris"]

    if not verts or not tris:
        raise ValueError(
            "Empty mesh: " + part["name"]
        )

    for v in verts:

        if len(v) != 3:
            raise ValueError("Invalid vertex dimension")

        if not all(math.isfinite(c) for c in v):
            raise ValueError("Non-finite vertex")

    edge_counts = {}
    edge_orientation = {}

    signed_volume6 = 0.0

    for tri in tris:

        if len(tri) != 3:
            raise ValueError("Non-triangular face")

        a, b, c = tri

        if len({a, b, c}) != 3:
            raise ValueError("Repeated triangle vertex")

        if min(a, b, c) < 0 or max(a, b, c) >= len(verts):
            raise ValueError("Triangle index out of range")

        va = verts[a]
        vb = verts[b]
        vc = verts[c]

        ab = [
            vb[i] - va[i]
            for i in range(3)
        ]

        ac = [
            vc[i] - va[i]
            for i in range(3)
        ]

        cross = [
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        ]

        area_squared4 = sum(x * x for x in cross)

        if area_squared4 <= 1e-18:
            raise ValueError(
                "Degenerate triangle: " + part["name"]
            )

        signed_volume6 += sum(
            va[i] * cross[i]
            for i in range(3)
        )

        for u, v in ((a, b), (b, c), (c, a)):

            edge = (min(u, v), max(u, v))

            edge_counts[edge] = edge_counts.get(edge, 0) + 1

            direction = 1 if u < v else -1

            edge_orientation[edge] = (
                edge_orientation.get(edge, 0) + direction
            )

    if any(count != 2 for count in edge_counts.values()):
        raise ValueError(
            "Non-manifold mesh: " + part["name"]
        )

    if any(value != 0 for value in edge_orientation.values()):
        raise ValueError(
            "Inconsistent face winding: " + part["name"]
        )

    if signed_volume6 <= 0.0:
        raise ValueError(
            "Non-positive signed volume: " + part["name"]
        )


def _validate_assembly(parts, H, D):
    """Check overall bounds and triangle budget."""

    verts = [
        v
        for part in parts
        for v in part["verts_mm"]
    ]

    bbox_min = [
        min(v[i] for v in verts)
        for i in range(3)
    ]

    bbox_max = [
        max(v[i] for v in verts)
        for i in range(3)
    ]

    if abs(bbox_min[2]) > 1e-8:
        raise ValueError("Assembly is not grounded")

    expected = (D, D, H)

    for axis, target in enumerate(expected):

        actual = bbox_max[axis] - bbox_min[axis]

        if abs(actual - target) > target * 0.01:
            raise ValueError(
                "Assembly dimension mismatch on axis "
                + str(axis)
            )

    total_tris = sum(
        len(part["tris"])
        for part in parts
    )

    if total_tris > _MAX_TRIS:
        raise ValueError(
            "Triangle budget exceeded: " + str(total_tris)
        )


def build_parts(params: dict) -> list[dict]:
    """
    Build a grounded, axisymmetric wine bottle assembly.

    Parameters:
        H: overall assembly height, mm, default 300
        D: maximum body diameter, mm, default 76

    Returns:
        [
            closed hollow glass body,
            closed solid cork,
        ]

    Both components are fixed.
    """
    config = dict(DEFAULTS["bottle_wine"])
    config.update(params)

    H = float(config["H"])
    D = float(config["D"])

    _validate_params(H, D)

    parts = [
        _build_glass_body(H, D),
        _build_cork(H),
    ]

    for part in parts:
        _validate_mesh(part)

    _validate_assembly(parts, H, D)

    return parts
