import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import StatusAlert from './components/StatusAlert';
import UploadedResumesSection from './components/UploadedResumesSection';
import RawJsonModal from './components/RawJsonModal';
import CompanyDashboard from './components/CompanyDashboard/CompanyDashboard';
import {
  parseResumeApi,
  listResumesApi,
  getResumeByIdApi,
  deleteResumeApi,
} from './services/api';

const SUCCESS_PERSISTENCE_MSG =
  'Your resume has been submitted successfully, and your parsed JSON data has been saved to our database.';

export default function App() {
  const [activeMainTab, setActiveMainTab] = useState('resumes'); // 'resumes' | 'companies'
  const [isLoading, setIsLoading] = useState(false);
  const [alert, setAlert] = useState(null);

  // Recently processed resume from upload flow (JSON is kept hidden until View JSON is clicked)
  const [recentlyProcessedResume, setRecentlyProcessedResume] = useState(null);

  // Uploaded resumes history list
  const [uploadedResumes, setUploadedResumes] = useState([]);
  const [isLoadingResumes, setIsLoadingResumes] = useState(false);

  // Shared Modal State for Click-to-View JSON functionality
  const [selectedResume, setSelectedResume] = useState(null);
  const [selectedResumeJson, setSelectedResumeJson] = useState(null);
  const [isJsonViewerOpen, setIsJsonViewerOpen] = useState(false);
  const [isLoadingJson, setIsLoadingJson] = useState(false);
  const [jsonViewerError, setJsonViewerError] = useState(null);
  const [loadingHistoryDocId, setLoadingHistoryDocId] = useState(null);

  // Fetch uploaded resumes on initial load
  useEffect(() => {
    fetchResumes();
  }, []);

  const fetchResumes = async () => {
    setIsLoadingResumes(true);
    try {
      const items = await listResumesApi();
      setUploadedResumes(items);
    } catch (err) {
      console.warn('Failed to fetch uploaded resumes history:', err);
    } finally {
      setIsLoadingResumes(false);
    }
  };

  const handleUpload = async (file) => {
    if (isLoading) return; // Prevent repeated submissions during processing
    setIsLoading(true);
    setAlert(null);

    try {
      const response = await parseResumeApi(file);

      // Verify persistence confirmation contract
      const resumeId = response?.resume_id || response?.document_id;
      const isSaved = response?.saved === true;
      const isSuccess = response?.success === true || response?.status === 'completed';

      if (!isSuccess || !isSaved || !resumeId) {
        throw new Error(
          response?.message || 'Database persistence could not be verified by the backend.'
        );
      }

      // Associate recently processed resume record (remains hidden until View JSON is clicked)
      setRecentlyProcessedResume({
        ...response,
        filename: file.name,
      });

      // Display the existing success message
      setAlert({
        type: response.duplicate ? 'warning' : 'success',
        message: SUCCESS_PERSISTENCE_MSG,
      });

      // Refresh the uploaded resumes list immediately to show the new record in history
      fetchResumes();
    } catch (err) {
      // Clear recent processed result so no stale / false success button is shown
      setRecentlyProcessedResume(null);
      setAlert({
        type: 'error',
        message: err.message || 'Failed to process resume. Please verify the file and try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // View JSON from the upload form area
  const handleViewRecentJson = () => {
    if (!recentlyProcessedResume) return;

    const dataObj = recentlyProcessedResume.data || recentlyProcessedResume;
    const cleanDoc = { ...dataObj };
    delete cleanDoc._id;
    delete cleanDoc.created_at;

    setSelectedResume({
      id: recentlyProcessedResume.resume_id || recentlyProcessedResume.document_id,
      filename: recentlyProcessedResume.filename || recentlyProcessedResume.data?.metadata?.file_name || 'Resume',
      candidate_name: recentlyProcessedResume.data?.profile?.full_name,
    });
    setSelectedResumeJson(cleanDoc);
    setJsonViewerError(null);
    setIsLoadingJson(false);
    setIsJsonViewerOpen(true);
  };

  // View JSON from the history table (Actions column)
  const handleViewHistoryJson = async (documentId) => {
    const historyItem = uploadedResumes.find((r) => r.id === documentId);
    setSelectedResume({
      id: documentId,
      filename: historyItem?.filename || 'Resume',
      candidate_name: historyItem?.candidate_name,
    });
    setSelectedResumeJson(null); // Clear previous to prevent showing stale JSON
    setJsonViewerError(null);
    setIsLoadingJson(true);
    setLoadingHistoryDocId(documentId);
    setIsJsonViewerOpen(true);

    try {
      const fullDoc = await getResumeByIdApi(documentId);
      const cleanDoc = { ...fullDoc };
      delete cleanDoc._id;
      delete cleanDoc.created_at;
      setSelectedResumeJson(cleanDoc);
    } catch (err) {
      setJsonViewerError(`Failed to load resume details: ${err.message || 'Network error'}`);
    } finally {
      setIsLoadingJson(false);
      setLoadingHistoryDocId(null);
    }
  };

  const handleViewCustomJson = (customData, title) => {
    setSelectedResume({
      id: customData.id || customData._id || 'view',
      filename: title || 'JSON Document',
    });
    setSelectedResumeJson(customData);
    setJsonViewerError(null);
    setIsLoadingJson(false);
    setIsJsonViewerOpen(true);
  };

  const handleCloseJsonViewer = () => {
    setIsJsonViewerOpen(false);
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this resume? This will permanently remove the candidate record and all associated evaluations.')) {
      return;
    }
    try {
      await deleteResumeApi(documentId);
      if (
        recentlyProcessedResume &&
        (recentlyProcessedResume.resume_id === documentId ||
          recentlyProcessedResume.document_id === documentId)
      ) {
        setRecentlyProcessedResume(null);
      }
      setAlert({
        type: 'success',
        message: 'Resume record and associated evaluations deleted successfully.',
      });
      fetchResumes();
    } catch (err) {
      setAlert({
        type: 'error',
        message: `Failed to remove resume record: ${err.message}`,
      });
    }
  };

  return (
    <div className={`app-container ${activeMainTab === 'companies' ? 'app-container-wide' : ''}`}>
      <Header />

      {/* Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '0.6rem',
          margin: '0 auto 2rem',
          background: 'rgba(255, 255, 255, 0.75)',
          backdropFilter: 'blur(10px)',
          padding: '0.4rem',
          borderRadius: '9999px',
          width: 'fit-content',
          border: '1px solid #e2dcf4',
          boxShadow: '0 4px 16px rgba(102, 84, 232, 0.08)',
        }}
      >
        <button
          onClick={() => setActiveMainTab('resumes')}
          style={{
            padding: '0.6rem 1.4rem',
            borderRadius: '9999px',
            border: 'none',
            fontWeight: 700,
            fontSize: '0.92rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background:
              activeMainTab === 'resumes'
                ? 'linear-gradient(90deg, #6654e8 0%, #974bea 100%)'
                : 'transparent',
            color: activeMainTab === 'resumes' ? '#ffffff' : '#6b7280',
            boxShadow:
              activeMainTab === 'resumes'
                ? '0 2px 8px rgba(102, 84, 232, 0.35)'
                : 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>📄</span>
          <span>Candidate Resumes &amp; Upload</span>
        </button>

        <button
          onClick={() => setActiveMainTab('companies')}
          style={{
            padding: '0.6rem 1.4rem',
            borderRadius: '9999px',
            border: 'none',
            fontWeight: 700,
            fontSize: '0.92rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background:
              activeMainTab === 'companies'
                ? 'linear-gradient(90deg, #6654e8 0%, #974bea 100%)'
                : 'transparent',
            color: activeMainTab === 'companies' ? '#ffffff' : '#6b7280',
            boxShadow:
              activeMainTab === 'companies'
                ? '0 2px 8px rgba(102, 84, 232, 0.35)'
                : 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <span>🏢</span>
          <span>Company Recruitment Dashboard</span>
        </button>
      </div>

      {alert && (
        <StatusAlert
          type={alert.type}
          message={alert.message}
          onClose={() => setAlert(null)}
        />
      )}

      {activeMainTab === 'resumes' ? (
        <>
          <FileUpload
            onUpload={handleUpload}
            isLoading={isLoading}
            recentlyProcessedResume={recentlyProcessedResume}
            onViewRecentJson={handleViewRecentJson}
          />

          <UploadedResumesSection
            resumes={uploadedResumes}
            isLoading={isLoadingResumes}
            loadingDocId={loadingHistoryDocId}
            onRefresh={fetchResumes}
            onViewJson={handleViewHistoryJson}
            onDelete={handleDelete}
          />
        </>
      ) : (
        <CompanyDashboard onViewJson={handleViewCustomJson} />
      )}

      <RawJsonModal
        isOpen={isJsonViewerOpen}
        onClose={handleCloseJsonViewer}
        data={selectedResumeJson}
        isLoading={isLoadingJson}
        error={jsonViewerError}
        title={
          selectedResume?.filename
            ? selectedResume.filename.startsWith('Canonical') ||
              selectedResume.filename.startsWith('Company') ||
              selectedResume.filename.startsWith('Evaluation')
              ? selectedResume.filename
              : `Canonical JSON — ${selectedResume.filename}`
            : 'Canonical JSON Schema Object (MongoDB Format)'
        }
      />
    </div>
  );
}

