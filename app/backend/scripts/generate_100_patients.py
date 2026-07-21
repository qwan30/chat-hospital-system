"""
Generate 100 realistic Vietnamese hospital patients as XLSX.
Run: python scripts/generate_100_patients.py
Output: data/patients_100.xlsx
"""
import random
import datetime
from pathlib import Path

try:
    from openpyxl import Workbook
except ImportError:
    print("Install openpyxl: pip install openpyxl")
    raise

# ── English/Unsigned Vietnamese name components ────────────────────────
SURNAMES = [
    "Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Vo",
    "Dang", "Bui", "Do", "Ho", "Ngo", "Duong", "Ly", "Trinh", "Dinh",
    "Mai", "Cao", "To", "Doan", "Truong", "Lam", "Ha", "Thai", "Ta",
]

MALE_MIDDLES = ["Van", "Duc", "Minh", "Quang", "Thanh", "Huu", "Xuan", "Dinh", "Quoc", "Tuan"]
FEMALE_MIDDLES = ["Thi", "Thanh", "Minh", "Ngoc", "My", "Hong", "Thu", "Dieu", "Kim", "Phuong"]

MALE_NAMES = [
    "An", "Binh", "Cuong", "Dung", "Dat", "Hai", "Hieu", "Hung", "Khang",
    "Khanh", "Long", "Loi", "Manh", "Nam", "Nghia", "Phong", "Phu",
    "Quan", "Quy", "Son", "Tai", "Thanh", "Thang", "Thien", "Tho",
    "Tien", "Toan", "Tri", "Trung", "Tuan", "Vinh",
]

FEMALE_NAMES = [
    "Anh", "Bich", "Chi", "Diep", "Dung", "Giang", "Ha", "Hanh", "Hoa",
    "Huong", "Lan", "Linh", "Loan", "Ly", "Mai", "Nga", "Ngan", "Nhung",
    "Phuong", "Quynh", "Tam", "Thao", "Thuy", "Thuong", "Trang", "Tuyet",
    "Uyen", "Van", "Yen", "Xuan",
]

DEPARTMENTS = [
    "Cardiology", "Internal Medicine", "Neurology",
    "Obstetrics & Gynecology", "Pediatrics", "Emergency Medicine", "Oncology",
    "Orthopedics",
]

STATUS_WEIGHTS = [("active", 85), ("discharged", 10), ("deceased", 5)]


def random_dob():
    """Generate DOB between 1940 and 2005 with realistic distribution."""
    year = random.choices(
        population=[(1940, 1960), (1961, 1980), (1981, 2000), (2001, 2005)],
        weights=[15, 35, 40, 10],
        k=1,
    )[0]
    y = random.randint(*year)
    m = random.randint(1, 12)
    d = random.randint(1, 28)  # Avoid month-end edge cases
    return datetime.date(y, m, d)


def generate_name(gender: str):
    surname = random.choice(SURNAMES)
    if gender == "male":
        middle = random.choice(MALE_MIDDLES)
        given = random.choice(MALE_NAMES)
    else:
        middle = random.choice(FEMALE_MIDDLES)
        given = random.choice(FEMALE_NAMES)
    return f"{surname} {middle} {given}"


def generate_patients(count=100, start_mrn=6):
    patients = []
    for i in range(count):
        mrn_num = start_mrn + i
        gender = random.choice(["male", "female"])
        status = random.choices(
            [s[0] for s in STATUS_WEIGHTS],
            weights=[s[1] for s in STATUS_WEIGHTS],
            k=1,
        )[0]
        patients.append({
            "mrn": f"MRN-{mrn_num:04d}",
            "full_name": generate_name(gender),
            "dob": random_dob().strftime("%Y-%m-%d"),
            "department": random.choice(DEPARTMENTS),
            "status": status,
        })
    return patients


def write_xlsx(patients, output_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Patients"
    ws.append(["mrn", "full_name", "dob", "department", "status"])
    for p in patients:
        ws.append([p["mrn"], p["full_name"], p["dob"], p["department"], p["status"]])
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 24
    ws.column_dimensions["E"].width = 12
    wb.save(output_path)
    print(f"Written {len(patients)} patients to {output_path}")


if __name__ == "__main__":
    random.seed(42)
    output = Path(__file__).parent.parent / "data" / "patients_100.xlsx"
    patients = generate_patients(100, start_mrn=6)
    write_xlsx(patients, output)

    # Stats
    active = sum(1 for p in patients if p["status"] == "active")
    discharged = sum(1 for p in patients if p["status"] == "discharged")
    deceased = sum(1 for p in patients if p["status"] == "deceased")
    depts = {}
    for p in patients:
        depts[p["department"]] = depts.get(p["department"], 0) + 1
    print(f"  active={active}, discharged={discharged}, deceased={deceased}")
    print(f"  departments: {depts}")
