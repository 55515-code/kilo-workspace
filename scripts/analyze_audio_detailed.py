#!/usr/bin/env python3
"""Detailed audio analysis using librosa."""
import librosa
import numpy as np
import json
from pathlib import Path

def analyze_audio(audio_path="assets/source/audio/master.wav"):
    """Perform comprehensive audio analysis."""
    print(f"Loading audio: {audio_path}")
    y, sr = librosa.load(audio_path, sr=None)
    
    duration = len(y) / sr
    print(f"Duration: {duration:.2f}s")
    
    print("Detecting tempo and beats...")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    print("Detecting sections...")
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    sections = librosa.segment.agglomerative(onset_env, 15)
    
    print("Computing energy curve...")
    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    
    print("Computing spectral features...")
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    
    results = {
        "duration_seconds": float(duration),
        "sample_rate": int(sr),
        "tempo_bpm": float(tempo),
        "beat_times": beat_times.tolist(),
        "energy_curve": rms.tolist(),
        "spectral_centroid": spectral_centroid.tolist()
    }
    
    with open("analysis/audio_features.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("✓ Analysis saved to analysis/audio_features.json")

if __name__ == "__main__":
    analyze_audio()
