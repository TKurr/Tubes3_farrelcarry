import mysql.connector
from typing import List
from models import Applicant, Application

class DatabaseManager:
    _instance = None 

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, host="localhost", user="root", password="", database="cvApplicationDatabase"):
        if not hasattr(self, "conn"):  # Prevent re-initialization on multiple instantiations
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor(dictionary=True)

    def get_all_applicants(self) -> List[Applicant]:
        self.cursor.execute("SELECT * FROM ApplicantProfile")
        rows = self.cursor.fetchall()
        return [Applicant(**row) for row in rows]

    def get_all_applications(self) -> List[Application]:
        self.cursor.execute("SELECT * FROM ApplicationDetail")
        rows = self.cursor.fetchall()
        return [Application(**row) for row in rows]
    
    def get_applicant_by_id(self, applicant_id: int) -> Applicant:
        self.cursor.execute("SELECT * FROM ApplicantProfile WHERE applicant_id = %s", (applicant_id,))
        row = self.cursor.fetchone()
        return Applicant(**row) if row else None
    
    def get_applications_id(self, applicant_id: int) -> List[Application]:
        self.cursor.execute("SELECT * FROM ApplicationDetail WHERE applicant_id = %s", (applicant_id,))
        rows = self.cursor.fetchall()
        return [Application(**row) for row in rows]

    def close(self):
        if self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            DatabaseManager._instance = None  # Reset singleton when closed
