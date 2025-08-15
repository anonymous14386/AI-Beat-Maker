# AI Sample Sequencer 🎵

This web application uses a local AI model (via Ollama) to generate playable 4-bar drum loops from your personal sample library. You describe the beat you want, and the AI writes a "recipe" using your own samples, which can then be played back in the browser, downloaded as a WAV file, or recreated in your DAW.

## Features

-   **AI Beat Generation:** Uses a local large language model (Ollama with Llama 3) to generate drum patterns based on natural language prompts.
-   **Dynamic Sample Loading:** Intelligently loads only the required samples for the generated beat, keeping the app lightweight.
-   **Built-in Sequencer:** Plays back the generated beat in time with a variable BPM.
-   **Offline Rendering:** Allows you to download the complete, generated beat as a single WAV file.
-   **DAW-Ready Recipes:** Displays a clear breakdown of the beat, showing which sample is used on which beat, for easy recreation in any DAW like FL Studio or Ableton Live.

## Project Structure

This project is divided into two main parts: the Python scripts for preparing your sample library and the web application for generating and playing beats.


/
├── sample_organizer.py     # Python script to organize your raw samples.
├── analyze_library.py      # Python script to analyze samples and create the database.
├── index.html              # The main web page for the sequencer.
├── main.js                 # The core JavaScript logic for the app.
└── style.css               # (Optional) Your CSS stylesheet.


---

## Setup Instructions

To get this project running, you need to set up Ollama, prepare your sample library with the Python scripts, and then run a local web server.

### ### Step 1: Ollama Setup

This application requires a local Ollama server to be running.

1.  **Install Ollama:** Follow the official instructions at [ollama.com](https://ollama.com/).

2.  **Download the Model:** Once installed, run the following command in your terminal to download the Llama 3 model:
    ```bash
    ollama run llama3
    ```

3.  **Configure CORS:** The web app needs permission to communicate with Ollama. The easiest way to enable this for local development is to set an environment variable before starting the server. Run this command in your terminal:
    ```bash
    export OLLAMA_ORIGINS='*'
    ```
    *Note: For a permanent solution on Linux, you may need to edit the systemd service file for Ollama.*

4.  **Start the Ollama Server:** In the same terminal where you set the variable, run:
    ```bash
    ollama serve
    ```
    **Leave this terminal window open.** It is now your active AI server.

### ### Step 2: Prepare Your Sample Library

These Python scripts will organize your scattered sample files and create a searchable database.

1.  **Create a Python Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install librosa pandas
    ```

3.  **Organize Your Samples:**
    -   Create a folder named `All_My_Samples` in the project directory.
    -   Copy **all** of your raw sample packs and audio files into this folder.
    -   Run the organizer script. It will create a new, cleanly sorted folder named `Organized_Library_Final`.
        ```bash
        python sample_organizer.py
        ```

4.  **Analyze Your Library:**
    -   Run the analysis script. This will scan your new `Organized_Library_Final` and generate the `sample_database.csv` file that the web app needs.
        ```bash
        python analyze_library.py
        ```

### ### Step 3: Run the Web Server

Because of browser security policies, you cannot simply open `index.html` as a file. You must serve it locally.

1.  Open a **new terminal window** (leave the Ollama server running).
2.  Navigate to your project directory.
3.  Start Python's built-in web server:
    ```bash
    python3 -m http.server
    ```

4.  **Access the App:** Open your web browser and go to the following address:
    [http://localhost:8000](http://localhost:8000)

## How to Use the App

1.  **Wait for the database to load.** The status message will let you know when it's ready.
2.  **Describe a beat** in the text box (e.g., "a slow, heavy trap beat").
3.  Click **"Generate Beat"**.
4.  The app will load the necessary samples and display the "Beat Recipe."
5.  Click **"Play"** to listen to the loop.
6.  Click **"Download Beat"** to save the loop as a WAV file.
7.  Click the individual sample filenames in the recipe to download them.
