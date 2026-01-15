javascript:(function(){
    'use strict';

    // Power Automate Flow Extractor v2
    // Fetches full flow definition via API using browser auth

    const showStatus = (msg, isError = false) => {
        console.log(isError ? `[PA Extractor ERROR] ${msg}` : `[PA Extractor] ${msg}`);
    };

    // Extract IDs from current URL
    const getIdsFromUrl = () => {
        const url = window.location.href;
        const envMatch = url.match(/environments\/([a-f0-9-]+)/i);
        const flowMatch = url.match(/flows\/([a-f0-9-]+)/i);
        return {
            environmentId: envMatch ? envMatch[1] : null,
            flowId: flowMatch ? flowMatch[1] : null
        };
    };

    // Get auth token from page
    const getAuthToken = async () => {
        // Method 1: Check for token in sessionStorage/localStorage
        for (const storage of [sessionStorage, localStorage]) {
            for (let i = 0; i < storage.length; i++) {
                const key = storage.key(i);
                const value = storage.getItem(key);
                if (value && (key.includes('token') || key.includes('auth') || key.includes('msal'))) {
                    try {
                        const parsed = JSON.parse(value);
                        if (parsed.accessToken) return parsed.accessToken;
                        if (parsed.secret) return parsed.secret;
                        // MSAL format
                        if (parsed.credentialType === 'AccessToken') return parsed.secret;
                    } catch (e) {}
                    // Raw token
                    if (value.startsWith('eyJ')) return value;
                }
            }
        }

        // Method 2: Look for token in cookies
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (value && value.startsWith('eyJ')) return value;
        }

        return null;
    };

    // Fetch flow definition from API
    const fetchFlowDefinition = async (envId, flowId) => {
        // Power Automate API endpoints to try
        const apiEndpoints = [
            `https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/${envId}/flows/${flowId}?api-version=2016-11-01&$expand=swagger,properties.connectionReferences`,
            `https://management.azure.com/providers/Microsoft.ProcessSimple/environments/${envId}/flows/${flowId}?api-version=2016-11-01`,
            `https://flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/${envId}/flows/${flowId}?api-version=2016-11-01`,
        ];

        const token = await getAuthToken();
        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        for (const endpoint of apiEndpoints) {
            try {
                showStatus(`Trying: ${endpoint.split('?')[0]}`);
                const response = await fetch(endpoint, {
                    method: 'GET',
                    headers: headers,
                    credentials: 'include'
                });

                if (response.ok) {
                    const data = await response.json();
                    showStatus('Successfully fetched flow definition!');
                    return { success: true, data, endpoint };
                } else {
                    showStatus(`${response.status} from ${endpoint.split('/')[2]}`, true);
                }
            } catch (e) {
                showStatus(`Error: ${e.message}`, true);
            }
        }

        return { success: false, error: 'All API endpoints failed' };
    };

    // Search window object for flow data
    const searchWindowForFlowData = () => {
        const results = [];
        const searched = new Set();

        const search = (obj, path = 'window', depth = 0) => {
            if (depth > 5 || searched.has(obj)) return;
            if (!obj || typeof obj !== 'object') return;
            searched.add(obj);

            try {
                const keys = Object.keys(obj);
                for (const key of keys) {
                    try {
                        const value = obj[key];
                        const currentPath = `${path}.${key}`;

                        if (value && typeof value === 'object') {
                            // Check if this looks like a flow definition
                            if (value.definition && value.definition.actions) {
                                results.push({ path: currentPath, type: 'definition', data: value });
                            }
                            if (value.properties && value.properties.definition) {
                                results.push({ path: currentPath, type: 'flow', data: value });
                            }
                            if (value.$schema && value.actions) {
                                results.push({ path: currentPath, type: 'schema', data: value });
                            }

                            // Recurse
                            if (depth < 5) {
                                search(value, currentPath, depth + 1);
                            }
                        }
                    } catch (e) {}
                }
            } catch (e) {}
        };

        // Search common locations
        const locations = [
            'window.__INITIAL_STATE__',
            'window.__PRELOADED_STATE__',
            'window.FlowClient',
            'window.Flow',
            'window.msla',
            'window.PowerAutomate'
        ];

        for (const loc of locations) {
            try {
                const obj = eval(loc);
                if (obj) search(obj, loc, 0);
            } catch (e) {}
        }

        // Search window itself (limited)
        search(window, 'window', 0);

        return results;
    };

    // Extract from React DevTools or Fiber
    const extractFromReact = () => {
        const results = [];

        // Find all React roots
        const roots = document.querySelectorAll('[data-reactroot], #root, #app, [id*="react"]');

        for (const root of roots) {
            const fiberKey = Object.keys(root).find(k =>
                k.startsWith('__reactFiber') ||
                k.startsWith('__reactInternalInstance') ||
                k.startsWith('__reactContainer')
            );

            if (!fiberKey) continue;

            const visited = new WeakSet();

            const traverseFiber = (fiber, depth = 0) => {
                if (!fiber || depth > 100 || visited.has(fiber)) return;
                visited.add(fiber);

                // Check memoizedState for flow data
                let state = fiber.memoizedState;
                while (state) {
                    if (state.memoizedState) {
                        const ms = state.memoizedState;
                        if (ms.definition || ms.flow || ms.flowDefinition) {
                            results.push({ source: 'react-state', data: ms });
                        }
                    }
                    state = state.next;
                }

                // Check memoizedProps
                const props = fiber.memoizedProps;
                if (props) {
                    if (props.definition || props.flow || props.flowDefinition) {
                        results.push({ source: 'react-props', data: props });
                    }
                }

                // Traverse tree
                if (fiber.child) traverseFiber(fiber.child, depth + 1);
                if (fiber.sibling) traverseFiber(fiber.sibling, depth + 1);
            };

            try {
                traverseFiber(root[fiberKey]);
            } catch (e) {
                showStatus(`React traversal error: ${e.message}`, true);
            }
        }

        return results;
    };

    // Parse all visible action cards from DOM
    const parseActionsFromDOM = () => {
        const actions = [];

        // Power Automate action card selectors
        const selectors = [
            '[data-automation-id]',
            '[class*="msla-"]',
            '[class*="card-v2"]',
            '[class*="operation"]',
            '.ms-Panel-content'
        ];

        const cards = document.querySelectorAll(selectors.join(','));

        cards.forEach((card, index) => {
            const action = {
                index,
                element: card.tagName,
                classes: card.className,
            };

            // Try to get action name
            const nameEl = card.querySelector('[class*="title"], [class*="header"], [class*="name"], h2, h3');
            if (nameEl) action.name = nameEl.textContent?.trim();

            // Try to get action type
            const typeEl = card.querySelector('[class*="type"], [class*="connector"]');
            if (typeEl) action.type = typeEl.textContent?.trim() || typeEl.getAttribute('aria-label');

            // Get data attributes
            for (const attr of card.attributes) {
                if (attr.name.startsWith('data-')) {
                    action[attr.name] = attr.value;
                }
            }

            if (action.name || action['data-automation-id']) {
                actions.push(action);
            }
        });

        return actions;
    };

    // Get Monaco editor contents
    const getMonacoContents = () => {
        const contents = [];

        if (window.monaco && window.monaco.editor) {
            const models = window.monaco.editor.getModels();
            models.forEach((model, i) => {
                contents.push({
                    index: i,
                    uri: model.uri.toString(),
                    language: model.getLanguageId(),
                    content: model.getValue()
                });
            });
        }

        // Also try to find Monaco instances in DOM
        const monacoContainers = document.querySelectorAll('[class*="monaco-editor"]');
        monacoContainers.forEach((container, i) => {
            const lines = container.querySelectorAll('.view-line');
            if (lines.length > 0) {
                const text = Array.from(lines).map(l => l.textContent).join('\n');
                if (text.trim()) {
                    contents.push({
                        index: `dom-${i}`,
                        source: 'DOM',
                        content: text
                    });
                }
            }
        });

        return contents;
    };

    // Main extraction function
    const extractFlow = async () => {
        const ids = getIdsFromUrl();

        if (!ids.environmentId || !ids.flowId) {
            return {
                success: false,
                error: 'Could not find environment ID or flow ID in URL. Make sure you are on a flow edit page.',
                url: window.location.href
            };
        }

        showStatus(`Found Flow ID: ${ids.flowId}`);
        showStatus(`Found Environment ID: ${ids.environmentId}`);

        // Try API first (most reliable)
        const apiResult = await fetchFlowDefinition(ids.environmentId, ids.flowId);

        // Also gather other data
        const windowData = searchWindowForFlowData();
        const reactData = extractFromReact();
        const domActions = parseActionsFromDOM();
        const monacoContent = getMonacoContents();

        return {
            success: apiResult.success,
            ids,
            timestamp: new Date().toISOString(),
            pageTitle: document.title,
            pageUrl: window.location.href,

            // Primary: API response
            apiResponse: apiResult.success ? apiResult.data : null,
            apiError: apiResult.success ? null : apiResult.error,
            apiEndpoint: apiResult.endpoint,

            // Fallback data
            windowData: windowData.length > 0 ? windowData : null,
            reactData: reactData.length > 0 ? reactData : null,
            domActions: domActions.length > 0 ? domActions : null,
            monacoContent: monacoContent.length > 0 ? monacoContent : null
        };
    };

    // Create UI
    const showUI = (result) => {
        // Remove existing overlay
        const existing = document.getElementById('pa-extractor-overlay');
        if (existing) existing.remove();

        const hasDefinition = result.apiResponse?.properties?.definition ||
                            result.windowData?.some(w => w.data?.definition) ||
                            result.monacoContent?.length > 0;

        const overlay = document.createElement('div');
        overlay.id = 'pa-extractor-overlay';
        overlay.innerHTML = `
            <style>
                #pa-extractor-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.85);
                    z-index: 999999;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: 'Segoe UI', system-ui, sans-serif;
                }
                #pa-extractor-modal {
                    background: white;
                    border-radius: 8px;
                    width: 95%;
                    max-width: 1000px;
                    max-height: 90vh;
                    display: flex;
                    flex-direction: column;
                    box-shadow: 0 4px 30px rgba(0,0,0,0.4);
                }
                #pa-extractor-header {
                    padding: 16px 20px;
                    border-bottom: 1px solid #e0e0e0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: #0078d4;
                    color: white;
                    border-radius: 8px 8px 0 0;
                }
                #pa-extractor-header h2 {
                    margin: 0;
                    font-size: 18px;
                }
                #pa-extractor-close {
                    background: none;
                    border: none;
                    font-size: 28px;
                    cursor: pointer;
                    color: white;
                    line-height: 1;
                }
                #pa-extractor-close:hover { opacity: 0.8; }
                #pa-extractor-content {
                    flex: 1;
                    overflow: auto;
                    padding: 20px;
                }
                #pa-extractor-json {
                    background: #1e1e1e;
                    color: #d4d4d4;
                    padding: 16px;
                    border-radius: 4px;
                    font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
                    font-size: 11px;
                    white-space: pre-wrap;
                    word-break: break-all;
                    max-height: 450px;
                    overflow: auto;
                    line-height: 1.4;
                }
                #pa-extractor-actions {
                    padding: 16px 20px;
                    border-top: 1px solid #e0e0e0;
                    display: flex;
                    gap: 12px;
                    justify-content: flex-end;
                    flex-wrap: wrap;
                }
                .pa-btn {
                    padding: 10px 20px;
                    border-radius: 4px;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.2s;
                }
                .pa-btn-primary {
                    background: #0078d4;
                    color: white;
                }
                .pa-btn-primary:hover { background: #106ebe; }
                .pa-btn-secondary {
                    background: #f3f3f3;
                    color: #333;
                    border: 1px solid #ddd;
                }
                .pa-btn-secondary:hover { background: #e0e0e0; }
                .pa-btn-success {
                    background: #107c10;
                    color: white;
                }
                .pa-btn-success:hover { background: #0b5c0b; }
                #pa-extractor-info {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 16px;
                }
                .pa-info-card {
                    background: #f8f9fa;
                    padding: 12px;
                    border-radius: 6px;
                    border-left: 4px solid #0078d4;
                }
                .pa-info-card.success { border-left-color: #107c10; }
                .pa-info-card.warning { border-left-color: #ca5010; }
                .pa-info-card.error { border-left-color: #d13438; }
                .pa-info-card strong {
                    display: block;
                    color: #333;
                    margin-bottom: 4px;
                    font-size: 12px;
                    text-transform: uppercase;
                }
                .pa-info-card span {
                    color: #666;
                    font-size: 13px;
                    word-break: break-all;
                }
                .pa-tabs {
                    display: flex;
                    gap: 0;
                    margin-bottom: 12px;
                    border-bottom: 2px solid #e0e0e0;
                }
                .pa-tab {
                    padding: 10px 20px;
                    background: none;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                    color: #666;
                    border-bottom: 2px solid transparent;
                    margin-bottom: -2px;
                }
                .pa-tab:hover { color: #0078d4; }
                .pa-tab.active {
                    color: #0078d4;
                    border-bottom-color: #0078d4;
                    font-weight: 600;
                }
                .pa-tab-content { display: none; }
                .pa-tab-content.active { display: block; }
            </style>
            <div id="pa-extractor-modal">
                <div id="pa-extractor-header">
                    <h2>Power Automate Flow Extractor</h2>
                    <button id="pa-extractor-close">&times;</button>
                </div>
                <div id="pa-extractor-content">
                    <div id="pa-extractor-info">
                        <div class="pa-info-card ${result.success ? 'success' : 'error'}">
                            <strong>Status</strong>
                            <span>${result.success ? 'Flow definition retrieved!' : 'API call failed - see fallback data'}</span>
                        </div>
                        <div class="pa-info-card">
                            <strong>Flow ID</strong>
                            <span>${result.ids.flowId || 'Not found'}</span>
                        </div>
                        <div class="pa-info-card">
                            <strong>Environment</strong>
                            <span>${result.ids.environmentId || 'Not found'}</span>
                        </div>
                        <div class="pa-info-card ${hasDefinition ? 'success' : 'warning'}">
                            <strong>Definition Found</strong>
                            <span>${hasDefinition ? 'Yes' : 'Partial data only'}</span>
                        </div>
                    </div>

                    <div class="pa-tabs">
                        <button class="pa-tab active" data-tab="full">Full Export</button>
                        ${result.apiResponse ? '<button class="pa-tab" data-tab="definition">Definition Only</button>' : ''}
                        ${result.monacoContent?.length ? '<button class="pa-tab" data-tab="monaco">Code Views</button>' : ''}
                        ${result.domActions?.length ? '<button class="pa-tab" data-tab="actions">Actions (DOM)</button>' : ''}
                    </div>

                    <div id="pa-tab-full" class="pa-tab-content active">
                        <div id="pa-extractor-json">${JSON.stringify(result, null, 2)}</div>
                    </div>
                    ${result.apiResponse ? `
                        <div id="pa-tab-definition" class="pa-tab-content">
                            <div id="pa-extractor-json-def" class="pa-extractor-json" style="background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:4px;font-family:monospace;font-size:11px;white-space:pre-wrap;max-height:450px;overflow:auto;">${JSON.stringify(result.apiResponse.properties?.definition || result.apiResponse, null, 2)}</div>
                        </div>
                    ` : ''}
                    ${result.monacoContent?.length ? `
                        <div id="pa-tab-monaco" class="pa-tab-content">
                            <div style="background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:4px;font-family:monospace;font-size:11px;white-space:pre-wrap;max-height:450px;overflow:auto;">${result.monacoContent.map(m => `// ${m.uri || m.source}\n${m.content}`).join('\n\n---\n\n')}</div>
                        </div>
                    ` : ''}
                    ${result.domActions?.length ? `
                        <div id="pa-tab-actions" class="pa-tab-content">
                            <div style="background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:4px;font-family:monospace;font-size:11px;white-space:pre-wrap;max-height:450px;overflow:auto;">${JSON.stringify(result.domActions, null, 2)}</div>
                        </div>
                    ` : ''}
                </div>
                <div id="pa-extractor-actions">
                    <button class="pa-btn pa-btn-secondary" id="pa-copy-btn">Copy Full JSON</button>
                    ${result.apiResponse ? '<button class="pa-btn pa-btn-secondary" id="pa-copy-def-btn">Copy Definition Only</button>' : ''}
                    <button class="pa-btn pa-btn-primary" id="pa-download-btn">Download JSON</button>
                    ${result.apiResponse ? '<button class="pa-btn pa-btn-success" id="pa-download-def-btn">Download Definition</button>' : ''}
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Tab switching
        overlay.querySelectorAll('.pa-tab').forEach(tab => {
            tab.onclick = () => {
                overlay.querySelectorAll('.pa-tab').forEach(t => t.classList.remove('active'));
                overlay.querySelectorAll('.pa-tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(`pa-tab-${tab.dataset.tab}`).classList.add('active');
            };
        });

        // Event handlers
        document.getElementById('pa-extractor-close').onclick = () => overlay.remove();
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

        document.getElementById('pa-copy-btn').onclick = () => {
            navigator.clipboard.writeText(JSON.stringify(result, null, 2))
                .then(() => alert('Full JSON copied to clipboard!'))
                .catch(e => {
                    // Fallback for older browsers
                    const ta = document.createElement('textarea');
                    ta.value = JSON.stringify(result, null, 2);
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    alert('Copied!');
                });
        };

        const copyDefBtn = document.getElementById('pa-copy-def-btn');
        if (copyDefBtn && result.apiResponse) {
            copyDefBtn.onclick = () => {
                const def = result.apiResponse.properties?.definition || result.apiResponse;
                navigator.clipboard.writeText(JSON.stringify(def, null, 2))
                    .then(() => alert('Definition copied to clipboard!'));
            };
        }

        document.getElementById('pa-download-btn').onclick = () => {
            const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `power-automate-${result.ids.flowId || 'export'}-full-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        };

        const downloadDefBtn = document.getElementById('pa-download-def-btn');
        if (downloadDefBtn && result.apiResponse) {
            downloadDefBtn.onclick = () => {
                const def = result.apiResponse.properties?.definition || result.apiResponse;
                const blob = new Blob([JSON.stringify(def, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `power-automate-${result.ids.flowId || 'export'}-definition-${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
            };
        }
    };

    // Show loading
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'pa-extractor-loading';
    loadingOverlay.innerHTML = `
        <style>
            #pa-extractor-loading {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.8);
                z-index: 999999;
                display: flex;
                justify-content: center;
                align-items: center;
                font-family: 'Segoe UI', system-ui, sans-serif;
                color: white;
                flex-direction: column;
                gap: 20px;
            }
            .pa-spinner {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(255,255,255,0.3);
                border-top-color: #0078d4;
                border-radius: 50%;
                animation: pa-spin 1s linear infinite;
            }
            @keyframes pa-spin {
                to { transform: rotate(360deg); }
            }
        </style>
        <div class="pa-spinner"></div>
        <div>Extracting flow definition...</div>
    `;
    document.body.appendChild(loadingOverlay);

    // Run extraction
    extractFlow().then(result => {
        loadingOverlay.remove();
        showUI(result);
        console.log('Power Automate Flow Extraction Result:', result);
    }).catch(err => {
        loadingOverlay.remove();
        alert('Extraction failed: ' + err.message);
        console.error('PA Extractor Error:', err);
    });
})();
