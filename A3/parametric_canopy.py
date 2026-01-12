import Rhino.Geometry as rg
import numpy as np
import random

# ------------------------------------------------------------
# Inputs:
# Crv : closed planar curve
# U, V : grid resolution
# Amp : amplitude of heightmap
# Scale : perlin noise frequency
# H : Z-offset (height shift)
# Seed : random seed
# ------------------------------------------------------------

if Crv is None:
    a = None
    b = []
else:
    random.seed(Seed)
    np.random.seed(Seed)

    # --------------------------------------------------------
    # PERLIN NOISE (NumPy version)
    # --------------------------------------------------------

    def fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def lerp(a, b, t):
        return a + t * (b - a)

    perm = np.arange(256)
    np.random.shuffle(perm)
    perm = np.tile(perm, 2)

    def perlin(x, y):
        xi = (x.astype(int) & 255)
        yi = (y.astype(int) & 255)

        xf = x - x.astype(int)
        yf = y - y.astype(int)

        u = fade(xf)
        v = fade(yf)

        aa = perm[perm[xi]     + yi]
        ab = perm[perm[xi]     + yi + 1]
        ba = perm[perm[xi + 1] + yi]
        bb = perm[perm[xi + 1] + yi + 1]

        def grad(h, x, y):
            h = h & 3
            return np.where(
                h == 0, x + y,
                np.where(
                    h == 1, -x + y,
                    np.where(
                        h == 2, x - y,
                        -x - y
                    )
                )
            )

        x1 = lerp(grad(aa, xf,   yf),     grad(ba, xf - 1, yf),       u)
        x2 = lerp(grad(ab, xf,   yf - 1), grad(bb, xf - 1, yf - 1),   u)

        return lerp(x1, x2, v)

    # --------------------------------------------------------
    # BUILD UV GRID INSIDE CRV BOUNDING BOX
    # --------------------------------------------------------

    bbox = Crv.GetBoundingBox(True)
    x0, x1 = bbox.Min.X, bbox.Max.X
    y0, y1 = bbox.Min.Y, bbox.Max.Y

    xs = np.linspace(x0, x1, U + 1)
    ys = np.linspace(y0, y1, V + 1)
    XX, YY = np.meshgrid(xs, ys)

    flat_pts = np.stack([XX, YY], axis = -1).reshape((-1, 2))
    inside_mask = []

    pts2d = []
    for (x, y) in flat_pts:
        test_pt = rg.Point3d(x, y, 0)
        inside = (Crv.Contains(test_pt, rg.Plane.WorldXY, 1e-6) == rg.PointContainment.Inside)
        inside_mask.append(inside)
        pts2d.append(test_pt)

    pts2d = np.array([[p.X, p.Y] for p in pts2d]).reshape((V + 1, U + 1, 2))
    inside_mask = np.array(inside_mask).reshape((V + 1, U + 1))

    # --------------------------------------------------------
    # SOFT EDGE FALLOFF
    # --------------------------------------------------------
    distances = np.zeros((V + 1, U + 1))

    for j in range(V + 1):
        for i in range(U + 1):
            x = pts2d[j, i, 0]
            y = pts2d[j, i, 1]
            test_pt = rg.Point3d(x, y, 0)

            t = Crv.ClosestPoint(test_pt)[1]
            cp = Crv.PointAt(t)
            distances[j, i] = test_pt.DistanceTo(cp)

    max_d = np.max(distances)
    if max_d == 0:
        max_d = 1.0

    falloff = distances / max_d
    falloff = 0.3 + 0.7 * (falloff ** 2)

    # --------------------------------------------------------
    # APPLY PERLIN HEIGHTMAP
    # --------------------------------------------------------

    Uu, Vv = np.meshgrid(np.linspace(0, 1, U + 1), np.linspace(0, 1, V + 1))
    noise = perlin(Uu * Scale, Vv * Scale)

    # Apply Z-offset (H)
    Z = H + noise * Amp * falloff

    # --------------------------------------------------------
    # CREATE 3D POINTS
    # --------------------------------------------------------
    Pts = []
    for j in range(V + 1):
        for i in range(U + 1):
            x = pts2d[j, i, 0]
            y = pts2d[j, i, 1]
            z = Z[j, i]
            Pts.append(rg.Point3d(x, y, z))

    # --------------------------------------------------------
    # CREATE NURBS SURFACE
    # --------------------------------------------------------
    Srf = rg.NurbsSurface.CreateFromPoints(Pts, U + 1, V + 1, 3, 3)

    # --------------------------------------------------------
    # Outputs
    # --------------------------------------------------------
    a = Srf
    b = Pts

import Rhino.Geometry as rg
import random
import math

EPS = 1e-9

# ------------------------------------------------------------
# Inputs (from Grasshopper)
# Srf, U, V, N, J, Seed
# AtP  : attractor points
# S_min, S_max : scaling domain
# ------------------------------------------------------------

random.seed(Seed)

Pts = []
OuterCrv = []   # original closed curves
InnerCrv = []   # scaled curves


# ------------------------------------------------------------
# EXIT IF NO SURFACE
# ------------------------------------------------------------
if Srf is None:
    a = []
    b = []
    c = []
else:

    # ---------------------------------------------
    # UV domain
    # ---------------------------------------------
    du = Srf.Domain(0)
    dv = Srf.Domain(1)
    u0, u1 = du.T0, du.T1
    v0, v1 = dv.T0, dv.T1

    # ============================================================
    # MODE A: TRIANGLES & QUADS
    # ============================================================
    if N in (3,4):

        du_step = (u1 - u0) / float(U)
        dv_step = (v1 - v0) / float(V)

        pts_grid = []

        for i in range(U+1):
            row = []
            for j in range(V+1):
                u = u0 + du_step * i
                v = v0 + dv_step * j

                if 0 < i < U and 0 < j < V and J > 0:
                    u += random.uniform(-0.5, 0.5) * J * du_step
                    v += random.uniform(-0.5, 0.5) * J * dv_step

                p = Srf.PointAt(u, v)
                row.append(p)
                Pts.append(p)
            pts_grid.append(row)

        def make_polyline(pts):
            if len(pts) < 3:
                return None
            pl = rg.Polyline(pts + [pts[0]])
            return pl.ToNurbsCurve()

        # QUADS
        if N == 4:
            for i in range(U):
                for j in range(V):
                    p00 = pts_grid[i][j]
                    p10 = pts_grid[i+1][j]
                    p11 = pts_grid[i+1][j+1]
                    p01 = pts_grid[i][j+1]
                    cr = make_polyline([p00, p10, p11, p01])
                    if cr:
                        OuterCrv.append(cr)

        # TRIANGLES
        if N == 3:
            for i in range(U):
                for j in range(V):

                    p00 = pts_grid[i][j]
                    p10 = pts_grid[i+1][j]
                    p11 = pts_grid[i+1][j+1]
                    p01 = pts_grid[i][j+1]

                    if (i + j) % 2 == 0:
                        tr1 = make_polyline([p00, p10, p11])
                        tr2 = make_polyline([p00, p11, p01])
                    else:
                        tr1 = make_polyline([p10, p11, p01])
                        tr2 = make_polyline([p10, p01, p00])

                    if tr1: OuterCrv.append(tr1)
                    if tr2: OuterCrv.append(tr2)


    # ============================================================
    # MODE B: REAL VORONOI
    # ============================================================
    elif N == 5:

        site_count = U * V
        sites = []

        for _ in range(site_count):
            u = random.uniform(u0, u1)
            v = random.uniform(v0, v1)
            sites.append((u, v))

        # Voronoi helpers ----------------------------------
        def perp_bisector(a, b):
            ax, ay = a
            bx, by = b
            if abs(ax - bx) < EPS and abs(ay - by) < EPS:
                return None
            mx = (ax + bx) / 2.0
            my = (ay + by) / 2.0
            dx = bx - ax
            dy = by - ay
            L = math.hypot(dx, dy)
            if L < EPS:
                return None
            A = dx / L
            B = dy / L
            C = -(A * mx + B * my)
            return A, B, C

        def same_side(pt, A, B, C, ref):
            x, y = pt
            rx, ry = ref
            s1 = A * x + B * y + C
            s2 = A * rx + B * ry + C
            if abs(s1) < EPS: return True
            return (s1 >= 0) == (s2 >= 0)

        def intersect(A, B, C, p1, p2):
            x1, y1 = p1
            x2, y2 = p2
            dx = x2 - x1
            dy = y2 - y1
            denom = A * dx + B * dy
            if abs(denom) < EPS:
                return None
            t = -(A * x1 + B * y1 + C) / denom
            if 0 <= t <= 1:
                return (x1 + t * dx, y1 + t * dy)
            return None

        def clip(poly, A, B, C, ref):
            out = []
            m = len(poly)
            for i in range(m):
                P = poly[i]
                Q = poly[(i+1) % m]
                Pin = same_side(P, A, B, C, ref)
                Qin = same_side(Q, A, B, C, ref)
                if Pin and Qin:
                    out.append(Q)
                elif Pin and not Qin:
                    ip = intersect(A, B, C, P, Q)
                    if ip: out.append(ip)
                elif not Pin and Qin:
                    ip = intersect(A, B, C, P, Q)
                    if ip: out.append(ip)
                    out.append(Q)
            return out

        # Build initial UV box
        box = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        cells = []

        for i, s in enumerate(sites):
            cell = list(box)
            for j, o in enumerate(sites):
                if i == j:
                    continue
                bis = perp_bisector(s, o)
                if bis is None:
                    continue
                A, B, C = bis
                cell = clip(cell, A, B, C, s)
                if not cell:
                    break
            cells.append(cell)

        # Make closed curves
        for poly in cells:
            if len(poly) < 3:
                continue

            pts3 = [Srf.PointAt(u, v) for (u, v) in poly]
            cr = rg.Polyline(pts3 + [pts3[0]]).ToNurbsCurve()
            OuterCrv.append(cr)

            for (u, v) in poly:
                Pts.append(Srf.PointAt(u, v))

        # Remove duplicate points
        unique = []
        tol_dup = 1e-6
        for p in Pts:
            if not any(p.DistanceTo(q) < tol_dup for q in unique):
                unique.append(p)
        Pts = unique


# ------------------------------------------------------------
# ATTRACTOR SCALING (InnerCrv)
# ------------------------------------------------------------

# Centroids via curve area if planar, otherwise via local Patch surface
centroids = []
tol = 1e-6

for cr in OuterCrv:
    cen = None

    if cr is not None:
        amp = None
        # First try area on the (planar) closed curve
        try:
            amp = rg.AreaMassProperties.Compute(cr)
        except:
            amp = None

        if amp:
            cen = amp.Centroid
        else:
            # If that fails (non-planar), build a Patch just for this curve
            # (equivalent to grafted Patch component in Grasshopper)
            patch = None
            try:
                patch = rg.Brep.CreatePatch([cr], 10, 10, tol)
            except:
                patch = None

            if patch:
                amp2 = rg.AreaMassProperties.Compute(patch)
                if amp2:
                    cen = amp2.Centroid

    centroids.append(cen)

# Distance to attractors
distances = []
for cen in centroids:
    if cen is None:
        distances.append(0.0)
    elif AtP and len(AtP) > 0:
        distances.append(min([cen.DistanceTo(a) for a in AtP]))
    else:
        distances.append(0.0)

# Normalize distances
if len(distances) > 1:
    d_min = min(distances)
    d_max = max(distances)
    delta = d_max - d_min if d_max != d_min else 1.0
else:
    d_min = 0.0
    delta = 1.0

# Scale each curve
InnerCrv = []
for cr, cen, d in zip(OuterCrv, centroids, distances):

    if cen is None or cr is None:
        InnerCrv.append(cr)
        continue

    t = (d - d_min) / delta        # normalized 0..1
    s = S_min + t * (S_max - S_min)

    x = rg.Transform.Scale(cen, s)
    new_cr = cr.DuplicateCurve()
    new_cr.Transform(x)
    InnerCrv.append(new_cr)

# ------------------------------------------------------------
# CREATE RULED SURFACES + EXTRUSION
# ------------------------------------------------------------

RuledSrfs = []
Extruded = []

for oc, ic, cen in zip(OuterCrv, InnerCrv, centroids):

    if oc is None or ic is None or cen is None:
        RuledSrfs.append(None)
        Extruded.append(None)
        continue

    # Duplicate & make sure curves are closed
    oc2 = oc.DuplicateCurve()
    ic2 = ic.DuplicateCurve()
    oc2.MakeClosed(1e-6)
    ic2.MakeClosed(1e-6)

    # LOFT (ruled)
    loft = rg.Brep.CreateFromLoft(
        [oc2, ic2],
        rg.Point3d.Unset,
        rg.Point3d.Unset,
        rg.LoftType.Straight,   # force ruled
        False
    )

    if not loft or len(loft) == 0:
        RuledSrfs.append(None)
        Extruded.append(None)
        continue

    ruled = loft[0]
    RuledSrfs.append(ruled)

    # --- EXTRUDE THE FACE ALONG WORLD Z ---
    try:
        face = ruled.Faces[0]
        vec  = rg.Vector3d(0, 0, H)

        # Path curve for extrusion (start at centroid, go in Z)
        path = rg.LineCurve(cen, cen + vec)

        # This returns a Brep (solid if cap = True and geometry allows it)
        ext = face.CreateExtrusion(path, True)
    except:
        ext = None

    Extruded.append(ext)


# ------------------------------------------------------------
# OUTPUTS
# ------------------------------------------------------------
a = Pts
b = OuterCrv
c = InnerCrv
d = RuledSrfs
e = Extruded

import Rhino.Geometry as rg
import random
import math

# Inputs:
# P    : list of base points
# T    : list of canopy points
# R    : radius per base
# L    : vertical step (branch length)
# Seed : random seed

random.seed(Seed)

Lines = []
Tips  = []


# ------------------------------------------------------------
# Normalize inputs
# ------------------------------------------------------------
# bases
if isinstance(P, rg.Point3d):
    bases = [P]
else:
    try:
        bases = list(P)
    except:
        bases = [P]

# canopy
if isinstance(T, rg.Point3d):
    canopy_all = [T]
else:
    try:
        canopy_all = list(T)
    except:
        canopy_all = [T]

# radii
if isinstance(R, (int, float)):
    radii = [float(R)] * len(bases)
else:
    radii = list(R)
    if len(radii) < len(bases):
        radii += [radii[-1]] * (len(bases) - len(radii))


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def dist_xy(a, b):
    return math.hypot(a.X - b.X, a.Y - b.Y)

def canopy_in_radius(center, r, pts):
    return [pt for pt in pts if dist_xy(center, pt) <= r]


# ------------------------------------------------------------
# Merge function with XY drift toward base
# ------------------------------------------------------------
def merge_points(a, b, base):
    """Merge two children a,b into a parent that drifts toward base."""
    avg_x = (a.X + b.X) * 0.5
    avg_y = (a.Y + b.Y) * 0.5
    new_z = min(a.Z, b.Z) - L

    # XY drift factor (0 = no drift, 1 = full snap to base)
    drift = 0.25

    drift_x = (base.X - avg_x) * drift
    drift_y = (base.Y - avg_y) * drift

    px = avg_x + drift_x
    py = avg_y + drift_y
    pz = new_z

    return rg.Point3d(px, py, pz)


def merge_three(a, b, c, base):
    """Merge 3 children once as special case."""
    avg_x = (a.X + b.X + c.X) / 3.0
    avg_y = (a.Y + b.Y + c.Y) / 3.0
    new_z = min(a.Z, b.Z, c.Z) - L

    drift = 0.25
    drift_x = (base.X - avg_x) * drift
    drift_y = (base.Y - avg_y) * drift

    px = avg_x + drift_x
    py = avg_y + drift_y
    pz = new_z

    return rg.Point3d(px, py, pz)


# ------------------------------------------------------------
# Bottom-up tree construction per column
# ------------------------------------------------------------
for idx, base in enumerate(bases):

    radius = radii[idx]

    # canopy points for this column
    local_canopy = canopy_in_radius(base, radius, canopy_all)

    # reserve them globally
    for pt in local_canopy:
        if pt in canopy_all:
            canopy_all.remove(pt)

    if len(local_canopy) == 0:
        # no canopy → single trunk
        top = rg.Point3d(base.X, base.Y, base.Z + L)
        Lines.append(rg.Line(base, top).ToNurbsCurve())
        continue

    # create leaf nodes that lean toward the base (NOT random jitter)
    drift_strength = 0.35  # how strongly leaves point toward base
    tiny_jitter = L * 0.05  # small noise only for natural look

    leaves = []
    parent_map = {}

    for t in local_canopy:

        # horizontal direction from canopy point to base
        dir_x = base.X - t.X
        dir_y = base.Y - t.Y

        # normalize horizontal direction
        d = math.hypot(dir_x, dir_y)
        if d > 1e-6:
            dir_x /= d
            dir_y /= d
        else:
            dir_x = 0
            dir_y = 0

        # scale drift by drift_strength * L
        pull_x = dir_x * drift_strength * L
        pull_y = dir_y * drift_strength * L

        # tiny natural randomness
        jx = random.uniform(-tiny_jitter, tiny_jitter)
        jy = random.uniform(-tiny_jitter, tiny_jitter)

        # final leaf point BELOW the canopy
        leaf = rg.Point3d(
            t.X + pull_x + jx,
            t.Y + pull_y + jy,
            t.Z - L
        )

        leaves.append(leaf)
        parent_map[leaf] = t


    # start merging
    nodes = list(leaves)
    triple_used = False

    while len(nodes) > 1:

        nodes.sort(key=lambda p: (p.Z, p.X, p.Y))
        new_nodes = []

        i = 0
        while i < len(nodes):

            # Triple merge: only once, only if 3 remain
            if (len(nodes) - i == 3) and (not triple_used):
                a, b, c = nodes[i], nodes[i+1], nodes[i+2]
                parent = merge_three(a, b, c, base)

                Lines.append(rg.Line(parent, a).ToNurbsCurve())
                Lines.append(rg.Line(parent, b).ToNurbsCurve())
                Lines.append(rg.Line(parent, c).ToNurbsCurve())

                new_nodes.append(parent)
                triple_used = True
                i += 3
                continue

            # Pair merge
            if i + 1 < len(nodes):
                a, b = nodes[i], nodes[i+1]
                parent = merge_points(a, b, base)

                Lines.append(rg.Line(parent, a).ToNurbsCurve())
                Lines.append(rg.Line(parent, b).ToNurbsCurve())

                new_nodes.append(parent)
                i += 2
            else:
                # lone node → push downward
                a = nodes[i]
                parent = rg.Point3d(a.X, a.Y, a.Z - L)
                Lines.append(rg.Line(parent, a).ToNurbsCurve())
                new_nodes.append(parent)
                i += 1

        nodes = new_nodes

    # final root above trunk
    root = nodes[0]

    # connect base → root directly (no correction line!)
    Lines.append(rg.Line(base, root).ToNurbsCurve())

    # add final vertical-ish canopy links
    for leaf, canopy_pt in parent_map.items():
        Lines.append(rg.Line(leaf, canopy_pt).ToNurbsCurve())
        Tips.append(canopy_pt)

# ------------------------------------------------------------
# CREATE RECTANGULAR PIPES ON EACH LINE (W × H from inputs)
# ------------------------------------------------------------

Pipes = []

def rect_profile(w, h):
    hw = w * 0.5
    hh = h * 0.5
    pts = [
        rg.Point3d(-hw, -hh, 0),
        rg.Point3d(hw, -hh, 0),
        rg.Point3d(hw, hh, 0),
        rg.Point3d(-hw, hh, 0),
        rg.Point3d(-hw, -hh, 0)
    ]
    return rg.Polyline(pts).ToNurbsCurve()


for ln in Lines:

    if ln is None:
        Pipes.append(None)
        continue

    # Start & direction
    s = ln.PointAtStart
    e = ln.PointAtEnd
    vec = e - s

    if vec.IsTiny():
        Pipes.append(None)
        continue

    # Orientation plane for profile
    plane = rg.Plane(s, vec)

    # Create profile aligned with the line
    prof = rect_profile(W, H)    # <--- using your GH inputs W and H
    prof2 = prof.DuplicateCurve()
    xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane)
    prof2.Transform(xform)

    # Sweep
    sweep = rg.SweepOneRail()
    breps = sweep.PerformSweep(ln, prof2)

    if breps and len(breps) > 0:
        b = breps[0]

        # Cap ends
        capped = b.CapPlanarHoles(0.001)
        if capped:
            Pipes.append(capped)
        else:
            Pipes.append(b)
    else:
        Pipes.append(None)


# outputs
a = Lines
b = Tips
c = Pipes