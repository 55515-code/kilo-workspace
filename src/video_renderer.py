#!/usr/bin/env python3
"""
Main video renderer for The Magician's Empire music video.
Generates frames procedurally and assembles with FFmpeg.
"""
import os
import sys
import csv
import json
import shutil
import logging
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from scene_renderers import (
    MovementIRenderer, MovementIIRenderer, MovementIIIRenderer,
    MovementIVRenderer, MovementVRenderer
)
from effects import (
    apply_glitch_effect, apply_crt_effect, apply_film_grain,
    apply_vignette, apply_chromatic_aberration, apply_xerox_degradation,
    apply_scanlines, apply_color_shift
)
from typography import TypographyRenderer
from texture_generator import (
    generate_noise_texture, generate_grid_pattern, generate_circuit_pattern,
    generate_gradient, generate_radial_gradient
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class VideoRenderer:
    WIDTH = 1920
    HEIGHT = 1080
    FPS = 24
    
    MOVEMENT_CONFIGS = {
        1: {
            'name': 'Roles Assigned',
            'background': (10, 10, 15),
            'palette_group': 'opening',
            'effects': ['film_grain', 'vignette', 'xerox'],
            'effect_intensity': 0.3,
        },
        2: {
            'name': 'The Maze',
            'background': (30, 10, 50),
            'palette_group': 'escalation',
            'effects': ['glitch', 'scanlines', 'vignette'],
            'effect_intensity': 0.4,
        },
        3: {
            'name': 'Manufactured War',
            'background': (50, 10, 10),
            'palette_group': 'escalation',
            'effects': ['film_grain', 'chromatic_aberration', 'vignette'],
            'effect_intensity': 0.5,
        },
        4: {
            'name': 'Curtain Pulled Back',
            'background': (20, 10, 40),
            'palette_group': 'revelation',
            'effects': ['chromatic_aberration', 'scanlines', 'vignette'],
            'effect_intensity': 0.35,
        },
        5: {
            'name': 'Power Returned',
            'background': (10, 20, 40),
            'palette_group': 'resolution',
            'effects': ['film_grain', 'vignette'],
            'effect_intensity': 0.25,
        },
    }
    
    def __init__(self, base_dir=None, config_path="analysis/audio_features.json",
                 start_frame=0, end_frame=None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        self.base_dir = Path(base_dir)
        
        self.config_path = self.base_dir / config_path
        self.shot_list_path = self.base_dir / "docs" / "shot_list.csv"
        self.section_map_path = self.base_dir / "analysis" / "section_map.json"
        self.visual_palette_path = self.base_dir / "analysis" / "visual_palette.json"
        self.audio_features_path = self.base_dir / "analysis" / "audio_features.json"
        
        self.frames_dir = self.base_dir / "deliverables" / "frames"
        self.output_dir = self.base_dir / "deliverables"
        self.output_video = self.output_dir / "magicians_empire.mp4"
        
        self.start_frame = start_frame
        self.end_frame = end_frame
        
        self.shots = []
        self.sections = []
        self.palette = {}
        self.audio_features = {}
        self.total_duration = 270.0
        
        self.renderers = {
            1: MovementIRenderer(),
            2: MovementIIRenderer(),
            3: MovementIIIRenderer(),
            4: MovementIVRenderer(),
            5: MovementVRenderer(),
        }
        
        self.typography = TypographyRenderer()
        
        self._load_config()
        self._setup_directories()
    
    def _load_config(self):
        """Load all configuration files."""
        logger.info("Loading configuration files...")
        
        self._load_shot_list()
        self._load_section_map()
        self._load_visual_palette()
        self._load_audio_features()
        
        logger.info(f"Loaded {len(self.shots)} shots, {len(self.sections)} sections")
        logger.info(f"Total duration: {self.total_duration}s @ {self.FPS}fps = "
                    f"{int(self.total_duration * self.FPS)} frames")
    
    def _load_shot_list(self):
        """Load shot list from CSV."""
        if not self.shot_list_path.exists():
            logger.warning(f"Shot list not found: {self.shot_list_path}")
            return
        
        with open(self.shot_list_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                shot = {
                    'shot_id': row['shot_id'],
                    'start_time': self._parse_time(row['start_time']),
                    'end_time': self._parse_time(row['end_time']),
                    'duration': float(row['duration']),
                    'narrative_purpose': row.get('narrative_purpose', ''),
                    'primary_visual': row.get('primary_visual', ''),
                    'camera_movement': row.get('camera_movement', ''),
                    'transition_in': row.get('transition_in', ''),
                    'transition_out': row.get('transition_out', ''),
                    'dominant_palette': row.get('dominant_palette', ''),
                    'typography_use': row.get('typography_use', ''),
                    'production_method': row.get('production_method', ''),
                }
                self.shots.append(shot)
        
        if self.shots:
            self.total_duration = max(s['end_time'] for s in self.shots)
    
    def _load_section_map(self):
        """Load section map from JSON."""
        if not self.section_map_path.exists():
            logger.warning(f"Section map not found: {self.section_map_path}")
            return
        
        with open(self.section_map_path, 'r') as f:
            data = json.load(f)
        
        self.sections = data.get('sections', [])
        self.total_duration = data.get('total_duration_seconds', self.total_duration)
    
    def _load_visual_palette(self):
        """Load visual palette from JSON."""
        if not self.visual_palette_path.exists():
            logger.warning(f"Visual palette not found: {self.visual_palette_path}")
            return
        
        with open(self.visual_palette_path, 'r') as f:
            self.palette = json.load(f)
    
    def _load_audio_features(self):
        """Load audio features from JSON."""
        if not self.audio_features_path.exists():
            logger.warning(f"Audio features not found: {self.audio_features_path}")
            return
        
        with open(self.audio_features_path, 'r') as f:
            self.audio_features = json.load(f)
    
    def _setup_directories(self):
        """Create output directories."""
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _parse_time(time_str):
        """Parse time string (MM:SS or H:MM:SS) to seconds."""
        parts = time_str.strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return float(time_str)
    
    def _get_current_shot(self, timestamp):
        """Determine which shot is active at the given timestamp."""
        for shot in self.shots:
            if shot['start_time'] <= timestamp < shot['end_time']:
                return shot
        if self.shots and timestamp >= self.shots[-1]['start_time']:
            return self.shots[-1]
        return self.shots[0] if self.shots else None
    
    def _get_current_section(self, timestamp):
        """Determine which section is active at the given timestamp."""
        for section in self.sections:
            if section['start'] <= timestamp < section['end']:
                return section
        if self.sections and timestamp >= self.sections[-1]['start']:
            return self.sections[-1]
        return self.sections[0] if self.sections else None
    
    def _get_movement_for_shot(self, shot):
        """Determine which movement a shot belongs to."""
        if shot is None:
            return 1
        
        shot_num = int(shot['shot_id'][1:])
        
        if shot_num <= 13:
            return 1
        elif shot_num <= 23:
            return 2
        elif shot_num <= 35:
            return 3
        elif shot_num <= 48:
            return 4
        else:
            return 5
    
    def _get_energy_at_time(self, timestamp):
        """Interpolate energy value at given timestamp."""
        curve = self.audio_features.get('energy_curve', [])
        if not curve:
            return 0.5
        
        if timestamp <= curve[0]['time']:
            return curve[0]['energy']
        if timestamp >= curve[-1]['time']:
            return curve[-1]['energy']
        
        for i in range(len(curve) - 1):
            if curve[i]['time'] <= timestamp < curve[i + 1]['time']:
                t = (timestamp - curve[i]['time']) / (curve[i + 1]['time'] - curve[i]['time'])
                return curve[i]['energy'] + t * (curve[i + 1]['energy'] - curve[i]['energy'])
        
        return 0.5
    
    def _get_palette_for_movement(self, movement):
        """Get color palette for a movement."""
        config = self.MOVEMENT_CONFIGS.get(movement, self.MOVEMENT_CONFIGS[1])
        palette_group = config['palette_group']
        
        base_palette = self.palette.get('base_palette', {})
        colors = base_palette.get(palette_group, [])
        
        result = {
            'background': config['background'],
            'primary': (200, 200, 200),
            'secondary': (100, 100, 120),
            'accent': (255, 200, 100),
        }
        
        if len(colors) >= 1:
            result['primary'] = tuple(colors[0].get('rgb', [200, 200, 200]))
        if len(colors) >= 2:
            result['secondary'] = tuple(colors[1].get('rgb', [100, 100, 120]))
        if len(colors) >= 3:
            result['accent'] = tuple(colors[2].get('rgb', [255, 200, 100]))
        
        accent_colors = self.palette.get('accent_colors', [])
        if accent_colors:
            result['highlight'] = tuple(accent_colors[0].get('rgb', [255, 100, 100]))
        
        return result
    
    def _apply_transition(self, image, shot, timestamp):
        """Apply transition effects at shot boundaries."""
        if shot is None:
            return image
        
        shot_duration = shot['end_time'] - shot['start_time']
        shot_progress = (timestamp - shot['start_time']) / max(shot_duration, 0.001)
        
        transition_in = shot.get('transition_in', '')
        transition_out = shot.get('transition_out', '')
        
        fade_duration = 0.15
        
        if transition_in in ('Black fade-in',) and shot_progress < fade_duration:
            alpha = shot_progress / fade_duration
            img_array = np.array(image).astype(np.float32)
            img_array = img_array * alpha
            image = Image.fromarray(img_array.astype(np.uint8))
        
        if transition_out in ('Slow fade',) and shot_progress > (1 - fade_duration):
            alpha = (1 - shot_progress) / fade_duration
            img_array = np.array(image).astype(np.float32)
            img_array = img_array * alpha
            image = Image.fromarray(img_array.astype(np.uint8))
        
        return image
    
    def _apply_post_processing(self, image, movement, energy, timestamp):
        """Apply post-processing effects based on movement and energy."""
        config = self.MOVEMENT_CONFIGS.get(movement, self.MOVEMENT_CONFIGS[1])
        effects = config['effects']
        base_intensity = config['effect_intensity']
        
        intensity = base_intensity * (0.5 + energy * 0.5)
        
        for effect_name in effects:
            if effect_name == 'glitch':
                image = apply_glitch_effect(image, intensity=intensity * 0.5)
            elif effect_name == 'crt':
                image = apply_crt_effect(image, scanline_intensity=intensity * 0.3)
            elif effect_name == 'film_grain':
                image = apply_film_grain(image, intensity=intensity * 0.4)
            elif effect_name == 'vignette':
                image = apply_vignette(image, strength=intensity * 0.6)
            elif effect_name == 'chromatic_aberration':
                offset = max(1, int(intensity * 4))
                image = apply_chromatic_aberration(image, offset=offset)
            elif effect_name == 'xerox':
                image = apply_xerox_degradation(image, intensity=intensity * 0.3)
            elif effect_name == 'scanlines':
                image = apply_scanlines(image, line_spacing=3, intensity=intensity * 0.3)
        
        return image
    
    def _render_typography(self, image, shot, timestamp, movement):
        """Render typography overlays for the current shot."""
        if shot is None:
            return image
        
        typography_use = shot.get('typography_use', '')
        if not typography_use or typography_use == 'None':
            return image
        
        shot_duration = shot['end_time'] - shot['start_time']
        shot_progress = (timestamp - shot['start_time']) / max(shot_duration, 0.001)
        
        palette_colors = self._get_palette_for_movement(movement)
        text_color = palette_colors.get('primary', (200, 200, 200))
        
        if 'Title card' in typography_use:
            if shot_progress < 0.8:
                text = "THE MAGICIAN'S EMPIRE"
                text_img = self.typography.render_neon_text(
                    text, (self.WIDTH // 2 - 400, self.HEIGHT // 2 - 40),
                    text_color, glow_radius=15
                )
                image = Image.alpha_composite(image.convert('RGBA'), text_img)
        
        elif 'MASK' in typography_use:
            text = "MASK"
            text_img = self.typography.render_stamped_text(
                text, (self.WIDTH // 2 - 60, 80),
                text_color, angle=-5
            )
            image = Image.alpha_composite(image.convert('RGBA'), text_img)
        
        elif 'neighbor' in typography_use.lower() or 'enemy' in typography_use.lower():
            text = "YOUR NEIGHBOR IS NOT THE ENEMY"
            alpha = min(1.0, shot_progress * 2)
            if alpha > 0.1:
                text_color_rgba = (*text_color[:3], int(255 * alpha))
                text_img = self.typography.render_text(
                    text, (self.WIDTH // 2 - 400, self.HEIGHT - 120),
                    36, text_color_rgba, style="outline",
                    image=Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
                )
                image = Image.alpha_composite(image.convert('RGBA'), text_img)
        
        elif 'DEPARTMENT' in typography_use or 'Environmental text' in typography_use:
            text = typography_use.replace('Environmental text: ', '')
            if len(text) > 40:
                text = "DEPARTMENT OF COMPLIANCE"
            text_img = self.typography.render_glitch_text(
                text, (100, 50), text_color, glitch_amount=0.2
            )
            image = Image.alpha_composite(image.convert('RGBA'), text_img)
        
        elif 'lyric' in typography_use.lower() or 'fragment' in typography_use.lower():
            fragments = [
                "THE MAGICIAN'S EMPIRE",
                "YOUR NEIGHBOR IS NOT THE ENEMY",
                "MASK",
                "ROLES ASSIGNED",
                "THE MAZE",
                "MANUFACTURED WAR",
            ]
            idx = hash(shot.get('shot_id', '')) % len(fragments)
            text = fragments[idx]
            
            alpha = min(1.0, shot_progress * 3) * min(1.0, (1 - shot_progress) * 3)
            if alpha > 0.1:
                text_color_rgba = (*text_color[:3], int(180 * alpha))
                text_img = self.typography.render_text(
                    text, (self.WIDTH // 2 - 200, self.HEIGHT - 80),
                    28, text_color_rgba, style="normal",
                    image=Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
                )
                image = Image.alpha_composite(image.convert('RGBA'), text_img)
        
        return image
    
    def render_frame(self, frame_number, timestamp):
        """Render a single frame at the given timestamp."""
        shot = self._get_current_shot(timestamp)
        section = self._get_current_section(timestamp)
        movement = self._get_movement_for_shot(shot)
        energy = self._get_energy_at_time(timestamp)
        
        palette = self._get_palette_for_movement(movement)
        
        if shot:
            shot_duration = shot['end_time'] - shot['start_time']
            shot_progress = (timestamp - shot['start_time']) / max(shot_duration, 0.001)
            shot_progress = max(0.0, min(1.0, shot_progress))
        else:
            shot_progress = 0.0
        
        image = Image.new('RGB', (self.WIDTH, self.HEIGHT), palette['background'])
        draw = ImageDraw.Draw(image)
        
        renderer = self.renderers.get(movement, self.renderers[1])
        renderer.render(draw, self.WIDTH, self.HEIGHT, shot_progress, palette)
        
        image = self._render_typography(image, shot, timestamp, movement)
        
        image = self._apply_transition(image, shot, timestamp)
        
        image = self._apply_post_processing(image, movement, energy, timestamp)
        
        if movement == 5 and shot_progress > 0.9:
            fade = (1.0 - shot_progress) / 0.1
            img_array = np.array(image).astype(np.float32)
            img_array = img_array * fade
            image = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))
        
        return image
    
    def render_all_frames(self):
        """Render all frames for the video."""
        total_frames = int(self.total_duration * self.FPS)
        
        start = self.start_frame
        end = self.end_frame if self.end_frame is not None else total_frames
        end = min(end, total_frames)
        
        logger.info(f"Rendering frames {start} to {end} of {total_frames}")
        logger.info(f"Resolution: {self.WIDTH}x{self.HEIGHT} @ {self.FPS}fps")
        logger.info(f"Duration: {self.total_duration}s")
        
        current_movement = None
        
        for frame_num in range(start, end):
            timestamp = frame_num / self.FPS
            
            shot = self._get_current_shot(timestamp)
            movement = self._get_movement_for_shot(shot)
            
            if movement != current_movement:
                config = self.MOVEMENT_CONFIGS.get(movement, {})
                logger.info(f"Frame {frame_num}: Movement {movement} - "
                           f"{config.get('name', 'Unknown')}")
                current_movement = movement
            
            try:
                frame = self.render_frame(frame_num, timestamp)
                
                frame_path = self.frames_dir / f"frame_{frame_num:06d}.png"
                frame.save(str(frame_path), 'PNG')
                
            except Exception as e:
                logger.error(f"Error rendering frame {frame_num}: {e}")
                black = Image.new('RGB', (self.WIDTH, self.HEIGHT), (0, 0, 0))
                frame_path = self.frames_dir / f"frame_{frame_num:06d}.png"
                black.save(str(frame_path), 'PNG')
            
            if frame_num % 24 == 0:
                pct = (frame_num - start) / max(end - start, 1) * 100
                logger.info(f"Progress: {frame_num}/{end} ({pct:.1f}%) - "
                           f"t={timestamp:.2f}s")
        
        logger.info(f"Rendering complete. {end - start} frames saved to {self.frames_dir}")
    
    def assemble_video(self, audio_path=None):
        """Assemble frames into video with FFmpeg."""
        logger.info("Assembling video with FFmpeg...")
        
        pattern = str(self.frames_dir / "frame_%06d.png")
        
        if audio_path is None:
            audio_candidates = [
                self.base_dir / "assets" / "audio" / "magicians_empire.mp3",
                self.base_dir / "assets" / "audio" / "magicians_empire.wav",
                self.base_dir / "assets" / "magicians_empire.mp3",
                self.base_dir / "assets" / "magicians_empire.wav",
            ]
            for candidate in audio_candidates:
                if candidate.exists():
                    audio_path = str(candidate)
                    break
        
        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(self.FPS),
            '-i', pattern,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',
            '-crf', '18',
            '-vf', 'scale=1920:1080',
        ]
        
        if audio_path and os.path.exists(audio_path):
            cmd.extend([
                '-i', audio_path,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
            ])
        
        cmd.append(str(self.output_video))
        
        logger.info(f"FFmpeg command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info(f"Video assembled successfully: {self.output_video}")
                
                if os.path.exists(self.output_video):
                    size_mb = os.path.getsize(self.output_video) / (1024 * 1024)
                    logger.info(f"Output file size: {size_mb:.1f} MB")
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                logger.info("Attempting video assembly without audio...")
                
                cmd_no_audio = [
                    'ffmpeg', '-y',
                    '-framerate', str(self.FPS),
                    '-i', pattern,
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-preset', 'medium',
                    '-crf', '18',
                    '-vf', 'scale=1920:1080',
                    '-t', str(self.total_duration),
                    str(self.output_video),
                ]
                
                result = subprocess.run(cmd_no_audio, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    logger.info(f"Video assembled (no audio): {self.output_video}")
                else:
                    logger.error(f"FFmpeg error (no audio): {result.stderr}")
        
        except FileNotFoundError:
            logger.error("FFmpeg not found. Frames saved but video not assembled.")
            logger.info(f"Frames are in: {self.frames_dir}")
            logger.info("Install FFmpeg and run assembly manually:")
            logger.info(f"  ffmpeg -framerate {self.FPS} -i {pattern} "
                       f"-c:v libx264 -pix_fmt yuv420p {self.output_video}")
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timed out. Video assembly incomplete.")
    
    def cleanup_frames(self):
        """Remove rendered frames to save disk space."""
        if self.frames_dir.exists():
            shutil.rmtree(self.frames_dir)
            logger.info(f"Cleaned up frames directory: {self.frames_dir}")
    
    def main(self):
        """Main entry point."""
        logger.info("=" * 60)
        logger.info("THE MAGICIAN'S EMPIRE - Video Renderer")
        logger.info("=" * 60)
        
        self.render_all_frames()
        self.assemble_video()
        
        logger.info("=" * 60)
        logger.info("Rendering pipeline complete")
        logger.info("=" * 60)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Render The Magician's Empire music video"
    )
    parser.add_argument('--start-frame', type=int, default=0,
                       help='First frame to render (default: 0)')
    parser.add_argument('--end-frame', type=int, default=None,
                       help='Last frame to render (default: all)')
    parser.add_argument('--base-dir', type=str, default=None,
                       help='Base project directory')
    parser.add_argument('--frames-only', action='store_true',
                       help='Only render frames, skip video assembly')
    parser.add_argument('--assemble-only', action='store_true',
                       help='Only assemble video from existing frames')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up frames after assembly')
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    renderer = VideoRenderer(
        base_dir=args.base_dir,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
    )
    
    if args.assemble_only:
        renderer.assemble_video()
    elif args.frames_only:
        renderer.render_all_frames()
    else:
        renderer.main()
    
    if args.cleanup and renderer.output_video.exists():
        renderer.cleanup_frames()
