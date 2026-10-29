# DEBUG_LOG.md
| Attempt | Hypothesis | Command / Action | Result |
|---|---|---|---|
| 1 | Baseline inspection of workspace structure and backend files | `ls backend/app && find backend/app -maxdepth 3 -name "*.py"` | Structure identified: company repository, routes, schema present. |
| 2 | Trailing commas in config.py field defaults | edit_file backend/app/core/config.py | Removed trailing commas from MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION |
| 3 | Real MongoDB Atlas connection vs mongomock silent fallback | BypassSandbox=True with real network | Connected successfully to pymongo MongoClient on Atlas (ping ok) |
| 4 | Company Form submission & raw DB read-back | POST /api/companies & raw find_one() | Saved ID 6ae1ea055b51b82b466ffc4b, raw read-back verified 100% field parity |
| 5 | Company update & no duplicate generation | PUT /api/companies/<id> & count_documents | Updated in-place, count remained 2, no duplicates |
| 6 | Server restart persistence | Killed and restarted uvicorn daemon & GET /api/companies/<id> | Persisted data returned intact with updated fields |
| 7 | Test cleanup & suite execution | pytest tests/ & DELETE /api/companies/<id> | 81/81 passed, test record cleanly removed, Epam System preserved |
| 8 | Candidate evaluation schema missing is_eligible boolean | edit_file app/schemas/evaluation_schema.py | Added is_eligible: bool and eligibility_status: str to evaluation schema |
| 9 | is_eligible and final decision rules implementation | edit_file app/services/evaluation_engine.py | Implemented is_eligible calculation, SELECTED/FAILED/REQUIRES_REVIEW decisions, and backlog criteria handling |
| 10 | Evaluation deduplication and list consistency | edit_file app/repositories/evaluation_repository.py | Set candidate_id as primary deduplication key in list_evaluations_for_company |
| 11 | Frontend Dashboard Selected/Failed/Review tabs and badges | edit_file frontend/src/components/CompanyDashboard/EvaluationResultsModal.jsx | Enhanced getStatusBadge, isCandidateSelected, and count tabs |
| 12 | Candidate classification verification on Atlas | POST /api/evaluations/evaluate | Evaluated 9 candidates: 1 Selected (Aayush), 8 Failed, invariant holds (1+8+0=9) |
