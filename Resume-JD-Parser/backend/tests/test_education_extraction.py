"""Automated regression test suite for education extraction and record association.

Covers all 11 required scenarios from the specification:
1. Degree and institution on separate lines.
2. CGPA appearing on the university line.
3. CGPA in format 8.78/10.0.
4. CGPA written without a grading scale.
5. Institution and CGPA successfully associated with the correct degree.
6. The parser does not create an extra CGPA-only education object.
7. Multiple legitimate education qualifications remain separate.
8. Class X and Class XII percentages are not mistaken for CGPA.
9. Missing CGPA remains null.
10. Numeric CGPA is preserved through Candidate JSON serialization.
11. Existing resume parsing and MongoDB persistence behavior remain compatible.
"""
import json
from unittest.mock import MagicMock, patch
import pytest

from app.schemas.resume_schema import (
    EducationItemSchema,
    ResumeCanonicalSchema,
    ProfileSchema,
    TechnicalSkillsSchema,
    ResumeMetadataSchema,
)
from app.services.deterministic_parser import DeterministicParser
from app.services.resume_service import ResumeService
from app.repositories.resume_repository import ResumeRepository
from app.services.text_extractor import TextExtractor


class TestEducationExtractionAndAssociation:
    """Test suite validating robust education parsing, record grouping, and CGPA extraction."""

    def test_01_user_reported_resume_single_unified_record(self):
        """User Context Resume Test:

        Bachelor of Technology (B.Tech) in Computer Science Engineering
        LNCT University, Bhopal, Madhya Pradesh — CGPA: 8.78/10.0
        Sep 2024 – Sep 2028

        Must produce exactly ONE record with all fields populated.
        """
        edu_text = """
        Bachelor of Technology (B.Tech) in Computer Science Engineering

        LNCT University, Bhopal, Madhya Pradesh — CGPA: 8.78/10.0

        Sep 2024 – Sep 2028
        """
        items = DeterministicParser.parse_education(edu_text)

        # Requirement 6: Exactly 1 record (no duplicate or CGPA-only object)
        assert len(items) == 1, f"Expected 1 education record, got {len(items)}"
        record = items[0]

        # Requirement 4 & 5: Institution correctly extracted without city/state
        assert record.institution == "LNCT University"
        assert record.degree == "B.Tech"
        assert record.specialization == "Computer Science Engineering"
        assert record.start_year == "2024"
        assert record.end_year == "2028"

        # Requirement 3: CGPA as numeric float and scale captured
        assert record.cgpa == 8.78
        assert isinstance(record.cgpa, float)
        assert record.cgpa_scale == 10.0
        assert isinstance(record.cgpa_scale, float)
        assert record.percentage is None

    def test_02_degree_and_institution_on_separate_lines(self):
        """1. Degree and institution on separate lines."""
        edu_text = """
        Bachelor of Technology in Information Technology
        Delhi Technological University
        2020 - 2024
        """
        items = DeterministicParser.parse_education(edu_text)
        assert len(items) == 1
        assert items[0].degree == "B.Tech"
        assert items[0].institution == "Delhi Technological University"
        assert items[0].start_year == "2020"
        assert items[0].end_year == "2024"
        assert items[0].cgpa is None

    def test_03_cgpa_appearing_on_university_line(self):
        """2. CGPA appearing on the university line."""
        edu_text = """
        Bachelor of Engineering in Electronics & Communication
        Thapar Institute of Engineering & Technology • CGPA: 8.92 / 10.0
        2019 - 2023
        """
        items = DeterministicParser.parse_education(edu_text)
        assert len(items) == 1
        assert items[0].degree == "B.E."
        assert "Thapar Institute of Engineering" in items[0].institution
        assert items[0].cgpa == 8.92
        assert items[0].cgpa_scale == 10.0

    def test_04_cgpa_format_with_slash_scale(self):
        """3. CGPA in the format 8.78/10.0 and out of scale variations."""
        text1 = "B.Tech, SRM University, CGPA: 8.78/10.0, 2020-2024"
        items1 = DeterministicParser.parse_education(text1)
        assert len(items1) == 1
        assert items1[0].cgpa == 8.78
        assert items1[0].cgpa_scale == 10.0

        text2 = "B.Sc in Computer Science\nManipal University\nCGPA: 8.78 out of 10\n2021 - 2024"
        items2 = DeterministicParser.parse_education(text2)
        assert len(items2) == 1
        assert items2[0].cgpa == 8.78
        assert items2[0].cgpa_scale == 10.0

    def test_05_cgpa_without_grading_scale(self):
        """4. CGPA written without a grading scale."""
        variations = [
            ("CGPA 8.78", 8.78),
            ("CGPA: 8.78", 8.78),
            ("C.G.P.A. 8.78", 8.78),
            ("8.78 CGPA", 8.78),
            ("Grade: 8.78", 8.78),
        ]
        for cgpa_str, expected_val in variations:
            edu_text = f"B.Tech in CSE\nLNCT University\n{cgpa_str}\n2020 - 2024"
            items = DeterministicParser.parse_education(edu_text)
            assert len(items) == 1, f"Failed for {cgpa_str}"
            assert items[0].cgpa == expected_val, f"Mismatch for {cgpa_str}"
            assert items[0].cgpa_scale is None, f"Expected None scale for {cgpa_str}"

    def test_06_institution_and_cgpa_associated_with_correct_degree(self):
        """5. Institution and CGPA successfully associated with the correct degree."""
        edu_text = """
        Master of Technology (M.Tech) in Software Engineering
        Indian Institute of Technology, Delhi — CGPA: 9.45 / 10.0
        2022 - 2024
        """
        items = DeterministicParser.parse_education(edu_text)
        assert len(items) == 1
        assert items[0].degree == "M.Tech"
        assert "Indian Institute of Technology" in items[0].institution
        assert items[0].cgpa == 9.45
        assert items[0].cgpa_scale == 10.0

    def test_07_no_extra_cgpa_only_education_object(self):
        """6. The parser does not create an extra CGPA-only education object."""
        # Separate blocks with empty lines or bullets
        edu_text = """
        • Bachelor of Technology in Mechanical Engineering
        • Indian Institute of Technology Bombay — CGPA: 8.65/10.0
        • 2018 - 2022
        """
        items = DeterministicParser.parse_education(edu_text)
        assert len(items) == 1
        assert items[0].degree == "B.Tech"
        assert items[0].institution == "Indian Institute of Technology Bombay"
        assert items[0].cgpa == 8.65
        # Ensure no second item was created
        assert not any(it.degree is None and it.cgpa is not None for it in items)

    def test_08_multiple_legitimate_education_qualifications_remain_separate(self):
        """7. Multiple legitimate education qualifications remain separate."""
        edu_text = """
        Bachelor of Technology (B.Tech) in Computer Science Engineering
        LNCT University, Bhopal, Madhya Pradesh — CGPA: 8.78/10.0
        Sep 2024 – Sep 2028

        Higher Secondary Certificate (Class XII)
        Delhi Public School, Bhopal
        Percentage: 88.4%
        2022 – 2024

        Secondary School Certificate (Class X)
        St. Joseph's Convent School, Bhopal
        Percentage: 91.2%
        2020 – 2022
        """
        items = DeterministicParser.parse_education(edu_text)
        assert len(items) == 3

        # Record 1: B.Tech
        btech = items[0]
        assert btech.degree == "B.Tech"
        assert btech.institution == "LNCT University"
        assert btech.cgpa == 8.78
        assert btech.cgpa_scale == 10.0
        assert btech.percentage is None

        # Record 2: Class XII
        class12 = items[1]
        assert "Class XII" in (class12.degree or "")
        assert "Delhi Public School" in class12.institution
        assert class12.percentage == "88.4%"
        assert class12.cgpa is None

        # Record 3: Class X
        class10 = items[2]
        assert "Class X" in (class10.degree or "")
        assert "St. Joseph's Convent" in class10.institution
        assert class10.percentage == "91.2%"
        assert class10.cgpa is None

    def test_09_class_x_and_xii_percentages_not_mistaken_for_cgpa(self):
        """8. Class X and Class XII percentages are not mistaken for CGPA."""
        edu_text = """
        Class XII (Senior Secondary)
        Kendriya Vidyalaya
        2022 | Score: 95.6%

        Class X (Secondary)
        Kendriya Vidyalaya
        2020 | Aggregate: 94.2%
        """
        items = DeterministicParser.parse_education(edu_text)
        assert len(items) == 2
        for it in items:
            assert it.cgpa is None
            assert it.percentage in ["95.6%", "94.2%"]

    def test_10_missing_cgpa_remains_null(self):
        """9. Missing CGPA remains null."""
        edu_text = """
        Bachelor of Science in Mathematics
        University of Delhi
        2019 - 2022
        """
        items = DeterministicParser.parse_education(edu_text)
        assert len(items) == 1
        assert items[0].cgpa is None
        assert items[0].cgpa_scale is None
        assert items[0].percentage is None

    def test_11_numeric_cgpa_preserved_in_canonical_serialization(self):
        """10. Numeric CGPA is preserved through Candidate JSON serialization."""
        item = EducationItemSchema(
            institution="LNCT University",
            degree="B.Tech",
            specialization="Computer Science Engineering",
            start_year="2024",
            end_year="2028",
            cgpa=8.78,
            cgpa_scale=10.0,
            percentage=None,
        )
        canonical = ResumeCanonicalSchema(
            profile=ProfileSchema(full_name="Aayush Rathore"),
            education=[item],
            technical_skills=TechnicalSkillsSchema(),
            metadata=ResumeMetadataSchema(
                filename="resume.pdf",
                file_hash="mockhash123",
                file_size_bytes=1024,
            ),
        )
        dumped = canonical.model_dump(mode="json")
        edu_json = dumped["education"][0]

        # Verify exact target types and keys
        assert edu_json["institution"] == "LNCT University"
        assert edu_json["degree"] == "B.Tech"
        assert edu_json["specialization"] == "Computer Science Engineering"
        assert edu_json["start_year"] == "2024"
        assert edu_json["end_year"] == "2028"
        assert edu_json["cgpa"] == 8.78
        assert isinstance(edu_json["cgpa"], float)
        assert edu_json["cgpa_scale"] == 10.0
        assert isinstance(edu_json["cgpa_scale"], float)
        assert edu_json["percentage"] is None

        # Verify JSON round-trip
        json_str = json.dumps(dumped)
        reloaded = json.loads(json_str)
        assert reloaded["education"][0]["cgpa"] == 8.78

    def test_12_end_to_end_resume_parsing_and_persistence(self):
        """11. Existing resume parsing and MongoDB persistence behavior remain compatible."""
        resume_raw = """
        Aayush Rathore
        aayush@example.com | +91 9876543210
        Bhopal, Madhya Pradesh, India
        linkedin.com/in/aayushrathore
        github.com/aayushrathore

        EDUCATION
        Bachelor of Technology (B.Tech) in Computer Science Engineering
        LNCT University, Bhopal, Madhya Pradesh — CGPA: 8.78/10.0
        Sep 2024 – Sep 2028

        TECHNICAL SKILLS
        Languages: Python, JavaScript, SQL
        Tools: Git, Docker
        """
        mock_repo = MagicMock(spec=ResumeRepository)
        mock_repo.find_by_file_hash.return_value = None
        mock_repo.insert_resume.return_value = "doc_lnct_123"
        service = ResumeService(repository=mock_repo)

        with patch.object(TextExtractor, "extract_text", return_value={
            "text": resume_raw,
            "is_scanned": False,
            "page_count": 1,
            "file_hash": "lnct_file_hash_123",
            "file_size": 2048,
        }):
            res = service.process_resume("lnct_resume.pdf", b"%PDF-mock-bytes")

        assert res.success is True
        assert res.saved is True
        assert res.resume_id == "doc_lnct_123"
        assert len(res.data.education) == 1

        edu = res.data.education[0]
        assert edu.institution == "LNCT University"
        assert edu.degree == "B.Tech"
        assert edu.specialization == "Computer Science Engineering"
        assert edu.cgpa == 8.78
        assert edu.cgpa_scale == 10.0
        assert edu.start_year == "2024"
        assert edu.end_year == "2028"

        # Verify MongoDB insert was called with the document
        mock_repo.insert_resume.assert_called_once()
        saved_doc = mock_repo.insert_resume.call_args[0][0]
        assert saved_doc["education"][0]["institution"] == "LNCT University"
        assert saved_doc["education"][0]["cgpa"] == 8.78
        assert saved_doc["education"][0]["cgpa_scale"] == 10.0
