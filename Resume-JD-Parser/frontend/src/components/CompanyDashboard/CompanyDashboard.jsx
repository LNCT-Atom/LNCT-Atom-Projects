import React, { useState, useEffect } from 'react';
import CompanyFormModal from './CompanyFormModal';
import EvaluationResultsModal from './EvaluationResultsModal';
import {
  listCompaniesApi,
  createCompanyApi,
  updateCompanyApi,
  deleteCompanyApi,
  evaluateCandidatesApi,
  listEvaluationsForCompanyApi,
} from '../../services/api';

export default function CompanyDashboard({ onViewJson }) {
  const [companies, setCompanies] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [alert, setAlert] = useState(null);

  // Form Modal State
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [isSubmittingForm, setIsSubmittingForm] = useState(false);

  // Evaluation Results Modal State
  const [isEvalModalOpen, setIsEvalModalOpen] = useState(false);
  const [selectedCompanyReq, setSelectedCompanyReq] = useState(null);
  const [companyEvaluations, setCompanyEvaluations] = useState([]);
  const [isLoadingEvaluations, setIsLoadingEvaluations] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluatingCompanyId, setEvaluatingCompanyId] = useState(null);

  // Load companies on mount
  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async (search = '') => {
    setIsLoading(true);
    try {
      const data = await listCompaniesApi(search);
      setCompanies(data);
    } catch (err) {
      setAlert({
        type: 'error',
        message: `Failed to load recruitment requirements: ${err.message}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchTerm(val);
    fetchCompanies(val);
  };

  const handleOpenCreate = () => {
    setEditingCompany(null);
    setIsFormOpen(true);
  };

  const handleOpenEdit = (comp) => {
    setEditingCompany(comp);
    setIsFormOpen(true);
  };

  const handleFormSubmit = async (payload) => {
    setIsSubmittingForm(true);
    try {
      if (editingCompany) {
        await updateCompanyApi(editingCompany.id, payload);
        setAlert({
          type: 'success',
          message: 'Company recruitment requirement updated successfully.',
        });
      } else {
        await createCompanyApi(payload);
        setAlert({
          type: 'success',
          message: 'Company recruitment requirement created and saved to MongoDB.',
        });
      }
      setIsFormOpen(false);
      fetchCompanies(searchTerm);
    } catch (err) {
      setAlert({
        type: 'error',
        message: err.message || 'Failed to save requirement.',
      });
    } finally {
      setIsSubmittingForm(false);
    }
  };

  const handleDelete = async (comp) => {
    if (!window.confirm(`Are you sure you want to delete requirement for ${comp.company?.name || 'this company'}?`)) {
      return;
    }
    try {
      await deleteCompanyApi(comp.id);
      setAlert({
        type: 'success',
        message: 'Requirement deleted successfully.',
      });
      fetchCompanies(searchTerm);
    } catch (err) {
      setAlert({
        type: 'error',
        message: `Failed to delete: ${err.message}`,
      });
    }
  };

  // View Company JSON
  const handleViewCompanyJson = (comp) => {
    const cleanDoc = { ...comp };
    delete cleanDoc._id;
    if (onViewJson) {
      onViewJson(cleanDoc, `Company JSON — ${comp.company?.name} (${comp.company?.job_role})`);
    }
  };

  // Run Deterministic Evaluation
  const handleRunEvaluation = async (comp) => {
    setEvaluatingCompanyId(comp.id);
    setIsEvaluating(true);
    try {
      const res = await evaluateCandidatesApi(comp.id);
      setAlert({
        type: 'success',
        message: res.message || 'Evaluation completed successfully.',
      });

      // Automatically open the evaluation results modal
      setSelectedCompanyReq(comp);
      if (Array.isArray(res?.evaluations) && res.evaluations.length > 0) {
        setCompanyEvaluations(res.evaluations);
      } else {
        await loadCompanyEvaluations(comp.id);
      }
      setIsEvalModalOpen(true);
    } catch (err) {
      setAlert({
        type: 'error',
        message: `Evaluation failed: ${err.message}`,
      });
    } finally {
      setIsEvaluating(false);
      setEvaluatingCompanyId(null);
    }
  };

  // View Existing Evaluations
  const handleOpenEvaluations = async (comp) => {
    setSelectedCompanyReq(comp);
    setIsEvalModalOpen(true);
    await loadCompanyEvaluations(comp.id);
  };

  const loadCompanyEvaluations = async (companyId) => {
    setIsLoadingEvaluations(true);
    try {
      const evals = await listEvaluationsForCompanyApi(companyId);
      setCompanyEvaluations(evals);
    } catch (err) {
      console.warn('Failed to fetch evaluations:', err);
      setCompanyEvaluations([]);
    } finally {
      setIsLoadingEvaluations(false);
    }
  };

  // View specific Evaluation JSON from within results modal
  const handleViewEvaluationJson = (evalDoc) => {
    const cleanDoc = { ...evalDoc };
    delete cleanDoc._id;
    if (onViewJson) {
      onViewJson(
        cleanDoc,
        `Evaluation JSON — Candidate: ${evalDoc.candidate_name || evalDoc.candidate_id}`
      );
    }
  };

  return (
    <div style={{ marginTop: '1.5rem' }}>
      {/* Alert banner */}
      {alert && (
        <div
          style={{
            marginBottom: '1.5rem',
            padding: '0.9rem 1.2rem',
            borderRadius: '10px',
            background: alert.type === 'error' ? '#fee2e2' : '#e0f7eb',
            color: alert.type === 'error' ? '#991b1b' : '#065f46',
            border: `1px solid ${alert.type === 'error' ? '#fca5a5' : '#a7f3d0'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.92rem',
            fontWeight: 500,
          }}
        >
          <span>{alert.message}</span>
          <button
            onClick={() => setAlert(null)}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.1rem',
              cursor: 'pointer',
              color: 'inherit',
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Top Controls & Search Bar */}
      <div
        style={{
          background: 'rgba(255, 255, 255, 0.92)',
          backdropFilter: 'blur(12px)',
          border: '1px solid #e8e4f3',
          borderRadius: '14px',
          padding: '1.4rem 1.8rem',
          boxShadow: '0 4px 20px rgba(120, 100, 180, 0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flex: 1, minWidth: '280px' }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '420px' }}>
            <span style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }}>
              🔍
            </span>
            <input
              type="text"
              placeholder="Search by company, role, or location..."
              value={searchTerm}
              onChange={handleSearchChange}
              style={{
                width: '100%',
                padding: '0.65rem 1rem 0.65rem 2.4rem',
                borderRadius: '9999px',
                border: '1px solid #dcd7ee',
                fontSize: '0.9rem',
                outline: 'none',
                background: '#ffffff',
              }}
            />
          </div>
          <button
            onClick={() => fetchCompanies(searchTerm)}
            disabled={isLoading}
            style={{
              padding: '0.65rem 1rem',
              borderRadius: '9999px',
              border: '1px solid #dcd7ee',
              background: '#f8f7ff',
              color: '#4b5563',
              fontSize: '0.86rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.3rem',
            }}
          >
            <span>🔄</span>
            <span>{isLoading ? 'Loading...' : 'Refresh'}</span>
          </button>
        </div>

        <button
          onClick={handleOpenCreate}
          style={{
            padding: '0.7rem 1.4rem',
            borderRadius: '10px',
            border: 'none',
            background: 'linear-gradient(90deg, #6654e8 0%, #974bea 100%)',
            color: '#ffffff',
            fontWeight: 700,
            fontSize: '0.9rem',
            cursor: 'pointer',
            boxShadow: '0 4px 14px rgba(102, 84, 232, 0.3)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'transform 0.15s ease',
          }}
        >
          <span>➕</span>
          <span>Post Recruitment Requirement</span>
        </button>
      </div>

      {/* Main Content: Two-Panel Layout */}
      <div
        className={`company-dashboard-layout ${isFormOpen ? 'has-open-form' : ''}`}
        style={{
          display: 'grid',
          gridTemplateColumns: isFormOpen ? 'minmax(0, 1fr) 520px' : '1fr',
          gap: '1.5rem',
          alignItems: 'start',
          marginTop: '1.5rem',
        }}
      >
        {/* Left Panel: View All Recruitment Requirements */}
        <div className="company-dashboard-left-panel">
          {/* Section Header: View All */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1.2rem',
              flexWrap: 'wrap',
              gap: '0.8rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h3
                style={{
                  fontFamily: 'Outfit, sans-serif',
                  fontSize: '1.28rem',
                  fontWeight: 700,
                  color: '#1a1a3a',
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
              >
                <span>📋</span>
                <span>View All</span>
                <span style={{ fontSize: '0.95rem', fontWeight: 500, color: '#6b7280' }}>
                  Recruitment Requirements
                </span>
              </h3>
              <span
                style={{
                  background: '#ede9fe',
                  color: '#6d28d9',
                  padding: '0.2rem 0.75rem',
                  borderRadius: '9999px',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                }}
              >
                {companies.length} {companies.length === 1 ? 'Requirement' : 'Requirements'}
              </span>
            </div>

            {searchTerm && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: '#6b7280' }}>
                <span>Filtered by: <strong>"{searchTerm}"</strong></span>
                <button
                  onClick={() => {
                    setSearchTerm('');
                    fetchCompanies('');
                  }}
                  style={{
                    background: '#f3f4f6',
                    border: 'none',
                    padding: '0.2rem 0.55rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    color: '#4b5563',
                    fontWeight: 600,
                  }}
                >
                  Clear ✕
                </button>
              </div>
            )}
          </div>

          {/* Cards or Empty/Loading State */}
          {isLoading && companies.length === 0 ? (
            <div style={{ padding: '3.5rem', textAlign: 'center', color: '#6b7280', background: 'rgba(255,255,255,0.7)', borderRadius: '14px', border: '1px solid #e8e4f3' }}>
              <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
              <p>Loading company recruitment requirements from database...</p>
            </div>
          ) : companies.length === 0 ? (
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.9)',
                borderRadius: '14px',
                border: '1px solid #e8e4f3',
                padding: '3.5rem 2rem',
                textAlign: 'center',
                color: '#6b7280',
              }}
            >
              <div style={{ fontSize: '3rem', marginBottom: '0.8rem' }}>🏢</div>
              <h3 style={{ color: '#1a1a3a', fontSize: '1.2rem', marginBottom: '0.4rem' }}>
                {searchTerm ? 'No Matching Requirements' : 'No Recruitment Requirements Found'}
              </h3>
              <p style={{ fontSize: '0.9rem', maxWidth: '480px', margin: '0 auto 1.2rem', color: '#6b7280' }}>
                {searchTerm
                  ? `No recruitment requirements matched '${searchTerm}'. Try clearing your search or creating a new requirement.`
                  : 'Create your first company requirement to start deterministically evaluating uploaded candidate resumes.'}
              </p>
              {searchTerm ? (
                <button
                  onClick={() => {
                    setSearchTerm('');
                    fetchCompanies('');
                  }}
                  style={{
                    padding: '0.65rem 1.4rem',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    background: '#ffffff',
                    color: '#374151',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Clear Search Filter
                </button>
              ) : (
                <button
                  onClick={handleOpenCreate}
                  style={{
                    padding: '0.65rem 1.4rem',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'linear-gradient(90deg, #6654e8 0%, #974bea 100%)',
                    color: '#fff',
                    fontWeight: 600,
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(102, 84, 232, 0.25)',
                  }}
                >
                  + Post Recruitment Requirement
                </button>
              )}
            </div>
          ) : (
            <div
              className="company-cards-grid"
              style={{
                display: 'grid',
                gridTemplateColumns: isFormOpen
                  ? 'repeat(auto-fill, minmax(310px, 1fr))'
                  : 'repeat(auto-fill, minmax(360px, 1fr))',
                gap: '1.25rem',
              }}
            >
            {companies.map((comp) => {
              const c = comp.company || {};
              const elig = comp.eligibility_criteria || {};
              const tech = comp.technical_skills || {};
              const exp = comp.experience_criteria || {};
              const isCurrEvaluating = isEvaluating && evaluatingCompanyId === comp.id;
              const isCurrentEditing = isFormOpen && editingCompany?.id === comp.id;

              return (
                <div
                  key={comp.id}
                  className={`company-card ${isCurrentEditing ? 'editing-active' : ''}`}
                  style={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    border: isCurrentEditing ? '2px solid #6366f1' : '1px solid #e8e4f3',
                    borderRadius: '14px',
                    padding: '1.4rem',
                    boxShadow: isCurrentEditing
                      ? '0 0 0 3px rgba(99, 102, 241, 0.18), 0 8px 24px rgba(102, 84, 232, 0.16)'
                      : '0 4px 18px rgba(120, 100, 180, 0.06)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                  }}
                >
                  {/* Card Header */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.6rem' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                          <span
                            style={{
                              background: '#ede9fe',
                              color: '#6d28d9',
                              fontSize: '0.74rem',
                              fontWeight: 700,
                              padding: '0.2rem 0.6rem',
                              borderRadius: '9999px',
                              display: 'inline-block',
                            }}
                          >
                            {c.job_type || 'Full-time'}
                          </span>
                          {isCurrentEditing && (
                            <span
                              style={{
                                background: '#4f46e5',
                                color: '#ffffff',
                                fontSize: '0.72rem',
                                fontWeight: 700,
                                padding: '0.2rem 0.55rem',
                                borderRadius: '9999px',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '0.2rem',
                              }}
                            >
                              <span>✏️</span>
                              <span>Editing in Form</span>
                            </span>
                          )}
                        </div>
                        <h4 style={{ margin: 0, fontSize: '1.18rem', fontWeight: 700, color: '#1a1a3a' }}>
                          {c.job_role || 'Job Role'}
                        </h4>
                        <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#4b5563', marginTop: '0.2rem' }}>
                          🏢 {c.name || 'Company Name'}
                        </div>
                      </div>

                      {c.location && (
                        <span style={{ fontSize: '0.8rem', color: '#6b7280', whiteSpace: 'nowrap' }}>
                          📍 {c.location}
                        </span>
                      )}
                    </div>

                    {c.job_description && (
                      <p
                        style={{
                          fontSize: '0.82rem',
                          color: '#6b7280',
                          marginTop: '0.6rem',
                          lineHeight: '1.4',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {c.job_description}
                      </p>
                    )}

                    {/* Criteria Snippets */}
                    <div style={{ marginTop: '0.9rem', display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.8rem', color: '#4b5563' }}>
                      {/* Academic */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, color: '#374151' }}>🎓 Eligibility:</span>
                        {elig.minimum_cgpa && (
                          <span style={{ background: '#f3f4f6', padding: '0.1rem 0.45rem', borderRadius: '4px' }}>
                            Min CGPA {elig.minimum_cgpa}
                          </span>
                        )}
                        {(elig.required_degree || []).length > 0 && (
                          <span style={{ background: '#f3f4f6', padding: '0.1rem 0.45rem', borderRadius: '4px' }}>
                            {elig.required_degree.join(', ')}
                          </span>
                        )}
                        {(elig.required_branches || []).length > 0 && (
                          <span style={{ background: '#f3f4f6', padding: '0.1rem 0.45rem', borderRadius: '4px' }}>
                            {elig.required_branches.join(', ')}
                          </span>
                        )}
                      </div>

                      {/* Mandatory Skills */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, color: '#374151' }}>⚙️ Mandatory:</span>
                        {(tech.mandatory_technologies || []).length === 0 ? (
                          <span style={{ color: '#9ca3af' }}>None specified</span>
                        ) : (
                          tech.mandatory_technologies.map((t, tIdx) => (
                            <span
                              key={tIdx}
                              style={{
                                background: '#e0e7ff',
                                color: '#4338ca',
                                padding: '0.1rem 0.45rem',
                                borderRadius: '4px',
                                fontWeight: 600,
                                fontSize: '0.76rem',
                              }}
                            >
                              {t}
                            </span>
                          ))
                        )}
                      </div>

                      {/* Experience */}
                      {exp.internship_required && (
                        <div style={{ color: '#059669', fontWeight: 600, fontSize: '0.78rem' }}>
                          ✓ Prior Internship Required
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Card Actions Footer */}
                  <div
                    style={{
                      marginTop: '1.2rem',
                      paddingTop: '0.9rem',
                      borderTop: '1px solid #f0edf8',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '0.5rem',
                    }}
                  >
                    {/* Left: Evaluation Action */}
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button
                        onClick={() => handleRunEvaluation(comp)}
                        disabled={isCurrEvaluating}
                        title="Evaluate candidate resumes deterministically"
                        style={{
                          padding: '0.45rem 0.85rem',
                          borderRadius: '8px',
                          border: 'none',
                          background: 'linear-gradient(90deg, #6654e8 0%, #974bea 100%)',
                          color: '#ffffff',
                          fontWeight: 700,
                          fontSize: '0.8rem',
                          cursor: isCurrEvaluating ? 'not-allowed' : 'pointer',
                          opacity: isCurrEvaluating ? 0.7 : 1,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                        }}
                      >
                        <span>⚡</span>
                        <span>{isCurrEvaluating ? 'Evaluating...' : 'Evaluate'}</span>
                      </button>

                      <button
                        onClick={() => handleOpenEvaluations(comp)}
                        title="View candidate evaluation results"
                        style={{
                          padding: '0.45rem 0.85rem',
                          borderRadius: '8px',
                          border: '1px solid #dcd7ee',
                          background: '#f8f7ff',
                          color: '#4338ca',
                          fontWeight: 600,
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                        }}
                      >
                        <span>📊</span>
                        <span>Results</span>
                      </button>
                    </div>

                    {/* Right: View JSON, Edit, Delete */}
                    <div style={{ display: 'flex', gap: '0.35rem' }}>
                      <button
                        onClick={() => handleViewCompanyJson(comp)}
                        title="View Company JSON document"
                        style={{
                          padding: '0.45rem 0.65rem',
                          borderRadius: '8px',
                          border: '1px solid #dcd7ee',
                          background: '#ffffff',
                          color: '#4b5563',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        View JSON
                      </button>

                      <button
                        onClick={() => handleOpenEdit(comp)}
                        title="Edit requirement"
                        style={{
                          padding: '0.45rem 0.65rem',
                          borderRadius: '8px',
                          border: '1px solid #dcd7ee',
                          background: '#ffffff',
                          color: '#4b5563',
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                        }}
                      >
                        ✏️
                      </button>

                      <button
                        onClick={() => handleDelete(comp)}
                        title="Delete requirement"
                        style={{
                          padding: '0.45rem 0.65rem',
                          borderRadius: '8px',
                          border: '1px solid #fed7d7',
                          background: '#fff5f5',
                          color: '#c53030',
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                        }}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        </div>

        {/* Right Panel: Company Recruitment Form */}
        {isFormOpen && (
          <div className="company-dashboard-right-panel" style={{ width: '100%' }}>
            <CompanyFormModal
              isOpen={isFormOpen}
              onClose={() => {
                setIsFormOpen(false);
                setEditingCompany(null);
              }}
              onSubmit={handleFormSubmit}
              initialData={editingCompany}
              isLoading={isSubmittingForm}
              asPanel={true}
            />
          </div>
        )}
      </div>

      {/* Evaluation Results Modal */}
      <EvaluationResultsModal
        isOpen={isEvalModalOpen}
        onClose={() => setIsEvalModalOpen(false)}
        companyRequirement={selectedCompanyReq}
        evaluations={companyEvaluations}
        isLoading={isLoadingEvaluations}
        onViewEvaluationJson={handleViewEvaluationJson}
        onReevaluate={() => selectedCompanyReq && handleRunEvaluation(selectedCompanyReq)}
        isReevaluating={isEvaluating}
      />
    </div>
  );
}
