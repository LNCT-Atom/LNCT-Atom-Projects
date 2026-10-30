import React from 'react';

export default function SkillsSection({ technicalSkills }) {
  const skills = technicalSkills || {};
  const technologies = Array.isArray(skills.technologies) ? skills.technologies : [];

  // Fallback to older categorized fields if technologies is not present
  const legacySkills = [
    ...(skills.programming_languages || []),
    ...(skills.frameworks || []),
    ...(skills.databases || []),
    ...(skills.tools || []),
    ...(skills.other_skills || []),
  ];

  const allTechs = technologies.length > 0 ? technologies : legacySkills;

  return (
    <div className="result-card">
      <div className="card-header">
        <h3 className="card-title">
          <span>⚙️</span> Technical Skills ({allTechs.length})
        </h3>
        <span className="method-tag deterministic">Deterministic (Python)</span>
      </div>

      {allTechs.length === 0 ? (
        <p className="badge-missing">No technical skills detected in the skills section.</p>
      ) : (
        <div style={{ marginTop: '0.8rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {allTechs.map((tech, idx) => (
            <span
              key={idx}
              className="badge-pill"
              style={{
                borderColor: 'rgba(99, 102, 241, 0.35)',
                color: '#6366f1',
                background: 'rgba(99, 102, 241, 0.08)',
                fontWeight: 600,
                fontSize: '0.85rem',
                padding: '0.35rem 0.75rem',
              }}
            >
              {tech}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
