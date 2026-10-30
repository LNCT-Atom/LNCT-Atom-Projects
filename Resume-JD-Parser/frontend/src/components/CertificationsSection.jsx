import React from 'react';

export default function CertificationsSection({ certifications }) {
  const items = certifications || [];

  return (
    <div className="result-card">
      <div className="card-header">
        <h3 className="card-title">
          <span>📜</span> Certifications & Licenses ({items.length})
        </h3>
        <span className="method-tag deterministic">Deterministic (Python)</span>
      </div>

      {items.length === 0 ? (
        <p className="badge-missing">No certifications detected.</p>
      ) : (
        <div className="items-list">
          {items.map((cert, idx) => (
            <div key={idx} className="item-box">
              <div className="item-header">
                <span className="item-title">{cert.name || 'Certificate'}</span>
                {cert.issue_date && <span className="item-date">{cert.issue_date}</span>}
              </div>

              <div className="item-subtitle">
                {cert.issuer || <span className="badge-missing">Issuer Not Specified</span>}
                {cert.credential_id && ` • ID: ${cert.credential_id}`}
              </div>

              {cert.credential_url && (
                <div style={{ marginTop: '0.4rem' }}>
                  <a
                    href={cert.credential_url.startsWith('http') ? cert.credential_url : `https://${cert.credential_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', textDecoration: 'none' }}
                  >
                    View Credential ↗
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
