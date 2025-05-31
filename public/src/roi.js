export const toggleROI = state => {
  state.roiEnabled = !state.roiEnabled;

  // Send ROI preference to server
  if (state.websocket && state.websocket.readyState === WebSocket.OPEN) {
    state.websocket.send(
      JSON.stringify({
        type: 'roi-toggle',
        enabled: state.roiEnabled,
      })
    );
  }

  updateROIOverlay(state);
};

export const removeROIOverlay = state => {
  const overlay = document.getElementById('roi-overlay');
  if (overlay) {
    overlay.remove();
  }
};

export const updateROIOverlay = state => {
  let overlay = document.getElementById('roi-overlay');

  if (!state.roiEnabled) {
    // Hide overlay when ROI is disabled
    if (overlay) {
      overlay.style.display = 'none';
    }
    return;
  }

  // Create overlay if it doesn't exist
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'roi-overlay';
    overlay.style.position = 'absolute';
    overlay.style.border = '3px solid #00ff00';
    overlay.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
    overlay.style.pointerEvents = 'none';
    overlay.style.zIndex = '10';
    overlay.style.borderRadius = '4px';

    // Add label
    const label = document.createElement('div');
    label.textContent = 'ÀREA DEL SERVIDOR';
    label.style.position = 'absolute';
    label.style.top = '-25px';
    label.style.left = '0px';
    label.style.color = '#00ff00';
    label.style.fontSize = '12px';
    label.style.fontWeight = 'bold';
    label.style.textShadow = '1px 1px 2px rgba(0,0,0,0.8)';
    overlay.appendChild(label);

    // Make video container relative positioned
    state.video.parentElement.style.position = 'relative';
    state.video.parentElement.appendChild(overlay);
  }

  // Show overlay
  overlay.style.display = 'block';

  // Update overlay position based on video dimensions (matches server logic)
  positionROIOverlay(state);
};

export const positionROIOverlay = state => {
  const overlay = document.getElementById('roi-overlay');
  if (!overlay || !state.video.videoWidth || !state.video.videoHeight) {
    return;
  }

  // Get video display dimensions
  const rect = state.video.getBoundingClientRect();
  const displayWidth = rect.width;
  const displayHeight = rect.height;

  // Calculate scale factors
  const scaleX = displayWidth / state.video.videoWidth;
  const scaleY = displayHeight / state.video.videoHeight;

  // Server-side ROI logic: center 60% with padding
  const videoWidth = state.video.videoWidth;
  const videoHeight = state.video.videoHeight;

  const roiWidth = Math.floor(videoWidth * 0.6);
  const roiHeight = Math.floor(videoHeight * 0.6);
  const padding = 40;

  const centerX = Math.floor(videoWidth / 2);
  const centerY = Math.floor(videoHeight / 2);

  const x1 = Math.max(0, centerX - Math.floor(roiWidth / 2) - padding);
  const y1 = Math.max(0, centerY - Math.floor(roiHeight / 2) - padding);
  const x2 = Math.min(videoWidth, centerX + Math.floor(roiWidth / 2) + padding);
  const y2 = Math.min(
    videoHeight,
    centerY + Math.floor(roiHeight / 2) + padding
  );

  // Apply to overlay (scale to display size)
  overlay.style.left = x1 * scaleX + 'px';
  overlay.style.top = y1 * scaleY + 'px';
  overlay.style.width = (x2 - x1) * scaleX + 'px';
  overlay.style.height = (y2 - y1) * scaleY + 'px';
};
