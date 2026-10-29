import React, { useState, useRef } from 'react';

const MAX_SIZE_MB = 10;
const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];

export default function FileUpload({
  onUpload,
  isLoading,
  recentlyProcessedResume,
  onViewRecentJson,
}) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [validationError, setValidationError] = useState('');
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    setValidationError('');
    if (!file) return false;

    const lowerName = file.name.toLowerCase();
    const hasValidExt = ALLOWED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
    if (!hasValidExt) {
      setValidationError('Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx).');
      return false;
    }

    const fileSizeMb = file.size / (1024 * 1024);
    if (fileSizeMb > MAX_SIZE_MB) {
      setValidationError(`File size (${fileSizeMb.toFixed(2)} MB) exceeds the maximum limit of ${MAX_SIZE_MB} MB.`);
      return false;
    }

    if (file.size === 0) {
      setValidationError('The selected file is empty (0 bytes).');
      return false;
    }

    return true;
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    } else if (file) {
      setSelectedFile(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedFile || isLoading) return;
    onUpload(selectedFile);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="upload-card">
      <form onSubmit={handleSubmit}>
        <div
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            disabled={isLoading}
          />
          <div className="dropzone-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <h3 className="dropzone-title">Click to upload or drag and drop</h3>
          <p className="dropzone-desc">Upload your resume in PDF or DOCX format (Max {MAX_SIZE_MB}MB)</p>
        </div>

        {validationError && (
          <div style={{ color: 'var(--error)', fontSize: '0.9rem', marginTop: '0.8rem', textAlign: 'center' }}>
            ⚠️ {validationError}
          </div>
        )}

        {selectedFile && (
          <div className="file-preview">
            <div className="file-info">
              <span style={{ fontSize: '1.4rem' }}>
                {selectedFile.name.endsWith('.pdf') ? '📄' : '📝'}
              </span>
              <div>
                <div className="file-name">{selectedFile.name}</div>
                <div className="file-meta">{formatFileSize(selectedFile.size)}</div>
              </div>
            </div>
            {!isLoading && (
              <button
                type="button"
                className="btn-remove"
                onClick={() => setSelectedFile(null)}
                title="Remove file"
              >
                ✕
              </button>
            )}
          </div>
        )}

        <button
          type="submit"
          className="btn-submit"
          disabled={!selectedFile || isLoading}
        >
          {isLoading ? (
            <>
              <div className="spinner"></div>
              <span>Analyzing & Parsing Resume...</span>
            </>
          ) : (
            <>
              <span>Submit Resume</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </>
          )}
        </button>

        {/* View JSON for recently processed resume */}
        {recentlyProcessedResume && (
          <div
            className="upload-success-action"
            style={{
              marginTop: '1.25rem',
              padding: '1rem 1.25rem',
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.8rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '1.3rem' }}>✅</span>
              <div>
                <div style={{ fontWeight: 600, color: '#166534', fontSize: '0.92rem' }}>
                  Resume Processed Successfully
                </div>
                <div style={{ fontSize: '0.8rem', color: '#15803d', marginTop: '0.1rem' }}>
                  {recentlyProcessedResume.filename || recentlyProcessedResume.data?.metadata?.file_name || 'Processed Resume'}
                  {recentlyProcessedResume.data?.profile?.full_name ? ` • ${recentlyProcessedResume.data.profile.full_name}` : ''}
                </div>
              </div>
            </div>

            <button
              type="button"
              id="btn-upload-view-json"
              onClick={onViewRecentJson}
              title="View the generated canonical JSON for this resume"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                background: '#2563eb',
                color: '#ffffff',
                border: 'none',
                padding: '0.55rem 1.2rem',
                borderRadius: '9999px',
                fontSize: '0.88rem',
                fontWeight: 600,
                cursor: 'pointer',
                boxShadow: '0 2px 6px rgba(37, 99, 235, 0.25)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#1d4ed8')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#2563eb')}
            >
              <span>🔍</span>
              <span>View JSON</span>
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
