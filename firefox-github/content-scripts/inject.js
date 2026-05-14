/**
 * VS Code Dark+ for GitHub - Content Script
 * Handles toggle state via CSS class on html element
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'vscode-github-syntax-enabled';

  // Apply state by adding/removing class on html element
  function applyState(isEnabled) {
    if (isEnabled) {
      document.documentElement.classList.remove('vscode-github-syntax-disabled');
    } else {
      document.documentElement.classList.add('vscode-github-syntax-disabled');
    }
  }

  // Load and apply initial state
  function init() {
    browser.storage.local.get(STORAGE_KEY).then((result) => {
      // Default to enabled (true) if not set
      const isEnabled = result[STORAGE_KEY] !== false;
      applyState(isEnabled);
    }).catch((error) => {
      console.error('VS Code GitHub Syntax: Error reading state', error);
      // Default to enabled on error
      applyState(true);
    });
  }

  // Listen for messages from the popup
  browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'toggle') {
      applyState(message.enabled);
      sendResponse({ success: true });
    } else if (message.type === 'getState') {
      const isDisabled = document.documentElement.classList.contains('vscode-github-syntax-disabled');
      sendResponse({ enabled: !isDisabled });
    }
    return false;
  });

  // Run immediately
  init();

  // Also run when DOM is ready (in case we loaded too early)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  }
})();
