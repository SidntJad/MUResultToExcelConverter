import re
import pandas as pd
from collections import defaultdict
import pprint

def parse_marks(endsem_mid_total, grade_line):
    if not endsem_mid_total.strip() or not grade_line.strip():
        return {k: '' for k in ['ENDSEM', 'MIDTERMAVG', 'TOTAL', 'CR', 'GR', 'GP', 'C*G']}

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
    try:
        lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
        if len(lines) < 6:
            return None

        # Step 1: Extract roll no and name
        first_line_parts = lines[0].split("|")
        roll_no_name = first_line_parts[0].strip().split()
        roll_no = roll_no_name[0]
        student_name = " ".join(roll_no_name[1:]).title()
        paper_codes = [code.strip() for code in first_line_parts[1:-1]]

        # Step 2: Mother's name
        mother_info = lines[1].split("|")[0]
        try:
            _, mother_name = mother_info.split("-", 1)
        except ValueError:
            mother_name = ""
        mother_name = mother_name.strip().title()

        # Step 3: PRN
        prn = lines[3].split("|")[0].strip()

        # Step 4: Marks
        endsem_midterm_total = lines[1].split("|")[1:]
        grades_line = lines[3].split("|")[1:]

        # Step 5: Extra papers
        extra_codes = [x.strip() for x in lines[5].split("|")[1:] if x.strip()]
        extra_marks = [x.strip() for x in lines[6].split("|")[1:] if x.strip()]
        extra_grades = [x.strip() for x in lines[8].split("|")[1:] if x.strip()]

        # Step 6: Totals
        total_line = next((line for line in lines if "Total Credit" in line), "")
        total_credit = re.search(r'Total Credit\s+([\d.]+)', total_line)
        final_cgpi = re.search(r'FINAL CGPI\s+([-\d.]+)', total_line)
        final_grade = re.search(r'FINAL GRADE\s+([A-Z-]+)', total_line)

        # Step 7: Centre-College
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

        # Add initial papers
        for i, code in enumerate(paper_codes):
            paper_key = code if code not in student_dict["PAPERS"] else f"{code}[2]"
            student_dict["PAPERS"][paper_key] = parse_marks(
                endsem_midterm_total[i] if i < len(endsem_midterm_total) else "",
                grades_line[i] if i < len(grades_line) else ""
            )

        # Add extra papers
        for idx, code in enumerate(extra_codes):
            paper_key = code if code not in student_dict["PAPERS"] else f"{code}[2]"
            student_dict["PAPERS"][paper_key] = parse_marks(
                extra_marks[idx] if idx < len(extra_marks) else "",
                extra_grades[idx] if idx < len(extra_grades) else ""
            )

        # Fill empty slots
        for i in range(len(student_dict["PAPERS"]) + 1, 12):
            student_dict["PAPERS"][f"PAPER {i}"] = {k: '' for k in ['ENDSEM', 'MIDTERMAVG', 'TOTAL', 'CR', 'GR', 'GP', 'C*G']}

        return roll_no, student_dict
    except Exception as e:
        print(f"⚠ Error parsing block: {e}")
        return None

def parse_all_students(pdf_text):
    # Use a refined pattern to split blocks and ignore the header content
    student_blocks = re.split(r'(?=\n\s*\d{7,8}\s+[A-Z])', pdf_text)
    
    # Remove the initial header block
    if student_blocks and "University of Mumbai" in student_blocks[0]:
        student_blocks = student_blocks[1:]
    
    all_students = {}
    for block in student_blocks:
        result = parse_student_block(block)
        if result:
            roll_no, student_data = result
            all_students[roll_no] = student_data
    return all_students

def export_students_to_excel(all_students, output_path):
    rows = []
    for student_id, student_data in all_students.items():
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
        for paper_code, paper_data in student_data.get("PAPERS", {}).items():
            row = base_info.copy()
            row["Paper Code"] = paper_code
            row.update(paper_data)
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False)
    print(f"✅ Excel file saved to: {output_path}")

# Main execution logic
# This part of the script reads the file and processes it.
# The user's prompt suggests this part is already in place.
# The key change is in the `parse_all_students` function.

if __name__ == "__main__":
    with open("/home/adl/Desktop/csv/MUResultToExcelConverter/output.txt", encoding="utf-8") as f:
        pdf_text = f.read()

    # The part of the code that needs to be removed from the text is the header.
    # The `parse_all_students` function now handles this by splitting and then
    # removing the first element if it contains the header text.
    students = parse_all_students(pdf_text)

    # Pretty print the dictionary for inspection
    pprint.pprint(students, width=140)

    # Export to an Excel file
    output_path = "temp_data.xlsx"
    export_students_to_excel(students, output_path)

    # Subject dictionary (code → name)
    subject_dict = {}
    pattern = r'(\b[A-Z]*\d{5})-([A-Za-z &()\-]+?)[:\(]'
    for code, name in re.findall(pattern, pdf_text):
        subject_dict[code] = name.strip()

    print("\nSubject Dictionary:")
    pprint.pprint(subject_dict)