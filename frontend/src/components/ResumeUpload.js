import React, { useState } from 'react';
import './ResumeUpload.css';

const ResumeUpload = ({ onResumeUploaded, onSkip }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain'
    ];

    if (!validTypes.includes(selectedFile.type)) {
      setError('Please upload a PDF, DOC, DOCX, or TXT file');
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) { // 5MB limit
      setError('File size must be less than 5MB');
      return;
    }

    setFile(selectedFile);
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('resume', file);

    try {
      const response = await fetch('http://localhost:8000/upload-resume', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        onResumeUploaded(data);
      } else {
        setError(data.error || 'Failed to upload resume');
      }
    } catch (err) {
      setError('Error uploading resume. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="resume-upload-container">
      <div className="resume-upload-card">
        <h2>📄 Upload Your Resume</h2>
        <p className="subtitle">Help me personalize your interview experience</p>

        <div
          className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="resume-input"
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          
          {!file ? (
            <div className="upload-label">
                <div className="upload-icon">📎</div>
                <p>Drag & drop your resume here</p>
                <p className="or-text">or</p>
                <label htmlFor="resume-input">
                    <span className="browse-btn">
                    Browse Files
                    </span>
                </label>
                <p className="file-types">Supports PDF, DOC, DOCX, TXT (Max 5MB)</p>
            </div>
          ) : (
            <div className="file-selected">
              <div className="file-icon">✓</div>
              <p className="file-name">{file.name}</p>
              <p className="file-size">
                {(file.size / 1024).toFixed(2)} KB
              </p>
              <button
                type="button"
                className="change-file-btn"
                onClick={() => setFile(null)}
              >
                Change File
              </button>
            </div>
          )}
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="action-buttons">
          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Uploading...' : 'Continue with Resume'}
          </button>
          
          <button className="skip-btn" onClick={onSkip}>
            Skip for Now
          </button>
        </div>

        <div className="info-section">
          <p className="info-text">
            💡 <strong>Why upload?</strong> I'll ask questions tailored to your experience,
            making this interview more relevant and realistic.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResumeUpload;