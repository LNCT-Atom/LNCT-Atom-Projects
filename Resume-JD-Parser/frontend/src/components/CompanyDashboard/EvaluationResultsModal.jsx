import React, { useState } from 'react';
import { updateEducationManualApi } from '../../services/api';
export default function EvaluationResultsModal({
  isOpen,
  onClose,
  companyRequirement,
  evaluations = [],
  isLoading = false,
  onViewEvaluationJson,
  onReevaluate,
  isReevaluating = false,
}) {
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [expandedEvalId, setExpandedEvalId] = useState(null);
  const [manualFormState, setManualFormState] = useState({});

  const updateManualField = (evalId, field, val) => {
    setManualFormState((prev) => ({
      ...prev,
      [evalId]: {
        ...(prev[evalId] || {}),
        [field]: val,
        error: null,
      },
    }));
  };

  const handleSaveManual = async (ev) => {
    const evalId = ev.id || ev._id;
    const candidateId = ev.candidate_id;
    if (!candidateId) {
      setManualFormState((prev) => ({
        ...prev,
        [evalId]: { ...(prev[evalId] || {}), error: 'Candidate ID not found on evaluation.' },
      }));
      return;
    }

    const currentForm = manualFormState[evalId] || {};
    const c10 = currentForm.class_10;
    const c12 = currentForm.class_12;
    const bkl = currentForm.backlogs;

    if (
      (c10 === undefined || c10 === '') &&
      (c12 === undefined || c12 === '') &&
      (bkl === undefined || bkl === '')
    ) {
      setManualFormState((prev) => ({
        ...prev,
        [evalId]: { ...currentForm, error: 'Please enter at least one field to save.' },
      }));
      return;
    }

    const payload = {};
    if (c10 !== undefined && c10 !== '') {
      const val = parseFloat(c10);
      if (isNaN(val) || val < 0 || val > 100) {
        setManualFormState((prev) => ({
          ...prev,
          [evalId]: { ...currentForm, error: 'Class 10 % must be between 0 and 100.' },
        }));
        return;
      }
      payload.class_10_percentage = val;
    }

    if (c12 !== undefined && c12 !== '') {
      const val = parseFloat(c12);
      if (isNaN(val) || val < 0 || val > 100) {
        setManualFormState((prev) => ({
          ...prev,
          [evalId]: { ...currentForm, error: 'Class 12 % must be between 0 and 100.' },
        }));
        return;
      }
      payload.class_12_percentage = val;
    }

    if (bkl !== undefined && bkl !== '') {
      const val = parseInt(bkl, 10);
      if (isNaN(val) || val < 0) {
        setManualFormState((prev) => ({
          ...prev,
          [evalId]: { ...currentForm, error: 'Backlogs must be an integer >= 0.' },
        }));
        return;
      }
      payload.backlogs = val;
    }

    setManualFormState((prev) => ({
      ...prev,
      [evalId]: { ...currentForm, isSaving: true, error: null, success: null },
    }));

    try {
      await updateEducationManualApi(candidateId, payload);
      setManualFormState((prev) => ({
        ...prev,
        [evalId]: {
          class_10: '',
          class_12: '',
          backlogs: '',
          isSaving: false,
          error: null,
          success: 'Academic data saved successfully! Re-evaluating candidate...',
        },
      }));
      if (onReevaluate) {
        await onReevaluate();
      }
    } catch (err) {
      setManualFormState((prev) => ({
        ...prev,
        [evalId]: { ...currentForm, isSaving: false, error: err.message || 'Failed to save data' },
      }));
    }
  };

  if (!isOpen) return null;

  const company = companyRequirement?.company || {};

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'PASS' || s === 'SELECTED' || s === 'REQUIRES_REVIEW') {
      return {
        bg: '#e0f7eb',
        color: '#08794e',
        border: '#a8e6c7',
        label: 'SELECTED',
        icon: '✅',
      };
    }
    if (s === 'FAIL' || s === 'FAILED') {
      return {
        bg: '#ffe8e8',
        color: '#b42332',
        border: '#f2b9c0',
        label: 'FAILED',
        icon: '❌',
      };
    }
    if (s === 'UNKNOWN') {
      return {
        bg: '#f1f0f7',
        color: '#6b7280',
        border: '#ddd8f0',
        label: 'UNKNOWN',
        icon: '❓',
      };
    }
    return {
      bg: '#f3f4f6',
      color: '#9ca3af',
      border: '#e5e7eb',
      label: s || 'N/A',
      icon: '•',
    };
  };

  /**
   * Parse a numeric value from a string that may contain '%', whitespace, or other text.
   * Returns NaN if the value cannot be parsed.
   */
  const parseNumericValue = (val) => {
    if (val === null || val === undefined) return NaN;
    if (typeof val === 'number') return val;
    const str = String(val).replace(/%/g, '').trim();
    if (str === '') return NaN;
    const match = str.match(/([0-9]+\.?[0-9]*)/);
    return match ? parseFloat(match[1]) : NaN;
  };

  /**
   * Compute Academic Eligibility based solely on 3 criteria:
   *   - minimum_cgpa
   *   - minimum_class_10_percentage
   *   - minimum_class_12_percentage
   *
   * Decision rule:
   *   PASS: All three configured criteria have actual values that meet their cutoffs.
   *   FAIL: At least one configured criterion definitively fails.
   *   REQUIRES_REVIEW: No definitive failure, but one or more configured criteria
   *                     have missing or invalid actual values.
   *
   * Criteria that are NOT_APPLICABLE (not configured by the company) are skipped.
   */
  const computeAcademicEligibility = (ev, compReq) => {
    const ACADEMIC_CRITERIA = ['minimum_cgpa', 'minimum_class_10_percentage', 'minimum_class_12_percentage'];
    const CRITERION_LABELS = {
      minimum_cgpa: 'CGPA',
      minimum_class_10_percentage: 'Class 10 %',
      minimum_class_12_percentage: 'Class 12 %',
    };

    const eligResults = ev.eligibility_results || [];
    const eligCriteria = compReq?.eligibility_criteria || {};

    // Collect results for each of the 3 academic criteria
    const criterionDetails = [];
    let hasAnyConfigured = false;

    for (const key of ACADEMIC_CRITERIA) {
      const label = CRITERION_LABELS[key];

      // Find the matching result from the backend evaluation
      const result = eligResults.find((r) => r.criterion === key);

      // Determine the cutoff: prefer the result's `expected`, fall back to companyRequirement
      let cutoff = null;
      if (result && result.expected !== null && result.expected !== undefined) {
        cutoff = parseNumericValue(result.expected);
      } else if (eligCriteria[key] !== null && eligCriteria[key] !== undefined) {
        cutoff = parseNumericValue(eligCriteria[key]);
      }

      // If there's no cutoff configured (NOT_APPLICABLE), skip this criterion
      if (cutoff === null || isNaN(cutoff)) {
        // Also check backend status in case it explicitly says NOT_APPLICABLE
        const backendStatus = (result?.status || '').toUpperCase();
        if (backendStatus === 'NOT_APPLICABLE' || (!result && (eligCriteria[key] === null || eligCriteria[key] === undefined))) {
          criterionDetails.push({ key, label, configured: false, status: 'NOT_APPLICABLE', reason: `${label} criterion is not configured.` });
          continue;
        }
      }

      hasAnyConfigured = true;
      const actualRaw = result?.actual;
      const actualNum = parseNumericValue(actualRaw);
      const cutoffNum = isNaN(cutoff) ? parseNumericValue(result?.expected) : cutoff;

      if (isNaN(actualNum)) {
        // Actual value is missing or invalid — cannot determine pass/fail
        criterionDetails.push({
          key, label, configured: true, status: 'UNKNOWN',
          reason: `${label} value is not available in the parsed resume.`,
          actual: actualRaw, expected: cutoffNum,
        });
      } else if (!isNaN(cutoffNum) && actualNum >= cutoffNum) {
        criterionDetails.push({
          key, label, configured: true, status: 'PASS',
          reason: `${label}: ${actualRaw} meets minimum ${cutoffNum}.`,
          actual: actualRaw, expected: cutoffNum,
        });
      } else {
        criterionDetails.push({
          key, label, configured: true, status: 'FAIL',
          reason: `${label}: ${actualRaw ?? 'N/A'} is below minimum ${cutoffNum}.`,
          actual: actualRaw, expected: cutoffNum,
        });
      }
    }

    // If none of the 3 criteria are configured, report as not applicable
    if (!hasAnyConfigured) {
      return {
        status: 'UNKNOWN',
        reasonText: 'No academic criteria (CGPA, Class 10 %, Class 12 %) are configured for this company.',
        details: criterionDetails,
      };
    }

    const configuredDetails = criterionDetails.filter((d) => d.configured);
    const failedDetails = configuredDetails.filter((d) => d.status === 'FAIL');
    const unknownDetails = configuredDetails.filter((d) => d.status === 'UNKNOWN');
    const passedDetails = configuredDetails.filter((d) => d.status === 'PASS');

    if (failedDetails.length > 0) {
      return {
        status: 'FAIL',
        reasonText: failedDetails.map((d) => d.reason).join(' '),
        details: criterionDetails,
      };
    }

    if (unknownDetails.length > 0) {
      return {
        status: 'REQUIRES_REVIEW',
        reasonText: 'Missing: ' + unknownDetails.map((d) => d.label).join(', ') + '.',
        details: criterionDetails,
      };
    }

    // All configured criteria passed
    return {
      status: 'PASS',
      reasonText: passedDetails.map((d) => d.reason).join(' '),
      details: criterionDetails,
    };
  };

  const isCandidateSelected = (ev) => {
    if (ev.is_eligible === true) return true;
    const s = (ev.evaluation?.overall_status || ev.eligibility_status || '').toUpperCase();
    return s === 'PASS' || s === 'SELECTED' || s === 'REQUIRES_REVIEW' || (s !== 'FAIL' && s !== 'FAILED');
  };

  const isCandidateFailed = (ev) => {
    const s = (ev.evaluation?.overall_status || ev.eligibility_status || '').toUpperCase();
    return s === 'FAIL' || s === 'FAILED';
  };

  const filteredEvaluations = evaluations.filter((ev) => {
    if (statusFilter === 'ALL') return true;
    if (statusFilter === 'PASS' || statusFilter === 'SELECTED') return isCandidateSelected(ev);
    if (statusFilter === 'FAIL' || statusFilter === 'FAILED') return isCandidateFailed(ev);
    return true;
  });

  const selectedCount = evaluations.filter(isCandidateSelected).length;
  const failedCount = evaluations.filter(isCandidateFailed).length;

  return (
    <div className="modal-backdrop" onClick={onClose} style={{ zIndex: 1100 }}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: '920px',
          maxHeight: '92vh',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: '16px',
        }}
      >
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '1.4rem' }}>📊</span>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#1a1a3a' }}>
                Evaluation Results: {company.job_role || 'Job Role'}
              </h3>
              <span
                style={{
                  background: '#e0e7ff',
                  color: '#4338ca',
                  borderRadius: '9999px',
                  padding: '0.2rem 0.7rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                }}
              >
                {company.name || 'Company'}
              </span>
            </div>
            <p style={{ margin: '0.2rem 0 0', fontSize: '0.82rem', color: '#6b7280' }}>
              Deterministic Python evaluation engine results (Zero AI / LLM involvement).
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Filter Bar & Quick Stats */}
        <div
          style={{
            padding: '0.8rem 1.5rem',
            background: '#faf8ff',
            borderBottom: '1px solid #e8e4f3',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.8rem',
          }}
        >
          {/* Status Tabs */}
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => setStatusFilter('ALL')}
              style={{
                padding: '0.4rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #dcd7ee',
                background: statusFilter === 'ALL' ? '#6366f1' : '#ffffff',
                color: statusFilter === 'ALL' ? '#ffffff' : '#4b5563',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              All ({evaluations.length})
            </button>
            <button
              onClick={() => setStatusFilter('PASS')}
              style={{
                padding: '0.4rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #a8e6c7',
                background: (statusFilter === 'PASS' || statusFilter === 'SELECTED') ? '#08794e' : '#e0f7eb',
                color: (statusFilter === 'PASS' || statusFilter === 'SELECTED') ? '#ffffff' : '#08794e',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              ✅ Selected ({selectedCount})
            </button>
            <button
              onClick={() => setStatusFilter('FAIL')}
              style={{
                padding: '0.4rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #f2b9c0',
                background: (statusFilter === 'FAIL' || statusFilter === 'FAILED') ? '#b42332' : '#ffe8e8',
                color: (statusFilter === 'FAIL' || statusFilter === 'FAILED') ? '#ffffff' : '#b42332',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              ❌ Failed ({failedCount})
            </button>
          </div>

          {/* Re-evaluate Button */}
          {onReevaluate && (
            <button
              onClick={onReevaluate}
              disabled={isReevaluating}
              style={{
                padding: '0.45rem 1rem',
                borderRadius: '8px',
                border: 'none',
                background: 'linear-gradient(90deg, #6654e8 0%, #974bea 100%)',
                color: '#ffffff',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: isReevaluating ? 'not-allowed' : 'pointer',
                opacity: isReevaluating ? 0.7 : 1,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
              }}
            >
              <span>⚡</span>
              <span>{isReevaluating ? 'Evaluating...' : 'Re-Evaluate All Candidates'}</span>
            </button>
          )}
        </div>

        {/* Content Body */}
        <div style={{ overflowY: 'auto', padding: '1.2rem 1.5rem', flex: 1 }}>
          {isLoading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#6b7280' }}>
              <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
              <p>Loading candidate evaluation records...</p>
            </div>
          ) : filteredEvaluations.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#9ca3af' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📋</div>
              <h4 style={{ color: '#4b5563', marginBottom: '0.3rem' }}>No evaluations found</h4>
              <p style={{ fontSize: '0.88rem' }}>
                {evaluations.length === 0
                  ? 'Click "Re-Evaluate All Candidates" above to evaluate uploaded resumes against this job requirement.'
                  : 'No candidate evaluations match the selected filter.'}
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {filteredEvaluations.map((ev) => {
                const overallBadge = getStatusBadge(ev.evaluation?.overall_status);
                const academicEval = computeAcademicEligibility(ev, companyRequirement);
                const eligBadge = getStatusBadge(academicEval.status);
                const mandBadge = getStatusBadge(ev.evaluation?.mandatory_skills_status);
                const expBadge = getStatusBadge(ev.evaluation?.experience_status);
                const projBadge = getStatusBadge(ev.evaluation?.project_status);

                const skillsRes = ev.skills_results || {};
                const isExpanded = expandedEvalId === ev.id;

                const isSelectedCandidate = ev.is_eligible === true && (ev.eligibility_status === 'SELECTED' || ev.evaluation?.overall_status === 'PASS');

                return (
                  <div
                    key={ev.id}
                    style={{
                      background: '#ffffff',
                      border: '1px solid #e8e4f3',
                      borderRadius: '12px',
                      padding: '1.2rem',
                      boxShadow: '0 2px 8px rgba(120, 100, 180, 0.05)',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {/* Top Row: Candidate details & Overall Status Badge */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        flexWrap: 'wrap',
                        gap: '0.6rem',
                        marginBottom: '0.8rem',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontSize: '1.1rem' }}>👤</span>
                          <span style={{ fontWeight: 700, fontSize: '1.02rem', color: '#1a1a3a' }}>
                            {ev.candidate_name || 'Anonymous Candidate'}
                          </span>
                        </div>
                        {ev.candidate_email && (
                          <div style={{ fontSize: '0.82rem', color: '#6b7280', marginTop: '0.1rem' }}>
                            ✉️ {ev.candidate_email}
                          </div>
                        )}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        {ev.is_eligible !== undefined && (
                          <span
                            style={{
                              padding: '0.25rem 0.65rem',
                              borderRadius: '6px',
                              fontSize: '0.74rem',
                              fontWeight: 700,
                              fontFamily: 'monospace',
                              background: ev.is_eligible ? '#dcfce7' : '#fee2e2',
                              color: ev.is_eligible ? '#15803d' : '#b91c1c',
                              border: `1px solid ${ev.is_eligible ? '#86efac' : '#fca5a5'}`,
                            }}
                          >
                            is_eligible: {String(ev.is_eligible)}
                          </span>
                        )}

                        <span
                          style={{
                            padding: '0.35rem 0.9rem',
                            borderRadius: '9999px',
                            fontSize: '0.82rem',
                            fontWeight: 700,
                            background: overallBadge.bg,
                            color: overallBadge.color,
                            border: `1px solid ${overallBadge.border}`,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.3rem',
                          }}
                        >
                          <span>{overallBadge.icon}</span>
                          <span>{overallBadge.label}</span>
                        </span>

                        <button
                          onClick={() => setExpandedEvalId(isExpanded ? null : ev.id)}
                          style={{
                            padding: '0.35rem 0.8rem',
                            borderRadius: '8px',
                            border: '1px solid #dcd7ee',
                            background: '#f8f7ff',
                            color: '#4338ca',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          {isExpanded ? 'Hide Details ▲' : 'View Details ▼'}
                        </button>
                      </div>
                    </div>

                    {/* Quick Metric Pills */}
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                        gap: '0.6rem',
                        background: '#faf8ff',
                        padding: '0.75rem',
                        borderRadius: '8px',
                        border: '1px solid #ece7f8',
                      }}
                    >
                      {/* Eligibility */}
                      <div>
                        <div style={{ fontSize: '0.74rem', color: '#6b7280', fontWeight: 600 }}>
                          ACADEMIC ELIGIBILITY
                        </div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: eligBadge.color, marginTop: '0.15rem' }}>
                          {eligBadge.icon} {eligBadge.label}
                        </div>
                        {!isSelectedCandidate && academicEval.status === 'REQUIRES_REVIEW' && (
                          <div style={{ fontSize: '0.72rem', color: '#b45309', marginTop: '0.15rem', fontWeight: 600 }}>
                            {academicEval.reasonText}
                          </div>
                        )}
                        {academicEval.status === 'FAIL' && (
                          <div style={{ fontSize: '0.72rem', color: '#b42332', marginTop: '0.15rem', fontWeight: 600 }}>
                            {academicEval.reasonText}
                          </div>
                        )}
                        {academicEval.status === 'PASS' && (
                          <div style={{ fontSize: '0.72rem', color: '#08794e', marginTop: '0.15rem', fontWeight: 600 }}>
                            {academicEval.reasonText}
                          </div>
                        )}
                        {!isSelectedCandidate && academicEval.status === 'UNKNOWN' && (
                          <div style={{ fontSize: '0.72rem', color: '#6b7280', marginTop: '0.15rem', fontWeight: 600 }}>
                            {academicEval.reasonText}
                          </div>
                        )}
                      </div>

                      {/* Mandatory Skills */}
                      <div>
                        <div style={{ fontSize: '0.74rem', color: '#6b7280', fontWeight: 600 }}>
                          MANDATORY SKILLS
                        </div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: mandBadge.color, marginTop: '0.15rem' }}>
                          {mandBadge.icon} {skillsRes.mandatory_match_percentage ?? 0}% ({skillsRes.matched_mandatory_technologies?.length || 0}/{(skillsRes.matched_mandatory_technologies?.length || 0) + (skillsRes.missing_mandatory_technologies?.length || 0)})
                        </div>
                      </div>

                      {/* Preferred Skills */}
                      <div>
                        <div style={{ fontSize: '0.74rem', color: '#6b7280', fontWeight: 600 }}>
                          PREFERRED SKILLS
                        </div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#4338ca', marginTop: '0.15rem' }}>
                          {skillsRes.preferred_match_percentage ?? 0}% Match
                        </div>
                      </div>

                      {/* Experience */}
                      <div>
                        <div style={{ fontSize: '0.74rem', color: '#6b7280', fontWeight: 600 }}>
                          EXPERIENCE
                        </div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: expBadge.color, marginTop: '0.15rem' }}>
                          {expBadge.icon} {expBadge.label}
                        </div>
                      </div>

                      {/* Projects */}
                      <div>
                        <div style={{ fontSize: '0.74rem', color: '#6b7280', fontWeight: 600 }}>
                          PROJECTS
                        </div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: projBadge.color, marginTop: '0.15rem' }}>
                          {projBadge.icon} {projBadge.label}
                        </div>
                      </div>
                    </div>

                    {/* Skills Breakdown tags */}
                    <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.78rem', color: '#6b7280', fontWeight: 600 }}>Matched Skills:</span>
                      {(skillsRes.matched_mandatory_technologies || []).length === 0 ? (
                        <span style={{ fontSize: '0.76rem', color: '#9ca3af' }}>None</span>
                      ) : (
                        skillsRes.matched_mandatory_technologies.map((t, idx) => (
                          <span
                            key={idx}
                            style={{
                              padding: '0.15rem 0.55rem',
                              background: '#e0f7eb',
                              color: '#08794e',
                              borderRadius: '4px',
                              fontSize: '0.76rem',
                              fontWeight: 600,
                            }}
                          >
                            ✓ {t}
                          </span>
                        ))
                      )}

                      {(skillsRes.missing_mandatory_technologies || []).length > 0 && (
                        <>
                          <span style={{ fontSize: '0.78rem', color: '#b42332', fontWeight: 600, marginLeft: '0.5rem' }}>
                            Missing Mandatory:
                          </span>
                          {skillsRes.missing_mandatory_technologies.map((t, idx) => (
                            <span
                              key={idx}
                              style={{
                                padding: '0.15rem 0.55rem',
                                background: '#ffe8e8',
                                color: '#b42332',
                                borderRadius: '4px',
                                fontSize: '0.76rem',
                                fontWeight: 600,
                              }}
                            >
                              ✕ {t}
                            </span>
                          ))}
                        </>
                      )}
                    </div>

                    {/* EXPANDED DETAILS ACCORDION */}
                    {isExpanded && (
                      <div
                        style={{
                          marginTop: '1rem',
                          paddingTop: '1rem',
                          borderTop: '1px dashed #dcd7ee',
                        }}
                      >
                        <h5 style={{ color: '#1a1a3a', fontSize: '0.9rem', marginBottom: '0.6rem' }}>
                          🔍 Detailed Evaluation Breakdown & Explainability
                        </h5>

                        {/* Criteria Result Table */}
                        <div style={{ overflowX: 'auto', marginBottom: '0.8rem' }}>
                          <table style={{ width: '100%', fontSize: '0.82rem', borderCollapse: 'collapse' }}>
                            <thead>
                              <tr style={{ background: '#f4f3fb', color: '#4b5563', textAlign: 'left' }}>
                                <th style={{ padding: '0.5rem 0.75rem' }}>Criterion</th>
                                <th style={{ padding: '0.5rem 0.75rem' }}>Status</th>
                                <th style={{ padding: '0.5rem 0.75rem' }}>Actual vs Expected</th>
                                <th style={{ padding: '0.5rem 0.75rem' }}>Deterministic Reason</th>
                              </tr>
                            </thead>
                            <tbody>
                              {[
                                ...(ev.eligibility_results || []),
                                ...(ev.experience_results || []),
                                ...(ev.project_results || []),
                              ].map((cr, cIdx) => {
                                const cBadge = getStatusBadge(cr.status);
                                return (
                                  <tr key={cIdx} style={{ borderBottom: '1px solid #f0edf8' }}>
                                    <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600, color: '#374151' }}>
                                      {cr.criterion.replace(/_/g, ' ')}
                                    </td>
                                    <td style={{ padding: '0.5rem 0.75rem' }}>
                                      <span
                                        style={{
                                          padding: '0.15rem 0.5rem',
                                          borderRadius: '4px',
                                          fontSize: '0.74rem',
                                          fontWeight: 700,
                                          background: cBadge.bg,
                                          color: cBadge.color,
                                        }}
                                      >
                                        {cBadge.label}
                                      </span>
                                    </td>
                                    <td style={{ padding: '0.5rem 0.75rem', color: '#4b5563' }}>
                                      {cr.actual !== null && cr.actual !== undefined ? String(cr.actual) : 'Not Specified'}
                                      {cr.expected !== null && cr.expected !== undefined && ` (Req: ${JSON.stringify(cr.expected)})`}
                                    </td>
                                    <td style={{ padding: '0.5rem 0.75rem', color: '#6b7280' }}>
                                      {cr.reason}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>

                        {/* Missing Data Warnings */}
                        {ev.missing_data && ev.missing_data.length > 0 && (
                          <div
                            style={{
                              background: '#fffbeb',
                              border: '1px solid #fde68a',
                              borderRadius: '8px',
                              padding: '0.75rem 1rem',
                              marginTop: '0.6rem',
                            }}
                          >
                            <div style={{ fontWeight: 700, fontSize: '0.8rem', color: '#92400e', marginBottom: '0.3rem' }}>
                              ⚠️ Missing Resume Data (Treated as UNKNOWN, Not Hard Reject)
                            </div>
                            <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.78rem', color: '#b45309' }}>
                              {ev.missing_data.map((item, mIdx) => (
                                <li key={mIdx}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Manual Education Data Entry Form */}
                        {(() => {
                          const form = manualFormState[ev.id] || {
                            class_10: '',
                            class_12: '',
                            backlogs: '',
                            isSaving: false,
                            error: null,
                            success: null,
                          };
                          return (
                            <div
                              style={{
                                background: '#f8faff',
                                border: '1px solid #dbeafe',
                                borderRadius: '8px',
                                padding: '0.85rem 1rem',
                                marginTop: '0.8rem',
                              }}
                            >
                              <div
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  marginBottom: '0.4rem',
                                  flexWrap: 'wrap',
                                  gap: '0.4rem',
                                }}
                              >
                                <div
                                  style={{
                                    fontWeight: 700,
                                    fontSize: '0.82rem',
                                    color: '#1e40af',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.4rem',
                                  }}
                                >
                                  <span>✍️</span>
                                  <span>Enter / Update Verified Academic Data (T&P Admin)</span>
                                </div>
                                <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>
                                  Auto-reevaluates candidate upon saving
                                </span>
                              </div>
                              <p style={{ margin: '0 0 0.6rem 0', fontSize: '0.76rem', color: '#4b5563' }}>
                                Provide verified Class 10%, Class 12%, or Backlog count if omitted or unparsed from the resume.
                              </p>

                              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                                <div style={{ flex: '1 1 120px' }}>
                                  <label
                                    style={{
                                      display: 'block',
                                      fontSize: '0.72rem',
                                      fontWeight: 600,
                                      color: '#374151',
                                      marginBottom: '0.2rem',
                                    }}
                                  >
                                    Class 10 %
                                  </label>
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    max="100"
                                    placeholder="e.g. 85.0"
                                    value={form.class_10 || ''}
                                    onChange={(e) => updateManualField(ev.id, 'class_10', e.target.value)}
                                    style={{
                                      width: '100%',
                                      padding: '0.35rem 0.6rem',
                                      borderRadius: '6px',
                                      border: '1px solid #cbd5e1',
                                      fontSize: '0.8rem',
                                      boxSizing: 'border-box',
                                    }}
                                  />
                                </div>

                                <div style={{ flex: '1 1 120px' }}>
                                  <label
                                    style={{
                                      display: 'block',
                                      fontSize: '0.72rem',
                                      fontWeight: 600,
                                      color: '#374151',
                                      marginBottom: '0.2rem',
                                    }}
                                  >
                                    Class 12 %
                                  </label>
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    max="100"
                                    placeholder="e.g. 82.5"
                                    value={form.class_12 || ''}
                                    onChange={(e) => updateManualField(ev.id, 'class_12', e.target.value)}
                                    style={{
                                      width: '100%',
                                      padding: '0.35rem 0.6rem',
                                      borderRadius: '6px',
                                      border: '1px solid #cbd5e1',
                                      fontSize: '0.8rem',
                                      boxSizing: 'border-box',
                                    }}
                                  />
                                </div>

                                <div style={{ flex: '1 1 120px' }}>
                                  <label
                                    style={{
                                      display: 'block',
                                      fontSize: '0.72rem',
                                      fontWeight: 600,
                                      color: '#374151',
                                      marginBottom: '0.2rem',
                                    }}
                                  >
                                    Backlogs
                                  </label>
                                  <input
                                    type="number"
                                    step="1"
                                    min="0"
                                    placeholder="e.g. 0"
                                    value={form.backlogs || ''}
                                    onChange={(e) => updateManualField(ev.id, 'backlogs', e.target.value)}
                                    style={{
                                      width: '100%',
                                      padding: '0.35rem 0.6rem',
                                      borderRadius: '6px',
                                      border: '1px solid #cbd5e1',
                                      fontSize: '0.8rem',
                                      boxSizing: 'border-box',
                                    }}
                                  />
                                </div>

                                <div>
                                  <button
                                    type="button"
                                    disabled={form.isSaving}
                                    onClick={() => handleSaveManual(ev)}
                                    style={{
                                      padding: '0.45rem 1rem',
                                      borderRadius: '6px',
                                      border: 'none',
                                      background: form.isSaving ? '#94a3b8' : '#2563eb',
                                      color: '#ffffff',
                                      fontSize: '0.8rem',
                                      fontWeight: 600,
                                      cursor: form.isSaving ? 'not-allowed' : 'pointer',
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: '0.3rem',
                                    }}
                                  >
                                    {form.isSaving ? 'Saving...' : '💾 Save & Re-evaluate'}
                                  </button>
                                </div>
                              </div>

                              {form.error && (
                                <div style={{ marginTop: '0.5rem', color: '#dc2626', fontSize: '0.74rem', fontWeight: 600 }}>
                                  ⚠️ {form.error}
                                </div>
                              )}
                              {form.success && (
                                <div style={{ marginTop: '0.5rem', color: '#16a34a', fontSize: '0.74rem', fontWeight: 600 }}>
                                  ✅ {form.success}
                                </div>
                              )}
                            </div>
                          );
                        })()}

                        {/* Button to View Evaluation JSON */}
                        <div style={{ marginTop: '0.8rem', display: 'flex', justifyContent: 'flex-end' }}>
                          <button
                            onClick={() => onViewEvaluationJson && onViewEvaluationJson(ev)}
                            style={{
                              padding: '0.4rem 0.9rem',
                              borderRadius: '6px',
                              border: '1px solid #a5b4fc',
                              background: '#ffffff',
                              color: '#4f46e5',
                              fontSize: '0.8rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.3rem',
                            }}
                          >
                            <span>📄</span>
                            <span>View Complete Evaluation JSON</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
