"""Typography rendering for lyrics and titles."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import os


class TypographyRenderer:
    def __init__(self):
        self.fonts = {}
        self._load_fonts()
    
    def _load_fonts(self):
        """Load available fonts with fallbacks."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ]
        
        mono_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        ]
        
        self.fonts['bold'] = None
        for path in font_paths:
            if os.path.exists(path):
                self.fonts['bold'] = path
                break
        
        self.fonts['mono'] = None
        for path in mono_paths:
            if os.path.exists(path):
                self.fonts['mono'] = path
                break
        
        if self.fonts['bold'] is None:
            self.fonts['bold'] = 'default'
        if self.fonts['mono'] is None:
            self.fonts['mono'] = self.fonts['bold']
    
    def _get_font(self, font_size, font_type='bold'):
        """Get font object with specified size."""
        font_path = self.fonts.get(font_type, self.fonts['bold'])
        
        try:
            if font_path == 'default':
                return ImageFont.load_default()
            return ImageFont.truetype(font_path, font_size)
        except:
            return ImageFont.load_default()
    
    def render_text(self, text, position, font_size, color, style="normal", image=None):
        """Render text with various styles."""
        if image is None:
            image = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        
        draw = ImageDraw.Draw(image)
        font = self._get_font(font_size)
        
        if style == "normal":
            draw.text(position, text, fill=color, font=font)
        elif style == "bold":
            for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                draw.text((position[0] + offset[0], position[1] + offset[1]), 
                         text, fill=color, font=font)
        elif style == "outline":
            outline_color = (0, 0, 0, 255)
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        draw.text((position[0] + dx, position[1] + dy), 
                                 text, fill=outline_color, font=font)
            draw.text(position, text, fill=color, font=font)
        
        return image
    
    def render_stamped_text(self, text, position, color, angle=0):
        """Render text as if stamped by bureaucratic machine."""
        font_size = 48
        font = self._get_font(font_size, 'bold')
        
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0] + 40
        text_height = bbox[3] - bbox[1] + 40
        
        stamp_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        stamp_draw = ImageDraw.Draw(stamp_img)
        
        border_color = (*color[:3], 200)
        stamp_draw.rectangle([5, 5, text_width-6, text_height-6], 
                           outline=border_color, width=3)
        
        text_x = (text_width - (bbox[2] - bbox[0])) // 2
        text_y = (text_height - (bbox[3] - bbox[1])) // 2
        stamp_draw.text((text_x, text_y), text, fill=color, font=font)
        
        stamp_array = np.array(stamp_img)
        noise = np.random.randint(-30, 30, stamp_array.shape)
        stamp_array[:, :, 3] = np.clip(stamp_array[:, :, 3] + noise[:, :, 3], 0, 255)
        stamp_img = Image.fromarray(stamp_array)
        
        if angle != 0:
            stamp_img = stamp_img.rotate(angle, expand=True, resample=Image.BICUBIC)
        
        result = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        result.paste(stamp_img, position, stamp_img)
        
        return result
    
    def render_neon_text(self, text, position, color, glow_radius=10):
        """Render text with neon glow effect."""
        font_size = 64
        font = self._get_font(font_size, 'bold')
        
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0] + glow_radius * 4
        text_height = bbox[3] - bbox[1] + glow_radius * 4
        
        text_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        
        text_x = (text_width - (bbox[2] - bbox[0])) // 2
        text_y = (text_height - (bbox[3] - bbox[1])) // 2
        
        glow_color = (*color[:3], 100)
        for offset in range(glow_radius, 0, -2):
            alpha = int(100 * (1 - offset / glow_radius))
            glow_color = (*color[:3], alpha)
            for dx in range(-offset, offset+1, 2):
                for dy in range(-offset, offset+1, 2):
                    text_draw.text((text_x + dx, text_y + dy), 
                                  text, fill=glow_color, font=font)
        
        text_draw.text((text_x, text_y), text, fill=(*color[:3], 255), font=font)
        
        result = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        result.paste(text_img, position, text_img)
        
        return result
    
    def render_glitch_text(self, text, position, color, glitch_amount=0.3):
        """Render text with glitch effect."""
        font_size = 56
        font = self._get_font(font_size, 'bold')
        
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0] + 20
        text_height = bbox[3] - bbox[1] + 20
        
        text_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        
        text_x = 10
        text_y = 10
        
        r_color = (255, 0, 0, 200)
        g_color = (0, 255, 0, 200)
        b_color = (0, 0, 255, 200)
        
        offset = int(glitch_amount * 5)
        text_draw.text((text_x - offset, text_y), text, fill=r_color, font=font)
        text_draw.text((text_x, text_y), text, fill=g_color, font=font)
        text_draw.text((text_x + offset, text_y), text, fill=b_color, font=font)
        
        text_array = np.array(text_img)
        num_slices = int(glitch_amount * 10)
        
        for _ in range(num_slices):
            y_start = np.random.randint(0, text_height - 5)
            slice_height = np.random.randint(1, 5)
            y_end = min(y_start + slice_height, text_height)
            
            x_offset = np.random.randint(-10, 10)
            if x_offset > 0:
                text_array[y_start:y_end, x_offset:] = text_array[y_start:y_end, :-x_offset]
                text_array[y_start:y_end, :x_offset] = 0
            elif x_offset < 0:
                text_array[y_start:y_end, :x_offset] = text_array[y_start:y_end, -x_offset:]
                text_array[y_start:y_end, x_offset:] = 0
        
        text_img = Image.fromarray(text_array)
        
        result = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        result.paste(text_img, position, text_img)
        
        return result
    
    def render_typewriter_text(self, text, position, color, progress=1.0):
        """Render text as if being typed."""
        visible_chars = int(len(text) * progress)
        visible_text = text[:visible_chars]
        
        font_size = 36
        font = self._get_font(font_size, 'mono')
        
        text_img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        
        draw.text(position, visible_text, fill=color, font=font)
        
        if progress < 1.0 and int(progress * 20) % 2 == 0:
            cursor_x = position[0] + draw.textlength(visible_text, font=font)
            draw.rectangle([cursor_x, position[1], cursor_x + 2, position[1] + font_size], 
                          fill=color)
        
        return text_img
