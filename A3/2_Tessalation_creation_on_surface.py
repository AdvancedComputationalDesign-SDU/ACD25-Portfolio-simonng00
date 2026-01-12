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
