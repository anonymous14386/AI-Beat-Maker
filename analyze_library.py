import os
import re
import librosa
import pandas as pd
import numpy as np

# --- Configuration ---
# This is the folder created by the organization script.
LIBRARY_DIR = './Organized_Library_Final'
# This is the output file where all your data will be saved.
OUTPUT_CSV = 'sample_database.csv'
# --- End Configuration ---

def parse_filename(filename):
    """
    Parses the structured filename to extract metadata.
    Example: 'Ghosthack_AC2024_Kick_Base_95bpm_Cmaj.wav'
    """
    parts = os.path.splitext(filename)[0].split('_')
    
    # Defaults
    pack_name = "Unknown"
    sample_name = "Unknown"
    bpm = None
    key = None

    # Regex to find bpm and key
    bpm_regex = re.compile(r'(\d{2,3})bpm')
    key_regex = re.compile(r'([A-G][#b]?(maj|min)?)')

    # Find BPM and Key and remove them from the parts list
    remaining_parts = []
    for part in parts:
        if bpm_regex.match(part) and bpm is None: # take first bpm found
            bpm = part
        elif key_regex.match(part) and key is None: # take first key found
            key = part
        else:
            remaining_parts.append(part)
    
    # If the first part is a generic folder name, ignore it.
    if remaining_parts and remaining_parts[0].upper() in ['SAMPLES', 'ONE-SHOTS']:
        remaining_parts.pop(0)

    if len(remaining_parts) > 1:
        pack_name = remaining_parts[0]
        sample_name = ' '.join(remaining_parts[1:])
    elif len(remaining_parts) == 1:
        sample_name = remaining_parts[0]
        
    return pack_name, sample_name, bpm, key


def analyze_audio_file(filepath):
    """
    Loads an audio file and extracts a set of acoustic features using librosa.
    Returns a dictionary of features.
    """
    features = {}
    try:
        # Load audio file. Use a duration limit for efficiency on long files.
        y, sr = librosa.load(filepath, sr=None, duration=30)

        # --- Feature Extraction ---
        
        # 1. Computed Tempo (BPM)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)[0]
        features['computed_bpm'] = np.round(tempo, 2)

        # 2. Spectral Centroid (Brightness)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        features['brightness'] = np.round(np.mean(spectral_centroid), 2)

        # 3. Spectral Bandwidth (Frequency Range)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        features['spectral_bandwidth'] = np.round(np.mean(spectral_bandwidth), 2)

        # 4. Zero-Crossing Rate (Noisiness / Percussiveness)
        zcr = librosa.feature.zero_crossing_rate(y)
        features['zero_crossing_rate'] = np.round(np.mean(zcr), 4)

        # 5. RMS Energy (Loudness)
        rms = librosa.feature.rms(y=y)
        features['loudness_rms'] = np.round(np.mean(rms), 4)
        
    except Exception as e:
        # Provide a more detailed error message
        print(f"Could not process {os.path.basename(filepath)}: {type(e).__name__} - {e}")
        return None

    return features

def main():
    """
    Main function to walk through the library, analyze files,
    and save the results to a CSV.
    """
    if not os.path.exists(LIBRARY_DIR):
        print(f"Error: Directory not found at '{LIBRARY_DIR}'")
        return

    all_samples_data = []
    file_count = 0
    
    print("Starting sample analysis...")

    # Walk through the organized library
    for root, _, files in os.walk(LIBRARY_DIR):
        for filename in files:
            # FIX: Skip hidden macOS metadata files and other dotfiles
            if filename.startswith('._') or filename.startswith('.'):
                continue

            if not filename.lower().endswith(('.wav', '.aif', '.mp3')):
                continue
            
            file_count += 1
            print(f"Analyzing ({file_count}): {filename}")
            
            full_path = os.path.join(root, filename)
            
            # --- 1. Get metadata from filename and path ---
            category = os.path.basename(root)
            pack, name, bpm, key = parse_filename(filename)
            
            # --- 2. Analyze the audio to get acoustic features ---
            audio_features = analyze_audio_file(full_path)
            
            if audio_features:
                # --- 3. Combine all data into one record ---
                sample_record = {
                    'filename': filename,
                    'category': category,
                    'pack': pack,
                    'sample_name': name,
                    'bpm_from_name': bpm,
                    'key_from_name': key,
                    **audio_features # Unpack the dictionary of computed features
                }
                all_samples_data.append(sample_record)

    if not all_samples_data:
        print("No audio files were processed. Exiting.")
        return

    # --- 4. Create a DataFrame and save to CSV ---
    print(f"\nAnalysis complete. Saving {len(all_samples_data)} samples to '{OUTPUT_CSV}'...")
    df = pd.DataFrame(all_samples_data)
    
    # Reorder columns for clarity
    column_order = [
        'filename', 'category', 'pack', 'sample_name', 'bpm_from_name', 
        'key_from_name', 'computed_bpm', 'brightness', 'loudness_rms', 
        'zero_crossing_rate', 'spectral_bandwidth'
    ]
    # Ensure all columns exist before reordering
    df_columns = [col for col in column_order if col in df.columns]
    df = df[df_columns]
    
    df.to_csv(OUTPUT_CSV, index=False)
    print("Successfully created the sample database!")


if __name__ == '__main__':
    main()
