#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json

def sanitize_name(name):
    """Convert to lowercase and replace spaces with underscores"""
    return name.lower().replace(' ', '_')

def rename_directories(root_path, log_file, dry_run=False):
    """Rename all directories to lowercase with underscores, bottom-up"""
    print("\nPhase 1: Renaming directories...")
    log_file.write("\n=== PHASE 1: DIRECTORY RENAMING ===\n\n")
    
    renamed_count = 0
    
    # Get all directories sorted by depth (deepest first)
    all_dirs = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        if dirpath != str(root_path):
            all_dirs.append(Path(dirpath))
    
    # Sort by depth (deepest first) so we rename children before parents
    all_dirs.sort(key=lambda p: len(p.parts), reverse=True)
    
    for old_dir in all_dirs:
        if not old_dir.exists():
            continue  # Already renamed as part of parent
            
        old_name = old_dir.name
        new_name = sanitize_name(old_name)
        
        if old_name != new_name:
            new_dir = old_dir.parent / new_name
            
            try:
                rel_old = old_dir.relative_to(root_path)
                rel_new = new_dir.relative_to(root_path)
            except:
                # If we can't get relative path, use absolute
                rel_old = old_dir
                rel_new = new_dir
            
            print(f"  {rel_old} -> {new_name}")
            log_file.write(f"Rename: {rel_old} -> {new_name}\n")
            
            if not dry_run:
                try:
                    old_dir.rename(new_dir)
                    renamed_count += 1
                except Exception as e:
                    log_file.write(f"  ERROR: Could not rename: {e}\n")
                    print(f"    ✗ Error: {e}")
    
    print(f"  Renamed {renamed_count} directories")
    log_file.write(f"\nRenamed {renamed_count} directories\n")
    return renamed_count

def process_audio_file(input_path, output_path, log_file):
    """Convert audio file to 44.1kHz 16-bit WAV using ffmpeg"""
    try:
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-ar', '44100',
            '-sample_fmt', 's16',
            '-ac', '2',
            '-y',
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            log_file.write(f"  FFmpeg error: {result.stderr[:200]}\n")
            return False
        return True
    except subprocess.TimeoutExpired:
        log_file.write(f"  FFmpeg timeout (>30s)\n")
        return False
    except Exception as e:
        log_file.write(f"  Exception: {e}\n")
        return False

def process_files(root_path, base_path, log_file, dry_run=False):
    """Process all audio files in-place"""
    print("\nPhase 2: Processing audio files...")
    log_file.write("\n=== PHASE 2: AUDIO FILE PROCESSING ===\n\n")
    
    # Collect all audio files
    audio_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dir_path = Path(dirpath)
        for filename in filenames:
            if filename.lower().endswith(('.wav', '.aif', '.aiff', '.mp3', '.flac')):
                if filename != 'processing_log.txt':
                    audio_files.append(dir_path / filename)
    
    total = len(audio_files)
    print(f"  Found {total} audio files to process")
    log_file.write(f"Found {total} audio files\n\n")
    
    if total == 0:
        print("  No audio files found!")
        return 0, 0
    
    processed = 0
    renamed = 0
    converted = 0
    failed = 0
    
    for i, old_path in enumerate(audio_files, 1):
        if not old_path.exists():
            continue  # May have been processed already
            
        # Determine new name
        old_name = old_path.stem
        new_name = sanitize_name(old_name)
        needs_rename = (old_name != new_name)
        
        # Check format conversion needs for all audio files
        needs_conversion = False
        if old_path.suffix.lower() == '.wav':
            # Check if WAV file needs format conversion
            try:
                result = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-show_streams', '-print_format', 'json', str(old_path)],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    for stream in info.get('streams', []):
                        if stream.get('codec_type') == 'audio':
                            rate = int(stream.get('sample_rate', 0))
                            bits = stream.get('bits_per_sample', 0)
                            # Check if format needs conversion
                            if rate != 44100 or bits != 16:
                                needs_conversion = True
                            break
            except:
                needs_conversion = True  # Assume needs conversion if probe fails
        else:
            # Non-WAV files always need conversion
            needs_conversion = True
        
        # Determine final path
        final_path = old_path.parent / (new_name + '.wav')
        
        try:
            rel_old = old_path.relative_to(base_path)
        except:
            rel_old = old_path.name
        
        # Skip if nothing to do
        if not needs_rename and not needs_conversion:
            continue  # Skip this file
        
        print(f"  [{i}/{total}] {rel_old}")
        log_file.write(f"[{i}/{total}] Processing: {rel_old}\n")
        
        if dry_run:
            if needs_rename or needs_conversion:
                action = []
                if needs_rename:
                    action.append("rename")
                if needs_conversion:
                    action.append("convert")
                    # Show current format for files that need conversion
                    try:
                        result = subprocess.run(
                            ['ffprobe', '-v', 'quiet', '-show_streams', '-print_format', 'json', str(old_path)],
                            capture_output=True, text=True, timeout=5
                        )
                        if result.returncode == 0:
                            info = json.loads(result.stdout)
                            for stream in info.get('streams', []):
                                if stream.get('codec_type') == 'audio':
                                    rate = int(stream.get('sample_rate', 0))
                                    bits = stream.get('bits_per_sample', 0)
                                    print(f"    Current: {rate}Hz, {bits}-bit")
                                    break
                    except:
                        print(f"    Current format unknown")
                
                print(f"    -> {final_path.name} ({', '.join(action)})")
                log_file.write(f"  Would {', '.join(action)} to: {final_path.name}\n")
                
                # Update counters for dry-run
                if needs_rename:
                    renamed += 1
                if needs_conversion:
                    converted += 1
            processed += 1
            continue
        
        # Actual processing
        success = False
        
        if needs_conversion:
            # Need to convert format - first show current format
            try:
                result = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-show_streams', '-print_format', 'json', str(old_path)],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    for stream in info.get('streams', []):
                        if stream.get('codec_type') == 'audio':
                            rate = int(stream.get('sample_rate', 0))
                            bits = stream.get('bits_per_sample', 0)
                            print(f"    Format: {rate}Hz, {bits}-bit (needs conversion)")
                            break
            except:
                print(f"    Converting audio format")
            
            temp_path = old_path.parent / f"_tmp_{new_name}.wav"
            
            if process_audio_file(old_path, temp_path, log_file):
                # Remove original and rename temp to final
                try:
                    old_path.unlink()
                    temp_path.rename(final_path)
                    success = True
                    converted += 1
                    if needs_rename:
                        renamed += 1
                    log_file.write(f"  SUCCESS: Converted to {final_path.name}\n")
                    print(f"    ✓ Converted to {final_path.name}")
                except Exception as e:
                    log_file.write(f"  ERROR: {e}\n")
                    if temp_path.exists():
                        temp_path.unlink()
                    print(f"    ✗ Error: {e}")
            else:
                print(f"    ✗ Conversion failed")
                if temp_path.exists():
                    temp_path.unlink()
                failed += 1
        
        elif needs_rename:
            # Just need to rename
            try:
                old_path.rename(final_path)
                success = True
                renamed += 1
                log_file.write(f"  SUCCESS: Renamed to {final_path.name}\n")
                print(f"    ✓ Renamed to {final_path.name}")
            except Exception as e:
                log_file.write(f"  ERROR: {e}\n")
                print(f"    ✗ Error: {e}")
                failed += 1
        
        if success:
            processed += 1
    
    print(f"\n  Processed: {processed}/{total}")
    print(f"  Converted format: {converted}")
    print(f"  Renamed files: {renamed}")
    if failed > 0:
        print(f"  Failed: {failed}")
    
    log_file.write(f"\nSummary:\n")
    log_file.write(f"  Processed: {processed}/{total}\n")
    log_file.write(f"  Converted: {converted}\n")
    log_file.write(f"  Renamed: {renamed}\n")
    log_file.write(f"  Failed: {failed}\n")
    
    return processed, failed

def main():
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except:
        print("Error: ffmpeg/ffprobe is not installed or not in PATH")
        print("Please install ffmpeg first:")
        print("  brew install ffmpeg")
        sys.exit(1)
    
    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    force = '--force' in sys.argv
    
    # Get target folder from arguments or use current directory
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        target_folder = sys.argv[1]
    else:
        print("Usage: m8-sample-processor <folder_path> [--dry-run|--force]")
        print("\nExample:")
        print("  m8-sample-processor ./samples --dry-run")
        print("  m8-sample-processor ./samples --force")
        sys.exit(1)
    
    # Resolve paths
    base_path = Path('.').resolve()
    target_path = Path(target_folder).resolve()
    
    # Check if target exists
    if not target_path.exists():
        print(f"Error: Folder '{target_folder}' does not exist!")
        sys.exit(1)
    
    if not target_path.is_dir():
        print(f"Error: '{target_folder}' is not a directory!")
        sys.exit(1)
    
    # Create log file in the target directory
    log_path = target_path / 'processing_log.txt'
    
    print("=" * 60)
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    else:
        print("Audio Processing Script - Single Folder Test")
    print("=" * 60)
    print(f"Target folder: {target_folder}")
    print(f"Full path: {target_path}")
    
    # Count files first
    audio_count = 0
    for dirpath, dirnames, filenames in os.walk(target_path):
        for filename in filenames:
            if filename.lower().endswith(('.wav', '.aif', '.aiff', '.mp3', '.flac')):
                audio_count += 1
    
    print(f"Audio files found: {audio_count}")
    
    if not dry_run and not force:
        print("\n" + "!" * 60)
        print("WARNING: This will modify files in the target folder!")
        print("!" * 60)
        response = input("\nDo you have a backup? (yes/no): ")
        if response.lower() != 'yes':
            print("Please create a backup first!")
            print(f"Run: cp -r '{target_folder}' '{target_folder}_backup'")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    
    with open(log_path, 'w') as log_file:
        log_file.write(f"Audio Processing Log - {'DRY RUN' if dry_run else 'LIVE'}\n")
        log_file.write("=" * 60 + "\n")
        log_file.write(f"Target: {target_path}\n")
        log_file.write(f"Files found: {audio_count}\n")
        
        # Phase 1: Rename directories
        rename_directories(target_path, log_file, dry_run)
        
        # Phase 2: Process files
        processed, failed = process_files(target_path, base_path, log_file, dry_run)
        
        print("\n" + "=" * 60)
        if dry_run:
            print("DRY RUN COMPLETE")
            print(f"Review log: {log_path}")
            print("\nTo apply changes, run without --dry-run:")
            print(f"  python3 test_folder_process.py {target_folder}")
        else:
            print("PROCESSING COMPLETE")
            if failed > 0:
                print(f"Warning: {failed} files failed to process")
            print(f"Check log: {log_path}")
        print("=" * 60)

if __name__ == "__main__":
    main()