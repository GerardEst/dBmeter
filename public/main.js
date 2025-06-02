import { createInitialState } from './src/state.js';
import * as roi from './src/roi.js';
import * as websocket from './src/websocket.js';

document.addEventListener('DOMContentLoaded', () => {
  const state = createInitialState();

  state.startBtn.onclick = () => startCamera(state);
  state.stopBtn.onclick = () => stopCamera(state);

  websocket.initialize(state, message => {
    if (message.type === 'numbers') {
      displayNumbers(message.data, state);
    }
  });
});

const displayNumbers = (numbers, state) => {
  state.results.textContent = numbers;
};

const startCamera = async state => {
  const mediaConstraints = {
    video: {
      width: { ideal: 1280 },
      height: { ideal: 720 },
      frameRate: { ideal: 30 },
      facingMode: 'environment',
    },
  };
  try {
    // getUserMedia ens dona un MediaStream -> un flux de dades de video (o audio) a temps real
    // que podem passar a srcObject per renderitzar-lo
    state.stream = await navigator.mediaDevices.getUserMedia(mediaConstraints);

    state.video.srcObject = state.stream;
    state.startBtn.disabled = true;
    state.stopBtn.disabled = false;

    state.video.onloadedmetadata = () => {
      roi.updateROIOverlay(state);
    };
    window.addEventListener('resize', () => {
      roi.positionROIOverlay(state);
    });

    await websocket.setupWebRTC(state);
  } catch (error) {
    console.error('Error accessing camera:', error);
    state.results.textContent = `Error: ${error.message}`;
  }
};

const stopCamera = state => {
  if (state.stream) {
    state.stream.getTracks().forEach(track => track.stop());
    state.stream = null;
  }

  if (state.peerConnection) {
    state.peerConnection.close();
    state.peerConnection = null;
  }

  roi.removeROIOverlay(state);

  state.video.srcObject = null;
  state.startBtn.disabled = false;
  state.stopBtn.disabled = true;
};
