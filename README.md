# Get Fit Django Application

A Django-based web application for fitness tracking and management.

## Important Notes
- Always use `uv run` before any Python command execution
- The project uses uv as the package manager instead of pip
- Virtual environment is automatically managed by uv

## Project Structure
```
get_fit/
├── backend/         # Django backend application
└── frontend/        # Frontend application (to be added)
```

## Backend Setup Instructions

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Navigate to backend directory:
```bash
cd backend
```

3. Initialize project with uv:
```bash
uv init
```

4. Install dependencies using uv:
```bash
uv add -r requirements.txt
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

6. Run migrations:
```bash
uv run python manage.py migrate
```

7. Create a superuser:
```bash
uv run python manage.py createsuperuser
```

8. Run the development server:
```bash
uv run python manage.py runserver
```

## Development

- The project uses Django 5.0.2
- Django REST Framework for API development
- Celery for background tasks
- PostgreSQL as the database
- Redis for caching and task queues

## Backend Structure

- `core/` - Main Django project settings
- `apps/` - Django applications
- `static/` - Static files
- `templates/` - HTML templates
- `media/` - User-uploaded files

## Common Commands

- Create a new Django app:
```bash
uv run python manage.py startapp app_name
```

- Make migrations:
```bash
uv run python manage.py makemigrations
```

- Apply migrations:
```bash
uv run python manage.py migrate
```

- Run tests:
```bash
uv run python manage.py test
```

- Create a new migration:
```bash
uv run python manage.py makemigrations app_name
``` 