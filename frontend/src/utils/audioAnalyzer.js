/**
 * Real-Time Audio Analyzer
 * Analyzes audio patterns during recording to detect interruption triggers
 * WITHOUT needing transcript (works with current Whisper setup)
 */

class AudioAnalyzer {
  constructor() {
    this.audioContext = null;
    this.analyser = null;
    this.dataArray = null;
    this.bufferLength = null;
    
    // State tracking
    this.isAnalyzing = false;
    this.recordingStartTime = null;
    this.lastSoundTime = null;
    this.currentPauseDuration = 0;
    this.totalPauseDuration = 0;
    this.pauseCount = 0;
    this.longPauseCount = 0;
    this.excessivePauseCount = 0;
    this.soundSegments = [];
    this.volumeHistory = [];
    
    // Thresholds
    this.SILENCE_THRESHOLD = 0.01;
    this.LONG_PAUSE_THRESHOLD = 2000;
    this.EXCESSIVE_PAUSE_THRESHOLD = 3000;
    this.MIN_SOUND_DURATION = 200;
    
    // Analysis interval
    this.analysisInterval = null;
    this.ANALYSIS_RATE = 100;
  }

  async initialize(stream) {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      this.bufferLength = this.analyser.frequencyBinCount;
      this.dataArray = new Uint8Array(this.bufferLength);
      
      const source = this.audioContext.createMediaStreamSource(stream);
      source.connect(this.analyser);
      
      console.log('✅ Audio analyzer initialized');
      return true;
    } catch (error) {
      console.error('❌ Failed to initialize audio analyzer:', error);
      return false;
    }
  }

  start() {
    this.isAnalyzing = true;
    this.recordingStartTime = Date.now();
    this.lastSoundTime = Date.now();
    this.reset();
    
    this.analysisInterval = setInterval(() => {
      this.analyze();
    }, this.ANALYSIS_RATE);
    
    console.log('🎤 Audio analysis started');
  }

  stop() {
    this.isAnalyzing = false;
    if (this.analysisInterval) {
      clearInterval(this.analysisInterval);
      this.analysisInterval = null;
    }
    console.log('⏹️ Audio analysis stopped');
  }

  reset() {
    this.currentPauseDuration = 0;
    this.totalPauseDuration = 0;
    this.pauseCount = 0;
    this.longPauseCount = 0;
    this.excessivePauseCount = 0;
    this.soundSegments = [];
    this.volumeHistory = [];
  }

  analyze() {
    if (!this.isAnalyzing || !this.analyser) return;

    this.analyser.getByteTimeDomainData(this.dataArray);
    
    let sum = 0;
    for (let i = 0; i < this.bufferLength; i++) {
      const normalized = (this.dataArray[i] - 128) / 128;
      sum += normalized * normalized;
    }
    const rms = Math.sqrt(sum / this.bufferLength);
    
    this.volumeHistory.push(rms);
    if (this.volumeHistory.length > 50) {
      this.volumeHistory.shift();
    }
    
    const now = Date.now();
    const isSilence = rms < this.SILENCE_THRESHOLD;
    
    if (isSilence) {
      this.currentPauseDuration = now - this.lastSoundTime;
      
      if (this.currentPauseDuration > this.EXCESSIVE_PAUSE_THRESHOLD) {
        const wasExcessivePause = (now - this.EXCESSIVE_PAUSE_THRESHOLD) <= (this.lastSoundTime + this.EXCESSIVE_PAUSE_THRESHOLD);
        if (!wasExcessivePause) {
          this.excessivePauseCount++;
          console.log(`🚨 Excessive pause: ${(this.currentPauseDuration / 1000).toFixed(1)}s`);
        }
      }
      else if (this.currentPauseDuration > this.LONG_PAUSE_THRESHOLD) {
        const wasLongPause = (now - this.LONG_PAUSE_THRESHOLD) <= (this.lastSoundTime + this.LONG_PAUSE_THRESHOLD);
        if (!wasLongPause) {
          this.longPauseCount++;
          console.log(`⏸️ Long pause: ${(this.currentPauseDuration / 1000).toFixed(1)}s`);
        }
      }
    } else {
      if (this.currentPauseDuration > this.MIN_SOUND_DURATION) {
        this.totalPauseDuration += this.currentPauseDuration;
        this.pauseCount++;
        
        this.soundSegments.push({
          startTime: this.lastSoundTime,
          endTime: now,
          pauseDuration: this.currentPauseDuration
        });
      }
      
      this.lastSoundTime = now;
      this.currentPauseDuration = 0;
    }
  }

  getRecordingDuration() {
    if (!this.recordingStartTime) return 0;
    return (Date.now() - this.recordingStartTime) / 1000;
  }

  getAverageVolume() {
    if (this.volumeHistory.length === 0) return 0;
    const sum = this.volumeHistory.reduce((a, b) => a + b, 0);
    return sum / this.volumeHistory.length;
  }

  getVolumeVariance() {
    if (this.volumeHistory.length < 2) return 0;
    const avg = this.getAverageVolume();
    const squaredDiffs = this.volumeHistory.map(v => Math.pow(v - avg, 2));
    return squaredDiffs.reduce((a, b) => a + b, 0) / this.volumeHistory.length;
  }

  getSpeechRate() {
    const durationMinutes = this.getRecordingDuration() / 60;
    if (durationMinutes === 0) return 0;
    return this.soundSegments.length / durationMinutes;
  }

  getPauseRatio() {
    const totalTime = this.getRecordingDuration() * 1000;
    if (totalTime === 0) return 0;
    return this.totalPauseDuration / totalTime;
  }

  detectStruggling() {
    const duration = this.getRecordingDuration();
    
    if (duration < 5) return null;

    const issues = [];
    
    if (this.excessivePauseCount >= 3) {
      issues.push({
        type: 'EXCESSIVE_PAUSING',
        severity: 'critical',
        evidence: `${this.excessivePauseCount} pauses over 3 seconds`,
        priority: 3
      });
    }
    
    const pauseRatio = this.getPauseRatio();
    if (pauseRatio > 0.4) {
      issues.push({
        type: 'HIGH_HESITATION',
        severity: 'high',
        evidence: `${(pauseRatio * 100).toFixed(0)}% of time spent pausing`,
        priority: 5
      });
    }
    
    const avgVolume = this.getAverageVolume();
    if (avgVolume < 0.05 && duration > 10) {
      issues.push({
        type: 'LOW_CONFIDENCE',
        severity: 'medium',
        evidence: 'Speaking very quietly/uncertainly',
        priority: 9
      });
    }
    
    const volumeVariance = this.getVolumeVariance();
    if (volumeVariance > 0.01) {
      issues.push({
        type: 'INCONSISTENT_DELIVERY',
        severity: 'low',
        evidence: 'Very uneven speaking volume',
        priority: 10
      });
    }
    
    if (duration > 90) {
      issues.push({
        type: 'SPEAKING_TOO_LONG',
        severity: 'medium',
        evidence: `Speaking for ${duration.toFixed(0)} seconds`,
        priority: 10
      });
    }

    return issues.length > 0 ? issues : null;
  }

  getAnalysisReport() {
    return {
      recording_duration: this.getRecordingDuration(),
      pause_count: this.pauseCount,
      long_pause_count: this.longPauseCount,
      excessive_pause_count: this.excessivePauseCount,
      total_pause_duration: this.totalPauseDuration / 1000,
      pause_ratio: this.getPauseRatio(),
      average_volume: this.getAverageVolume(),
      volume_variance: this.getVolumeVariance(),
      speech_segments: this.soundSegments.length,
      speech_rate: this.getSpeechRate(),
      detected_issues: this.detectStruggling()
    };
  }

  cleanup() {
    this.stop();
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}

export default AudioAnalyzer;