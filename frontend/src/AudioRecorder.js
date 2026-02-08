import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './AudioRecorder.css';
import soundEffects from './utils/soundEffects';

function AudioRecorder({ onAudioReady, questionId, sessionId, onRecordingStateChange, onInterruption ,currentQuestionText}) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [wasInterrupted, setWasInterrupted] = useState(false);
  
  // PHASE 5: Real-time detection states
  const [realtimeTranscript, setRealtimeTranscript] = useState('');
  const [fillerWarning, setFillerWarning] = useState(null);
  const [silenceWarning, setSilenceWarning] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const recordingStartTime = useRef(null);
  const interruptionCheckInterval = useRef(null);
  
  // PHASE 5: Web Speech API for real-time detection
  const recognitionRef = useRef(null);
  const lastSpeechTime = useRef(null);
  const silenceCheckInterval = useRef(null);

  // PHASE 5: Filler word detection
  const FILLER_WORDS = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'literally', 'kind of', 'sort of'];
  const SILENCE_THRESHOLD = 5000; // 5 seconds of silence (increased from 4)

  // Detect filler words in real-time transcript
  const detectFillers = (text) => {
    const lowerText = text.toLowerCase();
    const words = lowerText.split(' ');
    const recentWords = words.slice(-10); // Check last 10 words
    
    // Count filler words in recent speech
    const fillerCount = recentWords.filter(word => 
      FILLER_WORDS.some(filler => word.includes(filler))
    ).length;
    
    // If 3+ fillers in last 10 words, show warning
    if (fillerCount >= 3) {
      return { type: 'filler', message: 'Avoid filler words' };
    }
    
    // Check for repetition
    const wordCounts = {};
    recentWords.forEach(word => {
      if (word.length > 3) { // Only check meaningful words
        wordCounts[word] = (wordCounts[word] || 0) + 1;
      }
    });
    
    // If any word repeated 3+ times
    for (let word in wordCounts) {
      if (wordCounts[word] >= 3) {
        return { type: 'repetition', message: "You're repeating yourself" };
      }
    }
    
    return null;
  };

  // PHASE 5: Setup Web Speech API for real-time detection
  useEffect(() => {
    if (isRecording) {
      // Check if browser supports Web Speech API
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        console.warn('Web Speech API not supported - filler detection disabled');
        return;
      }
      
      // Initialize speech recognition
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }
        
        // Update real-time transcript
        const fullTranscript = finalTranscript + interimTranscript;
        setRealtimeTranscript(prev => prev + finalTranscript);
        
        // Update last speech time and clear silence warning
        lastSpeechTime.current = Date.now();
        setSilenceWarning(false);
        
        // Check for filler words
        const fillerDetection = detectFillers(fullTranscript);
        if (fillerDetection) {
          setFillerWarning(fillerDetection);

          // PHASE 8: Play warning sound
  soundEffects.playWarning();
          // Clear warning after 2 seconds
          setTimeout(() => setFillerWarning(null), 2000);
        }
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        // Don't try to restart on errors - let onend handle it
      };
      
      recognition.onend = () => {
        // Restart if still recording
        if (isRecording && recognitionRef.current) {
          setTimeout(() => {
            if (isRecording && recognitionRef.current) {
              try {
                recognitionRef.current.start();
              } catch (e) {
                // Already started, ignore
                if (e.name !== 'InvalidStateError') {
                  console.error('Recognition restart error:', e);
                }
              }
            }
          }, 200);
        }
      };
      
      // Start recognition
      try {
        recognition.start();
        recognitionRef.current = recognition;
        lastSpeechTime.current = Date.now();
      } catch (e) {
        console.error('Failed to start speech recognition:', e);
      }
      
      // Check for silence every second
      silenceCheckInterval.current = setInterval(() => {
        if (lastSpeechTime.current && realtimeTranscript.length > 10) {
          // Only check silence if they've actually said something (>10 chars)
          const silenceDuration = Date.now() - lastSpeechTime.current;
          const timeSinceRecordingStart = Date.now() - recordingStartTime.current;
          
          // Only show silence warning if:
          // 1. Been recording for at least 8 seconds
          // 2. Silent for 4+ seconds
          // 3. They've spoken at least 10 characters worth
          if (timeSinceRecordingStart > 8000 && silenceDuration > SILENCE_THRESHOLD) {
            setSilenceWarning(true);
          } else {
            setSilenceWarning(false);
          }
        }
      }, 1000);
      
    } else {
      // Stop speech recognition when not recording
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      if (silenceCheckInterval.current) {
        clearInterval(silenceCheckInterval.current);
      }
      setRealtimeTranscript('');
      setFillerWarning(null);
      setSilenceWarning(false);
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (silenceCheckInterval.current) {
        clearInterval(silenceCheckInterval.current);
      }
    };
  }, [isRecording]);

  // PHASE 5: Check for interruptions during recording
  useEffect(() => {
    if (isRecording) {
      // Check every 2 seconds if interruption should trigger
      interruptionCheckInterval.current = setInterval(async () => {
        const duration = (Date.now() - recordingStartTime.current) / 1000;
        
        // Use real-time transcript for interruption check
        const transcriptForCheck = realtimeTranscript || '';
        
        // Check with backend if interruption should happen
        try {
          const response = await fetch(
          `http://localhost:8000/interview/check-interruption?session_id=${sessionId}&question_id=${questionId}&recording_duration=${duration}&partial_transcript=${encodeURIComponent(transcriptForCheck)}`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              current_question_text: currentQuestionText || ''  // ← ADD THIS
            })
          }
        );
          
          const data = await response.json();
          
          if (data.should_interrupt) {
            console.log('🔥 INTERRUPTION TRIGGERED!', data);
            
            // Mark that interruption happened (but keep recording!)
            setWasInterrupted(true);
            
            // Trigger interruption alert in parent (recording continues!)
            if (onInterruption) {
              onInterruption(data);
            }
            
            // Stop checking for more interruptions (only one per answer)
            if (interruptionCheckInterval.current) {
              clearInterval(interruptionCheckInterval.current);
            }
          }
        } catch (error) {
          console.error('Error checking interruption:', error);
        }
      }, 2000); // Check every 2 seconds
    } else {
      // Clear interval when not recording
      if (interruptionCheckInterval.current) {
        clearInterval(interruptionCheckInterval.current);
      }
    }

    return () => {
      if (interruptionCheckInterval.current) {
        clearInterval(interruptionCheckInterval.current);
      }
    };
  }, [isRecording, sessionId, questionId, onInterruption, realtimeTranscript]);

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
      recordingStartTime.current = Date.now();
      setWasInterrupted(false);

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
        
        // Auto-transcribe with Whisper (final accurate transcript)
        await transcribeAudio(blob);
      };

       mediaRecorder.start();
       setIsRecording(true);
       setRecordingTime(0);
    
    // PHASE 8: Play recording start sound
       soundEffects.playRecordingStart();

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
       soundEffects.playRecordingStop();
      // Clear interruption check interval
      if (interruptionCheckInterval.current) {
        clearInterval(interruptionCheckInterval.current);
      }

      console.log(`Recording stopped. Was interrupted: ${wasInterrupted}`);
    }
  };

  const transcribeAudio = async (blob) => {
    setTranscribing(true);
    
    try {
      const formData = new FormData();
      formData.append('audio_file', blob, 'recording.webm');

      console.log('Transcribing audio with Whisper...');

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
        console.log('Final Whisper transcript:', data.transcript);
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
      language: 'en',
      recording_duration: recordingTime,
      was_interrupted: wasInterrupted
    });
    
    resetRecording();
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    setTranscript('');
    setTranscribing(false);
    setWasInterrupted(false);
    setRealtimeTranscript('');
    setFillerWarning(null);
    setSilenceWarning(false);
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
              
              {/* PHASE 5: Real-time warnings */}
              <AnimatePresence>
                {fillerWarning && (
                  <motion.div
                    className="filler-warning"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    {fillerWarning.type === 'filler' && '⚠️'}
                    {fillerWarning.type === 'repetition' && '🔄'}
                    {' '}{fillerWarning.message}
                  </motion.div>
                )}
                
                {silenceWarning && (
                  <motion.div
                    className="silence-warning"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    ⏸️ Still there?
                  </motion.div>
                )}
              </AnimatePresence>
              
              {/* Show if interrupted (but keep recording!) */}
              {wasInterrupted && (
                <motion.div
                  className="interrupted-badge"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  ⚡ Interrupted - Keep answering the follow-up!
                </motion.div>
              )}
              
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
            {wasInterrupted && <span className="interrupted-label"> - Answered follow-up</span>}
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