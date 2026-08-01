# Environment Capabilities

## System Specifications

- **OS**: Linux 6.12.91 (Debian-based)
- **CPU**: 1 vCPU
- **RAM**: 2.9 GB total (2.0 GB available)
- **Disk**: 7.8 GB total (4.3 GB available)
- **GPU**: None (CPU-only rendering)

## Installed Tools

### Video/Audio Processing
- **ffmpeg**: 7.1.5
  - Encoders: libx264, libx265, prores_ks, dnxhd, aac
  - Supports: H.264, H.265, ProRes, DNxHD, AAC
- **ffprobe**: 7.1.5 (bundled with ffmpeg)

### Python Environment
- **Python**: 3.13.5
- **numpy**: 2.2.4
- **scipy**: 1.18.0
- **Pillow**: 12.3.0
- **opencv-python**: 5.0.0
- **librosa**: 0.11.0

### Graphics
- **Fonts**: 419 font files available
- **ImageMagick**: Not installed (use Python PIL/OpenCV instead)

### Node.js
- **Node**: v20.x
- **npm**: Available

## Capabilities

### What Works
- ✅ Video encoding (H.264, H.265, ProRes)
- ✅ Audio processing (AAC, MP3, WAV)
- ✅ Image manipulation (PIL, OpenCV)
- ✅ Audio analysis (librosa for beat detection, tempo, spectral analysis)
- ✅ Video compositing (ffmpeg filters, overlays)
- ✅ Python scripting for automation

### Limitations
- ⚠️ No GPU acceleration (CPU-only, slower rendering)
- ⚠️ Limited RAM (2.9 GB) - may struggle with 4K video
- ⚠️ Limited disk (4.3 GB free) - renders should be cleaned up
- ⚠️ No ImageMagick (use Python PIL/OpenCV for image ops)
- ⚠️ 1 vCPU - parallel processing limited

### Performance Expectations
- **1080p video**: Should work, but slow (expect 2-5x real-time for complex renders)
- **4K video**: May hit memory limits, recommend downscaling to 1080p for processing
- **Complex compositing**: Use simpler filters, avoid multiple heavy operations in parallel

## Recommended Settings

For this environment:
- **Resolution**: 1920x1080 (1080p)
- **Codec**: libx264 with `-preset fast` or `-preset medium`
- **CRF**: 18-23 (balance quality/speed)
- **Audio**: AAC 192-320 kbps
- **Pixel format**: yuv420p (maximum compatibility)

## Missing Tools (Optional)

These could be installed if needed:
- ImageMagick (advanced image manipulation)
- Blender (3D rendering)
- GIMP (image editing)
- Audacity (audio editing)
