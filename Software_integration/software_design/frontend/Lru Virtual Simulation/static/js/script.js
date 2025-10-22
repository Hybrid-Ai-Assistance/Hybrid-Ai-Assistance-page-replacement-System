let simulationTimeout;
let simulationRunning = false;
let currentStep = 0;
let currentTimeline = [];
let framesGlobal = 0;
let summarylru;
// Arrays to maintain state across stop/resume
let pageHistory = new Array(20).fill("-");
let frameHistory = [];
let lruStack = [];
let frameRows = [];
let pagelimt=0;
async function startSimulation() {
    if (simulationRunning) return;

    simulationRunning = true;
    currentStep = 0;

    const frames = parseInt(document.getElementById("frames").value);
    framesGlobal = frames; // save globally for resume
    const seq = parseInt(document.getElementById("seq").value);
    pagelimt = seq;

    const response = await fetch("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frames: frames, seq_length: seq })
    });
    const data = await response.json();
    
    // currentTimeline = data.timeline;
    currentTimeline = data.timeline;
    summarylru = data.summary;

    // Initialize tables and arrays
    initializeTables(frames);
    frameHistory = Array.from({ length: frames }, () => new Array(20).fill("-"));
    lruStack = [];

    runSimulation();
}

function runSimulation() {
    const pageTable = document.getElementById("pageTable");
    const frameTable = document.getElementById("frameTable");
    const stackTable = document.getElementById("stackTable");
    const currentPageDiv = document.getElementById("currentPage");

    if (frameRows.length === 0) {
        // first time populate frameRows for update
        for (let f = 0; f < framesGlobal; f++) frameRows.push(frameTable.rows[f + 1]);
    }

    function updateStep() {
        
        if (!simulationRunning || currentStep >= currentTimeline.length) {
            currentPageDiv.innerText = "Simulation Stopped or Finished.";
            simulationRunning = false;
            return;
        }

        const current = currentTimeline[currentStep];
        currentPageDiv.innerText = `Current Page: ${current.page} (Step ${current.t + 1})`;

        // --- Page History ---
        if (currentStep < 20) pageHistory[currentStep] = current.page;
        else {
            pageHistory.shift();
            pageHistory.push(current.page);
        }

        // --- Frame History ---
        for (let f = 0; f < framesGlobal; f++) {
            if (currentStep < 20) frameHistory[f][currentStep] = current.frames[f];
            else {
                frameHistory[f].shift();
                frameHistory[f].push(current.frames[f]);
            }
        }

        // --- Update Tables ---
        for (let c = 0; c < 20; c++) {
            const cell = pageTable.rows[0].cells[c + 1];
            cell.innerText = pageHistory[c] !== undefined ? pageHistory[c] : "-";
            cell.className ="";
            if(c === currentStep||c===19)
            cell.className = pageHistory[c] === current.page ? (current.isFault ? "fault" : "hit") : "";
        }

        for (let f = 0; f < framesGlobal; f++) {
            for (let c = 0; c < 20; c++) {
                const val = frameHistory[f][c] !== undefined ? frameHistory[f][c] : "-";
                const cell = frameRows[f].cells[c + 1];
                cell.innerText = val;
                cell.className ="";
                if(c === currentStep||c===19)
                cell.className = val === current.page ? (current.isFault ? "fault" : "hit") : "";
            }
        }

        // --- Stack Table ---
        const stackCells = stackTable.rows[0].cells;
        let idx = lruStack.indexOf(current.page);
        if (idx !== -1) {
            lruStack.splice(idx, 1);
            lruStack.push(current.page);
        } else {
            if (lruStack.length >= framesGlobal) lruStack.shift();
            lruStack.push(current.page);
        }
        for (let f = 0; f < framesGlobal; f++) {
            stackCells[f].innerText = lruStack[f] !== undefined ? lruStack[f] : "-";
            stackCells[f].className = "";
        }
        if (current.isFault) stackCells[0].className = "lruOldest";

        const delay = current.isFault ? 1000 : 700;
        console.log(currentStep,currentTimeline.length);
        if(currentStep >= currentTimeline.length-1 )
        document.getElementById("summary").innerHTML = `<b>Summary:</b> Faults=${summarylru.faults}, Hits=${summarylru.hits}`;
        currentStep++;
        simulationTimeout = setTimeout(updateStep, delay);
    }

    updateStep();
    
}

// --- Initialize Tables ---
function initializeTables(frames) {
    const pageTable = document.getElementById("pageTable");
    const frameTable = document.getElementById("frameTable");
    const stackTable = document.getElementById("stackTable");
    pageTable.innerHTML = "";
    frameTable.innerHTML = "";
    stackTable.innerHTML = "";

    // Page Table Header
    const pageHeader = document.createElement("tr");
    pageHeader.appendChild(document.createElement("th")).innerText = "Time/Page";
    for (let i = 0; i < 20; i++) {
        const th = document.createElement("th");
        th.innerText = i + 1;
        pageHeader.appendChild(th);
    }
    pageTable.appendChild(pageHeader);

    // Frame Table Header
    const frameHeader = document.createElement("tr");
    frameHeader.appendChild(document.createElement("th")).innerText = "Frames";
    for (let i = 0; i < 20; i++) {
        const th = document.createElement("th");
        th.innerText = i + 1;
        frameHeader.appendChild(th);
    }
    frameTable.appendChild(frameHeader);

    // Frame rows
    frameRows = [];
    for (let f = 0; f < frames; f++) {
        const row = document.createElement("tr");
        row.appendChild(document.createElement("th")).innerText = `F${f}`;
        for (let i = 0; i < 20; i++) {
            const td = document.createElement("td");
            td.innerText = "-";
            row.appendChild(td);
        }
        frameTable.appendChild(row);
        frameRows.push(row);
    }

    // Stack row
    const stackRow = document.createElement("tr");
    for (let f = 0; f < frames; f++) {
        const td = document.createElement("td");
        td.innerText = "-";
        stackRow.appendChild(td);
    }
    stackTable.appendChild(stackRow);
}

async function toggleSimulation() {
    const btn = document.getElementById("toggleBtn");

    if (!simulationRunning && currentTimeline.length === 0) {
        // Start new simulation
        btn.innerText = "Pause";
        simulationRunning = true;
        currentStep = 0;

        const frames = parseInt(document.getElementById("frames").value);
        framesGlobal = frames;
        const seq = parseInt(document.getElementById("seq").value);
        pagelimt = seq;

        const response = await fetch("/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ frames: frames, seq_length: seq })
        });
        const data = await response.json();
        currentTimeline = data.timeline;
        summarylru = data.summary;

        initializeTables(frames);
        frameHistory = Array.from({ length: frames }, () => new Array(20).fill("-"));
        lruStack = [];

        runSimulation();
    } else if (simulationRunning) {
        // Pause simulation
        simulationRunning = false;
        btn.innerText = "Resume";
        if (simulationTimeout) clearTimeout(simulationTimeout);
    } else {
        // Resume simulation
        simulationRunning = true;
        btn.innerText = "Pause";
        runSimulation();
    }
}