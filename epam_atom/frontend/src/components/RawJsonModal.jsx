import React, { useState, useEffect } from 'react';

export default function RawJsonModal({
  isOpen,
  onClose,
  data,
  title = 'Canonical JSON Schema Object (MongoDB Format)',
  isLoading = false,
  error = null,
}) {
  const [copied, setCopied] = useState(false);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const jsonString = data ? JSON.stringify(data, null, 2) : '';

  const handleCopy = () => {
    if (!jsonString) return;
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', minWidth: 0 }}>
            <span style={{ fontSize: '1.25rem', flexShrink: 0 }}>📦</span>
            <h3
              style={{
                fontSize: '1.05rem',
                fontFamily: 'var(--font-heading)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                color: '#171747',
              }}
              title={title}
            >
              {title}
            </h3>
          </div>
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexShrink: 0 }}>
            {data && !isLoading && (
              <button
                type="button"
                className="btn-copy"
                onClick={handleCopy}
                title="Copy formatted JSON to clipboard"
              >
                {copied ? '✓ Copied' : '📋 Copy JSON'}
              </button>
            )}
            <button
              type="button"
              className="btn-close"
              onClick={onClose}
              title="Close viewer (Esc)"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="modal-body">
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '3.5rem 1rem', color: '#6b7280' }}>
              <div
                className="spinner"
                style={{
                  margin: '0 auto 1.2rem',
                  borderColor: 'rgba(99, 102, 241, 0.2)',
                  borderTopColor: '#6366f1',
                  width: '28px',
                  height: '28px',
                }}
              ></div>
              <p style={{ fontSize: '0.95rem', fontWeight: 500 }}>
                Loading resume JSON from database...
              </p>
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: '#ef4444' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.8rem' }}>⚠️</div>
              <p style={{ fontSize: '0.95rem', fontWeight: 600 }}>{error}</p>
            </div>
          ) : data ? (
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {jsonString}
            </pre>
          ) : (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: '#9ca3af' }}>
              No JSON data available for this record.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

