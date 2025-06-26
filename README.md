# Boilerplate - Django REST API

A scalable and secure RESTful API built with Django and Django REST Framework for a multi-user property listing platform.

## 🚀 Features

- **Custom User Model**: Email-based authentication with role-based user types (Agent, Investor, Admin, User)
- **JWT Authentication**: Secure token-based authentication using SimpleJWT
- **Comprehensive User Management**: Registration, login, profile management, password change
- **Advanced Filtering & Search**: User listing with filtering, search, and pagination
- **Custom Response Format**: Standardized API response structure
- **Comprehensive Testing**: Unit tests and integration tests using Django's test framework and pytest
- **Database Optimization**: Proper indexing and query optimization
- **Error Handling**: Centralized exception handling with custom error responses
- **Logging**: Comprehensive logging for debugging and monitoring

## 🛠 Tech Stack

- **Python 3.10+**
- **Django 5.0+**
- **Django REST Framework 3.14+**
- **Django SimpleJWT 5.3+**
- **PostgreSQL** (production) / **SQLite** (development)
- **Redis** (for caching and task queues)
- **Celery** (for background tasks)
- **Django Filter** (for advanced filtering)
- **Pytest** (for testing)

## 📋 Prerequisites

- Python 3.10 or higher
- uv package manager
- PostgreSQL (for production)
- Redis (for caching and Celery)

## 🚀 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd get_fit/backend
   ```

2. **Install dependencies using uv**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migrations**
   ```bash
   uv run python manage.py makemigrations
   uv run python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   uv run python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   uv run python manage.py runserver
   ```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication
All protected endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

### User Endpoints

#### 1. User Registration
**POST** `/users/register/`

Register a new user account.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123",
    "confirm_password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "user_type": "agent",
    "company_name": "Real Estate Co",
    "license_number": "LIC123456",
    "bio": "Experienced real estate agent",
    "website": "https://example.com"
}
```

**Response:**
```json
{
    "message": "User registered successfully",
    "data": {
        "user_id": 1,
        "email": "user@example.com"
    },
    "error": null
}
```

#### 2. User Login
**POST** `/users/login/`

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "message": "Login successful",
    "data": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "email": "user@example.com",
            "full_name": "John Doe",
            "user_type": "agent"
        }
    },
    "error": null
}
```

#### 3. Token Refresh
**POST** `/users/token/refresh/`

Refresh the access token using a refresh token.

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 4. Get User Profile
**GET** `/users/profile/`

Get current user's profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "message": "Profile retrieved successfully",
    "data": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "display_name": "John Doe",
        "phone_number": "+1234567890",
        "user_type": "agent",
        "is_verified": false,
        "date_joined": "2024-01-15T10:30:00Z",
        "last_login": "2024-01-15T14:20:00Z",
        "company_name": "Real Estate Co",
        "license_number": "LIC123456",
        "bio": "Experienced real estate agent",
        "website": "https://example.com",
        "profile_picture": null
    },
    "error": null
}
```

#### 5. Update User Profile
**PUT** `/users/profile/`

Update current user's profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Smith",
    "bio": "Updated bio information",
    "website": "https://newwebsite.com"
}
```

#### 6. Change Password
**POST** `/users/change-password/`

Change user's password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "old_password": "currentpassword123",
    "new_password": "newpassword123",
    "confirm_new_password": "newpassword123"
}
```

#### 7. List Users
**GET** `/users/users/`

Get a list of users with filtering and search capabilities.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `user_type`: Filter by user type (agent, investor, admin, user)
- `is_verified`: Filter by verification status (true/false)
- `search`: Search in email, first_name, last_name, company_name
- `ordering`: Sort by date_joined, email, first_name, last_name
- `page`: Page number for pagination

**Example:**
```
GET /users/users/?user_type=agent&search=john&ordering=-date_joined&page=1
```

**Response:**
```json
{
    "message": "Users retrieved successfully",
    "data": {
        "users": [
            {
                "id": 1,
                "email": "agent@example.com",
                "full_name": "John Doe",
                "user_type": "agent",
                "is_verified": true,
                "date_joined": "2024-01-15T10:30:00Z"
            }
        ],
        "count": 1,
        "next": null,
        "previous": null
    },
    "error": null
}
```

#### 8. Get User Details
**GET** `/users/users/{user_id}/`

Get detailed information about a specific user.

**Headers:**
```
Authorization: Bearer <access_token>
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/get_fit_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=5
JWT_REFRESH_TOKEN_LIFETIME=1

# Email Settings (for production)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration

For production, update the database settings in `core/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'get_fit_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run python manage.py test

# Run specific test file
uv run python manage.py test users.tests

# Run with coverage
uv run coverage run --source='.' manage.py test
uv run coverage report
uv run coverage html
```

### Test Structure

- **Model Tests**: Test user model creation, validation, and methods
- **Serializer Tests**: Test data validation and serialization
- **View Tests**: Test API endpoints and responses
- **Integration Tests**: Test complete user workflows

## 📊 Database Schema

### User Model

```python
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=17, blank=True)
    user_type = models.CharField(max_length=10, choices=UserType.choices)
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now, db_index=True)
    last_login = models.DateTimeField(null=True, blank=True)
    profile_picture = models.URLField(blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
```

### User Types

- **agent**: Real estate agents
- **investor**: Property investors
- **admin**: System administrators
- **user**: Regular users

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Validation**: Strong password requirements
- **Email Validation**: Proper email format validation
- **Phone Number Validation**: International phone number format
- **CSRF Protection**: Built-in Django CSRF protection
- **SQL Injection Protection**: Django ORM protection
- **XSS Prevention**: Django template protection

## 🚀 Deployment

### Production Checklist

1. **Environment Variables**: Set all production environment variables
2. **Database**: Configure PostgreSQL database
3. **Static Files**: Configure static file serving
4. **Security**: Set `DEBUG=False` and configure `ALLOWED_HOSTS`
5. **HTTPS**: Configure SSL/TLS certificates
6. **Monitoring**: Set up logging and monitoring
7. **Backup**: Configure database backups

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request
