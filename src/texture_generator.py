"""Generate procedural textures for backgrounds and overlays."""
import numpy as np
from PIL import Image
import math


def generate_noise_texture(width, height, scale=50, octaves=4):
    """Generate Perlin-like noise texture."""
    def interpolate(a, b, x):
        ft = x * math.pi
        f = (1 - math.cos(ft)) * 0.5
        return a * (1 - f) + b * f
    
    def noise_2d(x, y, seed=0):
        n = int(x) + int(y) * 57 + seed * 131
        n = (n << 13) ^ n
        return 1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0
    
    def smooth_noise(x, y, seed=0):
        corners = (noise_2d(x-1, y-1, seed) + noise_2d(x+1, y-1, seed) +
                  noise_2d(x-1, y+1, seed) + noise_2d(x+1, y+1, seed)) / 16
        sides = (noise_2d(x-1, y, seed) + noise_2d(x+1, y, seed) +
                noise_2d(x, y-1, seed) + noise_2d(x, y+1, seed)) / 8
        center = noise_2d(x, y, seed) / 4
        return corners + sides + center
    
    def perlin_noise(x, y, seed=0):
        total = 0
        frequency = 1
        amplitude = 1
        total_amplitude = 0
        
        for _ in range(octaves):
            total += smooth_noise(x * frequency, y * frequency, seed) * amplitude
            total_amplitude += amplitude
            amplitude *= 0.5
            frequency *= 2
        
        return total / total_amplitude
    
    arr = np.zeros((height, width), dtype=np.float32)
    
    for y in range(height):
        for x in range(width):
            arr[y, x] = perlin_noise(x / scale, y / scale)
    
    arr = (arr + 1) / 2
    arr = (arr * 255).astype(np.uint8)
    
    return Image.fromarray(arr, mode='L')


def generate_grid_pattern(width, height, spacing=50, color=(255, 255, 255), line_width=1):
    """Generate grid pattern."""
    img = Image.new('RGB', (width, height), (0, 0, 0))
    pixels = np.array(img)
    
    for x in range(0, width, spacing):
        pixels[:, x:x+line_width] = color
    
    for y in range(0, height, spacing):
        pixels[y:y+line_width, :] = color
    
    return Image.fromarray(pixels)


def generate_circuit_pattern(width, height, density=0.3):
    """Generate circuit board pattern."""
    img = Image.new('RGB', (width, height), (0, 0, 0))
    pixels = np.array(img)
    
    num_lines = int(density * width / 10)
    
    for _ in range(num_lines):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        length = np.random.randint(20, 100)
        horizontal = np.random.choice([True, False])
        
        color = (0, 255, 0) if np.random.random() > 0.5 else (0, 200, 0)
        
        if horizontal:
            end_x = min(x + length, width)
            pixels[y:y+2, x:end_x] = color
        else:
            end_y = min(y + length, height)
            pixels[y:end_y, x:x+2] = color
        
        if np.random.random() > 0.7:
            node_x = x + length // 2 if horizontal else x
            node_y = y if horizontal else y + length // 2
            if 0 <= node_x < width and 0 <= node_y < height:
                pixels[node_y-2:node_y+2, node_x-2:node_x+2] = (255, 255, 0)
    
    return Image.fromarray(pixels)


def generate_halftone_pattern(width, height, dot_size=5):
    """Generate halftone dot pattern."""
    img = Image.new('L', (width, height), 255)
    pixels = np.array(img)
    
    spacing = dot_size * 3
    
    for y in range(0, height, spacing):
        for x in range(0, width, spacing):
            radius = np.random.randint(1, dot_size)
            
            yy, xx = np.ogrid[-radius:radius+1, -radius:radius+1]
            mask = xx*xx + yy*yy <= radius*radius
            
            y_start = max(0, y - radius)
            y_end = min(height, y + radius + 1)
            x_start = max(0, x - radius)
            x_end = min(width, x + radius + 1)
            
            mask_y_start = y_start - (y - radius)
            mask_y_end = mask_y_start + (y_end - y_start)
            mask_x_start = x_start - (x - radius)
            mask_x_end = mask_x_start + (x_end - x_start)
            
            sub_mask = mask[mask_y_start:mask_y_end, mask_x_start:mask_x_end]
            pixels[y_start:y_end, x_start:x_end][sub_mask] = 0
    
    return Image.fromarray(pixels)


def generate_scanline_overlay(width, height, line_spacing=3, intensity=0.3):
    """Generate CRT scanline overlay."""
    img = Image.new('L', (width, height), 255)
    pixels = np.array(img)
    
    for y in range(0, height, line_spacing):
        pixels[y:y+1, :] = int(255 * (1 - intensity))
    
    return Image.fromarray(pixels)


def generate_gradient(width, height, color1, color2, direction='vertical'):
    """Generate gradient between two colors."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    
    for i in range(height if direction == 'vertical' else width):
        t = i / (height if direction == 'vertical' else width)
        color = tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2))
        
        if direction == 'vertical':
            arr[i, :] = color
        else:
            arr[:, i] = color
    
    return Image.fromarray(arr)


def generate_radial_gradient(width, height, center_color, edge_color, center=None):
    """Generate radial gradient from center to edges."""
    if center is None:
        center = (width // 2, height // 2)
    
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    max_dist = math.sqrt(center[0]**2 + center[1]**2)
    
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - center[0])**2 + (y - center[1])**2)
            t = min(dist / max_dist, 1.0)
            
            color = tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(center_color, edge_color))
            arr[y, x] = color
    
    return Image.fromarray(arr)


def generate_checkerboard(width, height, square_size=20, color1=(255, 255, 255), color2=(0, 0, 0)):
    """Generate checkerboard pattern."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            if ((x // square_size) + (y // square_size)) % 2 == 0:
                arr[y, x] = color1
            else:
                arr[y, x] = color2
    
    return Image.fromarray(arr)
