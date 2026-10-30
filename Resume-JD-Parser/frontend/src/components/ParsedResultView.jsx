import React, { useState } from 'react';
import RawJsonModal from './RawJsonModal';

export default function ParsedResultView({ result }) {
  const [showJsonModal, setShowJsonModal] = useState(false);

  if (!result || !result.data) return null;

  const { data, status, duplicate } = result;
  const resumeId = result.resume_id || result.document_id || 'N/A';
  const metadata = data.metadata || {};

  return (
    <div className="results-container">
      {/* Top Metadata Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          background: 'rgba(30, 41, 59, 0.4)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem 1.4rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flexWrap: 'wrap' }}>
          <span className="badge-pill" style={{ borderColor: 'rgba(16, 185, 129, 0.4)', color: '#34d399' }}>
            ● Status: {(status || 'COMPLETED').toUpperCase()}
          </span>

          {duplicate && (
            <span className="badge-pill" style={{ borderColor: 'rgba(245, 158, 11, 0.4)', color: '#f59e0b' }}>
              Duplicate Upload Detected
            </span>
          )}

          {metadata.is_scanned_pdf && (
            <span className="badge-pill" style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: '#f87171' }}>
              ⚠️ Scanned PDF Detected
            </span>
          )}

          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Resume ID:{' '}
            <code style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-code)' }}>
              {resumeId}
            </code>
          </span>
        </div>

        <button
          onClick={() => setShowJsonModal(true)}
          className="badge-pill"
          style={{ cursor: 'pointer', background: 'rgba(99, 102, 241, 0.15)', borderColor: 'rgba(99, 102, 241, 0.4)', color: '#a5b4fc' }}
        >
          <span>🔍</span> View Canonical JSON
        </button>
      </div>

      {/* JSON Viewer */}
      <pre style={{ background: 'var(--bg-code)', padding: '1rem', borderRadius: 'var(--radius-md)', overflowX: 'auto' }}>
        {JSON.stringify(data, null, 2)}
      </pre>
      <button
        onClick={() => navigator.clipboard.writeText(JSON.stringify(data, null, 2))}
        style={{ marginTop: '0.5rem', cursor: 'pointer', background: 'rgba(99,102,241,0.15)', borderColor: 'rgba(99,102,241,0.4)', color: '#a5b4fc', padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-sm)' }}
      >
        📋 Copy JSON
      </button>
      {/* Raw JSON Modal */}
      <RawJsonModal
        isOpen={showJsonModal}
        onClose={() => setShowJsonModal(false)}
        data={data}
      />
    </div>
  );
}
