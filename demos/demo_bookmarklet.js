javascript:(function(){
  /* Contract Analysis Agent Demo Controller - Draggable Version */

  const DEMO_STEPS = [
    { title: "List Contracts", message: "List all contracts available for analysis" },
    { title: "Full Workup", message: "Work on bella_rivers_recording_agreement.pdf" },
    { title: "Risk Deep Dive", message: "What are the biggest risks to the label in this contract?" },
    { title: "Compare Contracts", message: "Compare bella_rivers_recording_agreement.pdf with viper_morrison_recording_agreement.pdf" },
    { title: "Deal Breakers", message: "Identify all risks in viper_morrison_recording_agreement.pdf from the label's perspective. Flag any potential deal breakers." },
    { title: "Clause Extraction", message: "Extract only the financial and termination clauses from bella_rivers_recording_agreement.pdf" },
    { title: "Negotiation Strategy", message: "Based on the Viper Morrison contract risks, what should the label push back on during negotiations?" }
  ];

  /* Remove existing panel if present */
  const existingPanel = document.getElementById('demo-controller');
  if (existingPanel) { existingPanel.remove(); return; }

  /* Create draggable control panel */
  const panel = document.createElement('div');
  panel.id = 'demo-controller';

  /* Create style element */
  const style = document.createElement('style');
  style.textContent = `
    #demo-controller {
      position: fixed;
      top: 10px;
      right: 10px;
      width: 320px;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      border: 1px solid #0f3460;
      border-radius: 12px;
      padding: 0;
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
      color: #e0e0e0;
      font-size: 13px;
      cursor: default;
    }
    #demo-controller .drag-header {
      background: #0f3460;
      padding: 12px 16px;
      border-radius: 12px 12px 0 0;
      cursor: move;
      display: flex;
      justify-content: space-between;
      align-items: center;
      user-select: none;
    }
    #demo-controller .drag-header h3 {
      margin: 0;
      color: #00d4ff;
      font-size: 14px;
    }
    #demo-controller .drag-hint {
      font-size: 10px;
      color: #666;
      margin-left: 8px;
    }
    #demo-controller .header-btns {
      display: flex;
      gap: 8px;
    }
    #demo-controller .header-btn {
      background: none;
      border: none;
      color: #888;
      cursor: pointer;
      font-size: 16px;
      padding: 2px 6px;
      border-radius: 4px;
      line-height: 1;
    }
    #demo-controller .header-btn:hover { background: #1a4a7a; color: #00d4ff; }
    #demo-controller .minimize-btn { font-size: 20px; line-height: 0.8; }
    #demo-controller .close-btn:hover { color: #ff4444; }
    #demo-controller .content {
      padding: 12px 16px 16px;
    }
    #demo-controller.minimized .content { display: none; }
    #demo-controller.minimized { width: auto; min-width: 200px; }
    #demo-controller .step-btn {
      display: block;
      width: 100%;
      padding: 10px 12px;
      margin: 6px 0;
      background: #0f3460;
      color: #e0e0e0;
      border: 1px solid #1a4a7a;
      border-radius: 8px;
      cursor: pointer;
      text-align: left;
      font-size: 12px;
      transition: all 0.15s;
    }
    #demo-controller .step-btn:hover {
      background: #1a5a9a;
      border-color: #00d4ff;
      transform: translateX(4px);
    }
    #demo-controller .step-btn.done {
      background: #0a3a2a;
      border-color: #00ff88;
      color: #00ff88;
    }
    #demo-controller .step-num {
      display: inline-block;
      width: 20px;
      height: 20px;
      background: #00d4ff;
      color: #1a1a2e;
      border-radius: 50%;
      text-align: center;
      line-height: 20px;
      font-weight: bold;
      margin-right: 8px;
      font-size: 11px;
    }
    #demo-controller .status {
      margin-top: 12px;
      padding: 8px;
      background: #0a0a1a;
      border-radius: 6px;
      font-size: 11px;
      color: #888;
    }
    #demo-controller .custom-input {
      width: calc(100% - 16px);
      padding: 8px;
      margin: 8px 0;
      background: #0a0a1a;
      border: 1px solid #1a4a7a;
      border-radius: 6px;
      color: #e0e0e0;
      font-size: 12px;
    }
    #demo-controller .send-custom {
      background: #00d4ff;
      color: #1a1a2e;
      font-weight: bold;
    }
    #demo-controller .send-custom:hover {
      background: #00ffff;
    }
    #demo-controller .reset-btn {
      background: #3a1a1a;
      border-color: #5a2a2a;
      color: #ff8888;
      margin-top: 4px;
    }
    #demo-controller .reset-btn:hover {
      background: #4a2020;
      border-color: #7a3a3a;
    }
    #demo-controller hr {
      border: none;
      border-top: 1px solid #1a4a7a;
      margin: 12px 0;
    }
  `;
  document.head.appendChild(style);

  /* Build panel HTML */
  const header = document.createElement('div');
  header.className = 'drag-header';
  header.innerHTML = '<h3>Contract Demo<span class="drag-hint">(drag to move)</span></h3><div class="header-btns"><button class="header-btn minimize-btn" title="Minimize">−</button><button class="header-btn close-btn" title="Close">×</button></div>';

  const content = document.createElement('div');
  content.className = 'content';

  const stepsDiv = document.createElement('div');
  stepsDiv.id = 'demo-steps';

  const hr = document.createElement('hr');

  const customInput = document.createElement('input');
  customInput.type = 'text';
  customInput.className = 'custom-input';
  customInput.id = 'custom-msg';
  customInput.placeholder = 'Or type custom message...';

  const sendBtn = document.createElement('button');
  sendBtn.className = 'step-btn send-custom';
  sendBtn.textContent = 'Send Custom Message';

  const resetBtn = document.createElement('button');
  resetBtn.className = 'step-btn reset-btn';
  resetBtn.textContent = 'Reset All Steps';

  const statusDiv = document.createElement('div');
  statusDiv.className = 'status';
  statusDiv.id = 'demo-status';
  statusDiv.textContent = 'Drag header to reposition. Click steps to send.';

  content.appendChild(stepsDiv);
  content.appendChild(hr);
  content.appendChild(customInput);
  content.appendChild(sendBtn);
  content.appendChild(resetBtn);
  content.appendChild(statusDiv);

  panel.appendChild(header);
  panel.appendChild(content);
  document.body.appendChild(panel);

  /* Render step buttons */
  DEMO_STEPS.forEach(function(step, i) {
    const btn = document.createElement('button');
    btn.className = 'step-btn';
    btn.id = 'demo-step-' + i;
    btn.title = step.message;

    const num = document.createElement('span');
    num.className = 'step-num';
    num.textContent = i + 1;
    btn.appendChild(num);
    btn.appendChild(document.createTextNode(step.title));

    btn.addEventListener('click', function() { sendStep(i); });
    stepsDiv.appendChild(btn);
  });

  /* Make panel draggable */
  let isDragging = false;
  let dragOffsetX = 0;
  let dragOffsetY = 0;

  header.addEventListener('mousedown', function(e) {
    if (e.target.tagName === 'BUTTON') return;
    isDragging = true;
    dragOffsetX = e.clientX - panel.offsetLeft;
    dragOffsetY = e.clientY - panel.offsetTop;
    panel.style.transition = 'none';
  });

  document.addEventListener('mousemove', function(e) {
    if (!isDragging) return;
    const newX = e.clientX - dragOffsetX;
    const newY = e.clientY - dragOffsetY;
    panel.style.left = newX + 'px';
    panel.style.right = 'auto';
    panel.style.top = newY + 'px';
  });

  document.addEventListener('mouseup', function() {
    isDragging = false;
    panel.style.transition = '';
  });

  /* Button handlers */
  header.querySelector('.close-btn').addEventListener('click', function() {
    panel.remove();
    style.remove();
  });

  header.querySelector('.minimize-btn').addEventListener('click', function() {
    panel.classList.toggle('minimized');
    this.textContent = panel.classList.contains('minimized') ? '+' : '−';
  });

  sendBtn.addEventListener('click', sendCustom);
  resetBtn.addEventListener('click', resetSteps);
  customInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendCustom();
  });

  /* Functions */
  function updateStatus(msg) {
    document.getElementById('demo-status').textContent = msg;
  }

  async function sendMessage(message) {
    updateStatus('Finding chat input...');

    const input = document.querySelector('#m365-chat-editor-target-element') ||
                  document.querySelector('[aria-label="Message Copilot"]') ||
                  document.querySelector('[data-lexical-editor="true"]');

    if (!input) {
      updateStatus('Error: Could not find chat input!');
      return false;
    }

    input.focus();
    await new Promise(function(r) { setTimeout(r, 100); });
    document.execCommand('selectAll', false, null);
    await new Promise(function(r) { setTimeout(r, 50); });
    document.execCommand('delete', false, null);
    await new Promise(function(r) { setTimeout(r, 100); });

    updateStatus('Typing message...');
    document.execCommand('insertText', false, message);
    await new Promise(function(r) { setTimeout(r, 200); });

    const sendButton = document.querySelector('button[aria-label="Send"]') ||
                       document.querySelector('button[data-testid="send-button"]');

    if (sendButton && !sendButton.disabled) {
      updateStatus('Sending...');
      sendButton.click();
      updateStatus('Message sent! Waiting for response...');
      return true;
    } else {
      updateStatus('Message typed. Click Send or press Enter.');
      return false;
    }
  }

  async function sendStep(index) {
    const step = DEMO_STEPS[index];
    updateStatus('Sending: ' + step.title + '...');
    const success = await sendMessage(step.message);
    if (success) {
      document.getElementById('demo-step-' + index).classList.add('done');
    }
  }

  async function sendCustom() {
    const input = document.getElementById('custom-msg');
    if (input.value.trim()) {
      await sendMessage(input.value.trim());
      input.value = '';
    }
  }

  function resetSteps() {
    DEMO_STEPS.forEach(function(_, i) {
      const btn = document.getElementById('demo-step-' + i);
      if (btn) btn.classList.remove('done');
    });
    updateStatus('All steps reset. Ready!');
  }
})();
