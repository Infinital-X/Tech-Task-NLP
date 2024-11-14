import os
import pdfplumber
from docx import Document
import re
import json
import spacy

nlp = spacy.load("uk_core_news_sm")

def extract_pdf_text(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

def extract_docx_text(file_path):
    doc = Document(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

def extract_txt_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

phone_pattern = r"\+380\d{9}"
email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

def parse_contact_info(text):
    phone = re.search(phone_pattern, text)
    email = re.search(email_pattern, text)
    return {
        "phone": phone.group() if phone else None,
        "email": email.group() if email else None
    }

invalid_names = {"Java", "Python", "SQL", "JavaScript", "Excel", "Room", "Engineer", "Developer"}

def extract_name(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PER" and ent.text not in invalid_names:
            return ent.text.strip()

    name_patterns = [
        r"\bІм['’]я\s*[:\-]?\s*([А-ЯІЇЄҐ][а-яіїєґ']+\s[А-ЯІЇЄҐ][а-яіїєґ']+)\b",
        r"\bПІБ\s*[:\-]?\s*([А-ЯІЇЄҐ][а-яіїєґ']+\s[А-ЯІЇЄҐ][а-яіїєґ']+)\b",
        r"^\s*([А-ЯІЇЄҐ][а-яіїєґ']+\s[А-ЯІЇЄҐ][а-яіїєґ']+)", 
    ]

    for pattern in name_patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match and match.group(1) not in invalid_names:
            return match.group(1).strip()

    return None

def parse_experience(text):
    experience = []
    job_pattern = r"(Старший розробник|Розробник|Менеджер проектів|Інженер|.*)\n(.*)\n(\d{4}[-–—]\d{4})"
    job_matches = re.findall(job_pattern, text)
    
    for match in job_matches:
        title, company, dates = match
        experience.append({
            "title": title.strip(),
            "company": company.strip(),
            "dates": dates.strip(),
            "responsibilities": []
        })
    
    return experience

def parse_education(text):
    education = []
    education_pattern = r"(Національний технічний університет|Київський національний університет|.*)\n(.*)\n(\d{4})"
    education_matches = re.findall(education_pattern, text)
    
    for match in education_matches:
        institution, specialty, year = match
        education.append({
            "institution": institution.strip(),
            "specialty": specialty.strip(),
            "graduation_year": year.strip()
        })
    
    return education

def parse_skills(text):
    skills_list = ["Python", "JavaScript", "SQL", "Комунікативні навички", "Управління проектами"]
    skills = [skill for skill in skills_list if skill.lower() in text.lower()]
    return skills

def parse_resume(file_path):
    if file_path.endswith(".pdf"):
        text = extract_pdf_text(file_path)
    elif file_path.endswith(".docx"):
        text = extract_docx_text(file_path)
    elif file_path.endswith(".txt"):
        text = extract_txt_text(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

    contact_info = parse_contact_info(text)
    experience = parse_experience(text)
    education = parse_education(text)
    skills = parse_skills(text)

    name = extract_name(text)

    resume_data = {
        "name": name,
        "contact_info": contact_info,
        "experience": experience,
        "education": education,
        "skills": skills
    }

    return resume_data

def process_resumes_from_folder(folder_path, output_file):
    all_resumes = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            print(f"Обработка файла: {filename}")
            resume_data = parse_resume(file_path)
            all_resumes.append(resume_data)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"resumes": all_resumes}, f, ensure_ascii=False, indent=4)
    print(f"Все резюме сохранены в {output_file}")

def main():
    folder_path = "cv"  # Папка для резюме
    output_file = "all_resumes.json"  
    process_resumes_from_folder(folder_path, output_file)

if __name__ == "__main__":
    main()
