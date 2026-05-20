# Vardhaman College Event Management System

A robust, AI-powered backend API built with Python and FastAPI for managing college campus events. This system handles everything from role-based user authentication to QR-code attendance tracking and personalized event recommendations.

## Core Features
* **Role-Based Access:** Support for Students, Organizers, and Admins.
* **Smart Registration System:** Automatic capacity checking that seamlessly transitions full events into a waitlist.
* **QR Code Attendance:** Generates base64-encoded QR codes upon registration for organizers to scan at the venue door.
* **AI Recommendation Engine:** Uses TF-IDF and cosine similarity to recommend upcoming events based on a student's branch, year, and past registration history.
* **Admin Analytics:** A comprehensive dashboard aggregating real-time attendance, registration, and post-event feedback scores.

## Tech Stack
* **Framework:** FastAPI
* **Database:** SQLite & SQLAlchemy (ORM)
* **Authentication:** Passlib (Bcrypt)
* **Machine Learning:** Pandas, Scikit-learn
* **Utilities:** QRCode

