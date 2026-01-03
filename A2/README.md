[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/6QYsis9p)
# Assignment 2: Exploring Fractals through Recursive Geometric Patterns

This repository contains the starter materials for **Assignment 2: Exploring Fractals through Recursive Geometric Patterns**.

---

## Table of Contents

- [Pseudo-Code](#pseudo-code)
- [Technical Explanation](#technical-explanation)
- [Geometric Influences](#geometric-influences)
- [Appearance Mapping](#appearance-mapping)
- [Parameters, seeds & results](#parameters--seeds)
- [References](#references)

---

## Pseudo-Code

1. **evolve_sequence(seq)**
- Apply the core grammar rule S → S S R.

def evolve_sequence(seq):
    return seq + seq + ["R"]

- How it works:
    Duplicate the current sequence.
    Append "R" at the end.
- why:
    This exponential growth produces the recursive backbone of the fractal.

2. **apply_randomness_chunked(seq, randomness, chunk_size)**
- Add structured L/R flips in chunks instead of noisy symbol-level randomness.

while i < len(new):
    if random.random() < randomness:
        for j in range(i, min(i + chunk_size, len(new))):
            new[j] = "R" if new[j] == "L" else "L"
    i += chunk_size

- How it works:
    Sequence is divided into fixed-size blocks.
    Entire blocks flip left/right based on randomness probability.
- Why:
    Keeps coherence while adding variation, avoids messy jitter.

3. **apply_spatial_influence(… )**
- Modify heading or step length using a spatial attractor point and selected field mode.

dx = ax - x
dy = ay - y
distance = math.hypot(dx, dy)

if mode == "rotate":
    heading += strength * (1.0 / distance)

elif mode == "repel":
    heading += diff * (-strength)

elif mode == "oscillate":
    heading += math.sin(distance * 0.05) * strength

elif mode == "scale_step":
    step *= 1 + strength * (distance / 100.0)

- How it works:
    Compute vector & distance to attractor.
    Depending on mode, modify heading or step.

- Modes:
    rotate → vortex
    repel → push away
    oscillate → wavy motion
    scale_step → step size grows/shrinks with distance

- Why:
    Gives the fractal environmental responsiveness.

4. **sequence_to_points(… )**
- Interpret the symbolic sequences as geometric turtle-graphics.

if cmd == "L": heading += angle
elif cmd == "R": heading -= angle

heading, step = apply_spatial_influence(...)
x += step * math.cos(heading)
y += step * math.sin(heading)
pts.append((x, y))

- How it works:
    Apply L/R rotations.
    Apply spatial influence.
    Add forward-moved point.

- Why:
    Turns abstract grammar into real geometry.

5. **chaikin(points, iterations)**
- Smooth jagged polylines using Chaikin’s subdivision.

Q = (0.75*p0[0] + 0.25*p1[0], 0.75*p0[1] + 0.25*p1[1])
R = (0.25*p0[0] + 0.75*p1[0], 0.25*p0[1] + 0.75*p1[1])

- How it works:
    For each edge, compute Q and R points.
    Replace the line with the smoothed sequence.

- why:
    Creates an organic, continuous look.

6. **generate_fractal(… )**
- Full fractal generation pipeline linking grammar, randomness, spatial influence, and smoothing.

for _ in range(iterations):
    seq = evolve_sequence(seq)
    seq = apply_randomness_chunked(seq, randomness, chunk_size)

pts = sequence_to_points(...)
if smoothing:
    pts = chaikin(pts, smooth_iterations)

return LineString(pts)

- How it works:
    Evolve grammar, Apply chunk randomness, Convert to points, Smooth if needed, Output LineString.

- Why:
    Modular design makes it easy to experiment with different influences.

7. **plot_linestring(… )**
- The plotting function prepares the final visual output. It does not change the fractal geometry - only the presentation.

Steps:

- Render fractal (transparent):
    Plot the LineString in white on a fully transparent background so it can be layered.

- Motion-blur pass:
    Duplicate the fractal several times, offset each copy, and fade its alpha.
    This creates a soft glow around the crisp line.

- Composite layers:
    Blur underneath
    Crisp fractal on top
    Ensures clarity while adding atmospheric depth

- Square framing:
    Place the combined image inside a black square canvas to keep consistent proportions and presentation.

- Parameter text:
Add a small line of info at the bottom with: iterations, angle, smoothing, randomness & seed, attractor point & strength, chunk size & mode.

8. **Main Execution**
- This block configures all adjustable parameters before generating and plotting the fractal.

iterations: How many times the grammar expands (controls complexity)
angle_deg: Turning angle for L/R commands
step: Forward movement distance per command
smoothing: Enable/disable Chaikin smoothing
smooth_iterations: Number of Chaikin passes
randomness: Probability of flipping each chunk block
chunk_size: Chunk length for block-randomness
seed: Fix randomness for repeatable outputs
attractor_point	(x, y):	Coordinates of spatial influence center
attractor_strength: Intensity of spatial field
mode: 'none', 'rotate', 'repel', 'oscillate', 'scale_step'
motion_blur_strength: Distance of each blur offset
motion_blur_steps: Number of blur layers
blur_opacity: Darkness/visibility of glow

## Technical Explanation
This project builds fractal patterns by combining a symbolic grammar system with spatial influence fields and custom image rendering. The core mechanism is a recursive grammar rule, S → S S R, which doubles the sequence at each iteration and appends a turn. Over several iterations, this produces a dense L/R instruction string that encodes the curve’s turning behavior.

To avoid purely deterministic forms, the script applies chunk-based randomness. Instead of flipping individual L/R symbols, it flips whole blocks, producing smoother, more coherent irregularities. Randomness strength, chunk size, and seed allow predictable or chaotic variations.

The L/R sequence is then converted into geometry. Each symbol rotates the heading by a fixed angle, and spatial influence fields—such as rotation, repulsion, oscillation, or distance-based scaling—modify the movement. These fields are always available but only have effect when their strength is above zero, enabling subtle or dramatic distortion of the fractal path.

Optional smoothing via Chaikin’s algorithm rounds the curve, softening sharp turns and producing more organic results.

For rendering, the fractal is drawn as a thin white line. A custom motion-blur effect layers multiple shifted, fading copies beneath it. The final result is centered inside a black square canvas, with all parameter settings displayed as white text at the bottom.

## Geometric Influences
The fractal isn’t shaped only by grammar rules; it also reacts to spatial fields that modify each step as the curve grows.

1. Rotation Field (rotate)
Pulls the curve into a soft vortex around the attractor. The heading rotates more strongly when the curve is close, adding swirl and twist to the geometry.

2. Repulsion Field (repel)
Pushes the curve away from the attractor by shifting its heading opposite the attractor direction. This creates openings, avoids clustering, and produces outward-flaring forms.

3. Oscillation Field (oscillate)
Applies a sine-based heading offset tied to distance. This introduces a gentle wave or ripple effect without breaking the fractal’s underlying structure.

4. Step Scaling (scale_step)
Changes step length rather than direction. Moving near the attractor can compress or stretch the geometry, creating zones of dense or expanded patterning.

These fields turn the curve into a responsive system, letting spatial context influence the final fractal form.

## Appearance Mapping
The final visual output is shaped by several layered rendering choices that control clarity, depth, and aesthetic feel.

1. Line Rendering
The fractal is drawn in pure white on a black background. Line thickness scales with iteration count (lw = max(0.3, 2.0 / (iterations + 1))), so deeper fractals remain visually sharp instead of overwhelming the image.

2. Motion Blur Layer
The crisp fractal is duplicated, shifted multiple times, and blended with brightness and alpha decay. This creates a subtle glow-trail behind the geometry while keeping the original line perfectly sharp on top.

3. Opacity Decay
Each blur step fades based on its distance from the center of the blur stack, giving the effect of motion dissolving outward. This enhances depth without drowning the main geometry.

## Parameters, seeds & results

Normal fractal & step size with no attractor or randomness:
![alt text](images/fractal_1.png)
![alt text](images/fractal_2.png)
![alt text](images/fractal_3.png)
![alt text](images/fractal_4.png)
![alt text](images/fractal_5.png)
![alt text](images/fractal_7.png)
![alt text](images/fractal_10.png)
![alt text](images/fractal_15.png)
![alt text](images/fractal_16.png)
![alt text](images/fractal_17.png)
![alt text](images/fractal_151.png)

Experimenting with randomness and different kind of attractors:
![alt text](images/fractal_200.png)
![alt text](images/fractal_201.png)
![alt text](images/fractal_202.png)
![alt text](images/fractal_203.png)
![alt text](images/fractal_204.png)
![alt text](images/fractal_205.png)
![alt text](images/fractal_206.png)
![alt text](images/fractal_207.png)
![alt text](images/fractal_208.png)
![alt text](images/fractal_209.png)
![alt text](images/fractal_210.png)
![alt text](images/fractal_211.png)
![alt text](images/fractal_212.png)
![alt text](images/fractal_213.png)
![alt text](images/fractal_214.png)

experimenting with different curve, smoothness & angles
![alt text](images/fractal_214.png)
![alt text](images/fractal_215.png)
![alt text](images/fractal_216.png)
![alt text](images/fractal_217.png)
![alt text](images/fractal_218.png)

## Challenges and Solutions

1. Transitioning Away From the Dragon Curve
Challenge: The original system was tightly built around dragon-curve recursion, which limited exploration and made it hard to mix spatial rules with grammar evolution.
Solution: Rebuilt the generator from scratch using a symbolic L/R grammar. This opened the door to new structural outcomes, cleaner rule control, and easier integration of fields, smoothing, and randomness.

2. Implementing an Attractor-Based Spatial Field
Challenge: Adding spatial influences wasn’t straightforward—direct steering produced unstable, chaotic motions or extreme distortions.
Solution: Created a dedicated apply_spatial_influence() function with multiple modes (rotate, repel, oscillate, scale_step). Each mode computes distance, heading difference, and falloff so the influence stays stable and physically intuitive.

3. Adding Controlled Randomness (Chunk-Based Noise)
Challenge: Early randomness flipped individual turns, making the structure messy and unreadable. It lost all recognisable form.
Solution: Switched to chunked randomness, where whole blocks of the sequence flip together. This preserves large-scale structure while still introducing local variation you can tune.

## References
http://www.fractalcurves.com/Root7.html
https://www.youtube.com/watch?v=KplEgbUDcXc
https://github.com/SergiuPogor/PYTHON_PEAK
https://www.reddit.com/user/sudhabin/
http://fractalcurves.com/all_curves/2G_family.html
http://www.fractalcurves.com/familytree/4.html
https://rosettacode.org/wiki/Dragon_curve
https://www.reddit.com/r/proceduralgeneration/comments/1ooyj5h/a_norm9_fractal_space_filling_curve_self_avoiding/
https://thecodingtrain.com/challenges/162-self-avoiding-walk
https://deut-erium.github.io/pyfractal/
http://www.brainfillingcurves.com/index.html





