"""Resume section detector using regex, normalized headings, and contextual rules."""
import re
from typing import Dict, List, Tuple


class SectionDetector:
    # Normalized section patterns
    SECTION_PATTERNS = {
        "education": [
            r"^academic(?:s|\s+(?:background|qualifications?|records?|profile|details?|history|credentials?))?$",
            r"^educational?(?:\s+(?:qualifications?|background|details?|profile|history|credentials?))?$",
            r"^education(?:\s*(?:and|&|\/)\s*(?:qualifications?|academics?|training|credentials?|degrees?))?$",
            r"^academics?$",
            r"^degrees?(?:\s*(?:and|&)\s*qualifications?)?$",
            r"^qualifications?$",
            r"^studies$",
            r"^college\s+(?:and|&)?\s*school\s+education$",
            r"^formal\s+education$",
        ],
        "technical_skills": [
            r"^technical\s+skills?(?:\s*(?:and|&|\/)\s*(?:tools?|technolog(?:y|ies)|competenc(?:y|ies)|abilities))?$",
            r"^skills?(?:\s*(?:and|&|\/)\s*(?:technolog(?:y|ies)|tools?|frameworks?|abilities|competenc(?:y|ies)))?$",
            r"^technolog(?:y|ies)(?:\s*(?:and|&|\/)\s*(?:frameworks?|tools?|skills?))?$",
            r"^tools?(?:\s*(?:and|&|\/)\s*(?:technolog(?:y|ies)|skills?))?$",
            r"^core\s+(?:competenc(?:y|ies)|skills?|technical\s+skills?)$",
            r"^technical\s+(?:proficienc(?:y|ies)|competenc(?:y|ies)|expertise|stack)$",
            r"^tech\s+stack$",
            r"^areas?\s+of\s+expertise$",
            r"^programming\s+skills?$",
            r"^computer\s+skills?$",
            r"^it\s+skills?$",
            r"^software\s+skills?$",
            r"^professional\s+skills?$",
            r"^skill\s*set$",
            r"^key\s+skills?$",
        ],
        "projects": [
            r"^(?:(?:technical|academic|personal|key|major|relevant|notable|selected|coursework|capstone|software|engineering)\s*(?:and|&|\/|\+)?\s*)+projects?(?:\s*(?:and|&|\/)\s*(?:work|papers?|presentations?|portfolio|details?))?$",
            r"^projects?(?:\s*(?:and|&|\/)\s*(?:work|papers?|presentations?|portfolio|details?))?$",
            r"^project\s+work$",
            r"^projects?\s+undertaken$",
            r"^technical\s+projects?$",
            r"^academic\s*(?:and|&)\s*personal\s+projects?$",
        ],
        "experience": [
            r"^(?:work\s+|professional\s+|relevant\s+|industry\s+|career\s+|practical\s+)?experience(?:\s*(?:and|&|\/)\s*(?:internships?|employment|history))?$",
            r"^employment(?:\s+history)?$",
            r"^work\s+history$",
            r"^internships?(?:\s+experience)?$",
            r"^industry\s+experience$",
            r"^career\s+history$",
            r"^professional\s+background$",
            r"^experience\s*(?:and|&)\s*employment$",
            r"^work\s+experience\s*(?:and|&)\s*internships?$",
        ],
        "certifications": [
            r"^(?:licenses?\s*(?:&|and|\/)\s*)?certifications?(?:\s*(?:&|and|\/)\s*(?:licenses?|courses?|trainings?|(?:technical\s+)?achievements?|awards?))?$",
            r"^certificates?(?:\s*(?:and|&|\/)\s*(?:licenses?|courses?|trainings?|(?:technical\s+)?achievements?|awards?))?$",
            r"^certifications?\s*(?:and|&|\/)\s*(?:technical\s+)?achievements?$",
            r"^professional\s+certifications?$",
            r"^courses?\s*(?:&|and|\/)\s*certifications?$",
            r"^trainings?\s*(?:&|and|\/)\s*certifications?$",
            r"^credentials?$",
            r"^accreditations?$",
        ],
        "achievements": [
            r"^(?:honors?|honours?)\s*(?:&|and|\/)\s*awards?$",
            r"^awards?(?:\s*(?:&|and|\/)\s*(?:honors?|honours?|achievements?|recognitions?))?$",
            r"^achievements?(?:\s*(?:&|and|\/)\s*(?:accomplishments?|awards?|honors?|recognitions?|(?:technical\s+)?certifications?))?$",
            r"^(?:technical\s+)?achievements?(?:\s*(?:&|and|\/)\s*(?:certifications?|awards?|honors?))?$",
            r"^key\s+achievements?$",
            r"^accomplishments?$",
            r"^honors?$",
            r"^honours?$",
            r"^extra-?curricular\s+activities$",
            r"^co-?curricular\s+activities$",
            r"^extracurriculars?$",
            r"^activities\s*(?:and|&)\s*achievements?$",
            r"^recognitions?$",
        ],
        "summary": [
            r"^(?:professional\s+|career\s+|executive\s+|profile\s+)?summary$",
            r"^(?:career\s+|professional\s+)?objective$",
            r"^about\s+me$",
            r"^about$",
            r"^personal\s+profile$",
            r"^profile\s+summary$",
            r"^profile$",
        ],
    }

    @classmethod
    def clean_header_line(cls, line: str) -> str:
        """Strip markdown markers, underlines, colons, bullets, numbering, and emojis."""
        cleaned = line.strip()
        # Strip markdown headers (e.g. ###)
        cleaned = re.sub(r"^#+\s*", "", cleaned)
        # Strip bullets, stars, dashes, pipes, tildes, equals, and special symbols
        cleaned = re.sub(r"^[\*\-—~=_|•\s\u25aa\u25ab\u25fe\u25fd\u25cf\u25cb\u25c6\u25c7\u25ba\u25b6\u2713\u2714\u2705\u274c]+", "", cleaned)
        # Strip common emoji characters
        cleaned = re.sub(r"^[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\s]+", "", cleaned)
        # Strip numbering like "1. ", "1) ", "(1) ", "01. ", "I. ", "A. "
        cleaned = re.sub(r"^(?:[0-9]{1,2}[\.\)]|\([0-9]{1,2}\)|[IVXLCDMivxlcdm]+[\.\)]|[A-Za-z][\.\)])\s*", "", cleaned)
        # Strip trailing markers
        cleaned = re.sub(r"[:#\*\-—~=_|•\s]+$", "", cleaned)
        # If letters are spaced out like E D U C A T I O N, collapse
        if re.match(r"^(?:[A-Za-z]\s+){2,}[A-Za-z]$", cleaned):
            cleaned = re.sub(r"\s+", "", cleaned)
        return cleaned.strip()

    @classmethod
    def is_separator_line(cls, line: str) -> bool:
        """Check if line is purely an underline or divider (e.g. ---, ===, ___)."""
        stripped = line.strip()
        return bool(re.match(r"^[-=_~*•—]{2,}$", stripped))

    @classmethod
    def match_section_header(cls, line: str) -> Tuple[str, bool]:
        """Check if a line represents a known section header."""
        cleaned = cls.clean_header_line(line)
        if not cleaned:
            return "", False

        # Headings are usually concise (1-6 words, < 50 chars)
        words = cleaned.split()
        if len(words) > 6 or len(cleaned) > 50:
            return "", False

        lower_line = cleaned.lower()

        for section_name, patterns in cls.SECTION_PATTERNS.items():
            for pat in patterns:
                if re.match(pat, lower_line, re.IGNORECASE):
                    return section_name, True

        return "", False

    @classmethod
    def detect_inline_header(cls, line: str) -> Tuple[str, str, bool]:
        """Detect headers that have content on the same line, e.g. 'Technical Skills: Python, Java'."""
        cleaned = line.strip()
        for sep in [":", " - "]:
            if sep in cleaned:
                parts = cleaned.split(sep, 1)
                header_candidate = parts[0].strip()
                remainder = parts[1].strip()
                sec_name, is_hdr = cls.match_section_header(header_candidate)
                if is_hdr and remainder:
                    return sec_name, remainder, True
        return "", "", False

    @classmethod
    def partition_resume(cls, text: str) -> Dict[str, str]:
        """Split full resume text into classified sections."""
        lines = text.split("\n")
        sections: Dict[str, List[str]] = {
            "header_profile": [],
            "summary": [],
            "education": [],
            "technical_skills": [],
            "projects": [],
            "experience": [],
            "certifications": [],
            "achievements": [],
            "other": [],
        }

        current_section = "header_profile"

        for line in lines:
            # Skip pure divider/separator lines (e.g. --- or ===)
            if cls.is_separator_line(line):
                continue

            # First check for standalone section header
            detected_sec, is_header = cls.match_section_header(line)
            if is_header:
                # Disambiguate project/experience sub-attributes:
                # If currently inside projects or experience, sub-headings like "Tech Stack", "Tools", "Technologies", "Stack", "Environment"
                # belong to the current project/experience entry, NOT a switch back to global technical skills.
                if current_section in ("projects", "experience") and detected_sec == "technical_skills":
                    cleaned_sub = cls.clean_header_line(line).lower()
                    if re.match(r"^(?:tech\s+stack|tools?|technolog(?:y|ies)|stack|environment|key\s+technologies|technologies\s+used|tools\s+used)$", cleaned_sub):
                        sections[current_section].append(line)
                        continue

                current_section = detected_sec
                continue

            # Check for inline section header (e.g. "Technical Skills: Python, Java")
            inline_sec, remainder, is_inline = cls.detect_inline_header(line)
            if is_inline:
                # Disambiguate project/experience sub-attributes:
                # Lines like "Tech Stack: React, Node.js" or "Tools: Git" inside projects/experience belong to the project/experience entry!
                if current_section in ("projects", "experience") and inline_sec == "technical_skills":
                    sections[current_section].append(line)
                    continue

                # Also, inline technical skills should only trigger if the candidate is explicitly "technical skills" or "skills",
                # not sub-categories like "tools:" or "tech stack:".
                if inline_sec == "technical_skills":
                    hdr_candidate = line.split(":", 1)[0] if ":" in line else line.split(" - ", 1)[0]
                    hdr_clean = cls.clean_header_line(hdr_candidate).lower()
                    if not re.match(r"^(?:technical\s+)?skills?(?:\s*(?:and|&|\/)\s*technolog(?:y|ies))?$", hdr_clean):
                        sections[current_section].append(line)
                        continue

                current_section = inline_sec
                if current_section in sections:
                    sections[current_section].append(remainder)
                else:
                    sections["other"].append(remainder)
                continue

            # Regular content line
            if current_section in sections:
                sections[current_section].append(line)
            else:
                sections["other"].append(line)

        # Convert line lists to trimmed strings
        result: Dict[str, str] = {}
        for sec, sec_lines in sections.items():
            result[sec] = "\n".join(sec_lines).strip()

        return result
