export const createInitialState = () => ({
  video: document.getElementById('video'),
  startBtn: document.getElementById('startCamera'),
  stopBtn: document.getElementById('stopCamera'),
  toggleROIBtn: document.getElementById('toggleROI'),
  results: document.getElementById('detectedNumbers'),

  stream: null,
  peerConnection: null,
  websocket: null,
  roiEnabled: true,
});
