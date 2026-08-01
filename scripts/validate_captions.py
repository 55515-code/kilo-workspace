#!/usr/bin/env python3
"""Validate caption files."""
import re
from pathlib import Path

def validate_srt(srt_path):
    """Validate SRT caption file."""
    path = Path(srt_path)
    if not path.exists():
        print(f"⚠ SRT file not found: {srt_path}")
        return False
    
    content = path.read_text()
    lines = content.strip().split('\n')
    
    if len(lines) < 3:
        print(f"✗ SRT file too short: {srt_path}")
        return False
    
    entries = []
    current_entry = None
    line_num = 0
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        if not line:
            if current_entry:
                entries.append(current_entry)
                current_entry = None
            continue
        
        if re.match(r'^\d+$', line):
            if current_entry and 'text' in current_entry:
                entries.append(current_entry)
            current_entry = {'index': int(line), 'line': i}
        elif '-->' in line:
            if current_entry:
                match = re.match(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})', line)
                if match:
                    current_entry['start'] = match.group(1)
                    current_entry['end'] = match.group(2)
                else:
                    print(f"✗ Invalid timestamp format at line {i}: {line}")
                    return False
        elif current_entry:
            if 'text' not in current_entry:
                current_entry['text'] = line
            else:
                current_entry['text'] += '\n' + line
    
    if current_entry and 'text' in current_entry:
        entries.append(current_entry)
    
    if not entries:
        print(f"✗ No valid entries found in {srt_path}")
        return False
    
    for entry in entries:
        if 'start' not in entry or 'end' not in entry:
            print(f"✗ Entry {entry.get('index', '?')} missing timestamps")
            return False
        if 'text' not in entry:
            print(f"✗ Entry {entry['index']} missing text")
            return False
    
    for i in range(len(entries) - 1):
        if entries[i]['end'] > entries[i+1]['start']:
            print(f"⚠ Overlapping timestamps: entry {entries[i]['index']} and {entries[i+1]['index']}")
    
    print(f"✓ SRT valid: {len(entries)} entries")
    return True

def validate_vtt(vtt_path):
    """Validate WebVTT caption file."""
    path = Path(vtt_path)
    if not path.exists():
        print(f"⚠ VTT file not found: {vtt_path}")
        return False
    
    content = path.read_text()
    
    if not content.startswith('WEBVTT'):
        print(f"✗ VTT file missing WEBVTT header: {vtt_path}")
        return False
    
    lines = content.split('\n')
    entries = []
    current_entry = None
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
            if current_entry and 'text' in current_entry:
                entries.append(current_entry)
                current_entry = None
            continue
        
        if '-->' in line:
            if current_entry and 'text' in current_entry:
                entries.append(current_entry)
            
            match = re.match(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})', line)
            if match:
                current_entry = {
                    'start': match.group(1),
                    'end': match.group(2),
                    'line': i
                }
            else:
                print(f"✗ Invalid timestamp format at line {i}: {line}")
                return False
        elif current_entry:
            if 'text' not in current_entry:
                current_entry['text'] = line
            else:
                current_entry['text'] += '\n' + line
    
    if current_entry and 'text' in current_entry:
        entries.append(current_entry)
    
    if not entries:
        print(f"✗ No valid entries found in {vtt_path}")
        return False
    
    for entry in entries:
        if 'start' not in entry or 'end' not in entry:
            print(f"✗ Entry at line {entry.get('line', '?')} missing timestamps")
            return False
        if 'text' not in entry:
            print(f"✗ Entry at line {entry['line']} missing text")
            return False
    
    print(f"✓ VTT valid: {len(entries)} entries")
    return True

if __name__ == "__main__":
    srt_valid = False
    vtt_valid = False
    
    if Path("captions/song.srt").exists():
        srt_valid = validate_srt("captions/song.srt")
    
    if Path("captions/song.vtt").exists():
        vtt_valid = validate_vtt("captions/song.vtt")
    
    if not srt_valid and not vtt_valid:
        print("⚠ No caption files validated")
        exit(1)
    
    print("✓ Captions validated")
