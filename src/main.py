from db.model import *

if __name__ == "__main__":
    # Contoh data
    candidate_id = insert_candidate(
        name="Budi Santoso",
        email="budi@email.com",
        phone="08123456789",
        address="Jl. Kebon Jeruk No. 5",
        cv_path="/path/to/cv/budi_santoso.pdf"
    )

    insert_profile(
        candidate_id,
        summary="Lulusan ITB dengan pengalaman di bidang data science.",
        skills="Python, SQL, Machine Learning",
        experiences="Data Scientist di ABC Corp (2020-2023)",
        education="S1 Teknik Informatika, ITB, lulus 2020"
    )
