import React from 'react';

export default function EducationSection({ education }) {
  const items = education || [];

  return (
    <div className="result-card">
      <div className="card-header">
        <h3 className="card-title">
          <span>🎓</span> Education & Academics
        </h3>
        <span className="method-tag deterministic">Deterministic (Python)</span>
      </div>

      {items.length === 0 ? (
        <p className="badge-missing">No educational qualifications detected.</p>
      ) : (
        <div className="items-list">
          {items.map((edu, idx) => (
            <div key={idx} className="item-box">
              <div className="item-header">
                <span className="item-title">{edu.degree || 'Degree Not Specified'}</span>
                {(edu.start_year || edu.end_year) && (
                  <span className="item-date">
                    {edu.start_year ? `${edu.start_year} - ` : ''}
                    {edu.end_year || 'Ongoing'}
                  </span>
                )}
              </div>

              <div className="item-subtitle">
                {edu.institution || <span className="badge-missing">Institution Not Specified</span>}
                {edu.specialization && ` • ${edu.specialization}`}
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.6rem', flexWrap: 'wrap' }}>
                {edu.cgpa && (
                  <span className="badge-pill" style={{ borderColor: 'rgba(16, 185, 129, 0.4)', color: '#34d399' }}>
                    📊 CGPA: {edu.cgpa}{edu.cgpa_scale ? ` / ${edu.cgpa_scale}` : ''}
                  </span>
                )}
                {edu.percentage && (
                  <span className="badge-pill" style={{ borderColor: 'rgba(56, 189, 248, 0.4)', color: '#38bdf8' }}>
                    📈 Percentage: {edu.percentage}
                  </span>
                )}
                {!edu.cgpa && !edu.percentage && (
                  <span className="badge-missing">Score/Grade not specified</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
