import os
import shutil
import re

# --- Configuration ---
# Point this to the folder containing ALL your raw samples.
SOURCE_BASE_DIR = './All_My_Samples'
# This will be the name of your new, cleanly categorized library.
DEST_DIR = './Organized_Library_Final'
# --- End Configuration ---

def clean_name(name):
    """Removes special characters and extra spaces from a string."""
    name = re.sub(r'[@!()]', '', name)
    name = name.replace('_', ' ').replace('-', ' ')
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def parse_metadata(path_string):
    """Parses a string to find BPM and musical key."""
    bpm, key = None, None
    bpm_match = re.search(r'(\d{2,3})\s?bpm', path_string, re.IGNORECASE) or re.search(r'_(\d{2,3})_', path_string)
    if bpm_match:
        bpm = f"{bpm_match.group(1)}bpm"

    key_match = re.search(r'\b([A-G][#b]?)\s?(min|maj|minor|major)?\b', path_string, re.IGNORECASE)
    if key_match:
        note = key_match.group(1).replace('b', 'b').replace('#', 's')
        mode = (key_match.group(2) or "").lower()
        key = f"{note}{'min' if mode in ['minor', 'min', 'm'] else 'maj' if mode in ['major', 'maj'] else ''}"

    return bpm, key

def get_category_from_path(path):
    """Determines the sample category using keyword lists."""
    path_lower = path.lower()

    # Define keywords for each category
    DRUMS = ['kick', 'bd', 'snare', 'sd', 'hat', 'hh', 'clap', '808', 'tom', 'cymbal', 'cym', 'ride', 'crash']
    PERCUSSION = ['perc', 'shaker', 'tamb', 'conga', 'bongo', 'clave', 'rim', 'block', 'timbale']
    FX = ['fx', 'sfx', 'riser', 'fall', 'downer', 'whoosh', 'impact', 'hit', 'transition', 'sweep', 'braam', 'zap']
    MELODIC = ['bass', 'synth', 'pad', 'lead', 'pluck', 'keys', 'piano', 'guitar', 'strings', 'vox', 'vocal', 'chord', 'arp']
    AMBIENCE = ['ambience', 'amb', 'drone', 'texture']

    if 'midi' in path_lower: return 'MIDI'
    if 'stem' in path_lower or '!stems' in path_lower: return 'Stems'
    if any(k in path_lower for k in FX): return 'Sound Effects (FX)'
    if any(k in path_lower for k in AMBIENCE): return 'Ambience'

    is_loop = 'loop' in path_lower or 'bpm' in path_lower

    if any(k in path_lower for k in DRUMS):
        return 'Drum Loops' if is_loop else 'Drums'

    if any(k in path_lower for k in PERCUSSION):
        return 'Percussion Loops' if is_loop else 'Percussion'

    if any(k in path_lower for k in MELODIC):
        return 'Melodic Loops' if is_loop else 'Melodic One-Shots'

    if is_loop: return 'Loops' # Generic loop category

    return 'Uncategorized'


def organize_library():
    """Main function to scan, parse, rename, and move audio files."""
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"Created destination directory: {DEST_DIR}")

    if not os.path.exists(SOURCE_BASE_DIR):
        print(f"Error: Source directory '{SOURCE_BASE_DIR}' not found. Please create it and add your samples.")
        return

    file_count = 0
    print(f"Scanning source folder: {SOURCE_BASE_DIR}...")

    for root, _, files in os.walk(SOURCE_BASE_DIR):
        for filename in files:
            if filename.startswith('.') or not filename.lower().endswith(('.wav', '.aif', '.mp3', '.mid')):
                continue

            original_full_path = os.path.join(root, filename)
            path_for_parsing = original_full_path.replace('\\', '/')

            category = get_category_from_path(path_for_parsing)
            bpm, key = parse_metadata(path_for_parsing)

            relative_path = os.path.relpath(root, SOURCE_BASE_DIR)
            path_parts = relative_path.replace('\\', '/').split('/')
            pack_name = clean_name(path_parts[0] if path_parts[0] != '.' else 'UnknownPack')
            sample_name = clean_name(os.path.splitext(filename)[0])

            # Further clean the sample name
            if bpm: sample_name = re.sub(r'\d{2,3}\s?bpm', '', sample_name, flags=re.IGNORECASE).strip()
            if key: sample_name = re.sub(r'\b[A-G][#b]?\s?(min|maj|minor|major)?\b', '', sample_name, flags=re.IGNORECASE).strip()
            sample_name = re.sub(r'_\s?([A-G][#b]?)\s?_', '', sample_name).strip()
            sample_name = re.sub(r'\s+', ' ', sample_name).strip()

            new_filename_parts = [pack_name, sample_name]
            if bpm: new_filename_parts.append(bpm)
            if key: new_filename_parts.append(key)

            extension = os.path.splitext(filename)[1]
            new_filename = '_'.join(part for part in new_filename_parts if part) + extension
            new_filename = new_filename.replace(' ', '_').replace('#', 's')

            dest_category_path = os.path.join(DEST_DIR, category)
            if not os.path.exists(dest_category_path):
                os.makedirs(dest_category_path)

            new_full_path = os.path.join(dest_category_path, new_filename)

            try:
                counter = 1
                while os.path.exists(new_full_path):
                    name, ext = os.path.splitext(new_filename)
                    new_full_path = os.path.join(dest_category_path, f"{name}_{counter}{ext}")
                    counter += 1
                shutil.move(original_full_path, new_full_path)
                print(f"Moved: {filename} -> {category}/{os.path.basename(new_full_path)}")
                file_count += 1
            except Exception as e:
                print(f"Error moving {filename}: {e}")

    print(f"\nOrganization complete! Moved {file_count} new files to '{DEST_DIR}'.")

if __name__ == '__main__':
    organize_library()
