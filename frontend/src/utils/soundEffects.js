/**
 * Sound Effects Utility
 * Generates audio feedback using Web Audio API
 * No external audio files needed!
 */

class SoundEffects {
  constructor() {
    this.audioContext = null;
    this.enabled = true;
    this.volume = 0.3; // Default volume (0.0 to 1.0)
    
    // Initialize audio context on user interaction (browsers require this)
    this.initAudioContext();
  }

  initAudioContext() {
    // Audio context must be created after user interaction
    if (!this.audioContext) {
      try {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      } catch (e) {
        console.warn('Web Audio API not supported:', e);
        this.enabled = false;
      }
    }
    
    // Resume context if suspended (browser policy)
    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }
  }

  // Play a frequency for a duration
  playTone(frequency, duration, type = 'sine', volumeMultiplier = 1) {
    if (!this.enabled || !this.audioContext) return;
    
    this.initAudioContext(); // Ensure context is ready
    
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);
    
    oscillator.frequency.value = frequency;
    oscillator.type = type; // 'sine', 'square', 'sawtooth', 'triangle'
    
    gainNode.gain.setValueAtTime(this.volume * volumeMultiplier, this.audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
    
    oscillator.start(this.audioContext.currentTime);
    oscillator.stop(this.audioContext.currentTime + duration);
  }

  // 🔔 Interruption Buzz - Attention-grabbing alert
  playInterruption() {
    if (!this.enabled) return;
    
    // Double beep pattern: high-low
    this.playTone(800, 0.15, 'square', 0.8);
    
    setTimeout(() => {
      this.playTone(600, 0.15, 'square', 0.8);
    }, 150);
    
    console.log('🔊 Sound: Interruption buzz');
  }

  // ✅ Success Chime - Positive feedback
  playSuccess() {
    if (!this.enabled) return;
    
    // Ascending chord: C-E-G
    this.playTone(523.25, 0.15, 'sine', 0.6); // C5
    
    setTimeout(() => {
      this.playTone(659.25, 0.15, 'sine', 0.6); // E5
    }, 80);
    
    setTimeout(() => {
      this.playTone(783.99, 0.3, 'sine', 0.6); // G5
    }, 160);
    
    console.log('🔊 Sound: Success chime');
  }

  // 🎯 Interview Complete - Victory fanfare
  playComplete() {
    if (!this.enabled) return;
    
    // Victory arpeggio: C-E-G-C
    const notes = [
      { freq: 523.25, delay: 0 },    // C5
      { freq: 659.25, delay: 100 },  // E5
      { freq: 783.99, delay: 200 },  // G5
      { freq: 1046.50, delay: 300 }  // C6
    ];
    
    notes.forEach(note => {
      setTimeout(() => {
        this.playTone(note.freq, 0.4, 'sine', 0.7);
      }, note.delay);
    });
    
    console.log('🔊 Sound: Interview complete');
  }

  // ⚡ Notification Ping - Quick alert
  playNotification() {
    if (!this.enabled) return;
    
    // Single high ping
    this.playTone(1000, 0.1, 'sine', 0.5);
    
    console.log('🔊 Sound: Notification ping');
  }

  // 🎤 Recording Start - Confirmation beep
  playRecordingStart() {
    if (!this.enabled) return;
    
    // Ascending beep
    this.playTone(600, 0.1, 'sine', 0.4);
    
    setTimeout(() => {
      this.playTone(800, 0.1, 'sine', 0.4);
    }, 100);
    
    console.log('🔊 Sound: Recording started');
  }

  // 🛑 Recording Stop - Confirmation beep
  playRecordingStop() {
    if (!this.enabled) return;
    
    // Descending beep
    this.playTone(800, 0.1, 'sine', 0.4);
    
    setTimeout(() => {
      this.playTone(600, 0.1, 'sine', 0.4);
    }, 100);
    
    console.log('🔊 Sound: Recording stopped');
  }

  // ⚠️ Warning - Filler word or silence alert
  playWarning() {
    if (!this.enabled) return;
    
    // Low warning tone
    this.playTone(300, 0.2, 'sawtooth', 0.3);
    
    console.log('🔊 Sound: Warning');
  }

  // 🎊 Celebration - Great performance
  playCelebration() {
    if (!this.enabled) return;
    
    // Rapid ascending scale
    const frequencies = [523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50];
    
    frequencies.forEach((freq, index) => {
      setTimeout(() => {
        this.playTone(freq, 0.15, 'sine', 0.5);
      }, index * 60);
    });
    
    console.log('🔊 Sound: Celebration');
  }

  // Enable/disable all sounds
  setEnabled(enabled) {
    this.enabled = enabled;
    console.log(`🔊 Sound effects ${enabled ? 'enabled' : 'disabled'}`);
  }

  // Set volume (0.0 to 1.0)
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    console.log(`🔊 Volume set to ${Math.round(this.volume * 100)}%`);
  }
}

// Create singleton instance
const soundEffects = new SoundEffects();

export default soundEffects;