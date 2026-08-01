#!/usr/bin/env python3
"""Generate contact sheet from animatic frames."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math
import json

def generate_contact_sheet():
    """Create contact sheet showing key frames."""
    frames_dir = Path("renders/proxy/frames")
    if not frames_dir.exists():
        print("⚠ Frames directory not found")
        return False
    
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        print("⚠ No frames found")
        return False
    
    print(f"  Found {len(frames)} frames")
    
    try:
        with open("analysis/section_map.json") as f:
            section_map = json.load(f)
        fps = 24
    except:
        section_map = None
        fps = 24
    
    num_frames = len(frames)
    sample_interval = max(1, num_frames // 48)
    sample_frames = frames[::sample_interval][:48]
    
    thumb_width = 320
    thumb_height = 180
    padding = 10
    label_height = 30
    
    cols = 6
    rows = math.ceil(len(sample_frames) / cols)
    
    sheet_width = cols * (thumb_width + padding) + padding
    sheet_height = rows * (thumb_height + padding + label_height) + padding
    
    sheet = Image.new('RGB', (sheet_width, sheet_height), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    for idx, frame_path in enumerate(sample_frames):
        col = idx % cols
        row = idx // cols
        
        x = padding + col * (thumb_width + padding)
        y = padding + row * (thumb_height + padding + label_height)
        
        try:
            frame = Image.open(frame_path)
            frame = frame.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            sheet.paste(frame, (x, y))
        except Exception as e:
            print(f"    ⚠ Failed to load {frame_path}: {e}")
            draw.rectangle([x, y, x + thumb_width, y + thumb_height], fill=(40, 40, 40))
        
        frame_num = int(frame_path.stem.split('_')[1])
        time_sec = frame_num / fps
        time_str = f"{int(time_sec // 60):02d}:{int(time_sec % 60):02d}"
        
        section_label = ""
        if section_map:
            for section in section_map["sections"]:
                if section["start"] <= time_sec < section["end"]:
                    section_label = section.get("label", section["id"])
                    break
        
        label_y = y + thumb_height + 5
        label_text = f"{time_str} - {section_label}" if section_label else time_str
        draw.text((x + 5, label_y), label_text, fill=(200, 200, 200), font=font)
    
    output_path = Path("review/contact_sheet.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    print(f"✓ Contact sheet saved to {output_path}")
    return True

if __name__ == "__main__":
    generate_contact_sheet()
