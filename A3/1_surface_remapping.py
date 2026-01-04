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
