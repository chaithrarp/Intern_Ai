import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import './AudioRecorder.css';

function AudioRecorder({ onAudioReady, questionId, sessionId, onRecordingStateChange }) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState('');   
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  
  // Start Recording
  const startRecording = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support audio recording. Please use Chrome or Edge.');
        return;
      }

      console.log('Requesting microphone access...');
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      console.log('Microphone access granted!');
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        
        stream.getTracks().forEach(track => track.stop());
        
        // Notify parent that recording stopped
        if (onRecordingStateChange) {
          onRecordingStateChange(false);
        }
        
        // Auto-transcribe
        await transcribeAudio(blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Notify parent that recording started
      if (onRecordingStateChange) {
        onRecordingStateChange(true);
      }

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Microphone error:', error);
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        alert('❌ Microphone permission denied.\n\nPlease:\n1. Click the camera/mic icon in the address bar\n2. Allow microphone access\n3. Refresh the page');
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        alert('❌ No microphone found.\n\nPlease:\n1. Connect a microphone\n2. Check Windows sound settings\n3. Refresh the page');
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        alert('❌ Microphone is being used by another application.\n\nPlease:\n1. Close other apps using the microphone (Zoom, Teams, etc.)\n2. Refresh the page');
      } else {
        alert(`❌ Microphone error: ${error.message}\n\nCheck browser console (F12) for details.`);
      }
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  const transcribeAudio = async (blob) => {
    setTranscribing(true);
    
    try {
      const formData = new FormData();
      formData.append('audio_file', blob, 'recording.webm');

      console.log('Transcribing audio...');

      const response = await fetch(
        `http://localhost:8000/interview/upload-audio?session_id=${sessionId}&question_id=${questionId}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      const data = await response.json();
      console.log('Transcription response:', data);

      if (data.success) {
        setTranscript(data.transcript);
        console.log('Transcript:', data.transcript);
      } else {
        alert('Transcription failed: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Transcription error:', error);
      alert('Failed to transcribe audio');
    } finally {
      setTranscribing(false);
    }
  };

  const submitAnswer = () => {
    if (!transcript) {
      alert('Transcript is empty. Please try re-recording.');
      return;
    }

    onAudioReady({
      transcript: transcript,
      language: 'en'
    });
    
    resetRecording();
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    setTranscript('');
    setTranscribing(false);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="audio-recorder">
      {!audioBlob ? (
        <div className="recording-interface">
          {!isRecording ? (
            <motion.button 
              className="btn-record"
              onClick={startRecording}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <span className="mic-icon">🎤</span>
              <span>Start Recording</span>
            </motion.button>
          ) : (
            <>
              <motion.div 
                className="recording-indicator"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                <div className="pulse-dot"></div>
                <span>Recording... {formatTime(recordingTime)}</span>
              </motion.div>
              <motion.button 
                className="btn-stop" 
                onClick={stopRecording}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                ⏹ Stop Recording
              </motion.button>
            </>
          )}
        </div>
      ) : (
        <motion.div 
          className="playback-interface"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <p className="recording-info">
            ✅ Recording captured ({formatTime(recordingTime)})
          </p>
          
          <audio controls src={URL.createObjectURL(audioBlob)} className="audio-player" />
          
          {transcribing && (
            <motion.div 
              className="transcribing-indicator"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="spinner"></div>
              <p>Transcribing your answer...</p>
            </motion.div>
          )}
          
          {transcript && !transcribing && (
            <motion.div 
              className="transcript-preview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <p className="transcript-label">📝 What I heard:</p>
              <p className="transcript-text">{transcript}</p>
            </motion.div>
          )}
          
          <div className="action-buttons">
            <motion.button 
              className="btn-rerecord" 
              onClick={resetRecording}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              🔄 Re-record
            </motion.button>
            <motion.button 
              className="btn-upload" 
              onClick={submitAnswer}
              disabled={transcribing || !transcript}
              whileHover={!transcribing && transcript ? { scale: 1.05 } : {}}
              whileTap={!transcribing && transcript ? { scale: 0.95 } : {}}
            >
              {transcribing ? 'Processing...' : '✅ Submit Answer'}
            </motion.button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default AudioRecorder;