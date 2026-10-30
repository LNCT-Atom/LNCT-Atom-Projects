import React from 'react';

export default function ExperienceSection({ experience }) {
  const items = experience || [];

  const getExperienceTypeBadge = (type) => {
    switch (type) {
      case 'internship':
        return { label: 'Internship', color: '#10b981', border: 'rgba(16, 185, 129, 0.4)' };
      case 'full_time':
        return { label: 'Full Time', color: '#6366f1', border: 'rgba(99, 102, 241, 0.4)' };
      case 'part_time':
        return { label: 'Part Time', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.4)' };
      default:
        return { label: type || 'Experience', color: '#94a3b8', border: 'rgba(148, 163, 184, 0.3)' };
    }
  };

  return (
    <div className="result-card">
      <div className="card-header">
        <h3 className="card-title">
          <span>💼</span> Work & Internship Experience ({items.length})
        </h3>
        <span className="method-tag ai">AI Extracted (OpenAI)</span>
      </div>

      {items.length === 0 ? (
        <p className="badge-missing">No work or internship experience detected.</p>
      ) : (
        <div className="items-list">
          {items.map((exp, idx) => {
            const expBadge = getExperienceTypeBadge(exp.experience_type);
            return (
              <div key={idx} className="item-box">
                <div className="item-header">
                  <div>
                    <span className="item-title">{exp.role || 'Role Not Specified'}</span>
                    <span
                      className="badge-pill"
                      style={{
                        marginLeft: '0.8rem',
                        fontSize: '0.75rem',
                        color: expBadge.color,
                        borderColor: expBadge.border,
                      }}
                    >
                      {expBadge.label}
                    </span>
                  </div>
                  {(exp.start_date || exp.end_date) && (
                    <span className="item-date">
                      {exp.start_date || ''} {exp.start_date && exp.end_date ? '–' : ''} {exp.end_date || 'Present'}
                    </span>
                  )}
                </div>

                <div className="item-subtitle">
                  {exp.company || <span className="badge-missing">Company Not Specified</span>}
                </div>

                {exp.description && (
                  <div className="item-description">{exp.description}</div>
                )}

                {(exp.technologies || exp.technical_skills) && (exp.technologies || exp.technical_skills).length > 0 && (
                  <div style={{ marginTop: '0.8rem', display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                    {(exp.technologies || exp.technical_skills).map((tech, tIdx) => (
                      <span
                        key={tIdx}
                        className="badge-pill"
                        style={{ fontSize: '0.78rem', background: 'rgba(14, 165, 233, 0.1)', borderColor: 'rgba(14, 165, 233, 0.25)', color: '#38bdf8' }}
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
