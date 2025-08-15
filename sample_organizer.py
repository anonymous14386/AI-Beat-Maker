import os
import shutil
import re

# --- Configuration ---
# Set the source to your new samples folder
SOURCE_BASE_DIR = './New_samples'
# The destination is your existing organized library
DEST_DIR = './Organized_Library'
# --- End Configuration ---

def clean_name(name):
    """Removes special characters and extra spaces from a string."""
    name = re.sub(r'[@!()]', '', name) # Remove @, !, (, )
    name = name.replace('_', ' ').replace('-', ' ') # Replace underscores and hyphens with spaces
    name = re.sub(r'\s+', ' ', name).strip() # Replace multiple spaces with a single one
    return name

def parse_metadata(path_string):
    """
    Parses a string (filename or folder name) to find BPM and musical key
    using regular expressions.
    """
    bpm = None
    key = None

    # --- BPM Patterns ---
    # Matches "120 BPM", "150BPM", "128_BPM" etc.
    bpm_match = re.search(r'(\d{2,3})\s?BPM', path_string, re.IGNORECASE)
    if bpm_match:
        bpm = f"{bpm_match.group(1)}bpm"
    else:
        # Matches numbers like "_150_" which often imply BPM
        bpm_match_underscore = re.search(r'_(\d{2,3})_', path_string)
        if bpm_match_underscore:
            bpm = f"{bpm_match_underscore.group(1)}bpm"

    # --- Key Patterns ---
    # Matches "C#min", "Fmaj", "G Minor", "Db Major", or just "_F#_"
    key_match = re.search(
        r'\b([A-G][#b]?)\s?(min|maj|minor|major)?\b', path_string, re.IGNORECASE
    )
    if key_match:
        note = key_match.group(1).replace('b', 'b').replace('#', '#')
        mode = (key_match.group(2) or "").lower()
        if mode in ['minor', 'min', 'm']:
            key = f"{note}min"
        elif mode in ['major', 'maj']:
            key = f"{note}maj"
        else:
            key = note

    return bpm, key

def get_category_from_path(path):
    """Determines the sample category based on keywords in the file path."""
    path_lower = path.lower()
    if 'midi' in path_lower:
        return 'MIDI'
    if 'stem' in path_lower or '!stems' in path_lower:
        return 'Stems'
    if 'loop' in path_lower or 'bpm' in path_lower:
        return 'Loops'
    if any(keyword in path_lower for keyword in ['one shot', 'one-shots', 'oneshot', 'kick', 'snare', 'hat', 'clap', '808', 'perc', 'tom', 'cym']):
        return 'One-Shots'
    # Default category if no keywords are found
    return 'Uncategorized'


def organize_library():
    """
    Main function to scan, parse, rename, and move audio files
    into a new, organized directory structure.
    """
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        print(f"Created destination directory: {DEST_DIR}")

    file_count = 0

    print(f"Scanning source folder: {SOURCE_BASE_DIR}...")

    # Check if the source directory exists before walking through it
    if not os.path.exists(SOURCE_BASE_DIR):
        print(f"Error: Source directory '{SOURCE_BASE_DIR}' not found.")
        return

    for root, _, files in os.walk(SOURCE_BASE_DIR):
        for filename in files:
            # Process only common audio and MIDI file types
            if not filename.lower().endswith(('.wav', '.aif', '.mp3', '.mid')):
                continue

            original_full_path = os.path.join(root, filename)
            path_for_parsing = original_full_path.replace('\\', '/')

            # --- 1. Determine Category ---
            category = get_category_from_path(path_for_parsing)

            # --- 2. Extract Metadata ---
            bpm_file, key_file = parse_metadata(filename)
            bpm_folder, key_folder = parse_metadata(root)

            final_bpm = bpm_file or bpm_folder
            final_key = key_file or key_folder

            # --- 3. Determine Pack and Sample Name ---
            # Correctly get the pack name relative to the SOURCE_BASE_DIR
            relative_path = os.path.relpath(root, SOURCE_BASE_DIR)
            path_parts = relative_path.replace('\\', '/').split('/')
            pack_name = clean_name(path_parts[0] if path_parts[0] != '.' else 'UnknownPack')
            sample_name = clean_name(os.path.splitext(filename)[0])

            # Clean up sample name by removing metadata that we've already parsed
            if final_bpm:
                sample_name = re.sub(r'\d{2,3}\s?bpm', '', sample_name, flags=re.IGNORECASE).strip()
            if final_key:
                sample_name = re.sub(r'\b[A-G][#b]?\s?(min|maj|minor|major)?\b', '', sample_name, flags=re.IGNORECASE).strip()

            sample_name = re.sub(r'_\s?([A-G][#b]?)\s?_', '', sample_name).strip() # remove _F_
            sample_name = re.sub(r'_\s?\d{2,3}\s?_', '', sample_name).strip() # remove _150_
            sample_name = re.sub(r'\s+', ' ', sample_name).strip()


            # --- 4. Construct New Filename and Path ---
            new_filename_parts = [pack_name, sample_name]
            if final_bpm:
                new_filename_parts.append(final_bpm)
            if final_key:
                new_filename_parts.append(final_key)

            extension = os.path.splitext(filename)[1]
            new_filename = '_'.join(part for part in new_filename_parts if part) + extension
            new_filename = new_filename.replace(' ', '_').replace('#', 's')

            dest_category_path = os.path.join(DEST_DIR, category)
            if not os.path.exists(dest_category_path):
                os.makedirs(dest_category_path)

            new_full_path = os.path.join(dest_category_path, new_filename)

            # --- 5. Move and Rename the File ---
            try:
                if not os.path.exists(new_full_path):
                    shutil.move(original_full_path, new_full_path)
                    print(f"Moved: {filename} -> {category}/{new_filename}")
                    file_count += 1
                else:
                    # Handle potential filename collisions by adding a number
                    counter = 1
                    while os.path.exists(new_full_path):
                        name, ext = os.path.splitext(new_filename)
                        new_full_path = os.path.join(dest_category_path, f"{name}_{counter}{ext}")
                        counter += 1
                    shutil.move(original_full_path, new_full_path)
                    print(f"Moved (renamed): {filename} -> {os.path.basename(new_full_path)}")
                    file_count += 1
            except Exception as e:
                print(f"Error moving {filename}: {e}")

    print(f"\nOrganization complete! Moved {file_count} new files to '{DEST_DIR}'.")

if __name__ == '__main__':
    organize_library()
