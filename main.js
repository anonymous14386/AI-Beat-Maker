window.addEventListener('load', () => {
    // --- 1. INITIAL SETUP ---
    // This URL is correct for running on the same machine.
    const OLLAMA_SERVER_URL = "http://localhost:11434"; 

    const audioContext = new AudioContext();
    const masterGainNode = audioContext.createGain();
    masterGainNode.connect(audioContext.destination);

    let bpm = 120;
    let isPlaying = false;
    let sequencerInterval = null;
    let sampleDatabase = [];
    let loadedSamples = {};
    let currentSequence = [];

    // UI Elements
    const playButton = document.getElementById('play-button');
    const aiButton = document.getElementById('ai-button');
    const downloadButton = document.getElementById('download-button');
    const bpmSlider = document.getElementById('bpm-slider');
    const bpmValueSpan = document.getElementById('bpm-value');
    const promptInput = document.getElementById('prompt-input');
    const statusDiv = document.getElementById('status');
    const recipeOutputDiv = document.getElementById('recipe-output');

    // --- 2. LOAD THE SAMPLE DATABASE ---
    async function loadDatabase() {
        try {
            const response = await fetch('sample_database.csv');
            const text = await response.text();
            const rows = text.split('\n').slice(1);
            sampleDatabase = rows.map(row => {
                const columns = row.split(',');
                return { filename: columns[0], category: columns[1], pack: columns[2] };
            }).filter(sample => sample.filename && sample.category);
            
            statusDiv.textContent = `Database loaded with ${sampleDatabase.length} samples. Ready to generate!`;
            aiButton.disabled = false;
        } catch (error) {
            statusDiv.textContent = "Error: Could not load sample_database.csv.";
            console.error("Error loading database:", error);
        }
    }

    // --- 3. DYNAMIC SAMPLE LOADING ---
    async function loadSamplesForSequence(sequence) {
        statusDiv.textContent = 'Loading required samples...';
        const uniqueFilenames = [...new Set(sequence.flatMap(track => track.steps.map(step => step.file)))];
        
        const loadPromises = uniqueFilenames.map(filename => {
            if (loadedSamples[filename] || !filename) return Promise.resolve();
            const path = `Organized_Library_Final/${filename}`;
            return fetch(path)
                .then(response => response.ok ? response.arrayBuffer() : Promise.reject(`Sample not found: ${path}`))
                .then(arrayBuffer => audioContext.decodeAudioData(arrayBuffer))
                .then(decodedData => { loadedSamples[filename] = decodedData; })
                .catch(err => console.error(`Failed to load sample: ${filename}`, err));
        });

        await Promise.all(loadPromises);
        statusDiv.textContent = 'Samples loaded. Ready to play!';
    }

    // --- 4. SEQUENCER ENGINE ---
    function playSample(filename, time, context = audioContext) {
        if (context.state === 'suspended') {
            context.resume();
        }
        if (loadedSamples[filename]) {
            const source = context.createBufferSource();
            source.buffer = loadedSamples[filename];
            source.connect(context.destination === masterGainNode ? masterGainNode : context.destination);
            source.start(time);
        }
    }

    function togglePlayback() {
        if (!currentSequence.length) return;
        if (audioContext.state === 'suspended') audioContext.resume();

        if (isPlaying) {
            clearInterval(sequencerInterval);
            sequencerInterval = null;
            isPlaying = false;
            playButton.textContent = 'Play';
        } else {
            isPlaying = true;
            playButton.textContent = 'Stop';
            
            let currentBeat = 0;
            const totalBeats = 16;
            const timePerBeat = 60.0 / bpm;

            sequencerInterval = setInterval(() => {
                const currentTime = audioContext.currentTime;
                currentSequence.forEach(track => {
                    const step = track.steps.find(s => s.beat === currentBeat);
                    if (step && step.file) {
                        playSample(step.file, currentTime);
                    }
                });
                currentBeat = (currentBeat + 1) % totalBeats;
            }, timePerBeat * 1000);
        }
    }
    
    // --- 5. AI INTEGRATION & PROMPT ENGINEERING ---
    function findSamples(category, count = 5) {
        return sampleDatabase
            .filter(s => s.category && s.category.toLowerCase().includes(category.toLowerCase()))
            .sort(() => 0.5 - Math.random())
            .slice(0, count)
            .map(s => s.filename);
    }
    
    function extractJson(text) {
        const jsonRegex = /[{\[]{1}[\s\S]*[}\]]{1}/;
        const match = text.match(jsonRegex);
        if (match) return JSON.parse(match[0]);
        throw new Error("No valid JSON object or array found in the AI response.");
    }

    async function getAIResponse() {
        statusDiv.textContent = '🤖 Finding samples and building prompt...';
        aiButton.disabled = true;
        downloadButton.disabled = true;
        let rawAIResponse = "No response received.";

        const kicks = findSamples('Drums', 5);
        const snares = findSamples('Drums', 5);
        const hats = findSamples('Drums', 5);
        
        if (kicks.length === 0 || snares.length === 0 || hats.length === 0) {
            statusDiv.textContent = "Error: Not enough drum samples found in the database.";
            aiButton.disabled = false;
            return;
        }

        const userPrompt = promptInput.value || "a simple 4-bar house beat";
        const finalPrompt = `You are an expert drum machine programmer. Your task is to create a 4-bar drum loop based on a user's request. You must only use the samples provided in the lists below. The beat should be 16 beats long (4 bars of 4/4 time). USER REQUEST: "${userPrompt}" AVAILABLE SAMPLES: - Kicks: ${JSON.stringify(kicks)} - Snares: ${JSON.stringify(snares)} - Hats: ${JSON.stringify(hats)}. Your output MUST be ONLY a valid JSON object containing a "tracks" array. Do not include any other text, explanation, or markdown formatting. Each object in the "tracks" array has a "name" and an array of "steps". Each "step" object must have a "beat" (an integer from 0 to 15) and a "file" (the exact filename of the sample to play). Example format: {"tracks": [{"name": "Kick", "steps": [{"beat": 0, "file": "${kicks[0]}"}]}]}`;
        
        statusDiv.textContent = '🤖 Asking the AI to generate a beat...';

        try {
            const response = await fetch(`${OLLAMA_SERVER_URL}/api/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: "llama3", prompt: finalPrompt, stream: false, format: "json" }),
            });
            
            if (!response.ok) throw new Error(`API request failed: ${response.statusText}`);
            const data = await response.json();
            rawAIResponse = data.response;
            
            let parsedData = extractJson(rawAIResponse);
            let sequenceData = Array.isArray(parsedData) ? parsedData : parsedData.tracks;

            if (!sequenceData) throw new Error("JSON response did not contain a 'tracks' array.");
            
            currentSequence = sequenceData;
            await loadSamplesForSequence(currentSequence);
            renderRecipe(currentSequence);
            downloadButton.disabled = false;

        } catch (error) {
            console.error("Error with AI generation:", error);
            statusDiv.textContent = `Error: Could not get a valid response from the AI.`;
            recipeOutputDiv.innerHTML = `<p><strong>AI Response that caused the error:</strong></p><pre>${rawAIResponse}</pre>`;
        } finally {
            aiButton.disabled = false;
        }
    }

    // --- 6. OFFLINE RENDERING & DOWNLOAD ---
    // ... (This section is unchanged)
    function bufferToWav(buffer) {
        const numOfChan = buffer.numberOfChannels,
            len = buffer.length * numOfChan * 2 + 44,
            wavBuffer = new ArrayBuffer(len),
            view = new DataView(wavBuffer),
            channels = [],
            sampleRate = buffer.sampleRate;
        let offset = 0, pos = 0;
        const setUint16 = (data) => { view.setUint16(pos, data, true); pos += 2; };
        const setUint32 = (data) => { view.setUint32(pos, data, true); pos += 4; };
        setUint32(0x46464952); setUint32(len - 8); setUint32(0x45564157);
        setUint32(0x20746d66); setUint32(16); setUint16(1); setUint16(numOfChan);
        setUint32(sampleRate); setUint32(sampleRate * 2 * numOfChan);
        setUint16(numOfChan * 2); setUint16(16); setUint32(0x61746164);
        setUint32(len - pos - 4);
        for (let i = 0; i < buffer.numberOfChannels; i++) channels.push(buffer.getChannelData(i));
        while (pos < len) {
            for (let i = 0; i < numOfChan; i++) {
                let sample = Math.max(-1, Math.min(1, channels[i][offset]));
                sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
                view.setInt16(pos, sample, true);
                pos += 2;
            }
            offset++;
        }
        return new Blob([view], { type: 'audio/wav' });
    }

    async function renderBeatToWav() {
        if (!currentSequence.length) return;
        statusDiv.textContent = 'Rendering beat to WAV file...';
        downloadButton.disabled = true;
        const totalBeats = 16;
        const timePerBeat = 60.0 / bpm;
        const duration = totalBeats * timePerBeat;
        const offlineContext = new OfflineAudioContext(2, 44100 * duration, 44100);
        currentSequence.forEach(track => {
            track.steps.forEach(step => {
                if (step.file) playSample(step.file, step.beat * timePerBeat, offlineContext);
            });
        });
        const renderedBuffer = await offlineContext.startRendering();
        const wavBlob = bufferToWav(renderedBuffer);
        const url = URL.createObjectURL(wavBlob);
        const a = document.createElement('a');
        a.style.display = 'none'; a.href = url; a.download = `ai-beat-${bpm}bpm.wav`;
        document.body.appendChild(a); a.click();
        window.URL.revokeObjectURL(url); document.body.removeChild(a);
        statusDiv.textContent = 'Download complete!';
        downloadButton.disabled = false;
    }

    // --- 7. UI RENDERING & EVENT LISTENERS ---
    // ... (This section is unchanged)
    function renderRecipe(sequence) {
        recipeOutputDiv.innerHTML = '';
        const table = document.createElement('table');
        table.style.width = '100%'; table.style.borderCollapse = 'collapse'; table.style.textAlign = 'left';
        sequence.forEach(track => {
            const row = table.insertRow();
            const nameCell = row.insertCell();
            nameCell.style.fontWeight = 'bold'; nameCell.style.padding = '8px';
            nameCell.style.verticalAlign = 'top'; nameCell.style.width = '100px';
            nameCell.textContent = track.name;
            const stepsCell = row.insertCell();
            stepsCell.style.padding = '8px'; stepsCell.style.whiteSpace = 'pre-wrap';
            stepsCell.style.wordBreak = 'break-word';
            track.steps.forEach(step => {
                const stepDiv = document.createElement('div');
                const link = document.createElement('a');
                link.href = `Organized_Library_Final/${step.file}`;
                link.textContent = step.file;
                link.download = step.file;
                stepDiv.textContent = `Beat ${step.beat}: `;
                stepDiv.appendChild(link);
                stepsCell.appendChild(stepDiv);
            });
        });
        recipeOutputDiv.appendChild(table);
    }

    playButton.addEventListener('click', togglePlayback);
    aiButton.addEventListener('click', getAIResponse);
    downloadButton.addEventListener('click', renderBeatToWav);
    bpmSlider.addEventListener('input', (e) => {
        bpm = parseInt(e.target.value, 10);
        bpmValueSpan.textContent = bpm;
        if (isPlaying) {
            togglePlayback(); // Stop
            togglePlayback(); // and start again
        }
    });

    // --- INITIALIZE ---
    loadDatabase();
});
