export const initialize = (state, onMessageCallback) => {
  try {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/webrtc-signaling`;

    state.websocket = new WebSocket(wsUrl);

    state.websocket.onopen = () => {
      state.results.textContent = 'WebRTC signaling connected';
    };

    state.websocket.onmessage = async event => {
      try {
        const message = JSON.parse(event.data);
        console.log('Signaling message:', message.type, message);

        if (message.type === 'answer') {
          await handleAnswer(message.answer, state);
        } else if (message.type === 'ice-candidate') {
          await handleIceCandidate(message.candidate, state);
        } else if (onMessageCallback) {
          onMessageCallback(message);
        }
      } catch (error) {
        console.error('Signaling error:', error);
      }
    };

    state.websocket.onclose = () => {
      console.log('WebRTC signaling disconnected, reconnecting...');
      state.results.textContent =
        'WebRTC signaling disconnected, reconnecting in 3sec';
      setTimeout(() => {
        initialize(state, onMessageCallback);
      }, 3000);
    };

    state.websocket.onerror = error => {
      console.error('WebRTC signaling error:', error);
      state.results.textContent = 'WebRTC signaling error';
    };
  } catch (error) {
    console.error('Error initializing WebRTC signaling:', error);
  }
};

export const setupWebRTC = async state => {
  try {
    state.peerConnection = new RTCPeerConnection({
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
      ],
    });

    // Add video stream to peer connection
    state.stream.getTracks().forEach(track => {
      state.peerConnection.addTrack(track, state.stream);
    });

    // Handle ICE candidates
    state.peerConnection.onicecandidate = event => {
      if (event.candidate) {
        console.log('Sending ICE candidate:', event.candidate);
        state.websocket.send(
          JSON.stringify({
            type: 'ice-candidate',
            candidate: event.candidate,
          })
        );
      }
    };

    // Monitors
    state.peerConnection.onconnectionstatechange = () => {
      console.log('Connection state:', state.peerConnection.connectionState);
    };
    state.peerConnection.oniceconnectionstatechange = () => {
      console.log(
        'ICE connection state:',
        state.peerConnection.iceConnectionState
      );
    };

    // Create offer
    const offer = await state.peerConnection.createOffer();
    await state.peerConnection.setLocalDescription(offer);

    // Send offer to server
    state.websocket.send(
      JSON.stringify({
        type: 'offer',
        offer: offer,
      })
    );

    console.log('WebRTC offer sent to server');
  } catch (error) {
    state.results.textContent = `Error WebRTC: ${error.message}`;
    console.error('Error setting up WebRTC:', error);
  }
};

const handleAnswer = async (answer, state) => {
  await state.peerConnection.setRemoteDescription(
    new RTCSessionDescription(answer)
  );
};

const handleIceCandidate = async (candidate, state) => {
  await state.peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
};
