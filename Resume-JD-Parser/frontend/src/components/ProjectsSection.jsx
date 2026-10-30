import React from 'react';

export default function ProjectsSection({ projects }) {
  const items = projects || [];

  return (
    <div className="result-card">
      <div className="card-header">
        <h3 className="card-title">
          <span>🚀</span> Projects ({items.length})
        </h3>
        <span className="method-tag ai">AI Extracted (OpenAI)</span>
      </div>

      {items.length === 0 ? (
        <p className="badge-missing">No projects detected in the resume.</p>
      ) : (
        <div className="items-list">
          {items.map((proj, idx) => (
            <div key={idx} className="item-box">
              <div className="item-header">
                <span className="item-title">{proj.title || 'Untitled Project'}</span>
                {proj.role ? (
                  <span className="badge-pill" style={{ borderColor: 'rgba(168, 85, 247, 0.4)', color: '#c084fc', fontSize: '0.8rem' }}>
                    {proj.role}
                  </span>
                ) : (
                  <span className="badge-missing">Role: Not specified</span>
                )}
              </div>

              {proj.description && (
                <div className="item-description">{proj.description}</div>
              )}

              {(proj.technologies || proj.technical_skills) && (proj.technologies || proj.technical_skills).length > 0 && (
                <div style={{ marginTop: '0.8rem', display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                  {(proj.technologies || proj.technical_skills).map((tech, tIdx) => (
                    <span
                      key={tIdx}
                      className="badge-pill"
                      style={{ fontSize: '0.78rem', background: 'rgba(99, 102, 241, 0.1)', borderColor: 'rgba(99, 102, 241, 0.25)', color: '#a5b4fc' }}
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
