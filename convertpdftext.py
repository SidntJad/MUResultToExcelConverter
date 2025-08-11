# import pdfplumber

# with pdfplumber.open("/home/dbms11/Downloads/IT (1).pdf") as pdf, open("/home/dbms11/Downloads/output.txt", "w", encoding="utf-8") as f:
    
#     for page in pdf.pages:
#         t = page.extract_text()
#         if t:
#             f.write(t + '\n')

import re
import re
from collections import defaultdict
import pandas as pd

def parse_marks(endsem_mid_total, grade_line):
    if not endsem_mid_total.strip() or not grade_line.strip():
        return {
            'ENDSEM': '',
            'MIDTERMAVG': '',
            'TOTAL': '',
            'CR': '',
            'GR': '',
            'GP': '',
            'C*G': ''
        }

    end_parts = endsem_mid_total.strip().split()
    grade_parts = grade_line.strip().split()

    return {
        'ENDSEM': end_parts[0] if len(end_parts) > 0 else '',
        'MIDTERMAVG': end_parts[1] if len(end_parts) > 1 else '',
        'TOTAL': end_parts[2] if len(end_parts) > 2 else '',
        'CR': grade_parts[0] if len(grade_parts) > 0 else '',
        'GR': grade_parts[1] if len(grade_parts) > 1 else '',
        'GP': grade_parts[2] if len(grade_parts) > 2 else '',
        'C*G': grade_parts[3] if len(grade_parts) > 3 else ''
    }

def parse_student_block(block):
    lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
    if len(lines) < 6:
        return None

    # Step 1: Extract student ID and name
    first_line_parts = lines[0].split("|")
    roll_no_name = first_line_parts[0].strip().split()
    roll_no = roll_no_name[0]
    student_name = " ".join(roll_no_name[1:]).title()
    paper_codes = [code.strip() for code in first_line_parts[1:-1]]

    # Step 2: Extract mother's name
    mother_info = lines[1].split("|")[0]
    try:
        _, mother_name = mother_info.split("-", 1)
    except ValueError:
        mother_name = ""
    mother_name = mother_name.strip().title()

    # Step 3: PRN
    prn = lines[3].split("|")[0].strip()

    # Step 4: marks
    endsem_midterm_total = lines[1].split("|")[1:]
    grades_line = lines[3].split("|")[1:]

    # Step 5: Extra papers
    extra_codes = [x.strip() for x in lines[5].split("|")[1:] if x.strip()]
    extra_marks = [x.strip() for x in lines[6].split("|")[1:] if x.strip()]
    extra_grades = [x.strip() for x in lines[8].split("|")[1:] if x.strip()]

    # Step 6: totals
    total_line = next((line for line in lines if "Total Credit" in line), "")
    total_credit = re.search(r'Total Credit\s+([\d.]+)', total_line)
    final_cgpi = re.search(r'FINAL CGPI\s+([-\d.]+)', total_line)
    final_grade = re.search(r'FINAL GRADE\s+([A-Z-]+)', total_line)

    # Step 7: centre-college
    centre_college = ""
    for line in lines:
        if re.match(r'^\(\d+\)', line.strip()):
            centre_college = line.split("|")[0].strip()
            break

    student_dict = {
        "NAME": student_name,
        "MOTHER'S NAME": mother_name,
        "PRN": prn,
        "CENTRE-COLLEGE": centre_college,
        "Total Credit": total_credit.group(1) if total_credit else "",
        "Final CGPI": final_cgpi.group(1) if final_cgpi else "",
        "Final Grade": final_grade.group(1) if final_grade else "",
        "PAPERS": {}
    }

    # Initial 7 papers
    for i, code in enumerate(paper_codes):
        paper_key = code if code not in student_dict["PAPERS"] else f"{code}[2]"
        student_dict["PAPERS"][paper_key] = parse_marks(
            endsem_midterm_total[i] if i < len(endsem_midterm_total) else "",
            grades_line[i] if i < len(grades_line) else ""
        )

    # Extra papers
    for idx, code in enumerate(extra_codes):
        paper_key = code if code not in student_dict["PAPERS"] else f"{code}[2]"
        student_dict["PAPERS"][paper_key] = parse_marks(
            extra_marks[idx] if idx < len(extra_marks) else "",
            extra_grades[idx] if idx < len(extra_grades) else ""
        )

    # Fill empty paper slots
    for i in range(len(student_dict["PAPERS"]) + 1, 12):
        student_dict["PAPERS"][f"PAPER {i}"] = {
            'ENDSEM': '',
            'MIDTERMAVG': '',
            'TOTAL': '',
            'CR': '',
            'GR': '',
            'GP': '',
            'C*G': ''
        }
    import pandas as pd

    rows = []
    for student_id, student_data in student_dict.items():
        base_info = {
            "Student ID": student_id,
            "PRN": student_data.get("PRN", ""),
            "Name": student_data.get("NAME", ""),
            "Mother's Name": student_data.get("MOTHER'S NAME", ""),
            "Centre-College": student_data.get("CENTRE-COLLEGE", ""),
            "Final CGPI": student_data.get("Final CGPI", ""),
            "Final Grade": student_data.get("Final Grade", ""),
            "Total Credit": student_data.get("Total Credit", "")
        }

        # Loop through each paper
        for paper_code, paper_data in student_data.get("PAPERS", {}).items():
            row = base_info.copy()
            row["Paper Code"] = paper_code
            
            # Add all paper-specific fields dynamically
            for k, v in paper_data.items():
                row[k] = v
            
            rows.append(row)

    # Convert list of dicts to DataFrame
    df = pd.DataFrame(rows)

    # Save to Excel
    df.to_excel("C:\\Users\\HP\\Downloads\\students_data.xlsx", index=False)

    print("✅ Excel file 'students_data.xlsx' created successfully!")



    return roll_no, student_dict


# Main Parsing Function
def parse_all_students(pdf_text):
    # Split by student blocks using roll number (assuming it starts with a 7-8 digit number)
    student_blocks = re.split(r'(?=\b\d{7,8}\b\s+[A-Z])', pdf_text)

    all_students = {}

    for block in student_blocks:
        result = parse_student_block(block)
        if result:
            roll_no, student_data = result
            all_students[roll_no] = student_data

    return all_students


# --- Example Usage ---

# If you have already extracted text using pdfplumber or PyMuPDF
# with open("your_text_file.txt") as f:
#     pdf_text = f.read()

# Or directly if you have pdfplumber:
# import pdfplumber
# with pdfplumber.open("your_file.pdf") as pdf:
#     pdf_text = "\n".join(page.extract_text() for page in pdf.pages)

# For demonstration, using sample text:
pdf_text = """PASTE YOUR FULL PDF TEXT CONTENT HERE"""
with open("""C:\\Users\\HP\\Downloads\\output.txt""") as f:
    pdf_text = f.read()
    students = parse_all_students(pdf_text)
#   print(f.read()) 
#   for line in f:
#     print(line)
#     break

# Pretty print result
import pprint
pprint.pprint(students, width=140)

# Optionally save to JSON
# import json
# with open("students_output.json", "w") as f:
#     json.dump(students, f, indent=2)


# Dictionary to store subject code → subject name
subject_dict = {}

# Open file and skip first 2 lines
# with open('/home/dbms11/Downloads/output.txt', 'r') as file:
#     lines = file.readlines()[2:]  # Start from line 3

#     # Join lines for easier regex parsing
#     text = ' '.join(lines)

#     # Regex pattern: match subject code and subject name before ':' or '('
#     pattern = r'(\b[A-Z]*\d{5})-([A-Za-z &()\-]+?)[:\(]'

#     # Extract and store in dictionary
#     for match in re.findall(pattern, text):
#         code, name = match
#         subject_dict[code] = name.strip()
#     parse_student_full(lines)
    

    

# Print the resulting dictionary
print(subject_dict)


    # If needed, you can access or replace subject codes later using `subject_dict`
