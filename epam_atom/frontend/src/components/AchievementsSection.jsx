import React from 'react';

export default function AchievementsSection({ achievements }) {
  const items = achievements || [];

  return (
    <div className="result-card">
      <div className="card-header">
        <h3 className="card-title">
          <span>🏆</span> Honors & Achievements ({items.length})
        </h3>
        <span className="method-tag deterministic">Deterministic (Python)</span>
      </div>

      {items.length === 0 ? (
        <p className="badge-missing">No achievements detected.</p>
      ) : (
        <div className="items-list">
          {items.map((ach, idx) => (
            <div key={idx} className="item-box">
              <div className="item-header">
                <span className="item-title">{ach.title || 'Achievement'}</span>
                {ach.date && <span className="item-date">{ach.date}</span>}
              </div>

              {ach.organization && (
                <div className="item-subtitle">Awarded by: {ach.organization}</div>
              )}

              {ach.description && (
                <div className="item-description">{ach.description}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
