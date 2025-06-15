from getpass import getpass
from databaseManager import DatabaseManager
from models import Applicant, Application
from setupDatabase import setup_database


def main():
    print("Masukkan kredensial database MySQL/MariaDB")
    user = input("Username: ")
    password = getpass("Password: ")

    try:
        DB_NAME = "cvApplicationDatabase"
        SQL_FILE = "../database/tubes3_seeding.sql"

        setup_database(
            host="localhost",
            user=user,
            password=password,
            db_name=DB_NAME,
            sql_path=SQL_FILE,
        )

        db = DatabaseManager(user=user, password=password)

        applicants = db.get_all_applicants()
        applications = db.get_all_applications()

        print(f"\nJumlah Pelamar: {len(applicants)}")
        print(f"Jumlah Lamaran (ApplicationDetail): {len(applications)}")

        print("\nDaftar Pelamar dan CV Path:")
        app_map = {app.applicant_id: app for app in applications}

        for a in applicants[:10]:
            app = app_map.get(a.applicant_id)
            cv_filename = app.cv_path if app else "Tidak ada"
            full_cv_path = (
                f"data/{cv_filename}"
                if app and cv_filename != "Tidak ada"
                else cv_filename
            )

            print(f"- {a.first_name} {a.last_name} | CV: {cv_filename}")
            print(
                f"  ID: {a.applicant_id}, Role: {app.application_role if app else 'Tidak ada'}"
            )
            print(f"  Full path: {full_cv_path}")
            print()

        # Test path construction
        print("🧪 Testing path construction:")
        if applications:
            test_app = applications[0]
            print(f"Database stores: '{test_app.cv_path}'")
            print(f"App will use: 'data/{test_app.cv_path}'")

        db.close()
        print("\nTes selesai. Koneksi ditutup.")

    except Exception as e:
        print(f"Gagal konek atau query ke database:\n{e}")


if __name__ == "__main__":
    main()
