import React from 'react';

export default function UploadedResumesSection({
  resumes = [],
  isLoading = false,
  loadingDocId = null,
  onRefresh,
  onViewJson,
  onDelete,
}) {
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const getStatusStyle = (status) => {
    const s = (status || 'COMPLETED').toUpperCase();
    if (s === 'COMPLETED') return {
      background: '#22c55e',
      color: '#fff',
      border: 'none',
      padding: '0.25rem 0.75rem',
      borderRadius: '9999px',
      fontSize: '0.78rem',
      fontWeight: 700,
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.3rem',
      whiteSpace: 'nowrap',
    };
    if (s === 'IN_PROGRESS' || s === 'PROCESSING') return {
      background: '#f59e0b',
      color: '#fff',
      border: 'none',
      padding: '0.25rem 0.75rem',
      borderRadius: '9999px',
      fontSize: '0.78rem',
      fontWeight: 700,
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.3rem',
      whiteSpace: 'nowrap',
    };
    return {
      background: '#ef4444',
      color: '#fff',
      border: 'none',
      padding: '0.25rem 0.75rem',
      borderRadius: '9999px',
      fontSize: '0.78rem',
      fontWeight: 700,
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.3rem',
      whiteSpace: 'nowrap',
    };
  };

  return (
    <div style={{
      background: 'rgba(255,255,255,0.88)',
      backdropFilter: 'blur(12px)',
      border: '1px solid #e8e4f3',
      borderRadius: '14px',
      padding: '1.6rem 1.8rem',
      boxShadow: '0 4px 20px rgba(120,100,180,0.08)',
      marginTop: '2rem',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.2rem', flexWrap: 'wrap', gap: '0.8rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.7rem' }}>
          <h3 style={{
            fontFamily: 'Outfit, sans-serif',
            fontSize: '1.2rem',
            fontWeight: 700,
            color: '#1a1a3a',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}>
            📁 Uploaded Resumes
          </h3>
          <span style={{
            background: '#4ade80',
            color: '#fff',
            borderRadius: '9999px',
            padding: '0.15rem 0.65rem',
            fontSize: '0.78rem',
            fontWeight: 700,
          }}>
            {resumes.length} {resumes.length === 1 ? 'record' : 'records'}
          </span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh list"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: '#f1f0f7',
            color: '#6b7280',
            border: '1px solid #ddd8f0',
            padding: '0.4rem 1rem',
            borderRadius: '9999px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: '0.88rem',
            fontWeight: 500,
            opacity: isLoading ? 0.6 : 1,
            transition: 'background 0.2s',
          }}
        >
          <span>🔄</span>
          <span>{isLoading ? 'Refreshing...' : 'Refresh History'}</span>
        </button>
      </div>

      {/* Body */}
      {isLoading && resumes.length === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
          <p>Loading uploaded resume history...</p>
        </div>
      ) : resumes.length === 0 ? (
        <div style={{ padding: '2.5rem 1.5rem', textAlign: 'center', color: '#9ca3af' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.8rem' }}>📄</div>
          <h4 style={{ color: '#6b7280', marginBottom: '0.4rem', fontSize: '1.05rem' }}>
            No Uploaded Resumes Found
          </h4>
          <p style={{ fontSize: '0.9rem' }}>
            Upload a resume above to create your first record.
          </p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr>
                <th style={{ background: '#f4bd58', color: '#3d2a00', padding: '0.75rem 1rem', fontWeight: 700, textAlign: 'left', borderRadius: '6px 0 0 6px' }}>File &amp; Candidate</th>
                <th style={{ background: '#f4bd58', color: '#3d2a00', padding: '0.75rem 1rem', fontWeight: 700, textAlign: 'left' }}>Uploaded At</th>
                <th style={{ background: '#f4bd58', color: '#3d2a00', padding: '0.75rem 1rem', fontWeight: 700, textAlign: 'left' }}>Status</th>
                <th style={{ background: '#f4bd58', color: '#3d2a00', padding: '0.75rem 1rem', fontWeight: 700, textAlign: 'left' }}>Record ID</th>
                <th style={{ background: '#f4bd58', color: '#3d2a00', padding: '0.75rem 1rem', fontWeight: 700, textAlign: 'right', borderRadius: '0 6px 6px 0' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {resumes.map((item, idx) => (
                <tr
                  key={item.id}
                  style={{
                    background: idx % 2 === 0 ? '#fafafa' : '#ffffff',
                    borderBottom: '1px solid #f0ecfa',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = '#f3f0fc'}
                  onMouseLeave={e => e.currentTarget.style.background = idx % 2 === 0 ? '#fafafa' : '#ffffff'}
                >
                  {/* File & Candidate */}
                  <td style={{ padding: '0.85rem 1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.7rem' }}>
                      <span style={{ fontSize: '1.3rem' }}>
                        {item.filename?.toLowerCase().endsWith('.docx') ? '📝' : '📄'}
                      </span>
                      <div>
                        <div style={{ fontWeight: 600, color: '#1a1a3a', fontSize: '0.92rem' }}>
                          {item.candidate_name || (
                            <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>Name Not Extracted</span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: '#9ca3af', marginTop: '0.1rem' }}>
                          {item.filename}
                          {item.candidate_email && (
                            <span style={{ marginLeft: '0.5rem' }}>• {item.candidate_email}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Uploaded At */}
                  <td style={{ padding: '0.85rem 1rem', color: '#6b7280', whiteSpace: 'nowrap', fontSize: '0.88rem' }}>
                    {formatDate(item.created_at)}
                  </td>

                  {/* Status */}
                  <td style={{ padding: '0.85rem 1rem' }}>
                    <span style={getStatusStyle(item.status)}>
                      ● {(item.status || 'COMPLETED').toUpperCase()}
                    </span>
                  </td>

                  {/* Record ID */}
                  <td style={{ padding: '0.85rem 1rem' }}>
                    <code style={{
                      color: '#6b7280',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: '0.8rem',
                      background: '#f0ecfa',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '6px',
                    }}>
                      {item.id ? `${item.id.slice(0, 8)}...` : 'N/A'}
                    </code>
                  </td>

                  {/* Actions */}
                  <td style={{ padding: '0.85rem 1rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'inline-flex', gap: '0.5rem', alignItems: 'center' }}>
                      <button
                        type="button"
                        id={`btn-view-history-json-${item.id}`}
                        onClick={() => onViewJson && onViewJson(item.id)}
                        disabled={loadingDocId === item.id}
                        title="View parsed canonical JSON"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          background: '#3b82f6',
                          color: '#fff',
                          border: 'none',
                          padding: '0.35rem 0.85rem',
                          borderRadius: '9999px',
                          cursor: loadingDocId === item.id ? 'wait' : 'pointer',
                          fontSize: '0.82rem',
                          fontWeight: 600,
                          opacity: loadingDocId === item.id ? 0.75 : 1,
                          transition: 'background 0.2s',
                        }}
                        onMouseEnter={e => e.currentTarget.style.background = '#2563eb'}
                        onMouseLeave={e => e.currentTarget.style.background = '#3b82f6'}
                      >
                        <span>🔍</span>
                        <span>{loadingDocId === item.id ? 'Loading...' : 'View JSON'}</span>
                      </button>

                      <button
                        onClick={() => onDelete && onDelete(item.id)}
                        title="Remove from records"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: '#ef4444',
                          color: '#fff',
                          border: 'none',
                          width: '32px',
                          height: '32px',
                          borderRadius: '50%',
                          cursor: 'pointer',
                          fontSize: '0.9rem',
                          transition: 'background 0.2s',
                        }}
                        onMouseEnter={e => e.currentTarget.style.background = '#dc2626'}
                        onMouseLeave={e => e.currentTarget.style.background = '#ef4444'}
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
