import React from 'react';

export default function StatusAlert({ type = 'info', message, onClose }) {
  if (!message) return null;

  const iconMap = {
    error: '⚠️',
    success: '✅',
    warning: '⚡',
    info: 'ℹ️',
  };

  return (
    <div className={`alert-banner alert-${type}`}>
      <span style={{ fontSize: '1.2rem' }}>{iconMap[type] || 'ℹ️'}</span>
      <div style={{ flex: 1 }}>{message}</div>
      {onClose && (
        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: '1rem' }}
        >
          ✕
        </button>
      )}
    </div>
  );
}
