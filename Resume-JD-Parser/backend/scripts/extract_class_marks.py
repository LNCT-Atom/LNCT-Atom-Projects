import os
import sys
from pathlib import Path

# Ensure the project root is in PYTHONPATH
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from app.repositories.resume_repository import ResumeRepository

def main():
    """Extract and print Class 10 and Class 12 percentages for all resumes.

    Output format (CSV without header):
    name,email,class_10_percentage,class_12_percentage
    """
    repo = ResumeRepository()
    collection = repo.get_collection()
    for doc in collection.find({}):
        profile = doc.get("profile", {})
        name = profile.get("full_name") or ""
        email = profile.get("email") or ""
        class_10 = ""
        class_12 = ""
        for edu in doc.get("education", []):
            if edu.get("class_10_percentage") and not class_10:
                class_10 = edu.get("class_10_percentage")
            if edu.get("class_12_percentage") and not class_12:
                class_12 = edu.get("class_12_percentage")
        print(f"{name},{email},{class_10},{class_12}")

if __name__ == "__main__":
    main()
