---
layout: default
title: Images
parent: "A4: Agent-Based Modeling for Surface Panelization"
nav_order: 3
---

## Variation 1: Curvature-Flow Relaxation

![alt text](images/image.png)

### Signals Used
- Principal curvature direction field (vector signal)
- Curvature magnitude field (scalar signal)
- Neighborhood spacing (geometric signal)

### Parameters Changed
![alt text](images/var1para.png)

### Description
In this variation, agents drift gently along the surface’s principal curvature directions. Curvature magnitude slows agents down in highly curved regions, producing tighter density around bumps and relaxed spacing across flatter zones. A light neighborhood repulsion keeps agents from clustering without overpowering the curvature-driven drift.

---

## Variation 2: Curvature-Slope Flow Field

![alt text](images/image2.png)

### Signals Used
- Principal curvature direction  
- Slope direction  
- Curvature magnitude field  
- Neighborhood spacing  

### Parameters Changed
![alt text](images/var2para.png)

### Description
Agents stop behaving like a grid and instead move like particles sliding over the surface. Curvature pulls them along bending directions while slope pushes them uphill, producing directional streaks and dense clusters.

---

## Variation 3: Curvature + Reverse-Slope Influence

![alt text](images/image3.png)

### Signals Used
- Curvature field  
- Reverse slope influence  

### Parameters Changed
![alt text](images/var3para.png)

### Description
This variation emphasizes unpredictable, turbulent motion by combining strong curvature following with a reverse-slope attractor. Agents accelerate across the surface with minimal stabilization, creating dense pockets, stretched voids, and rapidly shifting local neighborhoods.
