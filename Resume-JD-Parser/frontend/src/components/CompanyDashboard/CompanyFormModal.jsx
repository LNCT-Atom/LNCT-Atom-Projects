import React, { useState, useEffect } from 'react';

export default function CompanyFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData = null,
  isLoading = false,
  asPanel = false,
}) {
  const [activeTab, setActiveTab] = useState('company');

  // Form State
  const [companyInfo, setCompanyInfo] = useState({
    name: '',
    email: '',
    website: '',
    location: '',
    job_role: '',
    job_description: '',
    job_type: 'Full-time',
  });

  const [eligibility, setEligibility] = useState({
    minimum_cgpa: '',
    required_degree: 'B.Tech',
    required_branches: 'CSE, IT',
    eligible_graduation_years: '2026, 2027',
    minimum_class_10_percentage: '',
    minimum_class_12_percentage: '',
    backlog_criteria: '',
  });

  const [skills, setSkills] = useState({
    mandatory_technologies: 'Java, Spring Boot',
    preferred_technologies: 'MongoDB, React',
  });

  const [experience, setExperience] = useState({
    minimum_experience_months: '',
    relevant_technologies: '',
    internship_required: false,
  });

  const [projects, setProjects] = useState({
    required_technologies: 'Java, Spring Boot',
    minimum_relevant_projects: '1',
    description_keywords: '',
  });

  const [formError, setFormError] = useState('');

  // Pre-fill if editing
  useEffect(() => {
    if (initialData) {
      const c = initialData.company || {};
      setCompanyInfo({
        name: c.name || '',
        email: c.email || '',
        website: c.website || '',
        location: c.location || '',
        job_role: c.job_role || '',
        job_description: c.job_description || '',
        job_type: c.job_type || 'Full-time',
      });

      const e = initialData.eligibility_criteria || {};
      setEligibility({
        minimum_cgpa: e.minimum_cgpa !== null && e.minimum_cgpa !== undefined ? String(e.minimum_cgpa) : '',
        required_degree: (e.required_degree || []).join(', '),
        required_branches: (e.required_branches || []).join(', '),
        eligible_graduation_years: (e.eligible_graduation_years || []).join(', '),
        minimum_class_10_percentage: e.minimum_class_10_percentage !== null && e.minimum_class_10_percentage !== undefined ? String(e.minimum_class_10_percentage) : '',
        minimum_class_12_percentage: e.minimum_class_12_percentage !== null && e.minimum_class_12_percentage !== undefined ? String(e.minimum_class_12_percentage) : '',
        backlog_criteria: e.backlog_criteria || '',
      });

      const s = initialData.technical_skills || {};
      setSkills({
        mandatory_technologies: (s.mandatory_technologies || []).join(', '),
        preferred_technologies: (s.preferred_technologies || []).join(', '),
      });

      const exp = initialData.experience_criteria || {};
      setExperience({
        minimum_experience_months: exp.minimum_experience_months !== null && exp.minimum_experience_months !== undefined ? String(exp.minimum_experience_months) : '',
        relevant_technologies: (exp.relevant_technologies || []).join(', '),
        internship_required: !!exp.internship_required,
      });

      const p = initialData.project_criteria || {};
      setProjects({
        required_technologies: (p.required_technologies || []).join(', '),
        minimum_relevant_projects: p.minimum_relevant_projects !== null && p.minimum_relevant_projects !== undefined ? String(p.minimum_relevant_projects) : '',
        description_keywords: (p.description_keywords || []).join(', '),
      });
    } else {
      // Defaults for new form
      setCompanyInfo({
        name: '',
        email: '',
        website: '',
        location: '',
        job_role: '',
        job_description: '',
        job_type: 'Full-time',
      });
      setEligibility({
        minimum_cgpa: '7.0',
        required_degree: 'B.Tech',
        required_branches: 'CSE, IT',
        eligible_graduation_years: '2026, 2027',
        minimum_class_10_percentage: '',
        minimum_class_12_percentage: '',
        backlog_criteria: '',
      });
      setSkills({
        mandatory_technologies: 'Java, Spring Boot',
        preferred_technologies: 'MongoDB, React',
      });
      setExperience({
        minimum_experience_months: '',
        relevant_technologies: '',
        internship_required: false,
      });
      setProjects({
        required_technologies: 'Java, Spring Boot',
        minimum_relevant_projects: '1',
        description_keywords: '',
      });
    }
    setActiveTab('company');
    setFormError('');
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const STEP_KEYS = ['company', 'eligibility', 'skills', 'experience', 'projects'];
  const isFirstStep = activeTab === 'company';
  const isFinalStep = activeTab === 'projects';

  const splitComma = (str) => {
    if (!str) return [];
    return str
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  };

  const splitIntYears = (str) => {
    return splitComma(str)
      .map((y) => parseInt(y, 10))
      .filter((n) => !isNaN(n));
  };

  const validateStep = (stepKey) => {
    setFormError('');
    if (stepKey === 'company') {
      if (!companyInfo.name.trim()) {
        setFormError('Company Name is required.');
        return false;
      }
      if (!companyInfo.email.trim()) {
        setFormError('Company Email is required.');
        return false;
      }
      if (!companyInfo.job_role.trim()) {
        setFormError('Job Role / Position is required.');
        return false;
      }
    } else if (stepKey === 'eligibility') {
      if (eligibility.minimum_cgpa) {
        const cgpa = parseFloat(eligibility.minimum_cgpa);
        if (isNaN(cgpa) || cgpa < 0 || cgpa > 10) {
          setFormError('Minimum CGPA must be a valid number between 0 and 10.');
          return false;
        }
      }
      if (eligibility.minimum_class_10_percentage) {
        const p10 = parseFloat(eligibility.minimum_class_10_percentage);
        if (isNaN(p10) || p10 < 0 || p10 > 100) {
          setFormError('Class 10 percentage must be a number between 0 and 100.');
          return false;
        }
      }
      if (eligibility.minimum_class_12_percentage) {
        const p12 = parseFloat(eligibility.minimum_class_12_percentage);
        if (isNaN(p12) || p12 < 0 || p12 > 100) {
          setFormError('Class 12 percentage must be a number between 0 and 100.');
          return false;
        }
      }
    } else if (stepKey === 'experience') {
      if (experience.minimum_experience_months) {
        const exp = parseInt(experience.minimum_experience_months, 10);
        if (isNaN(exp) || exp < 0) {
          setFormError('Minimum experience months must be 0 or greater.');
          return false;
        }
      }
    } else if (stepKey === 'projects') {
      if (projects.minimum_relevant_projects) {
        const proj = parseInt(projects.minimum_relevant_projects, 10);
        if (isNaN(proj) || proj < 0) {
          setFormError('Minimum relevant projects must be 0 or greater.');
          return false;
        }
      }
    }
    return true;
  };

  const handleNext = (e) => {
    if (e) e.preventDefault();
    if (!validateStep(activeTab)) {
      return;
    }
    const currentIndex = STEP_KEYS.indexOf(activeTab);
    if (currentIndex < STEP_KEYS.length - 1) {
      setActiveTab(STEP_KEYS[currentIndex + 1]);
      setFormError('');
    }
  };

  const handlePrevious = (e) => {
    if (e) e.preventDefault();
    const currentIndex = STEP_KEYS.indexOf(activeTab);
    if (currentIndex > 0) {
      setActiveTab(STEP_KEYS[currentIndex - 1]);
      setFormError('');
    }
  };

  const handleTabClick = (targetKey) => {
    const currentIndex = STEP_KEYS.indexOf(activeTab);
    const targetIndex = STEP_KEYS.indexOf(targetKey);

    if (targetIndex <= currentIndex) {
      // Navigating backward is always permitted
      setActiveTab(targetKey);
      setFormError('');
    } else {
      // Navigating forward validates the current step first
      if (validateStep(activeTab)) {
        setActiveTab(targetKey);
        setFormError('');
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormError('');

    // Comprehensive validation across all steps
    if (!companyInfo.name.trim()) {
      setFormError('Company Name is required.');
      setActiveTab('company');
      return;
    }
    if (!companyInfo.email.trim()) {
      setFormError('Company Email is required.');
      setActiveTab('company');
      return;
    }
    if (!companyInfo.job_role.trim()) {
      setFormError('Job Role / Position is required.');
      setActiveTab('company');
      return;
    }

    if (eligibility.minimum_cgpa) {
      const cgpa = parseFloat(eligibility.minimum_cgpa);
      if (isNaN(cgpa) || cgpa < 0 || cgpa > 10) {
        setFormError('Minimum CGPA must be a valid number between 0 and 10.');
        setActiveTab('eligibility');
        return;
      }
    }

    if (experience.minimum_experience_months) {
      const exp = parseInt(experience.minimum_experience_months, 10);
      if (isNaN(exp) || exp < 0) {
        setFormError('Minimum experience months must be 0 or greater.');
        setActiveTab('experience');
        return;
      }
    }

    if (projects.minimum_relevant_projects) {
      const proj = parseInt(projects.minimum_relevant_projects, 10);
      if (isNaN(proj) || proj < 0) {
        setFormError('Minimum relevant projects must be 0 or greater.');
        setActiveTab('projects');
        return;
      }
    }

    const payload = {
      company: {
        name: companyInfo.name.trim(),
        email: companyInfo.email.trim(),
        website: companyInfo.website.trim() || null,
        location: companyInfo.location.trim() || null,
        job_role: companyInfo.job_role.trim(),
        job_description: companyInfo.job_description.trim() || null,
        job_type: companyInfo.job_type || 'Full-time',
      },
      eligibility_criteria: {
        minimum_cgpa: eligibility.minimum_cgpa ? parseFloat(eligibility.minimum_cgpa) : null,
        required_degree: splitComma(eligibility.required_degree),
        required_branches: splitComma(eligibility.required_branches),
        eligible_graduation_years: splitIntYears(eligibility.eligible_graduation_years),
        minimum_class_10_percentage: eligibility.minimum_class_10_percentage ? parseFloat(eligibility.minimum_class_10_percentage) : null,
        minimum_class_12_percentage: eligibility.minimum_class_12_percentage ? parseFloat(eligibility.minimum_class_12_percentage) : null,
        backlog_criteria: eligibility.backlog_criteria.trim() || null,
      },
      technical_skills: {
        mandatory_technologies: splitComma(skills.mandatory_technologies),
        preferred_technologies: splitComma(skills.preferred_technologies),
      },
      experience_criteria: {
        minimum_experience_months: experience.minimum_experience_months ? parseInt(experience.minimum_experience_months, 10) : null,
        relevant_technologies: splitComma(experience.relevant_technologies),
        internship_required: experience.internship_required,
      },
      project_criteria: {
        required_technologies: splitComma(projects.required_technologies),
        minimum_relevant_projects: projects.minimum_relevant_projects ? parseInt(projects.minimum_relevant_projects, 10) : null,
        description_keywords: splitComma(projects.description_keywords),
      },
    };

    onSubmit(payload);
  };

  const tabStyle = (tabKey) => {
    const isActive = activeTab === tabKey;
    const currentIndex = STEP_KEYS.indexOf(activeTab);
    const tabIndex = STEP_KEYS.indexOf(tabKey);
    const isCompleted = tabIndex < currentIndex;

    return {
      padding: '0.55rem 0.85rem',
      borderRadius: '8px',
      cursor: 'pointer',
      fontWeight: isActive ? 700 : 500,
      background: isActive ? '#6366f1' : isCompleted ? '#ede9fe' : '#f3f0fc',
      color: isActive ? '#ffffff' : isCompleted ? '#4f46e5' : '#4b5563',
      border: isActive ? '1px solid #4f46e5' : isCompleted ? '1px solid #c7d2fe' : '1px solid transparent',
      fontSize: '0.84rem',
      whiteSpace: 'nowrap',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.35rem',
      transition: 'all 0.2s ease',
    };
  };

  const inputStyle = {
    width: '100%',
    padding: '0.65rem 0.85rem',
    border: '1px solid #dcd7ee',
    borderRadius: '8px',
    fontSize: '0.9rem',
    background: '#ffffff',
    color: '#1f2937',
    marginTop: '0.35rem',
    outline: 'none',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.84rem',
    fontWeight: 600,
    color: '#374151',
    marginTop: '0.85rem',
  };

  const helpTextStyle = {
    fontSize: '0.75rem',
    color: '#6b7280',
    marginTop: '0.2rem',
  };

  const handleSafeClose = () => {
    const isDirty =
      companyInfo.name ||
      companyInfo.email ||
      companyInfo.job_role ||
      companyInfo.location ||
      companyInfo.job_description;
    if (isDirty && !initialData) {
      if (
        !window.confirm(
          'You have unsaved changes in the recruitment form. Are you sure you want to discard them and close?'
        )
      ) {
        return;
      }
    }
    onClose();
  };

  const formContent = (
    <div
      className={asPanel ? 'company-form-panel' : 'modal-content'}
      onClick={asPanel ? undefined : (e) => e.stopPropagation()}
      style={
        asPanel
          ? {
              background: 'rgba(255, 255, 255, 0.98)',
              backdropFilter: 'blur(16px)',
              border: '1px solid #dcd7ee',
              borderRadius: '16px',
              boxShadow: '0 8px 30px rgba(102, 84, 232, 0.12)',
              display: 'flex',
              flexDirection: 'column',
              maxHeight: 'calc(100vh - 4.5rem)',
              position: 'sticky',
              top: '1.5rem',
              overflow: 'hidden',
              width: '100%',
              zIndex: 10,
            }
          : {
              maxWidth: '780px',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              borderRadius: '16px',
            }
      }
    >
      {/* Modal / Panel Header */}
      <div className="modal-header" style={{ padding: '1.1rem 1.4rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '1.4rem' }}>🏢</span>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#1a1a3a' }}>
              {initialData ? 'Edit Recruitment Requirement' : 'Post Recruitment Requirement'}
            </h3>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#6b7280' }}>
              Configure criteria used by the deterministic Python evaluation engine.
            </p>
          </div>
        </div>
        <button
          type="button"
          className="modal-close-btn"
          onClick={handleSafeClose}
          title="Close form"
          style={{ cursor: 'pointer' }}
        >
          ✕
        </button>
      </div>

        {/* Section Tabs / Wizard Step Navigation */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.5rem',
            padding: '0.65rem 1.4rem',
            background: '#faf8ff',
            borderBottom: '1px solid #e8e4f3',
            overflowX: 'auto',
          }}
        >
          <div style={{ display: 'flex', gap: '0.35rem', overflowX: 'auto', scrollbarWidth: 'thin' }}>
            <button type="button" style={tabStyle('company')} onClick={() => handleTabClick('company')} title="Step A: Company Information">
              <span>{STEP_KEYS.indexOf(activeTab) > 0 ? '✓' : 'A.'}</span>
              <span>Info</span>
            </button>
            <button type="button" style={tabStyle('eligibility')} onClick={() => handleTabClick('eligibility')} title="Step B: Eligibility Criteria">
              <span>{STEP_KEYS.indexOf(activeTab) > 1 ? '✓' : 'B.'}</span>
              <span>Eligibility</span>
            </button>
            <button type="button" style={tabStyle('skills')} onClick={() => handleTabClick('skills')} title="Step C: Technical Skills">
              <span>{STEP_KEYS.indexOf(activeTab) > 2 ? '✓' : 'C.'}</span>
              <span>Skills</span>
            </button>
            <button type="button" style={tabStyle('experience')} onClick={() => handleTabClick('experience')} title="Step D: Experience Criteria">
              <span>{STEP_KEYS.indexOf(activeTab) > 3 ? '✓' : 'D.'}</span>
              <span>Experience</span>
            </button>
            <button type="button" style={tabStyle('projects')} onClick={() => handleTabClick('projects')} title="Step E: Project Criteria">
              <span>E.</span>
              <span>Projects</span>
            </button>
          </div>
          <span
            style={{
              fontSize: '0.74rem',
              fontWeight: 700,
              color: '#6d28d9',
              background: '#ede9fe',
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              whiteSpace: 'nowrap',
            }}
          >
            Step {STEP_KEYS.indexOf(activeTab) + 1} of 5
          </span>
        </div>

        {/* Error Alert */}
        {formError && (
          <div
            style={{
              margin: '0.8rem 1.5rem 0',
              padding: '0.6rem 1rem',
              background: '#fee2e2',
              color: '#b91c1c',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 600,
            }}
          >
            ⚠️ {formError}
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ overflowY: 'auto', padding: '1.2rem 1.5rem', flex: 1 }}>
          {/* TAB A: COMPANY INFO */}
          {activeTab === 'company' && (
            <div>
              <h4 style={{ color: '#4338ca', marginBottom: '0.5rem', fontSize: '0.98rem' }}>
                A. Company Information
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem' }}>
                <div>
                  <label style={labelStyle}>Company Name *</label>
                  <input
                    type="text"
                    required
                    style={inputStyle}
                    placeholder="e.g. EPAM Systems"
                    value={companyInfo.name}
                    onChange={(e) => setCompanyInfo({ ...companyInfo, name: e.target.value })}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Company Email *</label>
                  <input
                    type="email"
                    required
                    style={inputStyle}
                    placeholder="e.g. campus@epam.com"
                    value={companyInfo.email}
                    onChange={(e) => setCompanyInfo({ ...companyInfo, email: e.target.value })}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Job Role / Position *</label>
                  <input
                    type="text"
                    required
                    style={inputStyle}
                    placeholder="e.g. Java Software Engineer"
                    value={companyInfo.job_role}
                    onChange={(e) => setCompanyInfo({ ...companyInfo, job_role: e.target.value })}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Job Type</label>
                  <select
                    style={inputStyle}
                    value={companyInfo.job_type}
                    onChange={(e) => setCompanyInfo({ ...companyInfo, job_type: e.target.value })}
                  >
                    <option value="Full-time">Full-time</option>
                    <option value="Internship">Internship</option>
                    <option value="Contract">Contract</option>
                    <option value="Part-time">Part-time</option>
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Location</label>
                  <input
                    type="text"
                    style={inputStyle}
                    placeholder="e.g. Hyderabad / Remote"
                    value={companyInfo.location}
                    onChange={(e) => setCompanyInfo({ ...companyInfo, location: e.target.value })}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Company Website</label>
                  <input
                    type="url"
                    style={inputStyle}
                    placeholder="https://example.com"
                    value={companyInfo.website}
                    onChange={(e) => setCompanyInfo({ ...companyInfo, website: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label style={labelStyle}>Job Description</label>
                <textarea
                  rows={3}
                  style={inputStyle}
                  placeholder="Overview of the responsibilities and expectations..."
                  value={companyInfo.job_description}
                  onChange={(e) => setCompanyInfo({ ...companyInfo, job_description: e.target.value })}
                />
              </div>
            </div>
          )}

          {/* TAB B: ELIGIBILITY CRITERIA */}
          {activeTab === 'eligibility' && (
            <div>
              <h4 style={{ color: '#4338ca', marginBottom: '0.5rem', fontSize: '0.98rem' }}>
                B. Academic Eligibility Criteria
              </h4>
              <p style={helpTextStyle}>
                Deterministic evaluation matches candidate degree, branch, CGPA, and graduation year against these criteria.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem' }}>
                <div>
                  <label style={labelStyle}>Minimum CGPA</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="10"
                    style={inputStyle}
                    placeholder="e.g. 7.0"
                    value={eligibility.minimum_cgpa}
                    onChange={(e) => setEligibility({ ...eligibility, minimum_cgpa: e.target.value })}
                  />
                  <span style={helpTextStyle}>Leave empty if CGPA is optional.</span>
                </div>
                <div>
                  <label style={labelStyle}>Eligible Graduation Years</label>
                  <input
                    type="text"
                    style={inputStyle}
                    placeholder="e.g. 2026, 2027"
                    value={eligibility.eligible_graduation_years}
                    onChange={(e) => setEligibility({ ...eligibility, eligible_graduation_years: e.target.value })}
                  />
                  <span style={helpTextStyle}>Comma-separated graduation years.</span>
                </div>
                <div>
                  <label style={labelStyle}>Required Degree(s)</label>
                  <input
                    type="text"
                    style={inputStyle}
                    placeholder="e.g. B.Tech, B.E., MCA"
                    value={eligibility.required_degree}
                    onChange={(e) => setEligibility({ ...eligibility, required_degree: e.target.value })}
                  />
                  <span style={helpTextStyle}>Comma-separated degrees.</span>
                </div>
                <div>
                  <label style={labelStyle}>Required Branch / Departments</label>
                  <input
                    type="text"
                    style={inputStyle}
                    placeholder="e.g. CSE, IT, ECE"
                    value={eligibility.required_branches}
                    onChange={(e) => setEligibility({ ...eligibility, required_branches: e.target.value })}
                  />
                  <span style={helpTextStyle}>Comma-separated departments.</span>
                </div>
                <div>
                  <label style={labelStyle}>Minimum Class 10 Percentage (Optional)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    style={inputStyle}
                    placeholder="e.g. 60"
                    value={eligibility.minimum_class_10_percentage}
                    onChange={(e) => setEligibility({ ...eligibility, minimum_class_10_percentage: e.target.value })}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Minimum Class 12 Percentage (Optional)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    style={inputStyle}
                    placeholder="e.g. 60"
                    value={eligibility.minimum_class_12_percentage}
                    onChange={(e) => setEligibility({ ...eligibility, minimum_class_12_percentage: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label style={labelStyle}>Backlog Criteria (Optional)</label>
                <input
                  type="text"
                  style={inputStyle}
                  placeholder="e.g. No active backlogs allowed"
                  value={eligibility.backlog_criteria}
                  onChange={(e) => setEligibility({ ...eligibility, backlog_criteria: e.target.value })}
                />
                <span style={helpTextStyle}>
                  If configured, system marks status UNKNOWN when backlogs cannot be verified from resume.
                </span>
              </div>
            </div>
          )}

          {/* TAB C: TECHNICAL SKILLS */}
          {activeTab === 'skills' && (
            <div>
              <h4 style={{ color: '#4338ca', marginBottom: '0.5rem', fontSize: '0.98rem' }}>
                C. Technical Skills Criteria
              </h4>
              <p style={helpTextStyle}>
                Deterministic engine compares these against Candidate skills, projects, and experience technologies using canonical normalization (e.g. "Spring Boot" matches "SpringBoot").
              </p>
              <div>
                <label style={labelStyle}>Mandatory Technologies *</label>
                <input
                  type="text"
                  style={inputStyle}
                  placeholder="e.g. Java, Spring Boot, MySQL"
                  value={skills.mandatory_technologies}
                  onChange={(e) => setSkills({ ...skills, mandatory_technologies: e.target.value })}
                />
                <span style={helpTextStyle}>Comma-separated technologies required for passing.</span>
              </div>
              <div style={{ marginTop: '1rem' }}>
                <label style={labelStyle}>Preferred / Nice-to-Have Technologies</label>
                <input
                  type="text"
                  style={inputStyle}
                  placeholder="e.g. Docker, MongoDB, React, AWS"
                  value={skills.preferred_technologies}
                  onChange={(e) => setSkills({ ...skills, preferred_technologies: e.target.value })}
                />
                <span style={helpTextStyle}>Comma-separated preferred technologies for scoring.</span>
              </div>
            </div>
          )}

          {/* TAB D: EXPERIENCE CRITERIA */}
          {activeTab === 'experience' && (
            <div>
              <h4 style={{ color: '#4338ca', marginBottom: '0.5rem', fontSize: '0.98rem' }}>
                D. Work & Internship Experience Criteria
              </h4>
              <div style={{ marginTop: '0.8rem', padding: '0.8rem', background: '#f8f7ff', borderRadius: '8px', border: '1px solid #e5e0f7' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', fontWeight: 600, color: '#1f2937' }}>
                  <input
                    type="checkbox"
                    checked={experience.internship_required}
                    onChange={(e) => setExperience({ ...experience, internship_required: e.target.checked })}
                    style={{ width: '18px', height: '18px' }}
                  />
                  Prior Internship Experience Required
                </label>
                <span style={helpTextStyle}>
                  When checked, candidate must have an experience record marked as internship or role containing "intern".
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem', marginTop: '0.8rem' }}>
                <div>
                  <label style={labelStyle}>Minimum Experience (Months)</label>
                  <input
                    type="number"
                    min="0"
                    style={inputStyle}
                    placeholder="e.g. 6"
                    value={experience.minimum_experience_months}
                    onChange={(e) => setExperience({ ...experience, minimum_experience_months: e.target.value })}
                  />
                  <span style={helpTextStyle}>Leave empty if freshers are eligible.</span>
                </div>
                <div>
                  <label style={labelStyle}>Relevant Experience Technologies</label>
                  <input
                    type="text"
                    style={inputStyle}
                    placeholder="e.g. Java, Spring Boot, REST APIs"
                    value={experience.relevant_technologies}
                    onChange={(e) => setExperience({ ...experience, relevant_technologies: e.target.value })}
                  />
                  <span style={helpTextStyle}>Comma-separated technologies expected in experience.</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB E: PROJECT CRITERIA */}
          {activeTab === 'projects' && (
            <div>
              <h4 style={{ color: '#4338ca', marginBottom: '0.5rem', fontSize: '0.98rem' }}>
                E. Project Criteria
              </h4>
              <p style={helpTextStyle}>
                System deterministically inspects candidate projects and tech tags.
              </p>
              <div>
                <label style={labelStyle}>Required Project Technologies</label>
                <input
                  type="text"
                  style={inputStyle}
                  placeholder="e.g. Java, Spring Boot"
                  value={projects.required_technologies}
                  onChange={(e) => setProjects({ ...projects, required_technologies: e.target.value })}
                />
                <span style={helpTextStyle}>At least one candidate project must demonstrate these technologies.</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem', marginTop: '0.5rem' }}>
                <div>
                  <label style={labelStyle}>Minimum Number of Relevant Projects</label>
                  <input
                    type="number"
                    min="0"
                    style={inputStyle}
                    placeholder="e.g. 1"
                    value={projects.minimum_relevant_projects}
                    onChange={(e) => setProjects({ ...projects, minimum_relevant_projects: e.target.value })}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Required Project Description Keywords</label>
                  <input
                    type="text"
                    style={inputStyle}
                    placeholder="e.g. microservices, payment, authentication"
                    value={projects.description_keywords}
                    onChange={(e) => setProjects({ ...projects, description_keywords: e.target.value })}
                  />
                  <span style={helpTextStyle}>Comma-separated keywords to look for.</span>
                </div>
              </div>
            </div>
          )}

          {/* Modal / Panel Footer / Wizard Action Buttons */}
          <div
            style={{
              marginTop: '1.8rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '0.8rem',
              borderTop: '1px solid #e8e4f3',
              paddingTop: '1.2rem',
              flexWrap: 'wrap',
            }}
          >
            {/* Left: Cancel Control */}
            <button
              type="button"
              onClick={handleSafeClose}
              style={{
                padding: '0.65rem 1.2rem',
                borderRadius: '8px',
                border: '1px solid #d1d5db',
                background: '#ffffff',
                color: '#4b5563',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.88rem',
              }}
            >
              Cancel
            </button>

            {/* Right: Step Navigation Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              {/* Previous Button (Visible on Steps B, C, D, E) */}
              {!isFirstStep && (
                <button
                  type="button"
                  onClick={handlePrevious}
                  style={{
                    padding: '0.65rem 1.25rem',
                    borderRadius: '8px',
                    border: '1px solid #dcd7ee',
                    background: '#f8f7ff',
                    color: '#4b5563',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    fontSize: '0.88rem',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>←</span>
                  <span>Previous</span>
                </button>
              )}

              {/* Next Button (Visible on Steps A, B, C, D) */}
              {!isFinalStep && (
                <button
                  type="button"
                  onClick={handleNext}
                  style={{
                    padding: '0.65rem 1.5rem',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'linear-gradient(90deg, #6654e8 0%, #974bea 100%)',
                    color: '#ffffff',
                    fontWeight: 700,
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(102, 84, 232, 0.28)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    fontSize: '0.88rem',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>Next</span>
                  <span>→</span>
                </button>
              )}

              {/* Save / Update Requirement Button (Only on Step E) */}
              {isFinalStep && (
                <button
                  type="submit"
                  disabled={isLoading}
                  style={{
                    padding: '0.65rem 1.6rem',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'linear-gradient(90deg, #6654e8 0%, #974bea 100%)',
                    color: '#ffffff',
                    fontWeight: 700,
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    opacity: isLoading ? 0.7 : 1,
                    boxShadow: '0 4px 12px rgba(102, 84, 232, 0.3)',
                    fontSize: '0.88rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}
                >
                  <span>{isLoading ? 'Saving...' : initialData ? '✓ Update Requirement' : '✓ Save Requirement'}</span>
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    );

  if (asPanel) {
    return formContent;
  }

  return (
    <div className="modal-backdrop" onClick={handleSafeClose} style={{ zIndex: 1100 }}>
      {formContent}
    </div>
  );
}
