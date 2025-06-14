from faker import Faker
import os

fake = Faker()

cv_base_path = '../../data'
cv_entries = []

for role_folder in os.listdir(cv_base_path):
    role_path = os.path.join(cv_base_path, role_folder)
    if os.path.isdir(role_path):
        for file in os.listdir(role_path):
            if file.endswith('.pdf'):
                full_cv_path = os.path.join(role_path, file).replace("\\", "/")
                cv_entries.append((role_folder, full_cv_path))

with open("../database/database.sql", "w") as f:
    f.write("DROP DATABASE IF EXISTS cvApplicationDatabase;\n")
    f.write("CREATE DATABASE cvApplicationDatabase;\n")
    f.write("USE cvApplicationDatabase;\n\n")

    f.write("""
CREATE TABLE ApplicantProfile (
    applicant_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE,
    address VARCHAR(255),
    phone_number VARCHAR(20)
);\n
""")

    f.write("""
CREATE TABLE ApplicationDetail (
    detail_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT,
    application_role VARCHAR(100) DEFAULT NULL,
    cv_path TEXT,
    FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
);\n
""")

    f.write("\n-- INSERT INTO ApplicantProfile\n")
    for i in range(len(cv_entries)):
        first_name = fake.first_name()
        last_name = fake.last_name()
        dob = fake.date_of_birth(minimum_age=21, maximum_age=35)
        address = fake.address().replace('\n', ', ')
        phone = phone = '08' + ''.join(fake.random_choices(elements='0123456789', length=10))
        f.write(f"INSERT INTO ApplicantProfile (first_name, last_name, date_of_birth, address, phone_number) "
                f"VALUES ('{first_name}', '{last_name}', '{dob}', '{address}', '{phone}');\n")

    f.write("\n-- INSERT INTO ApplicationDetail\n")
    for i, (role, path) in enumerate(cv_entries):
        f.write(f"INSERT INTO ApplicationDetail (applicant_id, application_role, cv_path) "
                f"VALUES ({i+1}, '{role}', '{path}');\n")
