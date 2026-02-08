/**
 * Voice Service - Text-to-Speech for Interview Questions
 * Uses browser's built-in Web Speech API (SpeechSynthesis)
 */

class VoiceService {
  constructor() {
    this.synthesis = window.speechSynthesis;
    this.currentUtterance = null;
    this.enabled = true;
    this.rate = 1.0; // Speed (0.1 to 10)
    this.pitch = 1.0; // Pitch (0 to 2)
    this.volume = 0.8; // Volume (0 to 1)
    this.selectedVoice = null;
    
    // Wait for voices to load
    this.loadVoices();
  }

  // Load available voices
  loadVoices() {
    return new Promise((resolve) => {
      const voices = this.synthesis.getVoices();
      
      if (voices.length > 0) {
        this.selectDefaultVoice(voices);
        resolve(voices);
      } else {
        // Voices load asynchronously in some browsers
        this.synthesis.onvoiceschanged = () => {
          const voices = this.synthesis.getVoices();
          this.selectDefaultVoice(voices);
          resolve(voices);
        };
      }
    });
  }

  // Select a good default voice (prefer Google or Microsoft voices)
  selectDefaultVoice(voices) {
    // Priority order for voice selection
    const preferences = [
      'Google US English',
      'Microsoft David',
      'Google UK English Female',
      'Microsoft Zira',
      'Alex', // macOS
    ];

    // Try to find preferred voice
    for (let pref of preferences) {
      const voice = voices.find(v => v.name.includes(pref));
      if (voice) {
        this.selectedVoice = voice;
        console.log('🎤 Selected voice:', voice.name);
        return;
      }
    }

    // Fallback: First English voice
    const englishVoice = voices.find(v => v.lang.startsWith('en'));
    if (englishVoice) {
      this.selectedVoice = englishVoice;
      console.log('🎤 Selected voice:', englishVoice.name);
    } else if (voices.length > 0) {
      this.selectedVoice = voices[0];
      console.log('🎤 Selected default voice:', voices[0].name);
    }
  }

  // Get all available English voices
  getEnglishVoices() {
    const voices = this.synthesis.getVoices();
    return voices.filter(v => v.lang.startsWith('en'));
  }

  // Speak text
  speak(text, options = {}) {
    if (!this.enabled) {
      console.log('🔇 Voice disabled');
      return Promise.resolve();
    }

    if (!this.synthesis) {
      console.warn('🔇 Speech synthesis not supported');
      return Promise.resolve();
    }

    // Stop any current speech
    this.stop();

    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Apply settings
      utterance.voice = this.selectedVoice;
      utterance.rate = options.rate || this.rate;
      utterance.pitch = options.pitch || this.pitch;
      utterance.volume = options.volume || this.volume;

      // Event handlers
      utterance.onend = () => {
        console.log('🎤 Finished speaking');
        this.currentUtterance = null;
        resolve();
      };

      utterance.onerror = (event) => {
        console.error('🎤 Speech error:', event);
        this.currentUtterance = null;
        reject(event);
      };

      utterance.onstart = () => {
        console.log('🎤 Started speaking:', text.substring(0, 50) + '...');
      };

      // Store current utterance
      this.currentUtterance = utterance;

      // Speak
      this.synthesis.speak(utterance);
    });
  }

  // Stop speaking
  stop() {
    if (this.synthesis && this.synthesis.speaking) {
      this.synthesis.cancel();
      this.currentUtterance = null;
      console.log('🎤 Speech stopped');
    }
  }

  // Pause speaking
  pause() {
    if (this.synthesis && this.synthesis.speaking) {
      this.synthesis.pause();
      console.log('🎤 Speech paused');
    }
  }

  // Resume speaking
  resume() {
    if (this.synthesis && this.synthesis.paused) {
      this.synthesis.resume();
      console.log('🎤 Speech resumed');
    }
  }

  // Check if currently speaking
  isSpeaking() {
    return this.synthesis && this.synthesis.speaking;
  }

  // Enable/disable voice
  setEnabled(enabled) {
    this.enabled = enabled;
    if (!enabled) {
      this.stop();
    }
    console.log(`🎤 Voice ${enabled ? 'enabled' : 'disabled'}`);
  }

  // Change voice
  setVoice(voiceName) {
    const voices = this.synthesis.getVoices();
    const voice = voices.find(v => v.name === voiceName);
    
    if (voice) {
      this.selectedVoice = voice;
      console.log('🎤 Voice changed to:', voice.name);
      return true;
    }
    
    console.warn('🎤 Voice not found:', voiceName);
    return false;
  }

  // Set speaking rate
  setRate(rate) {
    this.rate = Math.max(0.1, Math.min(10, rate));
    console.log('🎤 Speech rate:', this.rate);
  }

  // Set pitch
  setPitch(pitch) {
    this.pitch = Math.max(0, Math.min(2, pitch));
    console.log('🎤 Speech pitch:', this.pitch);
  }

  // Set volume
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    console.log('🎤 Speech volume:', this.volume);
  }
}

// Create singleton instance
const voiceService = new VoiceService();

export default voiceService;