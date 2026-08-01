#!/usr/bin/env python3
"""Render low-resolution animatic frames."""
import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def render_animatic():
    """Render animatic frames at 960x540."""
    print("Loading analysis data...")
    
    with open("analysis/section_map.json") as f:
        section_map = json.load(f)
    
    with open("analysis/visual_palette.json") as f:
        palette = json.load(f)
    
    with open("analysis/lyric_timing.json") as f:
        lyrics = json.load(f)
    
    fps = 24
    width = 960
    height = 540
    output_dir = Path("renders/proxy/frames")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_duration = section_map["total_duration_seconds"]
    total_frames = int(total_duration * fps)
    
    print(f"Rendering {total_frames} frames at {width}x{height} @ {fps}fps")
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        
        current_section = None
        for section in section_map["sections"]:
            if section["start"] <= time_sec < section["end"]:
                current_section = section
                break
        
        if current_section is None:
            current_section = section_map["sections"][-1]
        
        section_id = current_section["id"]
        
        if "opening" in section_id or section_id == "intro":
            bg_colors = palette["base_palette"]["opening"]
        elif "hook" in section_id or "verse" in section_id:
            bg_colors = palette["base_palette"]["escalation"]
        elif "bridge" in section_id or "breakdown" in section_id:
            bg_colors = palette["base_palette"]["revelation"]
        else:
            bg_colors = palette["base_palette"]["resolution"]
        
        bg_color = hex_to_rgb(bg_colors[0]["hex"])
        
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        energy = current_section.get("energy", 0.5)
        bar_height = int(energy * height * 0.8)
        bar_y = (height - bar_height) // 2
        
        accent_color = hex_to_rgb(bg_colors[1]["hex"]) if len(bg_colors) > 1 else (255, 255, 255)
        draw.rectangle([width//4, bar_y, 3*width//4, bar_y + bar_height], fill=accent_color)
        
        section_label = current_section.get("label", section_id)
        bbox = draw.textbbox((0, 0), section_label, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, 40), section_label, fill=(255, 255, 255), font=font)
        
        current_lyric = None
        for line in lyrics["lines"]:
            if line["start"] <= time_sec < line["end"]:
                current_lyric = line
                break
        
        if current_lyric:
            lyric_text = current_lyric["text"]
            bbox = draw.textbbox((0, 0), lyric_text, font=small_font)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            draw.text((text_x, height - 80), lyric_text, fill=(255, 255, 255), font=small_font)
        
        time_str = f"{int(time_sec // 60):02d}:{int(time_sec % 60):02d}"
        draw.text((20, 20), time_str, fill=(200, 200, 200), font=small_font)
        
        frame_path = output_dir / f"frame_{frame_num:06d}.png"
        img.save(frame_path)
        
        if frame_num % 100 == 0:
            print(f"  Rendered frame {frame_num}/{total_frames}")
    
    print(f"✓ Rendered {total_frames} frames to {output_dir}")

if __name__ == "__main__":
    render_animatic()
