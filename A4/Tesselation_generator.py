import Rhino.Geometry as rg
import math

EPS = 1e-9

# ------------------------------------------------------------
# Inputs (from Grasshopper):
#   Srf       : surface or brep
#   AgentPts  : list of points
# Outputs:
#   a : Voronoi cell curves on surface
#   b : cell center points
# ------------------------------------------------------------

CellCrvs = []
Centers  = []

# ------------------------------------------------------------
# GUARD: if no data, just output empty lists
# ------------------------------------------------------------
if Srf is None or AgentPts is None or len(AgentPts) == 0:
    a = []
    b = []
else:
    # --------------------------------------------------------
    # 1) Get a single surface face to work with
    # --------------------------------------------------------
    if isinstance(Srf, rg.Brep):
        face = Srf.Faces[0]
    else:
        face = Srf

    # UV domain of the surface
    du = face.Domain(0)
    dv = face.Domain(1)
    u0, u1 = du.T0, du.T1
    v0, v1 = dv.T0, dv.T1

    # --------------------------------------------------------
    # 2) Map AgentPts to UV (parameter space)
    # --------------------------------------------------------
    sites = []
    for p in AgentPts:
        ok, u, v = face.ClosestPoint(p)
        if ok:
            sites.append((u, v))

    # If fewer than 2 sites, no Voronoi
    if len(sites) < 2:
        a = []
        b = []
    else:
        # ----------------------------------------------------
        # 3) Voronoi helper functions (same as your example)
        # ----------------------------------------------------
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
            if abs(s1) < EPS:
                return True
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
                Q = poly[(i + 1) % m]
                Pin = same_side(P, A, B, C, ref)
                Qin = same_side(Q, A, B, C, ref)

                if Pin and Qin:
                    out.append(Q)
                elif Pin and not Qin:
                    ip = intersect(A, B, C, P, Q)
                    if ip:
                        out.append(ip)
                elif not Pin and Qin:
                    ip = intersect(A, B, C, P, Q)
                    if ip:
                        out.append(ip)
                    out.append(Q)
            return out

        # ----------------------------------------------------
        # 4) Build initial UV-domain box & compute cells
        # ----------------------------------------------------
        uv_box = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        cells = []

        for i, s in enumerate(sites):
            cell = list(uv_box)
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

        # ----------------------------------------------------
        # 5) Convert each UV cell to 3D curve on surface
        #    + compute a simple center point
        # ----------------------------------------------------
        for poly in cells:
            if len(poly) < 3:
                continue

            # UV -> 3D
            pts3 = [face.PointAt(u, v) for (u, v) in poly]
            crv = rg.Polyline(pts3 + [pts3[0]]).ToNurbsCurve()
            CellCrvs.append(crv)

            # center = average of vertices
            cx = sum(p.X for p in pts3) / len(pts3)
            cy = sum(p.Y for p in pts3) / len(pts3)
            cz = sum(p.Z for p in pts3) / len(pts3)
            Centers.append(rg.Point3d(cx, cy, cz))

        # ----------------------------------------------------
        # 6) Assign to Grasshopper outputs
        # ----------------------------------------------------
        a = CellCrvs
        b = Centers
