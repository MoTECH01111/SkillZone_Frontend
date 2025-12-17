# SkillZONE Frontend – Flask Client Application

## Overview
This repository contains the **frontend client** for the SkillZONE SaaS application.  
The frontend is built using **Flask** and communicates with a **Ruby on Rails API-only backend** via RESTful HTTP requests using JSON and multipart data.

The frontend is responsible for:
- User interaction and navigation
- Session management and authentication handling
- Role-based user interfaces Admin and Employee
- Rendering views using server-side templates
- Generating and uploading course completion certificates

This application follows a **MVC-style architecture**, allowing the frontend and backend to be developed, tested, and deployed independently.

---

## Key Features

- User authentication and session management
- Role-based dashboards for Admins and Employees
- Course discovery, enrolment, and progress tracking
- PDF certificate generation using ReportLab
- RESTful communication with the backend API

---

## Technology Stack

- **Framework:** Flask (Python)
- **Templating:** Jinja2
- **HTTP Client:** Requests
- **PDF Generation:** ReportLab
- **Testing:** Pytest
- **Backend API:** Ruby on Rails (API-only)

---

## Prerequisites

Ensure the following are installed:
- Python 3.9+
- pip
- Git

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/MoTECH01111/SkillZone_Frontend.git
cd SkillZone_Frontend

Create Virtual Environment
python -m venv .venv
Activate the virtual environment:
macOS / Linux
source .venv/bin/activate
Windows
.venv\Scripts\activate
3. Install Dependencies
pip install -r requirements.txt

