"""
Assignment 2: Fractal Generator

Author: Simon Nguyen

Description:
This script generates fractal patterns using recursive functions and geometric transformations.
"""

import math
import random
import matplotlib.pyplot as plt
from shapely.geometry import LineString

#------------------------------------------------------------------------------------------------------#
# grammar rule
#------------------------------------------------------------------------------------------------------#

def evolve_sequence(seq):
    """
    Duplicate sequence and append a right turn.
    Basic generative rule: S -> S S R
    """
    return seq + seq + ["R"]

#------------------------------------------------------------------------------------------------------#
# randomness application
#------------------------------------------------------------------------------------------------------#

def apply_randomness_chunked(seq, randomness, chunk_size=6):
    """
    Apply randomness in blocks rather than symbol-by-symbol noise.
    randomness: probability of flipping a whole chunk
    chunk_size: number of consecutive turns affected together
    """
    if randomness <= 0:
        return seq

    new = seq[:]
    i = 0

    while i < len(new):
        if random.random() < randomness:
            for j in range(i, min(i + chunk_size, len(new))):
                new[j] = "R" if new[j] == "L" else "L"
        i += chunk_size

    return new

#------------------------------------------------------------------------------------------------------#
# Spatial Influence
#------------------------------------------------------------------------------------------------------#

def apply_spatial_influence(
    x, y, heading,
    attractor_point,
    strength,
    mode,
    step
):
    """
    Modify heading or step length based on spatial fields.
    Modes:
      - "rotate": vortex-like angular field
      - "repel": pushes curve away from attractor point
      - "oscillate": sine-based angular modulation
      - "scale_step": compress or expand step length based on distance
    """

    if strength <= 0 or mode == "none":
        return heading, step

    ax, ay = attractor_point

    dx = ax - x
    dy = ay - y
    distance = math.hypot(dx, dy) + 1e-6       # avoid zero division
    desired = math.atan2(dy, dx)               # direction to attractor
    diff = (desired - heading + math.pi) % (2*math.pi) - math.pi

    # rotation field (vortex)
    if mode == "rotate":
        rotation = strength * (1.0 / distance)
        heading += rotation

    # repulsion field
    elif mode == "repel":
        repel_force = diff * (-strength)
        heading += repel_force

    # oscillation field
    elif mode == "oscillate":
        heading += math.sin(distance * 0.05) * strength

    # distance scaling
    elif mode == "scale_step":
        falloff = max(0.1, min(3.0, 1 + strength * (distance / 100.0)))
        step *= falloff

    return heading, step

#------------------------------------------------------------------------------------------------------#
# Sequence to Points Conversion
#------------------------------------------------------------------------------------------------------#

def sequence_to_points(
    seq,
    step=2,
    angle_deg=90,
    attractor_point=(0, 0),
    attractor_strength=0.0,
    mode="none"
):
    """
    Convert L/R grammar into a polyline, optionally affected by spatial fields.
    """

    x, y = 0.0, 0.0
    heading = 0.0
    pts = [(x, y)]

    angle = math.radians(angle_deg)

    for cmd in seq:

        # grammar turn
        if cmd == "L": heading += angle
        elif cmd == "R": heading -= angle

        # spatial field influence
        heading, step = apply_spatial_influence(
            x, y, heading,
            attractor_point,
            attractor_strength,
            mode,
            step
        )

        # forward step
        x += step * math.cos(heading)
        y += step * math.sin(heading)
        pts.append((x, y))

    return pts

#------------------------------------------------------------------------------------------------------#
# Chaikin Smoothing
#------------------------------------------------------------------------------------------------------#

def chaikin(points, iterations=2):
    """
    Apply Chaikin corner-cutting to smooth geometry.
    """
    for _ in range(iterations):
        new_pts = []
        for i in range(len(points) - 1):
            p0, p1 = points[i], points[i + 1]
            Q = (0.75*p0[0] + 0.25*p1[0], 0.75*p0[1] + 0.25*p1[1])
            R = (0.25*p0[0] + 0.75*p1[0], 0.25*p0[1] + 0.75*p1[1])
            new_pts.extend([Q, R])
        points = new_pts
    return points

#------------------------------------------------------------------------------------------------------#
# Fractal Generator
#------------------------------------------------------------------------------------------------------#

def generate_fractal(
    iterations=6,
    step=2,
    angle_deg=90,
    start_sequence=None,
    smoothing=False,
    smooth_iterations=2,
    randomness=0.0,
    seed=None,
    attractor_point=(0, 0),
    attractor_strength=0.0,
    chunk_size=6,
    mode="none"
):
    """
    Generate fractal defined by:
      - grammar evolution (evolve_sequence)
      - chunk-based randomness
      - spatial influence fields
      - optional smoothing
    """

    if seed is not None:
        random.seed(seed)

    if start_sequence is None:
        start_sequence = ["L", "R", "R", "R", "R", "L", "L"]

    seq = start_sequence[:]

    # grammar evolution
    for _ in range(iterations):
        seq = evolve_sequence(seq)
        seq = apply_randomness_chunked(seq, randomness, chunk_size)

    # geometry conversion
    pts = sequence_to_points(
        seq,
        step,
        angle_deg,
        attractor_point,
        attractor_strength,
        mode
    )

    # optional smoothing
    if smoothing:
        pts = chaikin(pts, iterations=smooth_iterations)

    return LineString(pts)

#------------------------------------------------------------------------------------------------------#
# Plotting
#------------------------------------------------------------------------------------------------------#

from io import BytesIO
from PIL import Image, ImageFilter, ImageChops, ImageEnhance, ImageDraw
from PIL import ImageFont

def plot_linestring(
    ls, iterations, angle_deg, smooth_iterations, randomness,
    seed, attractor_point, attractor_strength, chunk_size, mode,
    motion_blur_strength=5,
    motion_blur_steps=15,
    blur_opacity=0.30
):

    figsize = (9, 9)
    dpi = 200

    xs, ys = ls.xy
    lw = max(0.1, 2.0 / (iterations + 1))  # crisp line thickness

# render to transparent image buffer

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.plot(xs, ys, color="white", linewidth=lw)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True,
                bbox_inches=None, pad_inches=0)
    plt.close(fig)
    buf.seek(0)

    crisp_fractal = Image.open(buf).convert("RGBA")

# create motion blur effect

    blur_accum = Image.new("RGBA", crisp_fractal.size, (0, 0, 0, 0))

    for i in range(motion_blur_steps):
        offset = int((i - motion_blur_steps // 2) * motion_blur_strength)
        shifted = ImageChops.offset(crisp_fractal, offset, offset)

        # Brightness fade (same as before)
        fade_brightness = 1.0 - (abs(i - motion_blur_steps/ 2) / motion_blur_steps)
        shifted = ImageEnhance.Brightness(shifted).enhance(fade_brightness)

        # linear decay:
        fade_alpha = 1.0 - (i / motion_blur_steps)

        # apply global opacity
        fade_alpha *= blur_opacity

        # apply alpha fade
        r, g, b, a = shifted.split()
        a = a.point(lambda p, f=fade_alpha: int(p * f))
        shifted = Image.merge("RGBA", (r, g, b, a))

        blur_accum = Image.alpha_composite(blur_accum, shifted)

    # reduce opacity of blur
    r, g, b, a = blur_accum.split()
    a = a.point(lambda p: int(p * blur_opacity))
    blur_accum = Image.merge("RGBA", (r, g, b, a))

# combine crisp fractal with blur

    combined = Image.alpha_composite(blur_accum, crisp_fractal)

# build final image with text

    W, H = crisp_fractal.size
    final_size = max(W, H)  # make it a square

    final_img = Image.new("RGBA", (final_size, final_size), (0, 0, 0, 255))

    # center the fractal+blur combo
    offset_x = (final_size - W) // 2
    offset_y = (final_size - H) // 2
    final_img.paste(combined, (offset_x, offset_y), combined)

# add parameter text

    draw = ImageDraw.Draw(final_img)

    params = (
        f"Iterations: {iterations}   |   "
        f"Angle: {angle_deg}°   |   "
        f"Smoothing: {smooth_iterations}   |   "
        f"Randomness: {randomness}   |   "
        f"Seed: {seed}   |   "
        f"Attractor: {attractor_point}   |   "
        f"A-Strength: {attractor_strength}   |   "
        f"Chunk Size: {chunk_size}   |   "
        f"Mode: {mode}"
    )

    # margin from bottom
    text_y = final_size - 35

    # font settings
    font_size = 25
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)

    draw.text(
        (final_size // 2, text_y),
        params,
        fill=(255, 255, 255, 255),
        anchor="mm",
        align="center",
        font=font)
    
    # save final image
    import os
    from datetime import datetime

    os.makedirs("images", exist_ok=True)

    # filename logic
    if seed is None:
        fname_seed = datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        fname_seed = str(seed)

    filename = f"fractal_{fname_seed}.png"
    filepath = os.path.join("images", filename)

    final_img.save(filepath, format="PNG")

    print(f"✔ Saved image to {filepath}")


# display final image

    plt.figure(figsize=figsize, dpi=dpi)
    plt.imshow(final_img)
    plt.axis("off")
    plt.show()

#------------------------------------------------------------------------------------------------------#
# Main Execution Block
#------------------------------------------------------------------------------------------------------#

if __name__ == "__main__":

    # parameters
    iterations = 10
    angle_deg = 60
    smooth_iterations = 3
    smoothing = True
    randomness = 0.0
    seed = 218
    attractor_point = (200, 200)
    attractor_strength = 0.0000
    chunk_size = 5000 #has to be at least 1 if randomness > 0
    mode = "none" # options: "none", "rotate", "repel", "oscillate", "scale_step"

    fractal = generate_fractal(
        iterations=iterations,
        step=2,
        angle_deg=angle_deg,
        smoothing=smoothing,
        smooth_iterations=smooth_iterations,
        randomness=randomness,
        seed=seed,
        attractor_point=attractor_point,
        attractor_strength=attractor_strength,
        chunk_size=chunk_size,
        mode=mode
    )

    plot_linestring(
    fractal, iterations, angle_deg, smooth_iterations, randomness,
    seed, attractor_point, attractor_strength, chunk_size, mode,
    motion_blur_strength=10
)
