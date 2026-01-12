"""
Assignment 2: Fractal Generator

Author: Simon Nguyen

Description:
This script generates fractal patterns using recursive functions and geometric transformations.
"""

import math
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from shapely.affinity import rotate, scale, translate
import matplotlib.colors as mcolors
import numpy as np

#------------------------------------------------------------------------------------------------------#
# Smooth curve generator using quadratic Bezier curves
def make_curve(start, end, curvature, direction):

    """
    Generate a quadratic Bezier curve between start and end.
    curvature: how much the curve deviates from straight line
    direction: alternates bulge direction for recursive symmetry
    """

    x1, y1 = start # start point
    x2, y2 = end # end point
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 # midpoint

    dx, dy = x2 - x1, y2 - y1 # direction vector
    length = np.hypot(dx, dy) 
    nx, ny = -dy / length, dx / length # normal vector

    # control point
    cx = mx + nx * length * curvature * direction
    cy = my + ny * length * curvature * direction

    # Bezier
    t = np.linspace(0, 1, 20)
    xs = (1 - t)**2 * x1 + 2*(1 - t)*t*cx + t**2 * x2 # x coordinates
    ys = (1 - t)**2 * y1 + 2*(1 - t)*t*cy + t**2 * y2 # y coordinates

    return LineString(np.column_stack([xs, ys])) # return LineString

#------------------------------------------------------------------------------------------------------#

# globals
line_list = []
depth_list = []

#------------------------------------------------------------------------------------------------------#

# Golden Ratio Dragon generator
def generate_golden_ratio_dragon(x1, y1, x2, y2, turn, n, points):

    """
    Recursive φ-based dragon curve.
    Uses irrational scaling and rotation derived from the golden ratio to avoid exact repetition.
    """

    golden_ratio = (1 + 5**0.5) / 2
    r1 = r = (1 / golden_ratio)**(1 / golden_ratio)
    r2 = r1**2
    angle1 = math.acos((1 + r**2 - r**4) / (2 * r))
    angle2 = math.acos((1 + r**4 - r**2) / (2 * r**2))

    dist = math.hypot(x2 - x1, y2 - y1)
    if n <= 0 or dist < 1:
        points.append((x2, y2))
        return

    angle = math.atan2(y2 - y1, x2 - x1)
    if turn:
        px = x1 + dist * r1 * math.cos(angle + angle1)
        py = y1 + dist * r1 * math.sin(angle + angle1)
    else:
        px = x1 + dist * r2 * math.cos(angle - angle2)
        py = y1 + dist * r2 * math.sin(angle - angle2)

    generate_golden_ratio_dragon(x1, y1, px, py, True, n - 1, points)
    generate_golden_ratio_dragon(px, py, x2, y2, False, n - 1, points)

#------------------------------------------------------------------------------------------------------#

# Recursive dragon generator
def generate_dragon(segment, depth, max_depth, angle_deg, scale_factor, turn_left=True, curvature=0.2, direction=1):

    """
    Recursively generate a dragon curve segment.
    Each segment is rotated, scaled, and split into two curves.
    """

    if depth >= max_depth:
        line_list.append(segment)
        depth_list.append(depth)
        return

    start, end = segment.coords[0], segment.coords[-1]
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    
    # determine rotation angle
    angle = angle_deg if turn_left else -angle_deg
    
    # transform segment
    seg = rotate(segment, angle, origin=mid)
    seg = scale(seg, xfact=scale_factor, yfact=scale_factor, origin=mid)

    new_pt = seg.coords[-1]
    
    # split segments into two parts
    a1 = make_curve(start, new_pt, curvature=curvature, direction=direction)
    a2 = make_curve(new_pt, end, curvature=curvature, direction=-direction)

    # Recursive calls
    generate_dragon(a1, depth + 1, max_depth, angle_deg, scale_factor, True, curvature, -direction)
    generate_dragon(a2, depth + 1, max_depth, angle_deg, scale_factor, False, curvature, direction)

#------------------------------------------------------------------------------------------------------#

# morphing function
def morph_dragon(segment, depth, max_depth, morph, curvature=0.0, direction=1):

    """
    Morph dragon between Heighway and Golden Ratio forms using parameter blending.
    """

    # compute blended scale and angle based on φ relationship
    golden_ratio = (1 + 5**0.5) / 2
    r = (1 / golden_ratio)**(1 / golden_ratio)
    r2 = r**2
    angle_phi = math.degrees(math.acos((1 + r**2 - r**4) / (2 * r)))  # ~85.25°
    scale_phi = r  # main scale for the Golden Ratio Dragon

    # nonlinear blend (ease-in curve)
    m = morph**1.5
    angle_deg = (90 * (1 - m) + angle_phi * m)
    scale_factor = (1.0 * (1 - m) + scale_phi * m)

    generate_dragon(segment, depth, max_depth, angle_deg, scale_factor, turn_left=True, curvature=curvature, direction=direction)

#------------------------------------------------------------------------------------------------------#

# Plotting
import os

def plot_dragon(max_depth, dragon_type, curvature, figsize=(11, 7), segment_subdiv=1, morph=None):
    import matplotlib.collections as mcoll

    """
    Collect segments, apply gradient coloring, and save image.
    """

    segs = []
    seg_lengths = []

    for LS in line_list:
        x, y = np.asarray(LS.xy)
        for i in range(len(x) - 1):
            x0, y0 = x[i], y[i]
            x1, y1 = x[i+1], y[i+1]
            for s in range(segment_subdiv):
                t0 = s / segment_subdiv
                t1 = (s + 1) / segment_subdiv
                p0 = (x0 * (1 - t0) + x1 * t0, y0 * (1 - t0) + y1 * t0)
                p1 = (x0 * (1 - t1) + x1 * t1, y0 * (1 - t1) + y1 * t1)
                segs.append((p0, p1))
                seg_lengths.append(math.hypot(p1[0] - p0[0], p1[1] - p0[1]))

    seg_lengths = np.array(seg_lengths, dtype=float)
    total_len = seg_lengths.sum() if seg_lengths.sum() != 0 else 1.0
    cum = np.concatenate(([0.0], np.cumsum(seg_lengths)))
    mids = (cum[:-1] + cum[1:]) * 0.5 / total_len

    colors = ["#9be64a", "#2dd2e5", "#6b4be8"]
    cmap = mcolors.LinearSegmentedColormap.from_list("green_blue_purple", colors)
    norm = mcolors.Normalize(0.0, 1.0)
    seg_colors = [cmap(norm(m)) for m in mids]

    lc = mcoll.LineCollection(
        segs, colors=seg_colors,
        linewidths=np.clip(1.6 * (1 - mids) + 0.5, 0.5, 0.5),
        linestyles='solid', capstyle='round', joinstyle='round', zorder=2
    )

    fig, ax = plt.subplots(figsize=figsize, facecolor="black")
    ax.set_facecolor("black")
    ax.add_collection(lc)

    all_x = np.hstack([p[0] for seg in segs for p in seg])
    all_y = np.hstack([p[1] for seg in segs for p in seg])
    if all_x.size and all_y.size:
        minx, maxx = all_x.min(), all_x.max()
        miny, maxy = all_y.min(), all_y.max()
        padx = 0.04 * (maxx - minx if maxx > minx else 1.0)
        pady = 0.04 * (maxy - miny if maxy > miny else 1.0)
        ax.set_xlim(minx - padx, maxx + padx)
        ax.set_ylim(miny - pady, maxy + pady)

    ax.set_aspect('equal', 'box')
    plt.axis('off')
    fig.text(0.5, 0.03,
         f"Dragon Type: {dragon_type.capitalize()}   |   Iteration: {max_depth}   |   Curvature: {curvature}   |   Morph: {morph}",
         ha='center', va='center', color='white', fontsize=12, family='sans-serif')
    plt.tight_layout()

    # Save image
    os.makedirs("images", exist_ok=True)
    morph_str = f"{morph:.2f}" if morph is not None else "NA"
    filename = f"{dragon_type}_depth{max_depth}_morph{morph_str}_curv{curvature}.png"
    filepath = os.path.join("images", filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor="black")
    print(f"✅ Saved: {filepath}")

    plt.close(fig)

#------------------------------------------------------------------------------------------------------#

# dragon presets
presets = {
    "heighway": {"angle_deg": 90, "scale": 1.0},
    "terdragon": {"angle_deg": 120, "scale": 1 / math.sqrt(3)},
    "golden_ratio": {"angle_deg": None, "scale": None},  # uses phi-based recursion
}

#------------------------------------------------------------------------------------------------------#

# Main execution
if __name__ == "__main__":
    start, end = (0, 0), (100, 0)
    segment = LineString([start, end])

    # Parameters
    # ------------------------------------------------ #

    max_depth = 10
    curvature = 0
    direction = 1
    morph = 1  # 0 = Heighway, 1 = Golden Ratio
    dragon_type = "heighway" if morph == 0 else "golden_ratio" if morph == 1 else "beyond experiment"

    # ------------------------------------------------ #

    line_list.clear()
    depth_list.clear()

    if dragon_type == "golden_ratio":
        points = [(0, 0)]
        generate_golden_ratio_dragon(0, 0, 500, 0, True, max_depth, points)
        curve = LineString(points)
        line_list.append(curve)
        plot_dragon(max_depth, dragon_type, curvature, morph=morph)

    elif dragon_type in ("heighway", "terdragon"):
        preset = presets[dragon_type]
        generate_dragon(segment, 0, max_depth, preset["angle_deg"], preset["scale"],
                    True, curvature, direction)
        plot_dragon(max_depth, dragon_type, curvature, morph=morph)

    else:
        morph_dragon(segment, 0, max_depth, morph, curvature, direction)
        plot_dragon(max_depth, f"beyond experiment", curvature, morph=morph)

#------------------------------------------------------------------------------------------------------#
