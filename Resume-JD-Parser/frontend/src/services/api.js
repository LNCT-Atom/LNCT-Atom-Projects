/**
 * API service for communicating with the FastAPI backend.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export async function parseResumeApi(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/resumes/parse`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.detail || `Upload failed with HTTP status ${response.status}`;
    throw new Error(errorMsg);
  }

  return data;
}

export async function getResumeByIdApi(documentId) {
  const response = await fetch(`${API_BASE_URL}/resumes/${documentId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch resume details');
  }
  return response.json();
}

export async function listResumesApi() {
  const response = await fetch(`${API_BASE_URL}/resumes`);
  if (!response.ok) {
    throw new Error('Failed to fetch uploaded resumes');
  }
  const data = await response.json();
  return data.resumes || [];
}

export async function deleteResumeApi(documentId) {
  const response = await fetch(`${API_BASE_URL}/resumes/${documentId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete resume record');
  }
  return response.json();
}

// =================== COMPANY RECRUITMENT REQUIREMENTS ===================

export async function listCompaniesApi(search = '') {
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  const response = await fetch(`${API_BASE_URL}/companies${query}`);
  if (!response.ok) {
    throw new Error('Failed to fetch company recruitment requirements');
  }
  const data = await response.json();
  return data.companies || [];
}

export async function getCompanyByIdApi(companyId) {
  const response = await fetch(`${API_BASE_URL}/companies/${companyId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch company requirement details');
  }
  return response.json();
}

export async function createCompanyApi(payload) {
  const response = await fetch(`${API_BASE_URL}/companies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to create company recruitment requirement');
  }
  return data;
}

export async function updateCompanyApi(companyId, payload) {
  const response = await fetch(`${API_BASE_URL}/companies/${companyId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to update company requirement');
  }
  return data;
}

export async function deleteCompanyApi(companyId) {
  const response = await fetch(`${API_BASE_URL}/companies/${companyId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete company recruitment requirement');
  }
  return response.json();
}

// =================== DETERMINISTIC EVALUATION ===================

export async function evaluateCandidatesApi(companyId, candidateId = null) {
  const response = await fetch(`${API_BASE_URL}/evaluations/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ company_id: companyId, candidate_id: candidateId }),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to run deterministic candidate evaluation');
  }
  return data;
}

export async function listEvaluationsForCompanyApi(companyId) {
  const response = await fetch(`${API_BASE_URL}/evaluations/company/${companyId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch evaluation results for company');
  }
  const data = await response.json();
  return data.evaluations || [];
}

export async function getEvaluationByIdApi(evaluationId) {
  const response = await fetch(`${API_BASE_URL}/evaluations/${evaluationId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch evaluation record');
  }
  return response.json();
}

// =================== MANUAL EDUCATION DATA ENTRY ===================

export async function updateEducationManualApi(documentId, payload) {
  const response = await fetch(`${API_BASE_URL}/resumes/${documentId}/education-manual`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to update manual education data');
  }
  return data;
}
