---
layout: default
title: Project Documentation
parent: "A3: Parametric Structural Canopy"
nav_order: 2
nav_exclude: false
search_exclude: false
---

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Y7v5QwFr)
# Assignment 3: Parametric Structural Canopy

## Table of Contents

- [Pseudo-Code (Surface Generation)](#pseudo-code)
- [Pseudo-Code (Tessalation)](#pseudo-code)
- [Pseudo-Code (Column)](#pseudo-code)
- [Technical Explanation](#technical-explanation)
- [Parameters, seeds & results](#parameters--seeds)
- [References](#references)

---

## Pseudo-Code (Surface Generation)

1. **Initialize Random State**
Purpose:
- Ensure all noise and sampling is repeatable for the same seed.

How it works:
- Set Python’s random.seed(Seed)
- Set NumPy’s np.random.seed(Seed)

Why:
- Deterministic noise patterns and consistent surface generation.

2. **Define Perlin Noise Functions**
fade(t)
- Smooth easing function applied to fractional grid coordinates.
- Ensures continuous gradients and removes harsh edges.

lerp(a, b, t)
- Linear interpolation between two values.
- Core interpolation used for blending noise values.

Permutation Table
- Create an array of 0–255, shuffle it, and tile it twice.
- Used to index gradient directions.

perlin(x, y)
- Purpose:
    - Compute 2D Perlin noise for arrays of UV coordinates.

    How it works:
    - Split each coordinate into:
    - Integer cell index (xi, yi)
    - Fractional part inside the cell (xf, yf)
    - Look up pseudo-random gradient hashes around the cell corners.
    - Convert each hash into one of four gradient directions.
        Compute dot products between gradients and (xf, yf) offsets.

Bilinearly interpolate:
- Blend horizontally using fade(xf)
- Blend vertically using fade(yf)

Why:
- Produces a smooth and varied height field without harsh transitions.

3. **Construct UV Grid Inside the Curve’s Bounding Box**

Purpose:
- Generate a structured grid of sampling points covering the bounding rectangle.

How it works:
- Get bounding box of Crv
- Create linearly spaced arrays in X and Y
- Combine them into a 2D mesh grid (XX, YY)

Point inclusion test:
- Convert each (x, y) into a test point
- Use Crv.Contains() to determine if it's inside the boundary

Store:
- pts2d — 2D array of point coordinates
- inside_mask — boolean array marking valid points

Why:
- Ensures the heightmap only affects the region enclosed by the curve, not the entire bounding box.

4. **Compute Soft Edge Falloff Toward Boundary**

Purpose:
- Gradually lower displacement near the boundary so edges taper smoothly instead of creating cliffs.

How it works:
- For every grid point:
    - Find closest point on Crv
    - Measure distance to curve
    - Normalize distances by maximum distance

Apply nonlinear falloff curve:
- falloff = 0.3 + 0.7 * (normalized_distance^2)

Why:
- Prevents harsh, unnatural borders and creates smooth transitions at the shape boundary.

5. **Generate Perlin Noise Heightmap**

Purpose:
- Convert UV grid into noise heights.

How it works:
- Generate normalized U and V arrays (0→1)
- Scale UV coordinates by Scale
- Evaluate noise = perlin(U, V)

Combine all effects:
- Global Z offset H
- Perlin noise × amplitude
- Edge falloff scaling

Produce final height matrix:
- Z = H + noise * Amp * falloff

Why:
- This creates a controllable, sculptable heightfield influenced by both random noise and boundary distance.

6. **Assemble 3D Points**

Purpose:
- Flatten heightmap into list of actual 3D Rhino points.

How it works:
- For each UV cell:
- Read XY from pts2d
- Read Z from height matrix
- Create Point3d(x, y, z)
- Collect in a flat Python list.

Why:
- The Nurbs surface constructor requires point samples in 3D space.

7. **Create NURBS Surface**

Purpose:
- Produce a smooth Rhino surface from the grid of points.

How it works:
- Call NurbsSurface.CreateFromPoints()
- Dimensions: (U+1) × (V+1)
- Degree = 3 in both directions
- Rhino interpolates the points into a smooth surface.

Why:
- Creates a continuous, editable heightmap surface compatible with Grasshopper operations.

8. **Outputs**
a Srf: The generated NURBS heightmap surface
b Pts: List of all generated 3D grid points

![alt text](image.png)

## Pseudo-Code (Tessalation)

1. **Read Surface & Establish UV Domain**

Purpose:
- Set up the UV parameter space that all tessellation patterns will be sampled from.

How it works:
- Extract the U and V domains of the surface.
- Store the min/max parameter values: (u0→u1), (v0→v1).

Everything - random jitter, Voronoi sampling, curve generation - happens inside this UV rectangle.

Why:
- This keeps the tessellation consistent and fully parametric; changing U/V resolution or the underlying surface automatically reshapes the pattern.

2. **Generate Raw Tessellation (Grid → Triangles, Quads, or UV-Voronoi)**

The component branches into two major tessellation modes depending on input N.

2A. **Grid Sampling for Triangles & Quads (N = 3 or 4)**

Purpose:
- Sample a structured UV grid, optionally perturbing interior points to break uniformity.

How it works:
- Build a (U+1) x (V+1) lattice of UV coordinates.
- For interior points, add random jitter proportional to the global distortion parameter J.
- Convert each UV into 3D using Srf.PointAt().

Depending on N:
- Quads: connect each four neighbors into a closed polyline.
- Triangles: alternate diagonal direction across checkerboard cells.

Why:
- This keeps the geometry compatible with panelization, structural grids, or conventional faceting workflows - but with optional randomness.

2B. **UV-Space Voronoi Tessellation (N = 5)**

Purpose:
- Create irregular, organic, non-grid patterns across the same UV space.

How it works:
- Randomly scatter U×V seed sites across the UV domain.

For each site:
- Start with the full UV rectangle as its cell.
- Iteratively clip the polygon using perpendicular bisectors relative to all other sites.
- Keep only the half-plane containing the active site.
- Map every final polygon vertex from UV → 3D surface using Srf.PointAt().

Why:
- UV-Voronoi gives naturally varying cells that stay topologically consistent with the surface.

3. **Compute Cell Centroids for Attractor-Driven Scaling**

Purpose:
- Find a reliable “center point” for each tessellation cell so attractor forces can scale the shape inward/outward.

How it works:
- Attempt to compute centroid using curve area (works for planar loops).
- If that fails (slightly twisted loops on a curved surface), build a temporary local patch surface and compute centroid from that.
- Store all centroids.

Why:
- Accurate centroids are important for attractor-based transformations — the scaling center has to come from the centroid.

4. **Measure Distances to Attractor Points**

Purpose:
- Convert distance from each centroid to the nearest attractor into a scaling factor.

How it works:
- For each centroid, compute distance to all attractor points (if any).
- Normalize distances into 0–1 range.
- Remap them into user-defined scale domain [S_min → S_max].

Why:
- This creates local expansions or contractions - tighter near attractors, looser farther away.

5. **Create Inner Scaled Curves**

Purpose:
- Shrink or grow each cell toward/away from its centroid based on attractor influence.

How it works:
- For each original boundary curve (OuterCrv):
- Duplicate curve.
- Apply a uniform scale transform about the centroid.
- Store result as InnerCrv.

Why:
- This creates a tessellation with changing widths that gives the pattern a more dynamic and varied appearance.

6. **Generate Ruled Surfaces Between Outer and Inner Curves**

Purpose:
- Construct clean parametric walls between boundary loops.

How it works:
- Ensure both curves are closed.
- Apply a straight (ruled) loft between the outer and inner curve.
- Store resulting Brep surface.

Why:
- This step produces a consistent "panel thickness".

7. **Extrude Each Ruled Panel in the Z-Direction**

Purpose:
- Give the tessellation actual thickness in 3D.

How it works:
- For each ruled panel:
- Identify the face.
- Build a vertical line from the centroid with height H.
- Perform a face-extrusion along that path.
- Cap ends if possible.

Why:
- Turns the flat tessellation cells into 3D elements that have shape and thickness.

8. **Outputs**

a Pts: sampled UV grid or Voronoi vertices

b OuterCrv: outer boundary curves of each cell

c InnerCrv: attractor-scaled inner curves

d RuledSrfs: lofted wall surfaces

e Extruded: fully extruded 3D solids

![alt text](image-1.png)

## Pseudo-Code (Column)

1. **Normalize and Prepare Inputs**

Purpose:
- Convert all Grasshopper inputs into clean Python lists so the algorithm can treat bases, canopy points, and radii consistently.

How it works:
- Ensure P (bases) is a list of point objects.
- Ensure T (canopy points) is a list as well.
- Expand or repeat R (per-column canopy radius) so each base has a radius.

Why:
- Removes unpredictable Grasshopper casting behavior so the branching logic always receives stable inputs.

2. **Helper Functions**
dist_xy(a, b)
- Computes horizontal (XY only) distance.
- Used to group canopy points around bases without caring about elevation.

canopy_in_radius(center, r, pts)
- Returns all canopy points within radius r of the base.
- This determines which leaves “belong” to which column or tree.

Why:
- This makes the branches column-organized - each base collects nearby canopy points that it will grow upward to “feed.”

3. **Merge Functions for Branch Formation**
- merge_points(a, b, base)

Purpose:
- Combine two child nodes into their parent branch point.

How it works:
- Average their XY positions.
- Move the parent slightly toward the trunk base to give the tree an inward curvature.
- Lower Z by one vertical step L.

Why:
- This creates biologically plausible branch convergence - trees always lean inward toward the main stem.

merge_three(a, b, c, base)
- Same logic as the pair merge, but for a rare triple-merge case.
- Used once per tree to avoid lopsided structures.

Why:
- Adds natural variation and avoids height discontinuities when only three nodes remain.

4. **Create Leaf Nodes Under Each Canopy Point**

Purpose:
- Generate the initial “leaf layer” — the first child nodes from which higher merges will climb downward.

How it works:
- For each canopy point within a base’s radius:
- Compute direction from canopy → base in XY.
- Normalize this direction and scale by drift_strength × L to form a gentle inward pull.
- Add tiny random jitter for natural variation.
- Place a new point one step below the canopy in Z.

Why:
- It gives the whole structure an inward-sweeping, tree-like motion instead of vertical columns.

5. **Bottom-Up Branch Merging Loop**

Purpose:
- Recursively collapse all leaf nodes upward into a single trunk root for each base.

How it works:
- Start with all leaf nodes.

While more than one node remains:
- Sort nodes by (Z, X, Y) so merges happen bottom-up.
- If exactly three remain and triple-merge unused → merge those three.
- Else merge pairs sequentially.
- If one odd node remains → push it downward by L and merge.
- Collect lines connecting each parent to their children during merging.

Why:
- This creates a tree-like hierarchical skeleton that flows upward, with branching complexity emerging from canopy distribution.

**Note on Non-Recursive Merge Implementation**

The merging process is implemented as an iterative while-loop rather than a recursive function. This avoids Python’s recursion-depth limits (important when many canopy nodes exist), and it provides explicit control over special cases such as triple-merges and odd remaining nodes. The iterative approach also allows nodes to be globally sorted each cycle (bottom-up) and makes it easier to record all parent–child relationships used later for branch lines and pipe geometry.

6. **Connect the Root to the Base + Final Canopy Links**

Purpose:
- Finish the structural skeleton by linking trunk and leaves.

How it works:
- After merging completes, connect final root to the base point.
- For every leaf→canopy mapping, add a line back up to the original canopy point.

Why:
- This closes the full tree structure top-to-bottom:
- canopy → leaves → branches → root → trunk → ground.

7. **Outputs**

a Lines: the geometric skeleton of the branching tree.

b Tips: canopy endpoints tied to the structure.

c Pipes: capped rectangular beam geometry for every branch segment.

![alt text](image-2.png)

## Technical Explanation
The workflow starts by creating a Perlin-noise heightfield inside a closed curve. A UV grid is laid across the area, and each point is checked against the curve so the height smoothly fades toward the boundary. This prevents sharp edges and helps the noise blend naturally. The height values are then used to build a NURBS surface, which becomes the base geometry that the other parts of the project work on.

The second script takes this surface and generates a tessellation on top of it. Depending on the settings, the pattern can be made of triangles, quads, or Voronoi cells. Each cell’s centroid is measured against attractor points, and that distance controls how much the cell scales up or down. This creates smooth changes in size across the surface instead of a uniform pattern. After scaling, the cells are lofted and extruded to give them thickness, turning the tessellation into a set of simple 3D pieces.

The last script creates a branching structure that connects base points on the ground to canopy points above. It starts by placing leaf nodes under each canopy point, pulling them slightly toward the nearest base. These nodes are then merged step by step until only one root remains for each base. The lines produced during these merges form the branching layout. Finally, each line is given a rectangular profile and swept to create beam-like elements. All together, the three scripts create a connected system where the surface, the pattern, and the branching structure all relate to each other.

## Parameters, seeds & results

**Canopy 1**
Everything is internalized in the grasshopper script, with 3 different canopy settings.
![alt text](images/canopy1_1.jpg)
![alt text](images/canopy1_2.jpg)
![alt text](images/canopy1_3.jpg)

**Settings:**
**surface generation**
| Parameter              | Value |
| ---------------------- | ----- |
| Seed                   | 42    |
| U & V Resolution       | 43    |
| Amplitude              | -22   |
| Scale                  | 4     |
| H (Base Height Offset) | 45    |


**Tesselation**
| Parameter            | Value |
| -------------------- | ----- |
| U & V Resolution     | 15    |
| N (Cell Type)        | 3     |
| J (Jitter)           | 0.6   |
| S_min (Scale Min)    | 0.2   |
| S_max (Scale Max)    | 0.8   |
| H (Extrusion Height) | 1.5   |


**Branching Column**
| Parameter                | Value |
| ------------------------ | ----- |
| R (Canopy Radius)        | 35    |
| L (Vertical Step Length) | 5     |
| W (Pipe Width)           | 1     |
| H (Pipe Height)          | 1     |

Seed is the same for surface generation, tesselation & branchin column

**Canopy 2**
Everything is internalized in the grasshopper script, with 3 different canopy settings.
![alt text](images/canopy2_1.jpg)
![alt text](images/canopy2_2.jpg)
![alt text](images/canopy2_3.jpg)

**Settings:**
**surface generation**
| Parameter              | Value |
| ---------------------- | ----- |
| Seed                   | 45    |
| U & V Resolution       | 43    |
| Amplitude              | -68   |
| Scale                  | 2     |
| H (Base Height Offset) | 45    |


**Tesselation**
| Parameter            | Value |
| -------------------- | ----- |
| U & V Resolution     | 15    |
| N (Cell Type)        | 4     |
| J (Jitter)           | 0.6   |
| S_min (Scale Min)    | 0.2   |
| S_max (Scale Max)    | 0.8   |
| H (Extrusion Height) | 1.5   |


**Branching Column**
| Parameter                | Value |
| ------------------------ | ----- |
| R (Canopy Radius)        | 30    |
| L (Vertical Step Length) | 4     |
| W (Pipe Width)           | 1     |
| H (Pipe Height)          | 1     |

Seed is the same for surface generation, tesselation & branchin column

**Canopy 3**
Everything is internalized in the grasshopper script, with 3 different canopy settings.
![alt text](images/canopy_3.1.jpg)
![alt text](images/canopy3.2.jpg)
![alt text](images/canopy3.3.jpg)

**Settings:**
**surface generation**
| Parameter              | Value |
| ---------------------- | ----- |
| Seed                   | 48    |
| U & V Resolution       | 43    |
| Amplitude              | 70   |
| Scale                  | 1     |
| H (Base Height Offset) | 45    |


**Tesselation**
| Parameter            | Value |
| -------------------- | ----- |
| U & V Resolution     | 15    |
| N (Cell Type)        | 5     |
| J (Jitter)           | 0.2   |
| S_min (Scale Min)    | 0.2   |
| S_max (Scale Max)    | 0.8   |
| H (Extrusion Height) | 1.5   |


**Branching Column**
| Parameter                | Value |
| ------------------------ | ----- |
| R (Canopy Radius)        | 13    |
| L (Vertical Step Length) | 6     |
| W (Pipe Width)           | 1     |
| H (Pipe Height)          | 1     |

Seed is the same for surface generation, tesselation & branchin column

## Challenges and Solutions
One of the first issues I ran into was getting the branching columns to actually reach the canopy at the right points. When I tried building the tree from the ground up, the lines never matched the canopy exactly and the connections looked messy. The solution I found was to reverse the whole process. Instead of growing from the base, I started from the canopy points and merged everything downward. This guaranteed that each branch started exactly where it needed to, and the structure naturally worked its way down to the base.

Another challenge came from generating surface patterns that could switch between triangles, quads, and Voronoi cells while also supporting scaling and extrusion. At first it felt like too many steps were happening at the same time: sampling the surface, building the cells, shrinking them toward their centroids, and turning them into ruled surfaces for the panels. What made it work was sticking to the UV domain of the surface and treating every cell the same way once it was generated. That gave me a consistent workflow no matter which tessellation mode I used.

The Perlin noise heightfield also gave me trouble. I wanted the surface to match any closed curve shape, but the point grid and the noise field kept forming a square boundary because everything was based on the bounding box. I fixed this in the heightfield script by adding a falloff near the curve, but the issue came back during tessellation since UV grids are always rectangles. At that point I decided not to fight it and just accepted a squared roof for the project. It kept the system stable and let me move forward instead of getting stuck on one detail.

## References
https://web.arch.virginia.edu/arch541/handouts15.html?
chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://web.arch.virginia.edu/arch541/Handouts/whshops2020/rhino/workshop15images/pythonScripts11_5_20.pdf
https://www.youtube.com/watch?v=wV6W69b-l7w&t=1018s
https://chatgpt.com/share/691cd0da-dea4-8007-a7e7-adad42b3e0c3
https://chatgpt.com/share/691e2015-e3f0-8007-b3a5-1fbadd929a4b
https://chatgpt.com/share/691e201f-47d4-8007-b0fe-03ed8ebf0abc
