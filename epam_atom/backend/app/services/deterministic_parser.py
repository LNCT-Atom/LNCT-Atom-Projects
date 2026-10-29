"""Deterministic resume parser for Profile, Education, Technical Skills, Certifications, and Achievements.

STRICT RULE: AI must NOT be used for these 5 sections. All parsing is deterministic,
rule-based, regex-driven, and dictionary-assisted.
"""
import re
from typing import Any, Dict, List, Optional, Tuple, Set
from app.schemas.resume_schema import (
    ProfileSchema,
    EducationItemSchema,
    TechnicalSkillsSchema,
    CertificationItemSchema,
    AchievementItemSchema,
)
from app.services.text_cleaner import clean_text, clean_institution


class DeterministicParser:
    # ------------------ SKILLS DICTIONARIES ------------------
    LANGUAGES = {
        "python", "java", "c++", "c", "c#", "javascript", "typescript", "go", "golang",
        "rust", "kotlin", "swift", "php", "ruby", "r", "dart", "scala", "perl", "sql",
        "html", "html5", "css", "css3", "bash", "shell", "powershell", "assembly", "matlab",
        "solidity", "lua", "haskell", "clojure", "elixir", "erlang", "vba", "cobol", "fortran"
    }

    FRAMEWORKS = {
        "react", "react.js", "reactjs", "angular", "angularjs", "vue", "vue.js", "vuejs",
        "next.js", "nextjs", "nuxt", "nuxt.js", "node.js", "nodejs", "express", "express.js",
        "django", "fastapi", "flask", "spring", "spring boot", "asp.net", ".net", "dotnet",
        "flutter", "react native", "bootstrap", "tailwind", "tailwindcss", "pytorch",
        "tensorflow", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "graphql",
        "rest api", "redux", "svelte", "sveltekit", "jquery", "laravel", "ruby on rails",
        "rails", "nestjs", "fastify", "electron", "ionic", "hibernate", "gin", "echo"
    }

    DATABASES = {
        "mongodb", "mysql", "postgresql", "postgres", "sqlite", "redis", "oracle",
        "cassandra", "dynamodb", "elasticsearch", "firebase", "mariadb", "couchdb",
        "neo4j", "ms sql server", "sql server", "supabase", "cockroachdb", "snowflake",
        "bigquery", "faunadb", "realm"
    }

    TOOLS = {
        "git", "github", "gitlab", "docker", "kubernetes", "k8s", "aws", "amazon web services",
        "azure", "gcp", "google cloud", "linux", "jenkins", "jira", "postman", "figma",
        "vs code", "visual studio code", "intellij", "eclipse", "webpack", "vite",
        "ci/cd", "terraform", "ansible", "nginx", "apache", "maven", "gradle", "npm", "yarn",
        "pnpm", "travis ci", "circleci", "prometheus", "grafana", "splunk", "datadog",
        "bitbucket", "kafka", "rabbitmq"
    }

    # ------------------ EDUCATION CONSTANTS ------------------
    DEGREE_PATTERNS = [
        (r"\b(b\.?\s?tech(?:nology)?|bachelor\s+of\s+technology)\b", "B.Tech"),
        (r"\b(b\.?\s?e\.?|bachelor\s+of\s+engineering)\b", "B.E."),
        (r"\b(b\.?\s?c\.?\s?a\.?|bachelor\s+of\s+computer\s+applications?)\b", "BCA"),
        (r"\b(m\.?\s?c\.?\s?a\.?|master\s+of\s+computer\s+applications?)\b", "MCA"),
        (r"\b(m\.?\s?tech(?:nology)?|master\s+of\s+technology)\b", "M.Tech"),
        (r"\b(m\.?\s?e\.?|master\s+of\s+engineering)\b", "M.E."),
        (r"\b(b\.?\s?sc\.?|bachelor\s+of\s+science|b\.?\s?s\.?)\b", "B.Sc"),
        (r"\b(m\.?\s?sc\.?|master\s+of\s+science|m\.?\s?s\.?)\b", "M.Sc"),
        (r"\b(m\.?\s?b\.?\s?a\.?|master\s+of\s+business\s+administration)\b", "MBA"),
        (r"\b(b\.?\s?b\.?\s?a\.?|bachelor\s+of\s+business\s+administration)\b", "BBA"),
        (r"\b(b\.?\s?com\.?|bachelor\s+of\s+commerce)\b", "B.Com"),
        (r"\b(b\.?\s?a\.?|bachelor\s+of\s+arts)\b", "B.A."),
        (r"\b(class\s+(?:xii|12)\b|12th(?:\s+grade|\s+standard)?|higher\s+secondary(?:\s+school)?|senior\s+secondary(?:\s+school)?|hsc\b|cbse\s+(?:xii|12)|icse\s+(?:xii|12)|intermediate|aissce)\b", "Class XII / Higher Secondary"),
        (r"\b(class\s+(?:x\b|10\b)|10th(?:\s+grade|\s+standard)?|secondary\s+school(?:\s+certificate)?|ssc\b|cbse\s+(?:x|10)|icse\s+(?:x|10)|matriculation|aisse|high\s+school(?:\s+diploma|\s+certificate))\b", "Class X / Secondary"),
        (r"\b(diploma(?:\s+in\s+[\w\s]+)?)\b", "Diploma"),
        (r"\b(ph\.?\s?d\.?|doctor\s+of\s+philosophy|doctorate)\b", "Ph.D"),
    ]

    INSTITUTION_KEYWORDS = [
        "university", "institute", "college", "school", "academy", "polytechnic",
        "vidyalaya", "iit", "nit", "iiit", "bits", "campus", "faculty", "dtu", "nsut",
        "iiest", "coep", "vjti", "bhu", "amu", "vit", "srm", "thapar", "manipal",
        "technological institute", "technology", "engineering college"
    ]

    SPECIALIZATION_KEYWORDS = [
        "computer science and engineering", "computer science & engineering",
        "computer science engineering", "computer science",
        "information technology and engineering", "information technology & engineering",
        "information technology", "data science", "artificial intelligence",
        "machine learning", "electronics and communication engineering",
        "electronics & communication engineering", "electronics and communication",
        "electronics & communication", "electrical and electronics engineering",
        "electrical & electronics engineering", "electrical engineering",
        "mechanical engineering", "civil engineering", "aerospace engineering",
        "chemical engineering", "software engineering", "cyber security",
        "mathematics and computing", "mathematics", "applied science",
        "cse", "it", "ece", "eee", "mech", "civil", "ai & ml", "ai/ml"
    ]

    LOCATION_TOKENS = {
        # Indian Cities
        "bhopal", "indore", "pune", "mumbai", "delhi", "new delhi", "bengaluru", "bangalore",
        "hyderabad", "chennai", "kolkata", "noida", "gurgaon", "gurugram", "jaipur", "lucknow",
        "ahmedabad", "chandigarh", "kochi", "patna", "nagpur", "kanpur", "thane", "visakhapatnam",
        "vadodara", "ghaziabad", "ludhiana", "agra", "nashik", "faridabad", "meerut", "rajkot",
        "varanasi", "srinagar", "aurangabad", "dhanbad", "amritsar", "navi mumbai", "allahabad",
        "prayagraj", "howrah", "ranchi", "gwalior", "jabalpur", "coimbatore", "vijayawada", "jodhpur",
        "madurai", "raipur", "kota", "guwahati", "solapur", "hubli", "mysore", "tiruchirappalli",
        # Indian States & UTs
        "madhya pradesh", "uttar pradesh", "maharashtra", "karnataka", "tamil nadu", "andhra pradesh",
        "telangana", "gujarat", "rajasthan", "west bengal", "kerala", "punjab", "haryana", "bihar",
        "odisha", "assam", "jharkhand", "chhattisgarh", "uttarakhand", "himachal pradesh", "tripura",
        "meghalaya", "manipur", "nagaland", "goa", "arunachal pradesh", "mizoram", "sikkim",
        "jammu and kashmir", "ladakh", "puducherry",
        # Global
        "india", "usa", "uk", "canada", "germany", "singapore", "australia", "california", "new york",
        "texas", "massachusetts", "washington", "london", "toronto", "boston", "seattle", "austin", "san francisco"
    }

    KNOWN_ISSUERS = [
        "AWS", "Amazon Web Services", "Google Cloud", "Google", "Microsoft", "Azure",
        "IBM", "Oracle", "Cisco", "HackerRank", "Coursera", "Udemy", "edX", "Meta",
        "DeepLearning.AI", "Stanford", "Harvard", "freeCodeCamp", "Postman", "MongoDB",
        "NPTEL", "Udacity", "LinkedIn Learning", "Kaggle", "EPAM", "EPAM Systems",
        "Databricks", "Linux Foundation", "Red Hat", "HashiCorp"
    ]

    # ------------------ PROFILE EXTRACTION ------------------
    @classmethod
    def parse_profile(cls, header_text: str, summary_text: str, full_text: str) -> ProfileSchema:
        """Deterministically extract candidate profile without AI."""
        profile = ProfileSchema()

        # 1. Email extraction
        email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", full_text)
        if email_match:
            profile.email = email_match.group(0).strip()

        # 2. Phone extraction (supports +91, dashes, spaces, parentheses)
        phone_patterns = [
            r"(?:\+?91[\s.-]?)?[6-9]\d{4}[\s.-]?\d{5}\b",
            r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
            r"\+?\d{1,3}[\s.-]\d{3,4}[\s.-]\d{3,4}[\s.-]?\d{3,4}\b",
            r"\b[6-9]\d{9}\b",
        ]
        for pat in phone_patterns:
            phone_match = re.search(pat, header_text or full_text)
            if phone_match:
                cleaned_phone = phone_match.group(0).strip()
                if len(re.sub(r"\D", "", cleaned_phone)) >= 10:
                    profile.phone = cleaned_phone
                    break

        # 3. LinkedIn URL (support usernames with letters, digits, underscores, dashes, dots)
        linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_\-\.]+)/?", full_text, re.IGNORECASE)
        if linkedin_match:
            url = linkedin_match.group(0).strip()
            profile.linkedin_url = url if url.startswith("http") else f"https://{url}"

        # 4. GitHub URL
        github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)/?", full_text, re.IGNORECASE)
        if github_match:
            url = github_match.group(0).strip()
            profile.github_url = url if url.startswith("http") else f"https://{url}"

        # 5. Portfolio URL (personal site or developer portfolio)
        portfolio_match = re.search(
            r"\bhttps?://(?!www\.linkedin\.com|www\.github\.com|linkedin\.com|github\.com|gmail\.com)([a-zA-Z0-9.\-_]+\.[a-zA-Z]{2,4}(?:/[^\s]*)?)\b",
            header_text or full_text,
            re.IGNORECASE
        )
        if portfolio_match:
            profile.portfolio_url = portfolio_match.group(0).strip()
        else:
            # Check for portfolio handles like *.github.io, *.vercel.app, *.netlify.app without https
            dev_domain_match = re.search(
                r"\b([a-zA-Z0-9_\-]+\.(?:github\.io|vercel\.app|netlify\.app|dev|me))\b",
                header_text or full_text,
                re.IGNORECASE
            )
            if dev_domain_match:
                profile.portfolio_url = f"https://{dev_domain_match.group(1).strip()}"

        # 6. Candidate Name
        profile.full_name = cls._extract_name(header_text, full_text)

        # 7. Location
        profile.location = cls._extract_location(header_text or full_text)

        # 8. Summary / Objective
        if summary_text and summary_text.strip():
            profile.summary = clean_text(summary_text.strip())
        else:
            profile.summary = None

        return profile

    @classmethod
    def _extract_name(cls, header_text: str, full_text: str = "") -> Optional[str]:
        """Extract candidate full name using position, structure, and name heuristics."""
        # Check header_text first; if empty or no name found, fallback to top lines of full_text
        candidate_lines = []
        if header_text and header_text.strip():
            candidate_lines.extend([l.strip() for l in header_text.split("\n") if l.strip()])
        if not candidate_lines and full_text and full_text.strip():
            candidate_lines.extend([l.strip() for l in full_text.split("\n") if l.strip()][:6])

        for line in candidate_lines[:5]:
            # Skip contact lines and section titles
            lower_l = line.lower()
            if any(term in lower_l for term in [
                "resume", "curriculum", "cv", "email", "phone", "github", "linkedin",
                "http", "@", "www.", ".com", "portfolio", "address", "contact"
            ]):
                continue

            # Candidate line might have name followed by separator, e.g. "Rahul Sharma | Software Engineer"
            name_candidate = line
            for sep in ["|", " - ", ",", "•"]:
                if sep in name_candidate:
                    name_candidate = name_candidate.split(sep)[0].strip()

            cleaned = re.sub(r"[^\w\s\.]", "", name_candidate).strip()
            words = cleaned.split()

            # Names are usually 2 to 4 alphabetic words
            if 2 <= len(words) <= 4:
                if all(w.replace(".", "").isalpha() for w in words):
                    return " ".join(words)
            elif len(words) == 1 and words[0].isalpha() and len(words[0]) > 2:
                # Single name (e.g. John)
                return words[0]

        return None

    @classmethod
    def _extract_location(cls, text: str) -> Optional[str]:
        """Extract candidate location / city from header using patterns."""
        if not text:
            return None

        # Common location patterns evaluated per-line to prevent crossing newlines
        loc_patterns = [
            r"\b([A-Z][a-zA-Z]+(?:[ \t]+[A-Z][a-zA-Z]+)?),\s*([A-Z][a-zA-Z]+|India|USA|UK|Canada|Germany|Singapore)\b",
            r"\b([A-Z][a-zA-Z]+)\s*-\s*([0-9]{6})\b",  # Indian PIN code
            r"\b([A-Z][a-zA-Z]+),\s*([A-Z]{2})\s*([0-9]{5})\b",  # US State and ZIP
        ]

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines:
            for pat in loc_patterns:
                match = re.search(pat, line)
                if match:
                    cand = match.group(0).strip()
                    cand = re.sub(r"^[•\-\*,\s|~]+|[•\-\*,\s|~]+$", "", cand).strip()
                    if len(cand) > 3:
                        return cand

        # Check for major cities line by line
        cities = [
            "Bengaluru", "Bangalore", "Hyderabad", "Pune", "Mumbai", "Delhi", "New Delhi",
            "Noida", "Gurugram", "Gurgaon", "Chennai", "Kolkata", "Ahmedabad", "Jaipur",
            "Chandigarh", "Lucknow", "Indore", "Bhopal", "Kochi", "Patna", "San Francisco",
            "New York", "London", "Toronto", "Seattle", "Austin", "Boston"
        ]
        for line in lines:
            for city in cities:
                if re.search(rf"\b{re.escape(city)}\b", line, re.IGNORECASE):
                    # Check if line contains "City, State, Country" or "City, Country"
                    parts = [p.strip() for p in re.split(r"[•|~]", line) if p.strip()]
                    for p in parts:
                        if re.search(rf"\b{re.escape(city)}\b", p, re.IGNORECASE) and len(p) < 40:
                            clean_p = re.sub(r"^[•\-\*,\s|~]+|[•\-\*,\s|~]+$", "", p).strip()
                            return clean_p
                    return city

        return None

    # ------------------ EDUCATION EXTRACTION ------------------
    @classmethod
    def parse_education(cls, education_text: str, full_text: str = "") -> List[EducationItemSchema]:
        """Extract all educational qualifications deterministically.

        Extracts: institution, degree, specialization, start_year, end_year, cgpa, cgpa_scale, percentage.
        Supports multiple education entries, table rows, and structured lists.
        CGPA and percentage are preserved as separate fields without conversion.
        Associates related education lines (degree, institution, cgpa, duration) into single unified records.
        Maps school records (Class 10/12) into primary higher-education entry and stores audit records.
        """
        if not education_text or not education_text.strip():
            return []

        # 1. Partition into distinct qualification blocks
        blocks = cls._split_education_blocks(education_text)

        raw_items: List[EducationItemSchema] = []
        for block in blocks:
            b_text = block.strip()
            if not b_text or len(b_text) < 4:
                continue

# Disabled aggressive skip to allow Class 10/12 entries to be parsed


            item = cls._parse_single_education_block(b_text)
            if item and (item.degree or item.institution or item.start_year or item.cgpa is not None or item.percentage):
                raw_items.append(item)

        # 2. Contextual Association & Consolidation of fragmented records
        entries = cls._associate_education_records(raw_items, education_text)

        # Fallback: single pass if no entries were identified
        if not entries and education_text.strip():
            single_item = cls._parse_single_education_block(education_text)
            if single_item and (single_item.degree or single_item.institution or single_item.start_year or single_item.cgpa is not None or single_item.percentage):
                entries.append(single_item)

        # 3. Map school entries into primary higher education entry
        mapped_entries, raw_school = cls.map_school_entries(entries, full_text=full_text or education_text)
        cls.last_raw_school_entries = raw_school
        return mapped_entries

    @classmethod
    def _get_degree_tier(cls, degree: Optional[str]) -> Optional[str]:
        """Classify degree into broad tier to prevent improper merging."""
        if not degree:
            return None
        deg_lower = degree.lower()
        if any(k in deg_lower for k in ["class xii", "class 12", "12th", "higher secondary", "senior secondary", "hsc", "intermediate"]):
            return "CLASS_12"
        if any(k in deg_lower for k in ["class x", "class 10", "10th", "secondary school", "ssc", "matriculation", "high school"]):
            return "CLASS_10"
        if "diploma" in deg_lower:
            return "DIPLOMA"
        if any(k in deg_lower for k in ["ph.d", "doctorate", "doctor of philosophy"]):
            return "DOCTORATE"
        if any(k in deg_lower for k in ["m.tech", "m.e.", "mca", "m.sc", "mba", "master"]):
            return "PG"
        if any(k in deg_lower for k in ["b.tech", "b.e.", "bca", "b.sc", "b.com", "bba", "b.a.", "bachelor"]):
            return "UG"
        return "OTHER"

    INDIAN_CITIES = {
        "bhopal", "indore", "pune", "mumbai", "delhi", "new delhi", "bengaluru", "bangalore",
        "hyderabad", "chennai", "kolkata", "noida", "gurgaon", "gurugram", "jaipur", "lucknow",
        "ahmedabad", "chandigarh", "kochi", "patna", "nagpur", "kanpur", "thane", "visakhapatnam",
        "vadodara", "ghaziabad", "ludhiana", "agra", "nashik", "faridabad", "meerut", "rajkot",
        "varanasi", "srinagar", "aurangabad", "dhanbad", "amritsar", "navi mumbai", "allahabad",
        "prayagraj", "howrah", "ranchi", "gwalior", "jabalpur", "coimbatore", "vijayawada", "jodhpur",
        "madurai", "raipur", "kota", "guwahati", "solapur", "hubli", "mysore", "tiruchirappalli",
    }

    INDIAN_STATES = {
        "madhya pradesh", "uttar pradesh", "maharashtra", "karnataka", "tamil nadu", "andhra pradesh",
        "telangana", "gujarat", "rajasthan", "west bengal", "kerala", "punjab", "haryana", "bihar",
        "odisha", "assam", "jharkhand", "chhattisgarh", "uttarakhand", "himachal pradesh", "tripura",
        "meghalaya", "manipur", "nagaland", "goa", "arunachal pradesh", "mizoram", "sikkim",
        "jammu and kashmir", "ladakh", "puducherry",
    }

    @classmethod
    def _clean_institution_name(cls, text: str) -> Optional[str]:
        """Extract and clean institution name from a text block, stripping city/state/country/CGPA."""
        if not text:
            return None

        # Break by line or major delimiters
        raw_parts = [p.strip() for p in text.split("\n") if p.strip()]
        for line in raw_parts:
            # Strip leading bullets or list numbering
            line_clean = re.sub(r"^[•\-\*\d+\.\s]+", "", line).strip()

            # Split by dash/separator or bullets
            # Handles " — ", " – ", " - ", "|", "•", "~", ";"
            sub_parts = re.split(r"\s*[•|–—~]\s*|\s+-\s+|\s*;\s*", line_clean)

            for part in sub_parts:
                sp = part.strip()
                if not sp:
                    continue

                # Strip any trailing CGPA / percentage clause from part
                sp_clean = re.sub(
                    r"\b(?:cgpa|gpa|c\.g\.p\.a\.?|grade|percentage|marks?|aggregate)[:\s]*[0-9].*$",
                    "",
                    sp,
                    flags=re.IGNORECASE
                ).strip()
                # Strip bare trailing percentage or CGPA e.g. "PCM Senior Secondary School 87.4%" -> "PCM Senior Secondary School"
                sp_clean = re.sub(
                    r"\s*,?\s*\(?(?:(?:[0-9]{1,2}(?:\.[0-9]{1,2})?\s*%)|(?:[0-9](?:\.[0-9]{1,2})?\s*(?:/\s*10|cgpa|gpa)))\)?\s*$",
                    "",
                    sp_clean,
                    flags=re.IGNORECASE
                ).strip()
                sp_clean = re.sub(r"^[,\-–—:\s]+|[,\-–—:\s]+$", "", sp_clean).strip()

                lower_sp = sp_clean.lower()
                if not any(kw in lower_sp for kw in cls.INSTITUTION_KEYWORDS):
                    continue

                # Check if this line starts with a degree declaration
                is_degree = False
                for pat, _ in cls.DEGREE_PATTERNS:
                    clean_pat = pat.lstrip(r"\b")
                    if re.match(clean_pat, sp_clean, re.IGNORECASE):
                        is_degree = True
                        break
                if is_degree:
                    # If this line contains an institution keyword, separate the degree and specialization from the institution
                    if any(kw in lower_sp for kw in cls.INSTITUTION_KEYWORDS):
                        temp_sp = sp_clean
                        for pat, _ in cls.DEGREE_PATTERNS:
                            temp_sp = re.sub(pat, "", temp_sp, flags=re.IGNORECASE)
                        temp_sp = re.sub(r"\b(?:in|with|major\s+in|specialization\s+in|branch:?)\b", "", temp_sp, flags=re.IGNORECASE)
                        for spec in sorted(cls.SPECIALIZATION_KEYWORDS, key=len, reverse=True):
                            temp_sp = re.sub(rf"\b{re.escape(spec)}\b", "", temp_sp, flags=re.IGNORECASE)
                        # Strip dangling parentheses left after removing degree patterns like "(High School)"
                        temp_sp = re.sub(r"\(\s*\)", "", temp_sp)
                        temp_sp = re.sub(r"^[,\-–—:\s|~()]+|[,\-–—:\s|~()]+$", "", temp_sp).strip()
                        if any(kw in temp_sp.lower() for kw in cls.INSTITUTION_KEYWORDS) and len(temp_sp) >= 4:
                            sp_clean = temp_sp
                        else:
                            continue
                    else:
                        continue

                # Skip common metadata noise
                if any(kw in lower_sp for kw in ["certificate", "examination", "passing year", "graduation:"]):
                    continue

                # Clean city and state text appearing alongside institution name
                # E.g. "LNCT University, Bhopal, Madhya Pradesh" -> "LNCT University"
                # E.g. "LNCT University, Bhopal, MP" -> "LNCT University"
                tokens = [t.strip() for t in sp_clean.split(",") if t.strip()]
                if len(tokens) >= 2:
                    first_token = tokens[0]
                    first_lower = first_token.lower()
                    if any(kw in first_lower for kw in cls.INSTITUTION_KEYWORDS) and len(first_token) >= 4:
                        trailing_lower = [t.lower().strip() for t in tokens[1:]]
                        has_city = any(t in cls.INDIAN_CITIES for t in trailing_lower)
                        has_state = (
                            any(t in cls.INDIAN_STATES for t in trailing_lower) or
                            any(t in ["mp", "up", "ap", "tn", "mh", "dl", "wb", "rj", "gj"] for t in trailing_lower)
                        )
                        if has_city and has_state:
                            sp_clean = first_token

                if len(sp_clean) >= 4:
                    return sp_clean

        return None

    @classmethod
    def _extract_cgpa_and_scale(cls, text: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract numeric CGPA and optional grading scale from text deterministically.

        Supports:
        - CGPA: 8.78/10.0
        - CGPA 8.78
        - CGPA: 8.78
        - C.G.P.A. 8.78
        - CGPA: 8.78 out of 10
        - 8.78 / 10
        - 8.78 CGPA
        """
        if not text:
            return None, None

        # 1. Explicit keyword followed by score and optional scale
        m1 = re.search(
            r"\b(?:cgpa|c\.g\.p\.a\.?|gpa|grade)[:\s]*([0-9](?:\.[0-9]{1,2})?)\s*(?:(?:\/|\bout\s+of\b)\s*([0-9]+(?:\.[0-9]+)?))?\b",
            text,
            re.IGNORECASE
        )
        if m1:
            cgpa_val = float(m1.group(1))
            scale_val = float(m1.group(2)) if m1.group(2) else None
            return round(cgpa_val, 2), (round(scale_val, 1) if scale_val else None)

        # 2. Score followed by slash scale e.g. "9.15 / 10", "8.78/10.0", "3.8/4.0"
        m2 = re.search(
            r"\b([0-9](?:\.[0-9]{1,2})?)\s*(?:\/|\bout\s+of\b)\s*(10(?:\.0)?|4(?:\.0)?)\b",
            text,
            re.IGNORECASE
        )
        if m2:
            cgpa_val = float(m2.group(1))
            scale_val = float(m2.group(2))
            return round(cgpa_val, 2), round(scale_val, 1)

        # 3. Score followed by trailing CGPA/GPA e.g. "8.78 CGPA"
        m3 = re.search(
            r"\b([0-9](?:\.[0-9]{1,2})?)\s*(?:cgpa|gpa|c\.g\.p\.a\.?)\b",
            text,
            re.IGNORECASE
        )
        if m3:
            cgpa_val = float(m3.group(1))
            return round(cgpa_val, 2), None

        return None, None

    @classmethod
    def _extract_percentage(cls, text: str) -> Optional[str]:
        """Extract percentage deterministically without conversion."""
        if not text:
            return None
        pct_match = re.search(
            r"(?:percentage|marks?|aggregate|score)?[:\s]*([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*%",
            text,
            re.IGNORECASE
        )
        if pct_match:
            return f"{pct_match.group(1).strip()}%"

        pct_word_match = re.search(
            r"\b(?:percentage|marks?|aggregate)[:\s]*([5-9][0-9](?:\.[0-9]{1,2})?)\b",
            text,
            re.IGNORECASE
        )
        if pct_word_match:
            return f"{pct_word_match.group(1).strip()}%"

        return None

    @classmethod
    def _extract_years(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract start and end years handling ranges, month names, and Present."""
        if not text:
            return None, None

        # Check year range e.g. "Sep 2024 - Sep 2028", "2020 - 2024", "2021 to Present"
        range_match = re.search(
            r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*)?(20\d{2}|19\d{2})\s*(?:-|–|—|to)\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*)?(20\d{2}|19\d{2}|Present|Current|Expected)\b",
            text,
            re.IGNORECASE
        )
        if range_match:
            return range_match.group(1).strip(), range_match.group(2).strip()

        # Fallback to finding 4-digit years
        single_years = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
        if len(single_years) >= 2:
            return single_years[0], single_years[1]
        elif len(single_years) == 1:
            return None, single_years[0]

        return None, None

    @classmethod
    def _split_education_blocks(cls, text: str) -> List[str]:
        """Partition education text into distinct qualification blocks.

        Preserves multi-line qualifications where degree, institution, duration, and CGPA
        are on separate lines or separated by double newlines or bullets.
        """
        # 1. Pipe-delimited table detection
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        pipe_lines = [l for l in lines if "|" in l]
        if len(pipe_lines) >= 2 and len(pipe_lines) >= len(lines) * 0.5:
            return pipe_lines

        # 2. Divide by double newlines if present, else by lines
        raw_chunks = re.split(r"\n\s*\n", text) if "\n\n" in text else lines
        raw_chunks = [c.strip() for c in raw_chunks if c.strip()]

        # 2b. If any double-newline chunk itself contains multiple degree-bearing lines,
        #     expand it into its constituent lines so each can be split independently.
        expanded_chunks: List[str] = []
        for chunk in raw_chunks:
            chunk_lines = [l.strip() for l in chunk.split("\n") if l.strip()]
            if len(chunk_lines) <= 1:
                expanded_chunks.append(chunk)
                continue
            # Count lines that carry a degree keyword
            degree_bearing = []
            for cl in chunk_lines:
                for pat, _ in cls.DEGREE_PATTERNS:
                    if re.search(pat, cl, re.IGNORECASE):
                        degree_bearing.append(cl)
                        break
            # If 2+ distinct-degree lines exist inside one double-newline chunk,
            # treat each line independently (spaced-column table format).
            if len(degree_bearing) >= 2:
                expanded_chunks.extend(chunk_lines)
            else:
                expanded_chunks.append(chunk)
        raw_chunks = expanded_chunks

        blocks: List[str] = []
        current_chunk: List[str] = []

        for chunk in raw_chunks:
            # Detect degree in chunk
            chunk_degree = None
            for pat, deg_name in cls.DEGREE_PATTERNS:
                if re.search(pat, chunk, re.IGNORECASE):
                    chunk_degree = deg_name
                    break

            is_numbered_item = bool(re.match(r"^[0-9]{1,2}[\.\)]\s+", chunk))

            # Detect degree in current block
            curr_degree = None
            if current_chunk:
                curr_text = "\n".join(current_chunk)
                for pat, deg_name in cls.DEGREE_PATTERNS:
                    if re.search(pat, curr_text, re.IGNORECASE):
                        curr_degree = deg_name
                        break

            should_split = False
            if current_chunk:
                if is_numbered_item:
                    should_split = True
                elif chunk_degree and curr_degree:
                    # Both have degrees - separate qualifications!
                    should_split = True
                elif not chunk_degree and curr_degree:
                    # Current block already has degree, chunk has no degree.
                    # Check if chunk has a new institution when current already has an institution
                    curr_inst = cls._clean_institution_name("\n".join(current_chunk))
                    chunk_inst = cls._clean_institution_name(chunk)
                    if curr_inst and chunk_inst and curr_inst != chunk_inst:
                        should_split = True
                    else:
                        should_split = False
                elif chunk_degree and not curr_degree:
                    # Current block doesn't have degree yet, this degree belongs to current block
                    should_split = False
                elif not chunk_degree and not curr_degree:
                    curr_inst = cls._clean_institution_name("\n".join(current_chunk))
                    chunk_inst = cls._clean_institution_name(chunk)
                    if curr_inst and chunk_inst and curr_inst != chunk_inst:
                        should_split = True

            if should_split and current_chunk:
                blocks.append("\n".join(current_chunk))
                current_chunk = [chunk]
            else:
                current_chunk.append(chunk)

        if current_chunk:
            blocks.append("\n".join(current_chunk))

        return blocks if blocks else [text]

    @classmethod
    def _associate_education_records(cls, items: List[EducationItemSchema], original_text: str) -> List[EducationItemSchema]:
        """Consolidate fragmented records and ensure related education lines are properly associated.

        Requirements:
        - Never create a standalone education object with only CGPA or percentage.
        - Merge complementary orphan records into their corresponding degree records.
        - Never merge distinct qualification tiers (Class X, Class XII, Diploma, UG, PG).
        - Preserve all legitimate multiple education records.
        """
        if not items:
            return []

        consolidated: List[EducationItemSchema] = []

        for item in items:
            is_orphan = (not item.degree and not item.institution)

            if is_orphan:
                if consolidated:
                    target = consolidated[-1]
                    if target.cgpa is None and item.cgpa is not None:
                        target.cgpa = item.cgpa
                        target.cgpa_scale = item.cgpa_scale
                    if target.percentage is None and item.percentage is not None:
                        target.percentage = item.percentage
                    if not target.start_year and item.start_year:
                        target.start_year = item.start_year
                    if not target.end_year and item.end_year:
                        target.end_year = item.end_year
                continue

            # What if item has institution but no degree, and preceding record has degree but no institution?
            if consolidated and not item.degree and item.institution:
                target = consolidated[-1]
                if target.degree and not target.institution:
                    target.institution = item.institution
                    if target.cgpa is None and item.cgpa is not None:
                        target.cgpa = item.cgpa
                        target.cgpa_scale = item.cgpa_scale
                    if target.percentage is None and item.percentage is not None:
                        target.percentage = item.percentage
                    if not target.start_year and item.start_year:
                        target.start_year = item.start_year
                    if not target.end_year and item.end_year:
                        target.end_year = item.end_year
                    if not target.specialization and item.specialization:
                        target.specialization = item.specialization
                    continue

            # What if target has institution but no degree, and item has degree but no institution?
            if consolidated and not consolidated[-1].degree and consolidated[-1].institution and item.degree:
                target = consolidated[-1]
                if not item.institution:
                    item.institution = target.institution
                if item.cgpa is None and target.cgpa is not None:
                    item.cgpa = target.cgpa
                    item.cgpa_scale = target.cgpa_scale
                if item.percentage is None and target.percentage is not None:
                    item.percentage = target.percentage
                if not item.start_year and target.start_year:
                    item.start_year = target.start_year
                if not item.end_year and target.end_year:
                    item.end_year = target.end_year
                if not item.specialization and target.specialization:
                    item.specialization = target.specialization
                consolidated[-1] = item
                continue

            consolidated.append(item)

        # Final filter: ensure every returned record has at least degree or institution
        final_entries = [
            it for it in consolidated
            if it.degree or it.institution
        ]

        return final_entries

    @classmethod
    def _parse_single_education_block(cls, b_text: str) -> EducationItemSchema:
        """Deterministically extract all fields for a single education entry."""
        item = EducationItemSchema()

        # 0. Strip "Relevant Coursework" lines — they are metadata, not part of
        #    the education entry and can cause false specialization matches.
        cleaned_lines = []
        skip_rest = False
        for line in b_text.split("\n"):
            if re.match(r"^\s*relevant\s+course\s*work", line, re.IGNORECASE):
                skip_rest = True
                continue
            if skip_rest:
                continue
            cleaned_lines.append(line)
        b_text = "\n".join(cleaned_lines) if cleaned_lines else b_text

        # 1. Degree
        for pat, deg_name in cls.DEGREE_PATTERNS:
            if re.search(pat, b_text, re.IGNORECASE):
                item.degree = deg_name
                break

        # 2. Specialization
        for spec in cls.SPECIALIZATION_KEYWORDS:
            if re.search(rf"\b{re.escape(spec)}\b", b_text, re.IGNORECASE):
                item.specialization = spec.title().replace("And", "&")
                break

        # 3. Institution
        item.institution = cls._clean_institution_name(b_text)

        # 4. Years
        item.start_year, item.end_year = cls._extract_years(b_text)

        # 4b. Safety net: strip trailing year range from institution name
        item.institution, item.start_year, item.end_year = clean_institution(
            item.institution, item.start_year, item.end_year
        )

        # 5. CGPA and CGPA Scale
        item.cgpa, item.cgpa_scale = cls._extract_cgpa_and_scale(b_text)

        # 6. Percentage
        item.percentage = cls._extract_percentage(b_text)

        # 7. Class 10 / Class 12 percentage (only when explicitly labelled)
        item.class_10_percentage = cls._extract_class_percentage(b_text, level=10)
        item.class_12_percentage = cls._extract_class_percentage(b_text, level=12)

        # 8. Backlogs (only when explicitly stated; never infer 0 from silence)
        item.backlogs = cls._extract_backlogs(b_text)

        return item

    # ------------------ CLASS PERCENTAGE & BACKLOG EXTRACTION ------------------
    @classmethod
    def _extract_class_percentage(cls, text: str, level: int = 10) -> Optional[str]:
        """Extract Class 10 or Class 12 percentage only when explicitly labelled.

        Returns the percentage as a string like "85%" or None if absent.
        """
        if not text:
            return None

        if level == 10:
            # Match labels: "10th", "Class X", "SSC", "Matriculation", "Class 10", "High School", "Secondary" (without senior/higher prefix)
            label_pat = r"(?:10th|class\s+10\b|class\s+x\b|ssc\b|matriculation\b|high\s+school\b|(?<!senior\s)(?<!higher\s)secondary\b)"
        else:
            # Match labels: "12th", "Class XII", "HSC", "Intermediate", "Class 12", "Senior Secondary", "Higher Secondary"
            label_pat = r"(?:12th|class\s+12\b|class\s+xii\b|hsc\b|intermediate\b|senior\s+secondary\b|higher\s+secondary\b)"

        # 1. Label followed by optional separators and a percentage value or CGPA
        pattern = rf"\b{label_pat}[\s\S]{{0,40}}?([0-9](?:\.[0-9]{{1,2}})?\s*(?:/\s*10|cgpa|gpa)|[0-9]{{1,3}}(?:\.[0-9]{{1,2}})?\s*%)"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if not val.endswith("%") and not any(k in val.lower() for k in ["cgpa", "gpa", "/"]):
                val = f"{val}%"
            return val

        # 2. Also match: "percentage: 85" or bare number >= 35 after label within a short range
        pattern2 = rf"\b{label_pat}[^\n\r0-9]{{0,40}}?(?:percentage|marks?|aggregate|score)?[:\s\-]*([3-9][0-9](?:\.[0-9]{{1,2}})?)\b"
        m2 = re.search(pattern2, text, re.IGNORECASE)
        if m2:
            return f"{m2.group(1).strip()}%"

        return None

    @classmethod
    def map_school_entries(
        cls,
        items: List[EducationItemSchema],
        full_text: str = ""
    ) -> Tuple[List[EducationItemSchema], List[Dict[str, Any]]]:
        """Map school entries into the primary higher-education entry (e.g. B.Tech).

        - Class 10 labels: 10th, Class 10, Class X, SSC, Secondary, Matriculation, High School.
        - Class 12 labels: 12th, Class 12, Class XII, HSC, Senior Secondary, Higher Secondary, Intermediate.
        - Writes value to class_10_percentage / class_12_percentage on primary higher-ed entry.
        - Normalizes "87.4%" and "87.4" to one format and keeps CGPA-style marks (e.g. 9.2/10) with unit.
        - Leaves higher-ed entries in education list. Keeps raw school entries in audit list.
        """
        if not items:
            return [], []

        higher_edu: List[EducationItemSchema] = []
        school_entries: List[EducationItemSchema] = []

        for it in items:
            tier = cls._get_degree_tier(it.degree)
            deg_lower = (it.degree or "").lower()
            inst_lower = (it.institution or "").lower()
            is_school = (
                tier in ["CLASS_10", "CLASS_12"] or
                any(k in deg_lower for k in [
                    "class x", "class 10", "10th", "high school", "ssc", "matriculation", "secondary",
                    "class xii", "class 12", "12th", "senior secondary", "higher secondary", "hsc", "intermediate"
                ]) or
                any(k in inst_lower for k in [
                    "senior secondary school", "high school", "secondary school"
                ])
            )
            if is_school:
                school_entries.append(it)
            else:
                higher_edu.append(it)

        # Extract marks from school entries
        c10_val: Optional[str] = None
        c12_val: Optional[str] = None

        for sch in school_entries:
            deg_lower = (sch.degree or "").lower()
            inst_lower = (sch.institution or "").lower()
            tier = cls._get_degree_tier(sch.degree)
            val = (
                sch.percentage or
                (f"{sch.cgpa}{f'/{sch.cgpa_scale}' if sch.cgpa_scale else ''}" if sch.cgpa else None) or
                sch.class_10_percentage or
                sch.class_12_percentage
            )
            if val and not val.endswith("%") and not any(k in val.lower() for k in ["cgpa", "gpa", "/"]):
                val = f"{val}%"

            combined_text = f"{deg_lower} {inst_lower}"
            is_sch_10 = bool(re.search(
                r"\b(?:class\s+(?:x\b|10\b)|10th\b|high\s+school\b|ssc\b|matriculation\b|(?<!senior\s)(?<!higher\s)secondary\b)",
                combined_text,
                re.IGNORECASE,
            ))
            is_sch_12 = bool(re.search(
                r"\b(?:class\s+(?:xii\b|12\b)|12th\b|senior\s+secondary\b|higher\s+secondary\b|hsc\b|intermediate\b)",
                combined_text,
                re.IGNORECASE,
            ))

            if is_sch_12 and not c12_val and val:
                c12_val = val
            elif is_sch_10 and not c10_val and val:
                c10_val = val

        # Fallback to full resume text if not found in school items
        search_corpus = f"{full_text}\n{' '.join([s.institution or '' for s in school_entries])}"
        if not c10_val:
            c10_val = cls._extract_class_percentage(search_corpus, level=10)
        if not c12_val:
            c12_val = cls._extract_class_percentage(search_corpus, level=12)

        raw_audit = [s.model_dump() for s in school_entries]

        # If higher education exists (e.g. B.Tech), map school marks into the primary higher-ed entry
        if higher_edu:
            primary = higher_edu[0]
            if c10_val and not primary.class_10_percentage:
                primary.class_10_percentage = c10_val
            if c12_val and not primary.class_12_percentage:
                primary.class_12_percentage = c12_val
            return higher_edu + school_entries, raw_audit

        # If only school entries exist (no higher ed), return them
        return school_entries, raw_audit

    @classmethod
    def _extract_backlogs(cls, text: str) -> Optional[int]:
        """Extract backlog count only from explicit statements.

        Recognised patterns:
        - "Backlogs: 0", "Backlogs: 2", "Active Backlogs: 1"
        - "No backlogs", "Nil backlogs", "Zero backlogs", "Zero active backlogs"
        - "No active backlogs"

        Returns None when the text says nothing about backlogs (never infer 0
        from silence).
        """
        if not text:
            return None

        lower = text.lower()
        if "backlog" not in lower and "arrear" not in lower:
            return None

        # "No backlogs", "Nil backlogs", "Zero active backlogs", "No active backlogs"
        if re.search(r"\b(?:no|nil|zero)\s+(?:active\s+)?(?:backlog|arrear)s?\b", lower):
            return 0

        # "Backlogs: 0", "Active Backlogs: 2"
        m = re.search(r"\b(?:active\s+)?(?:backlog|arrear)s?\s*[:=\-]\s*(\d+)", lower)
        if m:
            return int(m.group(1))

        return None

    # ------------------ TECHNICAL SKILLS EXTRACTION ------------------
    @classmethod
    def _is_junk_skill(cls, token: str) -> bool:
        """Filter out page headers/footers and generic non-technologies like lone 'API'."""
        t_clean = token.strip()
        t_lower = t_clean.lower()
        if not t_clean or len(t_clean) > 35:
            return True
        # Lone API or APIs (case-insensitive) - preserve real APIs like "REST APIs", "OpenAI API"
        if t_lower in ["api", "apis"]:
            return True
        # Page footers/headers e.g. "Resume Page 1 of 1", "Page 1", "Page 1 of 2"
        if re.search(r"\bpage\s+\d+(\s+of\s+\d+)?\b", t_lower):
            return True
        if re.search(r"^(?:resume\s+)?page\b", t_lower):
            return True
        # Resume header noise
        if "resume" in t_lower and any(w in t_lower for w in ["page", "curriculum", "cv"]):
            return True
        return False

    @classmethod
    def parse_technical_skills(cls, skills_text: str) -> TechnicalSkillsSchema:
        """Extract explicitly listed skills into a unified technologies array.

        Preserves all technologies deterministically without dividing into categories.
        Filters out page headers/footers and lone generic tokens like 'API'.
        """
        res = TechnicalSkillsSchema()
        if not skills_text or not skills_text.strip():
            return res

        seen_lower: Set[str] = set()

        lines = skills_text.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Strip leading bullets, numbers, and symbols before matching categories
            cleaned_line = re.sub(r"^[•\-\*\d+\.\s|~]+", "", line_str).strip()
            if not cleaned_line:
                continue

            # Check if line matches category pattern like "Languages: Python, Java"
            cat_match = re.match(r"^([^:\-—|]+)[:\-—|]\s*(.+)$", cleaned_line)
            if cat_match:
                items_str = cat_match.group(2).strip()
                tokens = [t.strip().strip(",;|•") for t in re.split(r"[,;|•/]", items_str) if t.strip()]
                for token in tokens:
                    t_clean = token.strip()
                    if cls._is_junk_skill(t_clean) or t_clean.lower() in seen_lower:
                        continue
                    seen_lower.add(t_clean.lower())
                    res.technologies.append(t_clean)
            else:
                # Raw list or bullet items without category label
                tokens = [t.strip().strip(",;|•") for t in re.split(r"[,;|•\n/]", cleaned_line) if t.strip()]
                for token in tokens:
                    t_clean = token.strip()
                    if cls._is_junk_skill(t_clean) or t_clean.lower() in seen_lower:
                        continue
                    seen_lower.add(t_clean.lower())
                    res.technologies.append(t_clean)

        return res

    # ------------------ CERTIFICATIONS EXTRACTION ------------------
    @classmethod
    def parse_certifications(cls, certs_text: str, fallback_text: str = "") -> List[CertificationItemSchema]:
        """Extract certification details deterministically without AI."""
        text_to_use = certs_text.strip() if certs_text and certs_text.strip() else ""
        from_fallback = False
        if not text_to_use and fallback_text and fallback_text.strip():
            text_to_use = fallback_text.strip()
            from_fallback = True

        if not text_to_use:
            return []

        cert_items: List[CertificationItemSchema] = []
        # Split into blocks by double newlines or bullets or numbered items or single lines
        blocks = re.split(r"\n\s*\n|(?<=\n)(?=[•\-\*\d+\.])", text_to_use)
        if len(blocks) == 1 and "\n" in text_to_use:
            blocks = [l for l in text_to_use.split("\n") if l.strip()]

        sorted_issuers = sorted(cls.KNOWN_ISSUERS, key=len, reverse=True)
        ach_words = ["winner", "1st place", "2nd place", "3rd place", "hackathon", "solved", "problems", "finalist", "icpc", "olympiad"]

        for block in blocks:
            cleaned = re.sub(r"^[•\-\*\d+\.\s]+", "", block).strip()
            if not cleaned or len(cleaned) < 5:
                continue

            lower_c = cleaned.lower()
            # If from fallback or combined section, skip if it's purely an achievement
            is_pure_achievement = any(aw in lower_c for aw in ach_words) and not any(
                cw in lower_c for cw in ["certif", "accredit", "license", "credential", "course", "training"]
            ) and not any(re.search(rf"\b{re.escape(iss)}\b", cleaned, re.IGNORECASE) for iss in sorted_issuers)

            if is_pure_achievement:
                continue

            # If we're looking at fallback_text, make sure it has certification-related keywords
            if from_fallback:
                has_cert_sign = any(
                    cw in lower_c for cw in ["certif", "accredit", "license", "credential", "course", "training", "practitioner", "architect", "associate", "specialist"]
                ) or any(re.search(rf"\b{re.escape(iss)}\b", cleaned, re.IGNORECASE) for iss in sorted_issuers)
                if not has_cert_sign:
                    continue

            item = CertificationItemSchema()

            # Issuer (longer names first to prioritize Amazon Web Services over AWS)
            for issuer in sorted_issuers:
                if re.search(rf"\b{re.escape(issuer)}\b", cleaned, re.IGNORECASE):
                    item.issuer = issuer
                    break
            if not item.issuer:
                # Check for "Issued by <Name>" or "by <Name>"
                issued_by_match = re.search(r"\b(?:issued\s+by|by|from)\s+([A-Za-z0-9\s]+?)(?:\s*[-|–,\n]|$)", cleaned, re.IGNORECASE)
                if issued_by_match:
                    cand = issued_by_match.group(1).strip()
                    if 2 < len(cand) < 30:
                        item.issuer = cand

            # Credential URL
            url_match = re.search(r"https?://[^\s)]+", cleaned)
            if url_match:
                item.credential_url = url_match.group(0).strip()

            # Dates
            date_match = re.search(
                r"\b(?:issued|valid|date)?[:\s]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2}|20\d{2})\b",
                cleaned,
                re.IGNORECASE
            )
            if date_match:
                item.issue_date = date_match.group(1).strip()

            # Credential ID
            id_match = re.search(r"(?:credential\s*id|\bid\b|license\s*(?:number|id))[:\s]*([a-zA-Z0-9_\-]+)", cleaned, re.IGNORECASE)
            if id_match:
                item.credential_id = id_match.group(1).strip()

            # Name: first line or portion before separator
            lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
            first_line = lines[0].split("|")[0].split(" - ")[0].split(" – ")[0].strip()
            item.name = first_line

            cert_items.append(item)

        return cert_items

    # ------------------ ACHIEVEMENTS EXTRACTION ------------------
    @classmethod
    def parse_achievements(cls, ach_text: str, fallback_text: str = "") -> List[AchievementItemSchema]:
        """Extract achievements deterministically without AI."""
        text_to_use = ach_text.strip() if ach_text and ach_text.strip() else ""
        from_fallback = False
        if not text_to_use and fallback_text and fallback_text.strip():
            text_to_use = fallback_text.strip()
            from_fallback = True

        if not text_to_use:
            return []

        ach_items: List[AchievementItemSchema] = []
        blocks = re.split(r"\n\s*\n|(?<=\n)(?=[•\-\*\d+\.])", text_to_use)
        if len(blocks) == 1 and "\n" in text_to_use:
            blocks = [l for l in text_to_use.split("\n") if l.strip()]

        ach_words = [
            "winner", "1st place", "first place", "2nd place", "second place", "3rd place", "third place",
            "hackathon", "solved", "award", "awarded", "rank", "ranked", "finalist", "icpc",
            "olympiad", "top 1%", "top 5%", "problem solving", "competition", "contest"
        ]

        for block in blocks:
            cleaned = re.sub(r"^[•\-\*\d+\.\s]+", "", block).strip()
            if not cleaned or len(cleaned) < 5:
                continue

            lower_c = cleaned.lower()
            if from_fallback:
                # Must match at least one achievement indicator
                has_ach_sign = any(aw in lower_c for aw in ach_words)
                if not has_ach_sign:
                    continue

            item = AchievementItemSchema()
            lines = [l.strip() for l in cleaned.split("\n") if l.strip()]

            # Date
            date_match = re.search(
                r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2}|20\d{2})\b",
                cleaned,
                re.IGNORECASE
            )
            if date_match:
                item.date = date_match.group(1).strip()

            # Title & Description
            item.title = lines[0].split(":")[0].strip()
            item.description = " ".join(lines).strip()

            # Organization
            org_match = re.search(r"\b(?:by|at|from)\s+([A-Z][a-zA-Z0-9\s]+?)(?:[-|,\.]|$)", item.description)
            if org_match:
                cand_org = org_match.group(1).strip()
                if 2 < len(cand_org) < 40:
                    item.organization = cand_org

            ach_items.append(item)

        return ach_items
