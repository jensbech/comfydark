/**
 * VS Code Dark+ for GitHub - Popup Script
 * Handles the toggle UI in the browser toolbar
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'vscode-github-syntax-enabled';
  const toggle = document.getElementById('toggle');
  const status = document.getElementById('status');

  // Load initial state
  function loadState() {
    browser.storage.local.get(STORAGE_KEY).then((result) => {
      const isEnabled = result[STORAGE_KEY] !== false; // Default to enabled
      toggle.checked = isEnabled;
      updateStatus(isEnabled);
    }).catch((error) => {
      console.error('Error loading state:', error);
      toggle.checked = true;
      updateStatus(true);
    });
  }

  // Update the status text
  function updateStatus(isEnabled) {
    if (isEnabled) {
      status.textContent = 'Theme is active';
      status.className = 'status enabled';
    } else {
      status.textContent = 'Theme is disabled';
      status.className = 'status disabled';
    }
  }

  // Save state and notify content script
  function saveState(isEnabled) {
    browser.storage.local.set({ [STORAGE_KEY]: isEnabled }).then(() => {
      updateStatus(isEnabled);
      
      // Notify all GitHub tabs
      browser.tabs.query({ url: ['*://github.com/*', '*://gist.github.com/*'] }).then((tabs) => {
        tabs.forEach((tab) => {
          browser.tabs.sendMessage(tab.id, { type: 'toggle', enabled: isEnabled }).catch(() => {
            // Tab might not have content script loaded yet, ignore
          });
        });
      });
    }).catch((error) => {
      console.error('Error saving state:', error);
    });
  }

  // Handle toggle change
  toggle.addEventListener('change', (e) => {
    saveState(e.target.checked);
  });

  // Initialize
  loadState();
})();
