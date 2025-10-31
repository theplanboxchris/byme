 const API_BASE = 'http://localhost:9080';
        let allKeywords = [];
        let selectedKeywords = new Set();
        let connectedDevice = null;
        let deviceCharacteristic = null;

        // Load initial data
        async function init() {
            try {
                await Promise.all([loadKeywords(), loadCategories()]);
            } catch (error) {
                console.error('Failed to initialize:', error);
                document.getElementById('keywordList').innerHTML = 
                    '<div class="error">Failed to load keywords. Is the API server running?</div>';
            }
        }

        // Load all keywords
        async function loadKeywords() {
            try {
                const response = await fetch(`${API_BASE}/keywords`);
                if (!response.ok) throw new Error('Failed to fetch keywords');
                
                allKeywords = await response.json();
                renderKeywords(allKeywords);
            } catch (error) {
                throw error;
            }
        }

        // Load categories for filter dropdown
        async function loadCategories() {
            try {
                const response = await fetch(`${API_BASE}/categories`);
                if (!response.ok) throw new Error('Failed to fetch categories');
                
                const data = await response.json();
                const select = document.getElementById('filterCategory');
                
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Failed to load categories:', error);
            }
        }

        // Render keywords list
        function renderKeywords(keywords) {
            const listDiv = document.getElementById('keywordList');
            
            if (keywords.length === 0) {
                listDiv.innerHTML = '<div class="loading">No keywords found. Add some keywords first!</div>';
                return;
            }

            const html = keywords.map(keyword => `
                <div class="keyword-item">
                    <input type="checkbox" id="kw-${keyword.keyword_id}" 
                           onchange="toggleKeyword(${keyword.keyword_id}, '${keyword.word}')">
                    <div class="keyword-info">
                        <div class="keyword-word">${keyword.word}</div>
                        <span class="keyword-category">${keyword.category}</span>
                    </div>
                </div>
            `).join('');

            listDiv.innerHTML = `<div class="keyword-list">${html}</div>`;
        }

        // Filter keywords
        function filterKeywords() {
            const search = document.getElementById('searchKeyword').value.toLowerCase();
            const category = document.getElementById('filterCategory').value;

            const filtered = allKeywords.filter(keyword => {
                const matchesSearch = keyword.word.toLowerCase().includes(search);
                const matchesCategory = !category || keyword.category === category;
                return matchesSearch && matchesCategory;
            });

            renderKeywords(filtered);
        }

        // Toggle keyword selection
        function toggleKeyword(id, word) {
            const checkbox = document.getElementById(`kw-${id}`);
            const keywordObj = allKeywords.find(k => k.keyword_id === id);
            if (checkbox.checked) {
                selectedKeywords.add(keywordObj);
            } else {
                selectedKeywords.delete(keywordObj);
            }

            updateSelectedCount();
        }

    // Update selected count display
    function updateSelectedCount() {
        const count = selectedKeywords.size;
        const transferBtn = document.querySelector('.download-btn');

        transferBtn.disabled = count === 0;
        
        updateSelectedCountDisplay();
    }

    // Update the selected count display (without connection info)
    function updateSelectedCountDisplay() {
        const statusDiv = document.getElementById('connectionStatus');
        const count = selectedKeywords.size;

        statusDiv.textContent = `${count} keyword${count === 1 ? '' : 's'} selected`;
        statusDiv.style.background = '#dbeafe'; // light blue background
        statusDiv.style.color = '#1e40af';      // dark blue text
    }

        // Update connection status display
        function updateConnectionStatus() {
            const statusDiv = document.getElementById('connectionStatus');
            const count = selectedKeywords.size;
            
            if (connectedDevice) {
                statusDiv.textContent = `${count} keyword${count === 1 ? '' : 's'} selected`;
                statusDiv.style.background = '#dcfce7';
                statusDiv.style.color = '#166534';
            } else {
                statusDiv.textContent = `${count} keyword${count === 1 ? '' : 's'} selected`;
                statusDiv.style.background = '#fef2f2';
                statusDiv.style.color = '#dc2626';
            }
        }

        // Add new keyword
        async function addKeyword() {
            const wordInput = document.getElementById('newKeyword');
            const categorySelect = document.getElementById('newCategory');
            const errorDiv = document.getElementById('addError');

            const word = wordInput.value.trim();
            const category = categorySelect.value;

            if (!word) {
                showError('Please enter a keyword');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/keywords`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ word, category })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to add keyword');
                }

                // Success - reload keywords and clear form
                wordInput.value = '';
                categorySelect.value = 'general';
                errorDiv.style.display = 'none';
                
                await loadKeywords();
                await loadCategories(); // Refresh categories in case new one was added

            } catch (error) {
                showError(error.message);
            }
        }

        // Show error message
        function showError(message) {
            const errorDiv = document.getElementById('addError');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => errorDiv.style.display = 'none', 5000);
        }

        // Debug logging function
        function debugLog(message) {
            const debugConsole = document.getElementById('debugConsole');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = `[${timestamp}] ${message}\n`;
            
            console.log(message); // Also log to browser console
            
            if (debugConsole) {
                debugConsole.textContent += logEntry;
                debugConsole.scrollTop = debugConsole.scrollHeight; // Auto-scroll to bottom
            }
        }


async function sendKeywordsOnce() {
    const messageDiv = document.getElementById('sendKeywordsMessage');

    if (selectedKeywords.size === 0) {
        showKeywordMessage('❌ No keywords selected!', 'error');
        return;
    }

    try {

        // Prepare numbers array + EOF
        // NOTE: updated to send the format: [ 12534, 33156]
        const keywordsArray = Array.from(selectedKeywords).map(kw => kw.keyword_id);
        const jsonPart = JSON.stringify(keywordsArray);
        const eofMarker = "<EOF>";
        const jsonString = jsonPart + eofMarker;
        const encoder = new TextEncoder();
        const fullPayload = encoder.encode(jsonString);

        console.log('[Frontend] JSON data created');
        console.log(jsonPart);



        showKeywordMessage('🔍 Searching for NIMI_DEV_ device...', 'info');
        console.log('[Frontend] Requesting BLE device with NIMI_DEV_ prefix');

        // Request and connect to device - match any device starting with NIMI_DEV_
        const device = await navigator.bluetooth.requestDevice({
            filters: [{ namePrefix: 'NIMI_DEV_' }],
            optionalServices: ['a07498ca-ad5b-474e-940d-16f1fbe7e8cd']
        });

        showKeywordMessage('🔗 Connecting to device...', 'info');
        const server = await device.gatt.connect();
        console.log('[Frontend] Connected to GATT server');

        const service = await server.getPrimaryService('a07498ca-ad5b-474e-940d-16f1fbe7e8cd');
        console.log('[Frontend] Found service: a07498ca-ad5b-474e-940d-16f1fbe7e8cd');

        const characteristic = await service.getCharacteristic('b07498ca-ad5b-474e-940d-16f1fbe7e8cd');
        console.log('[Frontend] Found characteristic: b07498ca-ad5b-474e-940d-16f1fbe7e8cd');



        // Log only the words for clarity
        console.log(`[Frontend] Keywords: ${JSON.stringify(keywordsArray.map(kw => kw.word))}`);
        console.log(`[Frontend] JSON part: "${jsonPart}" (${jsonPart.length} bytes)`);
        console.log(`[Frontend] EOF marker: "${eofMarker}" (${eofMarker.length} bytes)`);
        console.log(`[Frontend] Complete string: "${jsonString}"`);
        console.log(`[Frontend] Total payload: ${fullPayload.length} bytes`);
        console.log(`[Frontend] Payload as array: [${Array.from(fullPayload).join(', ')}]`);

        showKeywordMessage(`📤 Sending ${keywordsArray.length} keyword(s)...`, 'info');

       try {
            console.log(`[Frontend] Sending payload in 20-byte chunks...`);
            const chunkSize = 20;
            const totalChunks = Math.ceil(fullPayload.length / chunkSize);
            let chunksSent = 0;

            showKeywordMessage(`📤 Sending ${keywordsArray.length} keyword(s) in ${totalChunks} chunks...`, 'info');

            for (let i = 0; i < fullPayload.length; i += chunkSize) {
                const chunk = fullPayload.slice(i, i + chunkSize);
                chunksSent++;

                try {
                    console.log(`[Frontend] Chunk ${chunksSent}/${totalChunks}: [${Array.from(chunk).join(', ')}] (${chunk.length} bytes)`);

                    if (characteristic.writeValueWithoutResponse) {
                        await characteristic.writeValueWithoutResponse(chunk);
                    } else {
                        await characteristic.writeValue(chunk);
                    }

                    console.log(`[Frontend] ✅ Chunk ${chunksSent} sent`);
                    await new Promise(r => setTimeout(r, 300)); // delay between chunks
                } catch (chunkError) {
                    console.error(`[Frontend] ❌ Chunk ${chunksSent} failed: ${chunkError.message}`);
                    throw chunkError;
                }
            }

            console.log(`[Frontend] ✅ All ${chunksSent} chunks sent`);
            showKeywordMessage(`📤 Payload sent. Waiting for device to save file...`, 'info');
        } catch (error) {
            console.error("BLE transfer failed:", error);
            showKeywordMessage(`❌ Transfer failed: ${error.message}`, 'error');
        }

        console.log(`[Frontend] Total bytes sent: ${fullPayload.length}`);
        showKeywordMessage(`📤 Payload sent. Waiting for device to save file...`, 'info');

        // Wait longer before disconnecting to ensure device finishes processing
        // This gives the ESP32 time to handle all IRQ events and save the file
        console.log('[Frontend] Waiting 5 seconds for device to process and save...');
        await new Promise(r => setTimeout(r, 5000));

        console.log('[Frontend] Disconnecting from device');
        await server.disconnect();

        showKeywordMessage(`✅ Keywords sent successfully! (${keywordsArray.length} keywords)`, 'success');
        console.log('[Frontend] Transfer complete!');

        // Auto-hide success message after 5 seconds
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);

    } catch (error) {
        console.error("BLE transfer failed:", error);
        console.error(`Error name: ${error.name}`);
        console.error(`Error message: ${error.message}`);
        showKeywordMessage(`❌ Transfer failed: ${error.message}`, 'error');
    }
}

// Helper function to show messages with styling
function showKeywordMessage(message, type) {
    const messageDiv = document.getElementById('sendKeywordsMessage');
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';

    if (type === 'success') {
        messageDiv.style.background = '#dcfce7';
        messageDiv.style.color = '#166534';
        messageDiv.style.border = '1px solid #86efac';
    } else if (type === 'error') {
        messageDiv.style.background = '#fef2f2';
        messageDiv.style.color = '#dc2626';
        messageDiv.style.border = '1px solid #fca5a5';
    } else if (type === 'info') {
        messageDiv.style.background = '#dbeafe';
        messageDiv.style.color = '#1e40af';
        messageDiv.style.border = '1px solid #93c5fd';
    }
}




        // Monitor device output
        async function monitorDevice() {
            if (!connectedDevice) {
                return;
            }
            
            const monitorBtn = document.getElementById('monitorBtn');
            const messageDiv = document.getElementById('transferMessage');
            const statusDiv = document.getElementById('transferStatus');
            
            try {
                monitorBtn.textContent = '📺 Getting Output...';
                monitorBtn.disabled = true;
                statusDiv.style.display = 'block';
                
                const response = await fetch('http://localhost:8000/esp32/serial');
                const result = await response.json();
                
                if (result.status === 'success' && result.output.length > 0) {
                    messageDiv.innerHTML = `
                        <strong>📺 ESP32-C3 Output:</strong><br>
                        <div style="background: #1f2937; color: #f3f4f6; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto; white-space: pre-wrap;">${result.output.join('\n')}</div>
                    `;
                } else {
                    messageDiv.textContent = '📺 No recent output from device. Device may be sleeping or restarting.';
                }
                
            } catch (error) {
                console.error('Monitor failed:', error);
                messageDiv.textContent = `❌ Monitor failed: ${error.message}`;
            } finally {
                monitorBtn.textContent = '📺 Monitor Device Output';
                monitorBtn.disabled = false;
            }
        }

        // Download selected keywords (backup function)
        function downloadKeywords() {
            if (selectedKeywords.size === 0) return;

            const keywordsArray = Array.from(selectedKeywords);
            // If you want only the words:
            // const data = { keywords: keywordsArray.map(kw => kw.word) };
            // If you want full objects, keep as is:
            const data = { keywords: keywordsArray };
            // Optionally, if you want to save as dictionary:
            // const data = Object.fromEntries(keywordsArray.map(kw => [kw.word, kw.keyword_id]));

            const blob = new Blob([JSON.stringify(data, null, 2)], 
                                { type: 'application/json' });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'keywords.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        // Handle Enter key in new keyword input
        document.getElementById('newKeyword').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addKeyword();
            }
        });

        // Initialize app
        init();
        updateConnectionStatus(); // Set initial connection status