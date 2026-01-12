import Rhino.Geometry as rg

# ------------------------------------------------------------
# Agent class
# ------------------------------------------------------------

class Agent(object):
    def __init__(self, u, v, surface, i, j, idx):
        # param space
        self.u = u
        self.v = v
        self.u0 = u  # home UV
        self.v0 = v

        # grid indices
        self.i = i   # col index
        self.j = j   # row index

        # bookkeeping
        self.idx = idx
        self.is_active = True
        self.still_steps = 0

        # 3D position
        self.pos = surface.PointAt(u, v)

    def update_position(self, surface):
        self.pos = surface.PointAt(self.u, self.v)


# ------------------------------------------------------------
# Build agents from input points + grid size
# ------------------------------------------------------------

def init_agents(surface, pts, u_count, v_count):
    agents = []
    agent_pts = []

    if surface is None or pts is None:
        return [], []

    # make sure we work with a Surface
    if hasattr(surface, "ToNurbsSurface"):
        surface = surface.ToNurbsSurface()

    total = len(pts)
    expected = u_count * v_count

    if total != expected:
        # you can print a warning if you want:
        # print("Warning: len(Pts) != Ucnt*Vcnt ({} vs {})".format(total, expected))
        pass

    for idx, p in enumerate(pts):
        # robust Point3d conversion
        if isinstance(p, rg.Point3d):
            pt = p
        else:
            pt = rg.Point3d(p[0], p[1], p[2])

        # find UV on surface
        res = surface.ClosestPoint(pt)
        if res is None:
            continue

        success, u, v = res
        if not success:
            continue

        # compute grid indices from idx
        i = idx % u_count   # column
        j = idx // u_count  # row

        ag = Agent(u, v, surface, i, j, idx)
        agents.append(ag)
        agent_pts.append(ag.pos)

    return agents, agent_pts


# ------------------------------------------------------------
# Grasshopper execution
# ------------------------------------------------------------

if Srf is None or Pts is None or Ucnt is None or Vcnt is None:
    Agents = []
    AgentPts = []
else:
    Agents, AgentPts = init_agents(Srf, Pts, Ucnt, Vcnt)
