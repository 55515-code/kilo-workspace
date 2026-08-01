"""Visual effects: glitch, CRT, film grain, scanlines, etc."""
import numpy as np
from PIL import Image, ImageFilter


def apply_glitch_effect(image, intensity=0.5):
    """Apply digital glitch effect."""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    num_glitches = int(intensity * 20)
    
    for _ in range(num_glitches):
        y_start = np.random.randint(0, height - 10)
        slice_height = np.random.randint(1, max(2, int(height * 0.05)))
        y_end = min(y_start + slice_height, height)
        
        offset = np.random.randint(-int(width * 0.1), int(width * 0.1))
        
        if offset > 0:
            img_array[y_start:y_end, offset:] = img_array[y_start:y_end, :width-offset]
            img_array[y_start:y_end, :offset] = 0
        elif offset < 0:
            img_array[y_start:y_end, :width+offset] = img_array[y_start:y_end, -offset:]
            img_array[y_start:y_end, width+offset:] = 0
    
    if intensity > 0.3:
        channel_shift = int(intensity * 10)
        r_channel = img_array[:, :, 0].copy()
        g_channel = img_array[:, :, 1].copy()
        b_channel = img_array[:, :, 2].copy()
        
        img_array[:, :, 0] = np.roll(r_channel, channel_shift, axis=1)
        img_array[:, :, 2] = np.roll(b_channel, -channel_shift, axis=1)
    
    return Image.fromarray(img_array)


def apply_crt_effect(image, scanline_intensity=0.3):
    """Apply CRT monitor effect with scanlines."""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    for y in range(0, height, 2):
        img_array[y, :] = (img_array[y, :] * (1 - scanline_intensity)).astype(np.uint8)
    
    blur_radius = 0.5
    img_pil = Image.fromarray(img_array)
    img_pil = img_pil.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    img_array = np.array(img_pil)
    
    for y in range(0, height, 2):
        img_array[y, :] = (img_array[y, :] * (1 - scanline_intensity)).astype(np.uint8)
    
    vignette_strength = 0.3
    center_y, center_x = height // 2, width // 2
    max_dist = np.sqrt(center_x**2 + center_y**2)
    
    for y in range(height):
        for x in range(width):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            factor = 1 - (dist / max_dist) * vignette_strength
            img_array[y, x] = (img_array[y, x] * factor).astype(np.uint8)
    
    return Image.fromarray(img_array)


def apply_film_grain(image, intensity=0.2):
    """Apply analog film grain."""
    img_array = np.array(image).astype(np.float32)
    height, width = img_array.shape[:2]
    
    noise = np.random.normal(0, intensity * 50, (height, width, 3))
    img_array = img_array + noise
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    return Image.fromarray(img_array)


def apply_vignette(image, strength=0.5):
    """Apply vignette darkening at edges."""
    img_array = np.array(image).astype(np.float32)
    height, width = img_array.shape[:2]
    
    center_y, center_x = height // 2, width // 2
    max_dist = np.sqrt(center_x**2 + center_y**2)
    
    y_coords, x_coords = np.ogrid[:height, :width]
    dist = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
    
    vignette_mask = 1 - (dist / max_dist) * strength
    vignette_mask = np.clip(vignette_mask, 0, 1)
    
    for c in range(3):
        img_array[:, :, c] = img_array[:, :, c] * vignette_mask
    
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    return Image.fromarray(img_array)


def apply_chromatic_aberration(image, offset=2):
    """Apply chromatic aberration."""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    result = np.zeros_like(img_array)
    
    r_channel = img_array[:, :, 0]
    g_channel = img_array[:, :, 1]
    b_channel = img_array[:, :, 2]
    
    result[:, :, 0] = np.roll(r_channel, offset, axis=1)
    result[:, :, 1] = g_channel
    result[:, :, 2] = np.roll(b_channel, -offset, axis=1)
    
    return Image.fromarray(result)


def apply_xerox_degradation(image, intensity=0.4):
    """Apply xerox photocopy degradation effect."""
    img_array = np.array(image).astype(np.float32)
    
    img_array = img_array * (1 + intensity * 0.3)
    img_array = np.clip(img_array, 0, 255)
    
    img_pil = Image.fromarray(img_array.astype(np.uint8))
    img_pil = img_pil.filter(ImageFilter.GaussianBlur(radius=intensity * 2))
    img_array = np.array(img_pil).astype(np.float32)
    
    threshold = 128
    img_array = np.where(img_array > threshold, 255, 0)
    
    noise = np.random.normal(0, intensity * 30, img_array.shape)
    img_array = img_array + noise
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    return Image.fromarray(img_array)


def apply_scanlines(image, line_spacing=3, intensity=0.3):
    """Apply scanline effect."""
    img_array = np.array(image)
    height = img_array.shape[0]
    
    for y in range(0, height, line_spacing):
        img_array[y, :] = (img_array[y, :] * (1 - intensity)).astype(np.uint8)
    
    return Image.fromarray(img_array)


def apply_color_shift(image, r_shift=0, g_shift=0, b_shift=0):
    """Apply color channel shift."""
    img_array = np.array(image).astype(np.int16)
    
    img_array[:, :, 0] = np.clip(img_array[:, :, 0] + r_shift, 0, 255)
    img_array[:, :, 1] = np.clip(img_array[:, :, 1] + g_shift, 0, 255)
    img_array[:, :, 2] = np.clip(img_array[:, :, 2] + b_shift, 0, 255)
    
    return Image.fromarray(img_array.astype(np.uint8))


def apply_pixelate(image, block_size=5):
    """Apply pixelation effect."""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    result = np.zeros_like(img_array)
    
    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            y_end = min(y + block_size, height)
            x_end = min(x + block_size, width)
            
            block = img_array[y:y_end, x:x_end]
            avg_color = block.mean(axis=(0, 1)).astype(np.uint8)
            
            result[y:y_end, x:x_end] = avg_color
    
    return Image.fromarray(result)
