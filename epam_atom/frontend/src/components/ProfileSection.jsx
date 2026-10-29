import React from 'react';

export default function ProfileSection({ profile }) {
  if (!profile) return null;

  const renderValue = (val, isLink = false) => {
    if (!val) {
      return <span className="badge-missing">Not Specified</span>;
    }
    if (isLink) {
      const href = val.startsWith('http') ? val : `https://${val}`;
      return (
        <a href={href} target="_blank" rel="noopener noreferrer">
          {val} ↗
        </a>
      );
    }
    return val;
  };

  return (
    <div className="result-card">
      <div className="card-header">
        <h3 className="card-title">
          <span>👤</span> Candidate Profile
        </h3>
        <span className="method-tag deterministic">Deterministic (Python)</span>
      </div>

      <div className="profile-grid">
        <div className="profile-field">
          <div className="profile-label">Full Name</div>
          <div className="profile-val" style={{ fontWeight: 600 }}>
            {renderValue(profile.full_name)}
          </div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Email Address</div>
          <div className="profile-val">{renderValue(profile.email)}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Phone Number</div>
          <div className="profile-val">{renderValue(profile.phone)}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Location</div>
          <div className="profile-val">{renderValue(profile.location)}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">LinkedIn</div>
          <div className="profile-val">{renderValue(profile.linkedin_url, true)}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">GitHub</div>
          <div className="profile-val">{renderValue(profile.github_url, true)}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Portfolio</div>
          <div className="profile-val">{renderValue(profile.portfolio_url, true)}</div>
        </div>
      </div>

      {profile.summary && (
        <div style={{ marginTop: '0.8rem', background: 'rgba(15, 23, 42, 0.4)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
          <div className="profile-label">Career Objective / Summary</div>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)' }}>{profile.summary}</p>
        </div>
      )}
    </div>
  );
}
