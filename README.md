# Audio Sample Processor

A Python script to batch process audio samples for standardization. Originally created for the Dirtywave M8 tracker, but perfect for any hardware sampler, DAW, or audio library that needs consistent 44.1kHz 16-bit WAV files with clean naming.

## ⚠️ WARNING: DESTRUCTIVE IN-PLACE OPERATION

**This script modifies your files directly!** It:
- **RENAMES** your folders and files permanently
- **CONVERTS** audio files, replacing originals
- **DELETES** original files after conversion

**ALWAYS BACKUP YOUR FILES BEFORE RUNNING THIS SCRIPT**

## What it does

### Phase 1: Directory Renaming (IN-PLACE)
- Renames all directories to lowercase
- Replaces spaces with underscores
- Example: `Drum Samples/Hip Hop` → `drum_samples/hip_hop`
- **Original folder names are gone forever**

### Phase 2: File Processing (IN-PLACE)
- Renames files to lowercase with underscores
- Converts all audio files to 44.1kHz, 16-bit WAV format
- Supports input formats: WAV, AIF, AIFF, MP3, FLAC
- Example: `Kick Drum 01.wav` → `kick_drum_01.wav` (renamed + converted from 24-bit to 16-bit)
- **Original files are deleted after conversion**

## Usage

### ESSENTIAL: Preview changes first with dry-run
```bash
python3 audio_processor.py path/to/folder --dry-run
```

### Process files (destructive operation)
```bash
python3 audio_processor.py path/to/folder --force
```

### Process entire directory tree
```bash
python3 audio_processor.py . --force
```

## Features

- **Batch processing** of entire directory trees
- **Two-phase processing**: Renames directories first, then processes files in place
- **Dry-run mode** to preview changes before applying
- **Detailed logging** of all operations
- **Format detection** - only converts files that need it
- **Safe conversion** - only deletes originals after successful conversion (but originals are still gone!)

## Requirements

- Python 3.6+
- ffmpeg and ffprobe (for audio conversion)

### Installing ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use:
```bash
winget install ffmpeg
```

## Examples

### Check what needs processing
```bash
# See what would change in a folder
python3 audio_processor.py my_samples --dry-run
```

### Process a sample library
```bash
# Convert all samples in a drum library
python3 audio_processor.py drums --force
```

### Process multiple folders
```bash
# Process each folder separately for better control
python3 audio_processor.py drums/kicks --force
python3 audio_processor.py drums/snares --force
python3 audio_processor.py drums/hats --force
```

## Output

The script provides real-time feedback:
```
Phase 1: Renaming directories...
  drums/Hip Hop -> hip_hop
  drums/Acoustic -> acoustic
  Renamed 2 directories

Phase 2: Processing audio files...
  [1/10] drums/hip_hop/Kick_01.wav
    Format: 48000Hz, 24-bit (needs conversion)
    ✓ Converted to kick_01.wav
```

A detailed log file `processing_log.txt` is created in each processed directory.

## Safety Tips

1. **ALWAYS backup your files before processing**
2. **ALWAYS use `--dry-run` first** to preview changes
3. Test on a small folder before processing large libraries
4. Keep your backups until you've verified the results
5. The script will ask for confirmation unless you use `--force`

## Common Use Cases

- Preparing samples for hardware samplers (MPC, Octatrack, M8, etc.)
- Standardizing sample libraries for DAW projects
- Reducing file sizes (24-bit → 16-bit conversion)
- Cleaning up sample pack folder/file names
- Ensuring compatibility across different systems

## License

MIT

## Contributing

Issues and pull requests welcome!