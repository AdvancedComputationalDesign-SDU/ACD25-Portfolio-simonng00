# Documentation for Assignment 1

This is a template for documenting your assignment. Feel free to use the structure below, add/remove section, or re-organize the order to explain your project.

## Table of Contents

- [Pseudo-Code](#pseudo-code)
- [Technical Explanation](#technical-explanation)
- [Results](#results)
- [References](#references)

---

## Pseudo-Code

1. **Parameters and imports**
- Import libraries: numpy, matplotlip, colorsys and random.
   - Random provides functions to generate random numbers and make random selections.
   - colorsys module helps converting colors between different color systems (like RGB, HLS, HSV).

2. **Define Functions**
- def complex_grid(xmin, xmax, ymin, ymax, pixel_density)
   - This function creates a 2D NumPy grid of complex numbers that represents the portion of the complex plane used for fractal
   generation.
   - The parameters xmin and xmax define the range of real numbers on the horizontal axis.
   - The parameters ymin and ymax define the range of imaginary numbers on the vertical axis.
   - pixel_density determines how many pixels are calculated per unit distance, controlling the resolution of the generated fractal.

   - Using np.linspace(), the function samples evenly spaced values between these limits for both real and imaginary parts.
      - def complex_grid(xmin, xmax, ymin, ymax, pixel_density):
        real = np.linspace(xmin, xmax, num=max(1, int((xmax-xmin) * pixel_density)))
        imag = np.linspace(ymin, ymax, num=max(1, int((ymax-ymin) * pixel_density)))
        - (adding a 1 ensures that we are preventing zero or negative sample counts, so the program always produces a valid array)
   
   - np.meshgrid() then combines these into two 2D coordinate arrays, which are merged into a single complex grid of the for:
   xx + 1j * yy.

- def fractal_set(xmin, xmax, ymin, ymax, pixel_density, c, n_iterations)
   - This function generates either a Mandelbrot or Julia fractal by iterating the complex function Z = Z² + C for each coordinate on the grid.
   - It determines how quickly each point diverges, which defines the shape and color intensity of the final fractal image.

   - z_grid = complex_grid(xmin, xmax, ymin, ymax, pixel_density)
      - Calls complex_grid() to obtain the 2D coordinate map. Each point in this grid corresponds to a unique complex number to be tested.
         - if c == 0:
            C = z_grid.copy()
            Z = np.zeros_like(z_grid)
           else:
            C = np.full(z_grid.shape, c, dtype=complex)
            Z = z_grid.copy()
            - When c = 0, the function generates a Mandelbrot set, where each grid point acts as a unique constant C and Z starts from zero.
            - Otherwise, it generates a Julia set, fixing one global constant C and iterating different starting values Z.
   
   - mask = np.full(Z.shape, True, dtype=bool)
      - A Boolean mask keeps track of which points are still active — this avoids unnecessary computation for points that already diverged.
   - escape = np.zeros(Z.shape, dtype=int)
      - Stores how many iterations each point takes before escaping the radius threshold. These values later translate into pixel color intensities.
   
   - for i in range(n_iterations): Now the loop begins.
      - Z[mask] = Z[mask] * Z[mask] + C[mask]
         escaped = np.abs(Z) > 2
         escape[mask & escaped] = i
         mask[mask & escaped] = False
         if not mask.any():
            break
            - The loop updates all active points and checks whether they escape beyond radius 2 (a standard fractal boundary).
            - The iteration count represents how quickly each point diverges, which encodes the fractal’s detailed edge structure.
      return escape
      - Returns a 2D array of escape times, which will later be mapped to color values during visualization.

3. **color coding**
- darken_color(rgb, desaturate=0.4, darken=0.6)
   - Converts an RGB color into HLS (Hue, Lightness, Saturation) using colorsys.rgb_to_hls.
   s *= desaturate
   l *= darken
      - Modifies the saturation and lightness to make the color darker and less saturated.
      - The purpose is to provide a background color that contrasts well with the fractal.

- contrast_colormap()
   - Generates a visually appealing colormap with distinct color stops and randomly selects two base hues (hue1 and hue2).

4. **input parameters**
- The variables xmin, xmax, ymin, ymax define the region of the complex plane to visualize.
   - Example ranges:
      - Julia set: xmin = -1.5, xmax = 1.5, ymin = -1.5, ymax = 1.5
      - Mandelbrot set: xmin = -2.0, xmax = 1.0, ymin = -1.5, ymax = 1.5

- Pixel_density sets the number of points per unit along the axes.
- n_iterations determines how many times the fractal formula is iterated for each point.

The c_values list contains complex numbers used for Julia sets (and optionally Mandelbrot).
- Each c produces a unique fractal pattern.
- For the Mandelbrot set, c = 0 is used internally since each grid point acts as its own constant.

5. **Plotting**
- import os.
- os.makedirs(output_folder, exist_ok=True) ensures that a folder named "results" exists to save images.
- exist_ok=True prevents errors if the folder already exists.
- Creating a for c in c_values:
   - For each c in the list, a new fractal image is generated.
   - Calls fractal_set() with the current c, grid boundaries, pixel density, and iteration count.
   Returns fractal_mask, a 2D array of escape-time values used to visualize the fractal.
- Color generation:
   - contrast_colormap() creates a colormap with multiple stops.
   - darken_color() is used to compute a dark background color for contrast.
- plotting:
   - The axes are turned off for a clean image.
   - A text label is added showing the current c value and n_iterations.
save image:
   - Constructs a filename using the real and imaginary parts of c.
   - Saves the figure to the "results" folder using plt.savefig().
   - Closes the plot to free memory with plt.close().
   - Prints a confirmation message in the console.

6. **Additional work**
- highlight_points (basically the same as the c_values) is a list of complex numbers corresponding to interesting locations on the Mandelbrot set.
- These points will be marked with circles on the final image.
- using the same idea from fractal_set(), c=0 and fractal_mask (calling it fractal_mask_2 for my understanding)
- for point in highlight_points:
    circle = patches.Circle((point.real, point.imag), 0.02, color='white', fill=False, linewidth=1.5)
    plt.gca().add_patch(circle)
    - for every point in highlight_points, where real and imaginary is defined with circle = ... it marks a circle, marking where the different julia sets are taken.

## Technical Explanation

This project generates Mandelbrot and Julia fractals using NumPy arrays. The complex plane is represented as a 2D grid of numbers created with np.meshgrid() in the complex_grid() function. The ranges xmin, xmax, ymin, ymax define the area of the plane, and pixel_density sets the resolution.

Each point in the grid is iteratively updated using the formula Z = Z*Z + C. For the Mandelbrot set, each point is its own constant C, with Z starting at zero. For Julia sets, C is fixed and Z starts at each grid point. A boolean mask tracks which points are still active, and an escape array records how many iterations each point takes to exceed a magnitude of 2. The number of iterations is controlled by n_iterations.

Colors are generated with contrast_colormap() and adjusted with darken_color() to create a clear, ASTHECTICALLY PLEASING image. The Mandelbrot map also includes circles marking important points (highlight_points) that correspond to interesting Julia sets.

## Results

All generated fractal images, including various Julia sets and the Mandelbrot map with highlighted points, can be found in the `results` folder.  

![alt text](images/c_n0.162_p1.040j.png)
![alt text](images/c_n0.296_p0.625j.png)
![alt text](images/c_n0.400_p0.600j.png)
![alt text](images/c_n0.540_p0.540j.png)
![alt text](images/c_n0.727_p0.189j.png)
![alt text](images/c_n0.770_n0.270j.png)
![alt text](images/c_n0.800_p0.156j.png)
![alt text](images/c_n1.280_p0.070j.png)
![alt text](images/c_n1.476_p0.000j_v1.png)
![alt text](images/c_n1.476_p0.000j_v2.png)
![alt text](images/c_p0.000_p0.000j_nopoints.png)
![alt text](images/c_p0.000_p0.800j_v1.png)
![alt text](images/c_p0.000_p0.800j_v2.png)
![alt text](images/c_p0.285_p0.010j.png)
![alt text](images/c_p0.355_p0.355j.png)
![alt text](images/c_p0.356_n0.337j_v1.png)
![alt text](images/c_p0.356_n0.337j_v2.png)
![alt text](images/c_p0.370_p0.100j.png)
![alt text](images/mandelbrot_map_cvalues.png)

## References

Real Python: [Mandelbrot Set in Python](https://realpython.com/mandelbrot-set-python/)
Medium: [Animating Fractals with Python, Julia, and Mandelbrot Sets](https://medium.com/@er_95882/animating-fractals-with-python-julia-and-maldelbrot-sets-e65a04549423)
Medium: [Create Stunning Fractal Art with Python](https://medium.com/data-science/create-stunning-fractal-art-with-python-a-tutorial-for-beginners-c83817fcb64b)
SquaresMagic: [Julia Set Generator](https://squaresmagic.com/julia-set)
NumPy Documentation: [Array Manipulation Routines](https://numpy.org/doc/stable/reference/routines.array-manipulation.html)
youtube:  [https://www.youtube.com/watch?v=u9GAnW8xFJY](https://www.youtube.com/watch?v=u9GAnW8xFJY) 
youtube:  [https://www.youtube.com/watch?v=xjjmkg9J7Gg&t=141s](https://www.youtube.com/watch?v=xjjmkg9J7Gg&t=141s)
youtube: [https://www.youtube.com/watch?v=gECmGwD0DaI](https://www.youtube.com/watch?v=gECmGwD0DaI)  
