// Improved version of the original JavaScript for file compression UI and Huffman tree visualization

// --- Helper Functions ---
function $(selector) {
    return document.querySelector(selector);
}
function $all(selector) {
    return document.querySelectorAll(selector);
}

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = Math.max(0, decimals);
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function setStatus(id, message, type = 'success') {
    const el = $(id);
    el.textContent = message;
    el.className = `status-message ${type}`;
    el.style.display = 'block';
}

// --- Tab Switching ---
$all('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        $all('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        $all('.tab-content').forEach(content => content.classList.remove('active'));
        const tabId = tab.dataset.tab;
        $(`#${tabId}-content`).classList.add('active');
    });
});

// --- File Upload Handlers ---
function handleFileUpload(inputId, labelId, buttonId) {
    const input = $(inputId);
    const label = $(labelId);
    const button = $(buttonId);

    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            label.textContent = `Selected file: ${e.target.files[0].name}`;
            button.disabled = false;
        } else {
            label.textContent = 'No file selected';
            button.disabled = true;
        }
    });
}

handleFileUpload('#file-upload', '#file-name', '#compress-btn');
handleFileUpload('#compressed-file-upload', '#compressed-file-name', '#decompress-btn');

// --- File Action (Compress/Decompress) ---
async function handleFileAction(btnId, inputId, spinnerId, downloadId, statusId, endpoint, downloadPathKey) {
    const file = $(inputId).files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    $(spinnerId).style.display = 'block';
    $(downloadId).style.display = 'none';
    $(statusId).style.display = 'none';

    try {
        const response = await fetch(endpoint, { method: 'POST', body: formData });
        if (!response.ok) throw new Error(`${endpoint} failed`);

        const result = await response.json();

        if (endpoint.includes('compress')) {
            $('#original-size').textContent = formatBytes(result.originalSize);
            $('#compressed-size').textContent = formatBytes(result.compressedSize);
            $('#compression-ratio').textContent = `${result.compressionRatio.toFixed(2)}%`;
        }

        const downloadBtn = $(downloadId);
        downloadBtn.href = `/api/${downloadPathKey}/${result[downloadPathKey].split('/').pop()}`;
        downloadBtn.style.display = 'inline-block';

        setStatus(statusId, `File ${endpoint.includes('compress') ? 'compressed' : 'decompressed'} successfully!`, 'success');
    } catch (err) {
        console.error(err);
        setStatus(statusId, `Error during ${endpoint.includes('compress') ? 'compression' : 'decompression'}.`, 'error');
    } finally {
        $(spinnerId).style.display = 'none';
    }
}

$('#compress-btn').addEventListener('click', () => {
    handleFileAction('#compress-btn', '#file-upload', '#compress-spinner', '#download-compressed', '#compress-status', '/api/compress', 'compressedFilePath');
});

$('#decompress-btn').addEventListener('click', () => {
    handleFileAction('#decompress-btn', '#compressed-file-upload', '#decompress-spinner', '#download-decompressed', '#decompress-status', '/api/decompress', 'decompressedFileName');
});

// --- Huffman Tree Visualization ---
class HuffmanNode {
    constructor(char, freq) {
        this.char = char;
        this.freq = freq;
        this.left = null;
        this.right = null;
    }
}

function buildHuffmanTree(text) {
    const freqMap = {};
    for (const char of text) freqMap[char] = (freqMap[char] || 0) + 1;

    const queue = Object.entries(freqMap).map(([char, freq]) => new HuffmanNode(char, freq));
    queue.sort((a, b) => a.freq - b.freq);

    while (queue.length > 1) {
        const [left, right] = [queue.shift(), queue.shift()];
        const parent = new HuffmanNode(null, left.freq + right.freq);
        parent.left = left;
        parent.right = right;
        queue.splice(queue.findIndex(n => n.freq >= parent.freq), 0, parent);
    }

    return queue[0];
}

function calculatePositions(node, level, x, positions) {
    if (!node) return;
    const id = Math.random().toString(36).slice(2);
    positions[id] = { node, x, y: level, id };
    calculatePositions(node.left, level + 1, x - 1 / (2 ** level), positions);
    calculatePositions(node.right, level + 1, x + 1 / (2 ** level), positions);
}

function renderNode(node, container, positions, scale = 100, vSpace = 80, offsetX = 200, offsetY = 50) {
    if (!node) return;
    const pos = Object.values(positions).find(p => p.node === node);
    if (!pos) return;

    const nodeDiv = document.createElement('div');
    nodeDiv.className = 'tree-node';
    nodeDiv.style.left = `${pos.x * scale + offsetX}px`;
    nodeDiv.style.top = `${pos.y * vSpace + offsetY}px`;
    nodeDiv.textContent = node.char ? `'${node.char}': ${node.freq}` : `${node.freq}`;
    container.appendChild(nodeDiv);

    if (node.left) renderNode(node.left, container, positions, scale, vSpace, offsetX, offsetY);
    if (node.right) renderNode(node.right, container, positions, scale, vSpace, offsetX, offsetY);
}

$('#visualize-btn').addEventListener('click', () => {
    const text = $('#sample-text').value;
    if (!text.trim()) return alert('Please enter some text.');

    const container = $('#tree-container');
    container.innerHTML = '';
    const tree = buildHuffmanTree(text);

    const positions = {};
    calculatePositions(tree, 0, 2, positions);
    renderNode(tree, container, positions);
});
