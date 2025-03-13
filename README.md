# Forum-template

Django forum template, with almost all logic.

## Overview

This project is a Django-based forum template providing a foundation for building online discussion platforms. It includes user authentication, forum posts (notes), comments, and user profiles.

## Features

* **User Authentication:** User registration, login, logout, and password management (including password reset).
* **Forum Posts (Notes):** Creating, viewing, editing, and deleting forum posts.
* **Comments:** Users can comment on forum posts, with editing and deletion capabilities.
* **User Profiles:** Users have profiles to manage their information.
* **Image Uploads:** Support for uploading images within forum posts.
* **Like Functionality:** Users can like forum posts and comments.
* **Location Tracking:** Notes can have location information (latitude, longitude, and text location).
* **Pagination:** Implements pagination for notes.
* **Logging:** Logging of user clicks and other events.
* **Custom Template Tags and Filters:** Includes custom template tags and filters.

## Technologies Used

* Python 3.11
* Django (Python framework)
* SQLite (default development database)
* MySQL or PostgreSQL (production - configurable via environment variables)
* HTML
* CSS
* JavaScript
* Tailwind

## Project Structure

The project is structured as a standard Django project:

Forum-template/
├── django_app/          # Django application containing the forum logic
│   ├── migrations/     # Database migrations
│   ├── models.py       # Database models
│   ├── views.py        # View functions
│   ├── urls.py         # Application-specific URLs
│   ├── admin.py        # Django admin configuration
│   ├── forms.py        # Forms for user input
│   ├── templatetags/  # Custom template tags
│   ├── context_processors.py # Context processors
│   ├── middleware.py   # Middleware components
│   ├── utils.py        # Utility functions
│   ├── apps.py         # Application configuration
│   ├── tests.py        # Tests for the application
│   └── ...
├── django_settings/     # Django project settings
│   ├── settings.py    # Main settings file (should be refactored for better env management)
│   ├── urls.py        # Project-level URLs
│   ├── asgi.py        # ASGI configuration
│   └── wsgi.py        # WSGI configuration
├── templates/         # HTML templates
│   ├── components/    # Reusable template components
│   ├── partials/      # Template partials
│   └── ...
├── static/             # Static files (CSS, JavaScript, images)
│   ├── css/
│   │   ├── style.css
│   │   └── bootstrap/
│   │       ├── css/
│   │       └── js/
│   └── js/
│       └── user-interactions.js
├── .env                # Environment variables (for local development)
├── manage.py           # Django management script
├── README.md           # This file
├── requirements.txt    # Python dependencies


## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/BladEvgen/Forum-template.git
    cd Forum-template
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    * Create a `.env` file in the project root.
    * Add the necessary environment variables (e.g., `SECRET_KEY`, database settings).  Example:

        ```
        SECRET_KEY=your_secret_key_here
        DB_TYPE=sqlite3
        #  For MySQL or PostgreSQL:
        #DB_NAME=your_db_name
        #DB_USER=your_db_user
        #DB_PASSWORD=your_db_password
        #DB_HOST=your_db_host
        #DB_PORT=your_db_port
        ```

5.  **Apply database migrations:**

    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser (for Django admin):**

    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**

    ```bash
    python manage.py runserver
    ```

8.  **Access the application in your browser:** `http://127.0.0.1:8000/`

## Configuration

* **Database:**
    * The project defaults to SQLite for development.
    * To use MySQL or PostgreSQL, set the `DB_TYPE` environment variable to `mysql` or `postgresql` respectively, and provide the necessary database credentials in the `.env` file.
* **Email:**
    * Email settings (e.g., for password reset) are configured via environment variables.  You'll need to set `EMAIL_BACKEND`, `EMAIL_HOST`, etc. in your `.env` file or system environment variables.
* **Security:**
    * **IMPORTANT:** In production, ensure you change the `SECRET_KEY` to a strong, randomly generated value and store it securely (e.g., as a system environment variable).
    * **IMPORTANT:** In production, set `DEBUG = False` in your settings.
    * **IMPORTANT:** Configure `ALLOWED_HOSTS` in your settings to prevent security vulnerabilities.
