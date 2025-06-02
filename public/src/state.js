export const createInitialState = () => ({
  video: document.getElementById('video'),
  startBtn: document.getElementById('startCamera'),
  stopBtn: document.getElementById('stopCamera'),
  results: document.getElementById('detectedNumbers'),

  stream: null,
  peerConnection: null,
  websocket: null,
});
