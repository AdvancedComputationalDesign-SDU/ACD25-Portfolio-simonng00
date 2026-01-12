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