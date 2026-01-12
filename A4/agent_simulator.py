import Rhino.Geometry as rg
import scriptcontext as sc

# ------------------------------------------------------------
# Curvature + principal direction sampling (RhinoCommon)
# ------------------------------------------------------------

def sample_curvature_and_direction(surface, u, v):
    """
    Returns:
        curv_mag : float      (max of |k0|, |k1|)
        dir_vec  : Vector3d   (principal direction of max curvature, unit)
    """
    scurv = surface.CurvatureAt(u, v)
    if scurv is None:
        return 0.0, rg.Vector3d(0, 0, 0)

    try:
        k0 = abs(scurv.Kappa(0))
        k1 = abs(scurv.Kappa(1))
    except:
        k0 = 0.0
        k1 = 0.0

    curv_mag = max(k0, k1)

    dir0 = scurv.Direction(0)
    dir1 = scurv.Direction(1)

    if k0 >= k1:
        dir_vec = dir0
    else:
        dir_vec = dir1

    if dir_vec is None or (not dir_vec.IsValid) or dir_vec.Length <= 1e-9:
        dir_vec = rg.Vector3d(0, 0, 0)
    else:
        dir_vec.Unitize()

    return curv_mag, dir_vec


# ------------------------------------------------------------
# Slope sampling (uphill direction on a heightmap-like surface)
# ------------------------------------------------------------

def sample_slope_direction(surface, u, v):
    """
    Approximate local uphill direction on the surface:
    - assumes Z encodes 'height'
    - returns a 3D unit vector tangent to the surface
    """
    dom_u = surface.Domain(0)
    dom_v = surface.Domain(1)
    du = 0.01 * (dom_u.T1 - dom_u.T0)
    dv = 0.01 * (dom_v.T1 - dom_v.T0)

    # center point
    p = surface.PointAt(u, v)

    # small steps in param space
    u1 = min(dom_u.T1, max(dom_u.T0, u + du))
    v1 = min(dom_v.T1, max(dom_v.T0, v + dv))

    pu = surface.PointAt(u1, v)   # step in u
    pv = surface.PointAt(u, v1)   # step in v

    # tangent vectors
    tu = pu - p
    tv = pv - p

    # Z-change along each tangent direction
    dz_du = pu.Z - p.Z
    dz_dv = pv.Z - p.Z

    # uphill vector in tangent basis
    uphill = rg.Vector3d(
        tu.X * dz_du + tv.X * dz_dv,
        tu.Y * dz_du + tv.Y * dz_dv,
        tu.Z * dz_du + tv.Z * dz_dv
    )

    if uphill.Length <= 1e-9:
        return rg.Vector3d(0, 0, 0)

    uphill.Unitize()
    return uphill   # downhill = -uphill


# ------------------------------------------------------------
# Helper: minimum neighbor distance
# ------------------------------------------------------------

def min_neighbor_distance(agent, agents):
    d_min = float("inf")
    for other in agents:
        if other is agent:
            continue
        d = agent.pos.DistanceTo(other.pos)
        if d < d_min:
            d_min = d
    if d_min == float("inf"):
        d_min = 1e9
    return d_min


# ------------------------------------------------------------
# One simulation step for a single agent
# ------------------------------------------------------------

def step_agent(agent, surface, agents,
               base_step, curv_weight, curv_scale,
               neigh_radius, neigh_weight,
               still_steps_limit, min_spacing,
               home_weight,
               slope_inf, slope_mode):

    # init dynamic attributes if not present
    if not hasattr(agent, "still_steps"):
        agent.still_steps = 0
    if not hasattr(agent, "is_active"):
        agent.is_active = True

    if not agent.is_active:
        return

    # --- sense curvature + direction ---
    curv_mag, curv_dir = sample_curvature_and_direction(surface, agent.u, agent.v)
    if curv_dir.Length == 0.0:
        agent.is_active = False
        return

    if curv_scale is None or curv_scale <= 1e-9:
        curv_scale = 1.0

    # slower in high curvature if curv_weight > 0
    t = min(curv_mag / curv_scale, 1.0)
    speed_factor = 1.0 - curv_weight * t
    step_len = base_step * max(speed_factor, 0.0)

    # --- blend curvature direction with slope direction ---
    # slope_inf in [0,1], slope_mode in [-1,0,1] (or between)
    slope_inf = max(0.0, min(1.0, slope_inf))
    # we don't hard clamp slope_mode, but you can if you want:
    # slope_mode = max(-1.0, min(1.0, slope_mode))

    final_dir = curv_dir

    if abs(slope_mode) > 1e-6 and slope_inf > 1e-6:
        uphill = sample_slope_direction(surface, agent.u, agent.v)
        if uphill.Length > 0.0:
            # downhill if slope_mode < 0, uphill if slope_mode > 0
            slope_dir = uphill * slope_mode
            # blend directions: (1 - slope_inf)*curv_dir + slope_inf*slope_dir
            blended = rg.Vector3d(
                curv_dir.X * (1.0 - slope_inf) + slope_dir.X * slope_inf,
                curv_dir.Y * (1.0 - slope_inf) + slope_dir.Y * slope_inf,
                curv_dir.Z * (1.0 - slope_inf) + slope_dir.Z * slope_inf
            )
            if blended.Length > 1e-9:
                blended.Unitize()
                final_dir = blended

    # base movement from direction field (curvature + optional slope)
    move_vec = final_dir * step_len

    # --- neighbor repulsion for spacing ---
    if neigh_weight > 0.0 and neigh_radius > 0.0:
        rep_vec = rg.Vector3d(0, 0, 0)
        count = 0

        for other in agents:
            if other is agent:
                continue

            d = agent.pos.DistanceTo(other.pos)
            if d < neigh_radius and d > 1e-6:
                v = agent.pos - other.pos
                v.Unitize()
                strength = 1.0 - (d / neigh_radius)
                rep_vec += v * strength
                count += 1

        if count > 0:
            rep_vec /= count
            rep_vec *= (neigh_weight * base_step)
            move_vec += rep_vec

    # --- home spring: softly pull back toward original grid position ---
    if home_weight > 0.0 and hasattr(agent, "u0") and hasattr(agent, "v0"):
        home_pt = surface.PointAt(agent.u0, agent.v0)
        spring_vec = home_pt - agent.pos
        spring_vec *= home_weight   # scale the pull
        move_vec += spring_vec

    # --- spacing check: nearest neighbor distance ---
    d_min = min_neighbor_distance(agent, agents)

    # convergence: good spacing for several steps in a row
    if d_min >= min_spacing:
        agent.still_steps += 1
    else:
        agent.still_steps = 0

    if agent.still_steps >= still_steps_limit:
        agent.is_active = False
        return

    # --- move in 3D, project back to surface ---
    new_pt = agent.pos + move_vec
    ok, u_new, v_new = surface.ClosestPoint(new_pt)
    if not ok:
        agent.is_active = False
        return

    agent.u = u_new
    agent.v = v_new

    if hasattr(agent, "update_position"):
        agent.update_position(surface)
    else:
        agent.pos = surface.PointAt(agent.u, agent.v)


# ------------------------------------------------------------
# Grasshopper execution
# ------------------------------------------------------------

AgentsOut = []
AgentPts = []
Dbg = ""
Done = False

if Srf is None or AgentsIn is None:
    Dbg = "No surface or agents."
else:
    # defaults
    if Steps is None:           Steps = 1
    if MaxSteps is None:        MaxSteps = 100
    if BaseStep is None:        BaseStep = 0.1
    if CurvWeight is None:      CurvWeight = 0.5
    if CurvScale is None:       CurvScale = 1.0
    if NeighborRadius is None:  NeighborRadius = 0.0
    if NeighborWeight is None:  NeighborWeight = 0.0
    if StillSteps is None:      StillSteps = 5
    if MinSpacing is None:      MinSpacing = 0.5
    if HomeWeight is None:      HomeWeight = 0.2   # gentle tether
    if SlopeInf is None:        SlopeInf = 0.0     # no slope by default
    if SlopeMode is None:       SlopeMode = 0.0    # off by default

    key = "agents_state"
    step_key = "agents_total_steps"
    done_key = "agents_done"

    state_missing = (key not in sc.sticky) or (step_key not in sc.sticky) or (done_key not in sc.sticky)

    # --- reset or continue global state ---
    if Reset or state_missing:
        agents = list(AgentsIn)   # fresh from builder
        total_steps = 0
        done_flag = False
    else:
        agents = sc.sticky[key]
        total_steps = sc.sticky[step_key]
        done_flag = sc.sticky[done_key]

    # --- run simulation only if under global MaxSteps, not resetting, and not already done ---
    if (not Reset) and (not done_flag) and (total_steps < MaxSteps):
        for _ in range(Steps):
            if total_steps >= MaxSteps or done_flag:
                break

            # one global step: update all agents
            for ag in agents:
                step_agent(ag, Srf, agents,
                           BaseStep, CurvWeight, CurvScale,
                           NeighborRadius, NeighborWeight,
                           StillSteps, MinSpacing,
                           HomeWeight,
                           SlopeInf, SlopeMode)
            total_steps += 1

            # check how many are still active
            active_count_step = sum(1 for a in agents if getattr(a, "is_active", True))
            if active_count_step == 0:
                done_flag = True
                break
    else:
        active_count_step = sum(1 for a in agents if getattr(a, "is_active", True))

    # store updated state
    sc.sticky[key] = agents
    sc.sticky[step_key] = total_steps
    sc.sticky[done_key] = done_flag

    # outputs
    AgentsOut = agents
    AgentPts = [ag.pos for ag in agents]
    active_count = sum(1 for a in agents if getattr(a, "is_active", True))
    Done = done_flag

    if done_flag:
        Dbg = "DONE ✅ | Total steps: {} | All agents satisfied spacing ≥ {}.".format(
            total_steps, MinSpacing)
    elif total_steps >= MaxSteps:
        Dbg = "STOP (MaxSteps) ⚠ | Total steps: {} / {} | Active agents: {}".format(
            total_steps, MaxSteps, active_count)
    else:
        Dbg = "Running… | Total steps: {} / {} | Active agents: {} | MinSpacing: {} | HomeWeight: {} | SlopeInf: {} | SlopeMode: {}".format(
            total_steps, MaxSteps, active_count, MinSpacing, HomeWeight, SlopeInf, SlopeMode)
