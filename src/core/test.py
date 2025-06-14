from getpass import getpass
from databaseManager import DatabaseManager
from models import Applicant, Application
from setupDatabase import setup_database

def main():
    print("🔐 Masukkan kredensial database MySQL/MariaDB")
    user = input("Username: ")
    password = getpass("Password: ")

    try:
        DB_NAME = "cvApplicationDatabase"
        SQL_FILE = "../database/database.sql"

        setup_database(
            host="localhost",
            user="root",
            password="root",  
            db_name=DB_NAME,
            sql_path=SQL_FILE
        )
    
        db = DatabaseManager(user=user, password=password)

        applicants = db.get_all_applicants()
        applications = db.get_all_applications()

       

        print(f"\n📋 Jumlah Pelamar: {len(applicants)}")
        print(f"📄 Jumlah Lamaran (ApplicationDetail): {len(applications)}")

        print("\n🔍 Daftar Pelamar dan CV Path:")
        app_map = {app.applicant_id: app for app in applications}

        for a in applicants[:10]:  
            app = app_map.get(a.applicant_id)
            print(f"- {a.full_name} | CV: {app.cv_path if app else '❌ Tidak ada'}")
            print(f"  ID: {a.applicant_id}, Role: {app.application_role if app else '❌ Tidak ada'}")

        db.close()
        print("\n✅ Tes selesai. Koneksi ditutup.")
    
    except Exception as e:
        print(f"❌ Gagal konek atau query ke database:\n{e}")

if __name__ == "__main__":
    main()
