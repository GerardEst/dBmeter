export class NumberDetector {
  constructor() {
    this.video = document.getElementById('video');
    this.startBtn = document.getElementById('startCamera');
    this.stopBtn = document.getElementById('stopCamera');
    this.toggleROIBtn = document.getElementById('toggleROI');
    this.results = document.getElementById('detectedNumbers');

    this.stream = null;
    this.peerConnection = null;
    this.websocket = null;
    this.roiEnabled = true;

    this.initializeEvents();
    this.initializeWebSocket();
  }

  initializeEvents() {
    this.startBtn.addEventListener('click', () => this.startCamera());
    this.stopBtn.addEventListener('click', () => this.stopCamera());
    this.toggleROIBtn.addEventListener('click', () => this.toggleROI());
  }

  toggleROI() {
    this.roiEnabled = !this.roiEnabled;

    // Send ROI preference to server
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(
        JSON.stringify({
          type: 'roi-toggle',
          enabled: this.roiEnabled,
        })
      );
    }

    this.updateROIOverlay();
  }

  updateROIOverlay() {
    let overlay = document.getElementById('roi-overlay');

    if (!this.roiEnabled) {
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
      this.video.parentElement.style.position = 'relative';
      this.video.parentElement.appendChild(overlay);
    }

    // Show overlay
    overlay.style.display = 'block';

    // Update overlay position based on video dimensions (matches server logic)
    this.positionROIOverlay();
  }

  positionROIOverlay() {
    const overlay = document.getElementById('roi-overlay');
    if (!overlay || !this.video.videoWidth || !this.video.videoHeight) {
      return;
    }

    // Get video display dimensions
    const rect = this.video.getBoundingClientRect();
    const displayWidth = rect.width;
    const displayHeight = rect.height;

    // Calculate scale factors
    const scaleX = displayWidth / this.video.videoWidth;
    const scaleY = displayHeight / this.video.videoHeight;

    // Server-side ROI logic: center 60% with padding
    const videoWidth = this.video.videoWidth;
    const videoHeight = this.video.videoHeight;

    const roiWidth = Math.floor(videoWidth * 0.6);
    const roiHeight = Math.floor(videoHeight * 0.6);
    const padding = 40;

    const centerX = Math.floor(videoWidth / 2);
    const centerY = Math.floor(videoHeight / 2);

    const x1 = Math.max(0, centerX - Math.floor(roiWidth / 2) - padding);
    const y1 = Math.max(0, centerY - Math.floor(roiHeight / 2) - padding);
    const x2 = Math.min(
      videoWidth,
      centerX + Math.floor(roiWidth / 2) + padding
    );
    const y2 = Math.min(
      videoHeight,
      centerY + Math.floor(roiHeight / 2) + padding
    );

    // Apply to overlay (scale to display size)
    overlay.style.left = x1 * scaleX + 'px';
    overlay.style.top = y1 * scaleY + 'px';
    overlay.style.width = (x2 - x1) * scaleX + 'px';
    overlay.style.height = (y2 - y1) * scaleY + 'px';
  }

  initializeWebSocket() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/webrtc-signaling`;

      console.log('Connecting to WebRTC signaling:', wsUrl);
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log('WebRTC signaling connected');
        this.results.textContent = 'WebRTC signaling connected';
      };

      this.websocket.onmessage = async event => {
        try {
          const message = JSON.parse(event.data);
          console.log('Signaling message:', message.type, message);

          if (message.type === 'numbers') {
            // Display numbers detected by server (with debug info)
            this.displayNumbers(message.data, message.frame_count);
          } else if (message.type === 'offer') {
            await this.handleOffer(message.offer);
          } else if (message.type === 'answer') {
            await this.handleAnswer(message.answer);
          } else if (message.type === 'ice-candidate') {
            await this.handleIceCandidate(message.candidate);
          }
        } catch (error) {
          console.error('Signaling error:', error);
        }
      };

      this.websocket.onclose = () => {
        console.log('WebRTC signaling disconnected, reconnecting...');
        this.results.textContent =
          'WebRTC signaling disconnected, reconnecting in 3sec';
        setTimeout(() => {
          this.initializeWebSocket();
        }, 3000);
      };

      this.websocket.onerror = error => {
        console.error('WebRTC signaling error:', error);
        this.results.textContent = 'WebRTC signaling error';
      };
    } catch (error) {
      console.error('Error initializing WebRTC signaling:', error);
    }
  }

  async startCamera() {
    try {
      // Get high-quality video stream
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 },
          facingMode: 'environment',
        },
      });

      this.video.srcObject = this.stream;
      this.startBtn.disabled = true;
      this.stopBtn.disabled = false;

      // Update ROI overlay when video metadata loads
      this.video.onloadedmetadata = () => {
        console.log(
          `Video: ${this.video.videoWidth}x${this.video.videoHeight}`
        );
        this.updateROIOverlay();
      };

      // Update overlay on window resize
      window.addEventListener('resize', () => {
        this.positionROIOverlay();
      });

      // Setup WebRTC connection
      await this.setupWebRTC();
    } catch (error) {
      console.error('Error accessing camera:', error);
      this.results.textContent = `Error: ${error.message}`;
    }
  }

  async setupWebRTC() {
    try {
      this.peerConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
        ],
      });

      // Add video stream to peer connection
      this.stream.getTracks().forEach(track => {
        this.peerConnection.addTrack(track, this.stream);
      });

      // Handle ICE candidates
      this.peerConnection.onicecandidate = event => {
        if (event.candidate) {
          console.log('Sending ICE candidate:', event.candidate);
          this.websocket.send(
            JSON.stringify({
              type: 'ice-candidate',
              candidate: event.candidate,
            })
          );
        }
      };

      // Monitor connection state
      this.peerConnection.onconnectionstatechange = () => {
        console.log('Connection state:', this.peerConnection.connectionState);
        this.updateConnectionStatus(this.peerConnection.connectionState);
      };

      // Monitor ICE connection state
      this.peerConnection.oniceconnectionstatechange = () => {
        console.log(
          'ICE connection state:',
          this.peerConnection.iceConnectionState
        );
      };

      // Create offer
      const offer = await this.peerConnection.createOffer();
      await this.peerConnection.setLocalDescription(offer);

      // Send offer to server
      this.websocket.send(
        JSON.stringify({
          type: 'offer',
          offer: offer,
        })
      );

      console.log('WebRTC offer sent to server');
    } catch (error) {
      console.error('Error setting up WebRTC:', error);
      this.results.textContent = `Error WebRTC: ${error.message}`;
    }
  }

  updateConnectionStatus(state) {
    let statusMessage = '';
    switch (state) {
      case 'connecting':
        statusMessage = 'Connectant WebRTC...';
        break;
      case 'connected':
        statusMessage = 'WebRTC connectat - Enviant video al servidor';
        break;
      case 'disconnected':
        statusMessage = 'WebRTC desconnectat';
        break;
      case 'failed':
        statusMessage = 'Error de connexió WebRTC';
        break;
      default:
        statusMessage = `WebRTC: ${state}`;
    }

    if (state !== 'connected') {
      this.results.textContent = statusMessage;
    }
  }

  async handleOffer(offer) {
    await this.peerConnection.setRemoteDescription(
      new RTCSessionDescription(offer)
    );
    const answer = await this.peerConnection.createAnswer();
    await this.peerConnection.setLocalDescription(answer);

    this.websocket.send(
      JSON.stringify({
        type: 'answer',
        answer: answer,
      })
    );
  }

  async handleAnswer(answer) {
    await this.peerConnection.setRemoteDescription(
      new RTCSessionDescription(answer)
    );
  }

  async handleIceCandidate(candidate) {
    await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    // Hide ROI overlay
    const overlay = document.getElementById('roi-overlay');
    if (overlay) {
      overlay.remove();
    }

    this.video.srcObject = null;
    this.startBtn.disabled = false;
    this.stopBtn.disabled = true;
  }

  displayNumbers(numbers) {
    if (numbers && numbers.length > 0) {
      this.results.textContent = numbers.join(' ');
    } else {
      this.results.textContent = 'No num detected';
    }
  }
}
