import React from 'react';

export default function Header() {
  return (
    <header className="app-header">
      <div className="badge-tag">
        <span>⚡</span> T&P Cell Automated System
      </div>
      <h1 className="main-title">Resume Parser</h1>
      <p className="subtitle">
        Upload your resume in PDF or DOCX format. Predictable sections are parsed with deterministic rules; Projects & Experience are analyzed with AI.
      </p>
    </header>
  );
}
