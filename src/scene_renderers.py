"""Scene renderers for each movement and shot type."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import math
import random


class MovementIRenderer:
    """Roles Assigned - bureaucratic chambers, masks descending."""
    
    def __init__(self):
        self.frame_count = 0
    
    def render(self, draw, width, height, progress, palette):
        """Render bureaucratic chamber scene."""
        bg_color = palette.get('background', (10, 10, 15))
        draw.rectangle([0, 0, width, height], fill=bg_color)
        
        self._draw_corridor(draw, width, height, progress)
        self._draw_filing_cabinets(draw, width, height, progress)
        self._draw_fluorescent_lights(draw, width, height, progress)
        
        if progress > 0.3:
            self._draw_masks_descending(draw, width, height, progress)
        
        self._draw_desk_figures(draw, width, height, progress)
        
        self.frame_count += 1
    
    def _draw_corridor(self, draw, width, height, progress):
        """Draw perspective corridor."""
        vanish_x = width // 2
        vanish_y = height // 3
        
        for i in range(20):
            t = i / 20
            x1 = int(vanish_x + (0 - vanish_x) * t)
            y1 = int(vanish_y + (height - vanish_y) * t)
            x2 = int(vanish_x + (width - vanish_x) * t)
            y2 = y1
            
            alpha = int(100 * (1 - t))
            color = (40, 40, 50, alpha)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=1)
        
        for i in range(10):
            t = i / 10
            y = int(vanish_y + (height - vanish_y) * t)
            x_offset = int((width // 2) * t)
            
            draw.line([(vanish_x - x_offset, y), (vanish_x + x_offset, y)], 
                     fill=(30, 30, 40), width=1)
    
    def _draw_filing_cabinets(self, draw, width, height, progress):
        """Draw rows of filing cabinets."""
        cabinet_color = (50, 45, 40)
        highlight = (70, 65, 55)
        
        for side in [-1, 1]:
            for i in range(5):
                x_base = width // 2 + side * (100 + i * 80)
                y_base = height - 200 - i * 30
                
                cabinet_width = 60 - i * 5
                cabinet_height = 150 - i * 10
                
                draw.rectangle([x_base, y_base, x_base + cabinet_width, y_base + cabinet_height],
                             fill=cabinet_color, outline=highlight)
                
                for drawer in range(4):
                    drawer_y = y_base + drawer * (cabinet_height // 4)
                    draw.rectangle([x_base + 5, drawer_y + 2, 
                                  x_base + cabinet_width - 5, drawer_y + cabinet_height // 4 - 2],
                                 fill=highlight)
                    draw.ellipse([x_base + cabinet_width // 2 - 2, drawer_y + 10,
                                x_base + cabinet_width // 2 + 2, drawer_y + 14],
                               fill=(100, 90, 70))
    
    def _draw_fluorescent_lights(self, draw, width, height, progress):
        """Draw flickering fluorescent lights."""
        flicker = (math.sin(self.frame_count * 0.3) + 1) / 2
        intensity = int(150 + flicker * 100)
        
        light_color = (intensity, intensity, int(intensity * 0.9))
        
        for i in range(3):
            x = width // 4 + i * (width // 4)
            y = 50 + i * 20
            
            draw.rectangle([x - 40, y, x + 40, y + 8], fill=light_color)
            
            glow_size = 60 + int(flicker * 20)
            for r in range(glow_size, 0, -2):
                alpha = int(30 * (1 - r / glow_size))
                glow_color = (*light_color, alpha)
                draw.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=glow_color)
    
    def _draw_masks_descending(self, draw, width, height, progress):
        """Draw masks descending on wires."""
        mask_progress = (progress - 0.3) / 0.7
        
        for i in range(3):
            x = width // 3 + i * (width // 3)
            y = int(height * 0.2 + mask_progress * height * 0.4)
            
            draw.line([(x, 0), (x, y - 30)], fill=(80, 80, 80), width=1)
            
            mask_size = 40
            draw.ellipse([x - mask_size // 2, y - mask_size // 2,
                         x + mask_size // 2, y + mask_size // 2],
                        fill=(200, 190, 170), outline=(100, 90, 70), width=2)
            
            eye_y = y - 5
            draw.ellipse([x - 12, eye_y - 4, x - 6, eye_y + 4], fill=(20, 20, 20))
            draw.ellipse([x + 6, eye_y - 4, x + 12, eye_y + 4], fill=(20, 20, 20))
            
            draw.arc([x - 8, y + 5, x + 8, y + 15], 0, 180, fill=(20, 20, 20), width=2)
    
    def _draw_desk_figures(self, draw, width, height, progress):
        """Draw slumped figures at desks."""
        for i in range(4):
            x = 200 + i * 150
            y = height - 150
            
            draw.rectangle([x - 30, y, x + 30, y + 40], fill=(60, 55, 50))
            
            figure_color = (80, 75, 70)
            draw.ellipse([x - 15, y - 30, x + 15, y], fill=figure_color)
            
            if progress < 0.5:
                draw.ellipse([x - 10, y - 20, x + 10, y - 5], fill=(100, 95, 85))


class MovementIIRenderer:
    """The Maze - impossible corridors, divided populations."""
    
    def __init__(self):
        self.frame_count = 0
    
    def render(self, draw, width, height, progress, palette):
        """Render maze scene."""
        bg_color = palette.get('background', (30, 10, 50))
        draw.rectangle([0, 0, width, height], fill=bg_color)
        
        self._draw_maze_walls(draw, width, height, progress)
        self._draw_divided_figures(draw, width, height, progress)
        self._draw_impossible_geometry(draw, width, height, progress)
        
        if progress > 0.5:
            self._draw_conflict_sparks(draw, width, height, progress)
        
        self.frame_count += 1
    
    def _draw_maze_walls(self, draw, width, height, progress):
        """Draw maze wall pattern."""
        wall_color = (80, 40, 120)
        highlight = (120, 60, 160)
        
        random.seed(42)
        
        for i in range(15):
            x = random.randint(0, width - 100)
            y = random.randint(0, height - 100)
            wall_length = random.randint(80, 200)
            horizontal = random.choice([True, False])
            
            shift = int(math.sin(self.frame_count * 0.02 + i) * 10)
            
            if horizontal:
                draw.rectangle([x + shift, y, x + wall_length + shift, y + 8],
                             fill=wall_color, outline=highlight)
            else:
                draw.rectangle([x, y + shift, x + 8, y + wall_length + shift],
                             fill=wall_color, outline=highlight)
    
    def _draw_divided_figures(self, draw, width, height, progress):
        """Draw figures on opposite sides of walls."""
        wall_x = width // 2
        
        draw.rectangle([wall_x - 10, 0, wall_x + 10, height], fill=(60, 30, 90))
        
        for side in [-1, 1]:
            for i in range(3):
                x = wall_x + side * (80 + i * 60)
                y = 200 + i * 150
                
                figure_color = (150, 140, 130) if side == -1 else (130, 140, 150)
                draw.ellipse([x - 15, y - 40, x + 15, y], fill=figure_color)
                draw.rectangle([x - 12, y, x + 12, y + 50], fill=figure_color)
                
                if progress > 0.3:
                    hand_x = x + side * 20
                    hand_y = y + 20
                    draw.line([(x, y + 20), (hand_x, hand_y)], fill=figure_color, width=3)
    
    def _draw_impossible_geometry(self, draw, width, height, progress):
        """Draw impossible architectural elements."""
        center_x = width // 2
        center_y = height // 2
        
        angle = self.frame_count * 0.01
        
        for i in range(4):
            a = angle + i * math.pi / 2
            x1 = int(center_x + math.cos(a) * 150)
            y1 = int(center_y + math.sin(a) * 150)
            x2 = int(center_x + math.cos(a + 0.5) * 200)
            y2 = int(center_y + math.sin(a + 0.5) * 200)
            
            draw.line([(x1, y1), (x2, y2)], fill=(100, 50, 150), width=3)
            
            x3 = int(center_x + math.cos(a + 1.0) * 100)
            y3 = int(center_y + math.sin(a + 1.0) * 100)
            draw.line([(x2, y2), (x3, y3)], fill=(100, 50, 150), width=3)
    
    def _draw_conflict_sparks(self, draw, width, height, progress):
        """Draw sparks of conflict."""
        spark_intensity = (progress - 0.5) * 2
        
        for _ in range(int(spark_intensity * 20)):
            x = random.randint(width // 2 - 50, width // 2 + 50)
            y = random.randint(height // 3, height * 2 // 3)
            
            spark_color = (255, 200, 100)
            size = random.randint(2, 5)
            draw.ellipse([x - size, y - size, x + size, y + size], fill=spark_color)


class MovementIIIRenderer:
    """Manufactured War - industrial conflict, machinery."""
    
    def __init__(self):
        self.frame_count = 0
    
    def render(self, draw, width, height, progress, palette):
        """Render industrial war scene."""
        bg_color = palette.get('background', (50, 10, 10))
        draw.rectangle([0, 0, width, height], fill=bg_color)
        
        self._draw_factory_structure(draw, width, height, progress)
        self._draw_assembly_line(draw, width, height, progress)
        self._draw_gears_and_machinery(draw, width, height, progress)
        self._draw_marching_figures(draw, width, height, progress)
        
        self.frame_count += 1
    
    def _draw_factory_structure(self, draw, width, height, progress):
        """Draw factory building structure."""
        steel_color = (80, 70, 60)
        rust_color = (120, 80, 50)
        
        for i in range(5):
            x = i * (width // 5)
            draw.rectangle([x, 0, x + 20, height], fill=steel_color)
            draw.rectangle([x + 5, 0, x + 15, height], fill=rust_color)
        
        for i in range(3):
            y = i * (height // 3)
            draw.rectangle([0, y, width, y + 15], fill=steel_color)
    
    def _draw_assembly_line(self, draw, width, height, progress):
        """Draw conveyor belt assembly line."""
        belt_y = height // 2
        belt_color = (60, 60, 60)
        
        draw.rectangle([0, belt_y - 10, width, belt_y + 10], fill=belt_color)
        
        offset = int((self.frame_count * 2) % 40)
        for x in range(-offset, width, 40):
            draw.rectangle([x, belt_y - 8, x + 20, belt_y + 8], fill=(80, 80, 80))
        
        for i in range(5):
            x = (i * 200 + offset) % width
            y = belt_y - 30
            
            draw.rectangle([x - 15, y, x + 15, y + 20], fill=(150, 140, 130))
            draw.ellipse([x - 10, y - 15, x + 10, y], fill=(150, 140, 130))
    
    def _draw_gears_and_machinery(self, draw, width, height, progress):
        """Draw rotating gears and machinery."""
        gear_positions = [(200, 150), (width - 200, 150), (width // 2, height - 150)]
        
        for gx, gy in gear_positions:
            radius = 60
            angle = self.frame_count * 0.05
            
            num_teeth = 12
            for i in range(num_teeth):
                a = angle + i * (2 * math.pi / num_teeth)
                x1 = int(gx + math.cos(a) * radius)
                y1 = int(gy + math.sin(a) * radius)
                x2 = int(gx + math.cos(a) * (radius + 15))
                y2 = int(gy + math.sin(a) * (radius + 15))
                
                draw.line([(x1, y1), (x2, y2)], fill=(100, 90, 70), width=8)
            
            draw.ellipse([gx - radius, gy - radius, gx + radius, gy + radius],
                        outline=(100, 90, 70), width=4)
            draw.ellipse([gx - 10, gy - 10, gx + 10, gy + 10], fill=(80, 70, 60))
    
    def _draw_marching_figures(self, draw, width, height, progress):
        """Draw marching masked figures."""
        march_offset = (self.frame_count * 3) % 100
        
        for i in range(8):
            x = i * 120 + march_offset
            if x > width:
                x -= width
            
            y = height - 100
            step = math.sin(self.frame_count * 0.1 + i) * 5
            
            figure_color = (120, 110, 100)
            draw.ellipse([x - 12, y - 35 + step, x + 12, y - 10 + step], fill=figure_color)
            draw.rectangle([x - 10, y - 10 + step, x + 10, y + 30 + step], fill=figure_color)
            
            draw.ellipse([x - 10, y - 30 + step, x + 10, y - 15 + step],
                        fill=(180, 170, 150), outline=(100, 90, 70))


class MovementIVRenderer:
    """Curtain Pulled Back - revealing the machinery."""
    
    def __init__(self):
        self.frame_count = 0
    
    def render(self, draw, width, height, progress, palette):
        """Render revelation scene."""
        bg_color = palette.get('background', (20, 10, 40))
        draw.rectangle([0, 0, width, height], fill=bg_color)
        
        self._draw_transparent_walls(draw, width, height, progress)
        self._draw_hidden_machinery(draw, width, height, progress)
        self._draw_control_panels(draw, width, height, progress)
        self._draw_revelation_light(draw, width, height, progress)
        
        self.frame_count += 1
    
    def _draw_transparent_walls(self, draw, width, height, progress):
        """Draw walls becoming transparent."""
        transparency = progress
        
        wall_color = (80, 40, 120, int(200 * (1 - transparency)))
        
        for i in range(3):
            x = 300 + i * 400
            draw.rectangle([x, 100, x + 50, height - 100], fill=wall_color)
            
            if transparency > 0.3:
                glass_color = (150, 200, 255, int(100 * transparency))
                draw.rectangle([x + 5, 105, x + 45, height - 105], fill=glass_color)
    
    def _draw_hidden_machinery(self, draw, width, height, progress):
        """Draw machinery behind walls."""
        if progress < 0.2:
            return
        
        machinery_alpha = min(1.0, (progress - 0.2) * 2)
        
        for i in range(4):
            x = 200 + i * 300
            y = 200 + (i % 2) * 200
            
            gear_radius = 40
            angle = self.frame_count * 0.03 * (1 if i % 2 == 0 else -1)
            
            for j in range(8):
                a = angle + j * math.pi / 4
                x1 = int(x + math.cos(a) * gear_radius)
                y1 = int(y + math.sin(a) * gear_radius)
                x2 = int(x + math.cos(a) * (gear_radius + 10))
                y2 = int(y + math.sin(a) * (gear_radius + 10))
                
                color = (255, 100, 200, int(200 * machinery_alpha))
                draw.line([(x1, y1), (x2, y2)], fill=color, width=6)
            
            draw.ellipse([x - gear_radius, y - gear_radius, 
                         x + gear_radius, y + gear_radius],
                        outline=(255, 100, 200, int(200 * machinery_alpha)), width=3)
        
        for i in range(5):
            x1 = 100 + i * 200
            y1 = 150
            x2 = x1 + 100
            y2 = height - 150
            
            draw.line([(x1, y1), (x2, y2)], 
                     fill=(200, 150, 255, int(150 * machinery_alpha)), width=2)
    
    def _draw_control_panels(self, draw, width, height, progress):
        """Draw control panels and screens."""
        if progress < 0.4:
            return
        
        panel_alpha = min(1.0, (progress - 0.4) * 2.5)
        
        panel_x = width // 2 - 150
        panel_y = height // 2 - 100
        
        draw.rectangle([panel_x, panel_y, panel_x + 300, panel_y + 200],
                      fill=(40, 40, 50, int(200 * panel_alpha)),
                      outline=(100, 200, 255, int(255 * panel_alpha)), width=2)
        
        for i in range(3):
            screen_x = panel_x + 20 + i * 90
            screen_y = panel_y + 20
            
            screen_color = (0, 255, 100, int(200 * panel_alpha))
            draw.rectangle([screen_x, screen_y, screen_x + 70, screen_y + 50],
                          fill=(20, 20, 30, int(200 * panel_alpha)),
                          outline=screen_color, width=2)
            
            for j in range(5):
                bar_x = screen_x + 5 + j * 12
                bar_height = int(30 * (0.5 + 0.5 * math.sin(self.frame_count * 0.1 + j)))
                draw.rectangle([bar_x, screen_y + 45 - bar_height, bar_x + 8, screen_y + 45],
                              fill=screen_color)
        
        for i in range(4):
            button_x = panel_x + 30 + i * 60
            button_y = panel_y + 100
            
            button_color = (255, 50, 50, int(200 * panel_alpha))
            draw.ellipse([button_x, button_y, button_x + 20, button_y + 20],
                        fill=button_color)
    
    def _draw_revelation_light(self, draw, width, height, progress):
        """Draw light of revelation."""
        if progress < 0.5:
            return
        
        light_intensity = (progress - 0.5) * 2
        
        center_x = width // 2
        center_y = height // 2
        
        for r in range(int(300 * light_intensity), 0, -5):
            alpha = int(50 * light_intensity * (1 - r / (300 * light_intensity)))
            color = (255, 200, 255, alpha)
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r],
                        fill=color)


class MovementVRenderer:
    """Power Returned - distributed agency, constellation people."""
    
    def __init__(self):
        self.frame_count = 0
        self.particles = []
        self._init_particles()
    
    def _init_particles(self):
        """Initialize particle system."""
        for i in range(50):
            self.particles.append({
                'x': random.randint(0, 1920),
                'y': random.randint(0, 1080),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'size': random.randint(2, 5),
                'color': random.choice([(255, 200, 100), (100, 200, 255), (200, 100, 255)])
            })
    
    def render(self, draw, width, height, progress, palette):
        """Render constellation people scene."""
        bg_color = palette.get('background', (10, 20, 40))
        draw.rectangle([0, 0, width, height], fill=bg_color)
        
        self._draw_light_fragments(draw, width, height, progress)
        self._draw_constellation_people(draw, width, height, progress)
        self._draw_connection_network(draw, width, height, progress)
        self._draw_creative_emergence(draw, width, height, progress)
        
        self.frame_count += 1
    
    def _draw_light_fragments(self, draw, width, height, progress):
        """Draw floating light fragments."""
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            if particle['x'] < 0 or particle['x'] > width:
                particle['vx'] *= -1
            if particle['y'] < 0 or particle['y'] > height:
                particle['vy'] *= -1
            
            size = particle['size']
            x, y = int(particle['x']), int(particle['y'])
            
            for r in range(size * 3, 0, -1):
                alpha = int(100 * (1 - r / (size * 3)) * progress)
                color = (*particle['color'], alpha)
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
            
            draw.ellipse([x - size, y - size, x + size, y + size], 
                        fill=(*particle['color'], 255))
    
    def _draw_constellation_people(self, draw, width, height, progress):
        """Draw people as constellation points."""
        center_x = width // 2
        center_y = height // 2
        radius = 250
        
        num_people = 12
        for i in range(num_people):
            angle = i * (2 * math.pi / num_people) + self.frame_count * 0.005
            x = int(center_x + math.cos(angle) * radius)
            y = int(center_y + math.sin(angle) * radius)
            
            person_color = (200, 220, 255)
            draw.ellipse([x - 15, y - 40, x + 15, y - 10], fill=person_color)
            draw.rectangle([x - 12, y - 10, x + 12, y + 30], fill=person_color)
            
            glow_size = 25 + int(10 * math.sin(self.frame_count * 0.1 + i))
            for r in range(glow_size, 0, -2):
                alpha = int(80 * (1 - r / glow_size))
                glow_color = (255, 255, 200, alpha)
                draw.ellipse([x - r, y - r, x + r, y + r], fill=glow_color)
    
    def _draw_connection_network(self, draw, width, height, progress):
        """Draw network of connections between people."""
        if progress < 0.3:
            return
        
        network_alpha = min(1.0, (progress - 0.3) * 2)
        
        center_x = width // 2
        center_y = height // 2
        radius = 250
        
        num_people = 12
        positions = []
        for i in range(num_people):
            angle = i * (2 * math.pi / num_people) + self.frame_count * 0.005
            x = int(center_x + math.cos(angle) * radius)
            y = int(center_y + math.sin(angle) * radius)
            positions.append((x, y))
        
        for i in range(num_people):
            for j in range(i + 1, num_people):
                if (i + j) % 3 == 0:
                    x1, y1 = positions[i]
                    x2, y2 = positions[j]
                    
                    pulse = (math.sin(self.frame_count * 0.05 + i + j) + 1) / 2
                    line_alpha = int(150 * network_alpha * (0.5 + 0.5 * pulse))
                    
                    draw.line([(x1, y1), (x2, y2)], 
                             fill=(255, 220, 100, line_alpha), width=2)
    
    def _draw_creative_emergence(self, draw, width, height, progress):
        """Draw creative emergence effects."""
        if progress < 0.6:
            return
        
        emergence = (progress - 0.6) * 2.5
        
        center_x = width // 2
        center_y = height // 2
        
        for i in range(8):
            angle = i * math.pi / 4 + self.frame_count * 0.02
            length = int(100 * emergence)
            
            x1 = center_x
            y1 = center_y
            x2 = int(center_x + math.cos(angle) * length)
            y2 = int(center_y + math.sin(angle) * length)
            
            color = (255, 200, 100, int(200 * emergence))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=3)
            
            for r in range(20, 0, -2):
                alpha = int(100 * emergence * (1 - r / 20))
                glow_color = (255, 220, 150, alpha)
                draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=glow_color)
