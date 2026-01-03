# Assignment 1: NumPy Array Manipulation for 2D Pattern Generation

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import random
import colorsys

#Following coding is inspired by https://realpython.com/mandelbrot-set-python/, https://medium.com/@er_95882/animating-fractals-with-python-julia-and-maldelbrot-sets-e65a04549423
# https://medium.com/data-science/create-stunning-fractal-art-with-python-a-tutorial-for-beginners-c83817fcb64b, https://nseverkar.medium.com/intro-to-drawing-fractals-with-python-6ad53bbc8208 
# and CHAT GPT for fixes!
# additional julia set found in julia set generator: https://squaresmagic.com/julia-set 

# Function to create a grid of complex numbers
def complex_grid(xmin, xmax, ymin, ymax, pixel_density):
    real = np.linspace(xmin, xmax, num=max(1, int((xmax-xmin) * pixel_density))) #real axis
    imag = np.linspace(ymin, ymax, num=max(1, int((ymax-ymin) * pixel_density))) #imaginary axis
    xx, yy = np.meshgrid(real, imag) #creates a grid of coordinates
    return xx + 1j * yy #combines real and imaginary parts into complex numbe

# Fractal generation function
def fractal_set(xmin, xmax, ymin, ymax, pixel_density, c, n_iterations): #generates the fractal set (Mandelbrot or Julia) based on the provided parameters.
    z_grid = complex_grid(xmin, xmax, ymin, ymax, pixel_density) #creates a grid of complex numbers
    if c == 0: 
        # Mandelbrot, each point is its own constant start at z = 0
        C = z_grid.copy()
        Z = np.zeros_like(z_grid)
    else:
        # Julia, c is fixed. Each point starts at z = point coordinate.
        C = np.full(z_grid.shape, c, dtype=complex)
        Z = z_grid.copy()
    
    mask = np.full(Z.shape, True, dtype=bool) #mask to track which points are still being iterated
    escape = np.zeros(Z.shape, dtype=int) #how many iterations before escape

    for i in range(n_iterations): #iterate the function
        Z[mask] = Z[mask] * Z[mask] + C[mask] #update Z for all active points
        escaped = np.abs(Z) > 2 #check which points have escaped
        escape[mask & escaped] = i #record the iteration count for escaped points
        mask[mask & escaped] = False #mark these points as no longer active
        if not mask.any():
            break #stop if all points have escaped
    
    return escape

#color coding functions
def darken_color(rgb, desaturate=0.4, darken=0.6):
    h, l, s = colorsys.rgb_to_hls(*rgb) #hue, lightness, saturation
    s *= desaturate
    l *= darken
    return colorsys.hls_to_rgb(h, l, s)

def contrast_colormap():
    hue1 = random.random()
    hue2 = (hue1 + random.uniform(0.45, 0.55)) % 1.0

    def make_color(hu, li, sa):
        return colorsys.hls_to_rgb(hu, li, sa)
    
    stops = [
        make_color(hue1, 0.2, 0.7),
        make_color(hue1, 0.4, 0.9),
        make_color(hue2, 0.6, 0.8),
        make_color(hue2, 0.85, 0.6)
    ]
    cmap = mcolors.LinearSegmentedColormap.from_list("contrast_cmap", stops, N=1024)
    return cmap, stops

# Julia set
# xmin = -1.5; xmax = 1.5
# ymin = -1.5; ymax = 1.5

# Mandelbrot set
xmin = -2.0; xmax = 1.0
ymin = -1.5; ymax = 1.5

# Parameters, iterations, zoom & pixel density.
base_pixel_density = 1000
base_iterations = 500
zoom = 1.0 
pixel_density = min(int(base_pixel_density * zoom), 1000)
n_iterations = int(base_iterations + np.log2(zoom) * 50)

# ------ Generate and save fractal images for various c values ------ #

# c = -0.4 + 0.6j  # Julia
# c = 0 + 0.8j # lightning like 
# c = 0.37 + 0.1j # spirals v.1
# c = -0.7269 + 0.1889j # Tornadoes within Spirals
# c = -0.8 + 0.156j # classic julia
# c = 0.355 + 0.355j # torndaoes
# c = -0.54 + 0.54j # spirals v.2
# c = 0.355534 - 0.337292j # by chris thomassen
# c = 0.285 + 0.01j # elephants
# c = -0.162 + 1.04j # very small lightning
# c = -1.476 + 0j # deep sea coral
# c = -0.163 + 0.085j
# c = -0.29609091 + 0.62491j #2500 iterations! (dont do that, do 1000 max)

# ------ Generate and save fractal images for various c values ------ #

c_values = [
    0,  # Mandelbrot
    -0.4 + 0.6j,
    0 + 0.8j,
    0.37 + 0.1j,
    -0.7269 + 0.1889j,
    -0.8 + 0.156j,
    0.355 + 0.355j,
    -0.54 + 0.54j,
    0.355534 - 0.337292j,
    0.285 + 0.01j,
    -0.162 + 1.04j,
    -1.476 + 0j,
    -0.29609091 + 0.62491j,
    -0.77 - 0.27j,
    -1.28 + 0.07j,
]

import os # create output directory
output_folder = "results" # folder to save images
os.makedirs(output_folder, exist_ok=True) # create folder if it doesn't exist

for c in c_values:
    # fractal generation
    fractal_mask = fractal_set(xmin, xmax, ymin, ymax, pixel_density, c, n_iterations)

    # color generation
    cmap, color_stops = generate_colormap = contrast_colormap()
    background_color = darken_color(color_stops[0])

    # Plotting
    plt.figure(figsize=(10,10), dpi=300)
    plt.imshow(fractal_mask, cmap=cmap, extent=[xmin, xmax, ymin, ymax])
    plt.gca().set_facecolor(background_color)
    plt.axis('off')
    plt.text(0.5, 0.02, f"c = {c.real:.6f} {'+' if c.imag >= 0 else '-'} {abs(c.imag):.6f}j | n_iterations = {n_iterations}",
    ha='center', va='bottom', fontsize=10, color='white', transform=plt.gca().transAxes)

    filename = f"c_{c.real:+.3f}_{c.imag:+.3f}j.png".replace('+', 'p').replace('-', 'n')
    filepath = os.path.join(output_folder, filename)

    plt.savefig(filepath, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"Saved fractal image for c={c} to {filepath}")

# mandelbrot map with highlighted points
# points taken from the c_values list above

import matplotlib.patches as patches # for drawing circles

highlight_points = [
    -0.4 + 0.6j,
    0 + 0.8j,
    0.37 + 0.1j,
    -0.7269 + 0.1889j,
    -0.8 + 0.156j,
    0.355 + 0.355j,
    -0.54 + 0.54j,
    0.355534 - 0.337292j,
    0.285 + 0.01j,
    -0.162 + 1.04j,
    -1.476 + 0j,
    -0.29609091 + 0.62491j,
    -0.77 - 0.27j,
    -1.28 + 0.07j,
]

# Mandelbrot set parameters
g = 0  # Mandelbrot
fractal_mask_2 = fractal_set(xmin, xmax, ymin, ymax, pixel_density, g, n_iterations)

# Color generation
cmap, color_stops = contrast_colormap()
background_color = darken_color(color_stops[0])

# Plotting
plt.figure(figsize=(10,10), dpi=300)
plt.imshow(fractal_mask_2, cmap=cmap, extent=[xmin, xmax, ymin, ymax])
plt.gca().set_facecolor(background_color)

# Add circles for each highlight point
for point in highlight_points:
    circle = patches.Circle((point.real, point.imag), 0.02, color='white', fill=False, linewidth=1.5)
    plt.gca().add_patch(circle)

plt.axis('off')
plt.text(0.5, 0.02, f"Mandelbrot Set | n_iterations = {n_iterations}", ha='center', va='bottom', fontsize=10, color='white',
    transform=plt.gca().transAxes)

filepath = os.path.join(output_folder, "mandelbrot_map_cvalues.png")
plt.savefig(filepath, bbox_inches='tight', pad_inches=0)
plt.close()
print(f"Saved Mandelbrot image with highlighted points to {filepath}")