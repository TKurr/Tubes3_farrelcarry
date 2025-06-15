from faker import Faker
import os
import random

fake = Faker()

# Scan data directory for all PDFs
data_dir = "../../data"
all_cv_files = []
for file in os.listdir(data_dir):
    if file.endswith(".pdf"):
        all_cv_files.append(file)

print(f"Found {len(all_cv_files)} PDFs in data directory")

# List of roles
roles = [
    "ACCOUNTANT",
    "ADVOCATE",
    "BUSINESS-DEVELOPMENT",
    "CONSULTANT",
    "DESIGNER",
    "ENGINEER",
    "FITNESS",
    "HEALTHCARE",
    "HR",
    "INFORMATION-TECHNOLOGY",
    "SALES",
    "TEACHER",
]


sql_file_path = "../database/database.sql"
with open(sql_file_path, "w") as f:
    # Write database structure
    f.write("DROP DATABASE IF EXISTS cvApplicationDatabase;\n")
    f.write("CREATE DATABASE cvApplicationDatabase;\n")
    f.write("USE cvApplicationDatabase;\n\n")

    f.write(
        """
CREATE TABLE ApplicantProfile (
    applicant_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE,
    address VARCHAR(255),
    phone_number VARCHAR(20)
);

CREATE TABLE ApplicationDetail (
    detail_id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT,
    application_role VARCHAR(100) DEFAULT NULL,
    cv_path TEXT,
    FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
);

"""
    )


    f.write("-- INSERT INTO ApplicantProfile\n")
    for i, cv_file in enumerate(all_cv_files):
        first_name = fake.first_name()
        last_name = fake.last_name()
        dob = fake.date_of_birth(minimum_age=21, maximum_age=35)
        address = fake.address().replace("\n", ", ").replace("'", "''")  
        phone = "08" + "".join(fake.random_choices(elements="0123456789", length=10))

        f.write(
            f"INSERT INTO ApplicantProfile (first_name, last_name, date_of_birth, address, phone_number) "
            f"VALUES ('{first_name}', '{last_name}', '{dob}', '{address}', '{phone}');\n"
        )

    f.write("\n-- INSERT INTO ApplicationDetail\n")
    for i, cv_file in enumerate(all_cv_files):
        applicant_id = i + 1
        random_role = random.choice(roles)


        f.write(
            f"INSERT INTO ApplicationDetail (applicant_id, application_role, cv_path) "
            f"VALUES ({applicant_id}, '{random_role}', '{cv_file}');\n"
        )

print("Fresh SQL file generated!")
print(f"- Created {len(all_cv_files)} applicants")
print(f"- Created {len(all_cv_files)} applications")
print(f"- All CV paths are just filenames")
