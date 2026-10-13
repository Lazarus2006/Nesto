# Nesto | Technical Documentation

Nesto is a community-driven platform designed to help students and newcomers discover useful local information when moving to an unfamiliar city.

This document focuses on Nesto's technical architecture, development setup, application structure, and implementation considerations. For the problem statement, product philosophy, intended community workflows, and long-term vision, see [`README.md`](README.md).

- **Live Prototype:** https://nesto-01xb.onrender.com/
- **Source Code:** https://github.com/Lazarus2006/Nesto

---

## 1. Technology Stack

Nesto uses a web application architecture built with open-source technologies.

| Technology | Purpose |
|---|---|
| Python | Server-side programming and application logic |
| Django | Web framework for request handling, routing, views, and database interaction |
| PostgreSQL | Relational database for persistent application data |
| HTML | Structure of web pages |
| CSS | Styling and layout |
| JavaScript | Browser-side interactions |
| Render | Hosting and deployment of the web application |
| Git and GitHub | Version control and source code collaboration |

The exact package versions and deployment settings should be checked against the current project configuration.

## 2. Application Architecture

Nesto follows a conventional client-server architecture.

A user's browser sends requests to the Django application. Django processes the requests, interacts with PostgreSQL when necessary, and returns an appropriate response to the browser.

```text
        User
         |
         v
    Web Browser
         |
         v
   Django Application
   /       |        \
Routing   Views    Templates
             |
             v
        Django ORM
             |
             v
        PostgreSQL
```

### Main Components

**Frontend**

HTML, CSS, and JavaScript provide the user interface and browser-side functionality.

**Backend**

Django handles URL routing, request processing, application logic, and communication with the database.

**Database**

PostgreSQL provides relational storage for application data. Django's ORM allows the application to work with database records through Python models.

**Deployment**

The web application is deployed on Render and can be accessed through the live prototype linked above.

## 3. Core Application Concepts

The product design described in `README.md` revolves around community contributions and structured local information.

The following concepts describe the intended domain model. Refer to the current Django models and migrations for the authoritative implementation details.

### Users

Users interact with the platform and contribute information through the functionality available in the application.

### Posts

Posts allow community members to share information, experiences, questions, or recommendations.

### Cities

City-specific organization is an important part of Nesto's intended design. It allows local information to be associated with the relevant city rather than treating every location as one shared community.

### Categories

Categories group related types of local information, such as accommodation, food, study spaces, and places to explore.

### Entities

An entity represents a particular place, service, or other item that can be associated with a category.

The intended relationship between posts, categories, and entities is explained in [`README.md`](README.md). The exact relationships and constraints should be verified against the current database models.

## 4. How the Application Works

At a high level, the application follows this sequence:

1. A user accesses a page through a web browser.
2. Django receives the request through its URL routing system.
3. The appropriate view processes the request.
4. The application retrieves or updates database records when necessary.
5. Django returns a response to the browser.

The available user workflows depend on the features implemented in the current version of the application.

## 5. Local Development Setup

The following instructions describe a typical Django development environment. Commands should be run from the directory containing `manage.py`.

### Prerequisites

Install:

- Git
- Python compatible with the project
- PostgreSQL, if using a local PostgreSQL database

### Step 1: Clone the Repository

```bash
git clone https://github.com/Lazarus2006/Nesto.git
cd Nesto
```

Locate the Django project directory and navigate to the folder containing `manage.py` before running Django commands.

### Step 2: Create a Virtual Environment

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

A virtual environment keeps project dependencies separate from system-wide Python packages.

### Step 3: Install Dependencies

install the dependencies with:

```bash
pip install -r requirements.txt
```

using the requirements.txt present in the repository.

### Step 4: Configure the Database

Configure the Django database settings to connect to the appropriate PostgreSQL database.

Ensure that:

- The database exists.
- The configured database user has the required permissions.
- The connection settings match the local environment.
- Required environment variables are configured.

Do not commit database passwords, secret keys, or other credentials to GitHub.

### Step 5: Apply Database Migrations

Run:

```bash
python manage.py migrate
```

Django migrations apply the database schema changes defined by the project.

### Step 6: Create an Administrator Account

This step is optional and is only necessary when administrative access is required.

```bash
python manage.py createsuperuser
```

Follow the prompts to create the account.

### Step 7: Start the Development Server

```bash
python manage.py runserver
```

Open the local address displayed in the terminal, usually:

`http://127.0.0.1:8000/`

If a command fails, check the project's directory structure, dependency files, database settings, and environment configuration.

## 6. Configuration and Deployment

A Django deployment may require configuration for:

- Secret key management
- Debug mode
- Allowed hosts
- Database connection settings
- Static files
- Environment variables
- Production server settings

The precise requirements depend on the current project configuration.

For production deployment:

- Keep secret keys and database credentials private.
- Disable Django debug mode.
- Configure allowed hosts appropriately.
- Use secure database credentials.
- Follow the deployment configuration used by the hosted application.

Consult the current repository and Render service configuration for the exact deployment procedure.

## 7. Current Scope and Limitations

Nesto is an evolving project with a deployed web prototype. Its current capabilities should be determined from the live application and source code.

Important considerations include:

- Community-contributed information may be incomplete, outdated, or inaccurate.
- Information should not be treated as verified merely because it appears on the platform.
- Availability of local information depends on the data present in the application.
- Moderation, reporting, verification, reputation systems, rewards, and community elections should only be described as implemented if the corresponding functionality exists in the current version.
- The long-term vision includes broader city-specific discovery and mobile access, but planned features should not be confused with the current implementation.
- Users should independently confirm important information, especially accommodation conditions, current prices, service availability, and safety-related details.

## 8. Potential Technical Improvements

Possible areas for future development include:

- Expanding and testing city-specific workflows.
- Improving validation of posts, categories, and entity relationships.
- Developing moderation and information-correction workflows.
- Adding automated tests for important models, views, forms, and user journeys.
- Improving accessibility and mobile responsiveness.
- Documenting environment variables and deployment procedures as the configuration stabilizes.

These are potential development tasks, not claims that the functionality is already implemented.

## 9. References

- **Nesto README:** [`README.md`](README.md)
- **Source Repository:** https://github.com/Lazarus2006/Nesto
- **Live Prototype:** https://nesto-01xb.onrender.com/
- **Django Documentation:** https://docs.djangoproject.com/
- **Python Documentation:** https://docs.python.org/3/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/

---

**Nesto**  
*Built by Penguin Cave Squad.*

For the project's motivation, intended community model, city-guide workflow, governance ideas, and long-term vision, refer to [`README.md`](README.md). This document is intended to complement that file by focusing on technical implementation and development.
