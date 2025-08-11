# Django Codebase — Dual-Schema Setup (Auth & Application)

This project is a Django codebase configured to use **two PostgreSQL schemas** in a single database for clean isolation: one schema for **authorization** and another for the **application domain**. It also ships with a **predefined logger**, a **centralized configuration loader**, **JWT authentication**, and **rate limiting** for secure API operations.

> **Why two schemas?**  
> To keep authentication (users, permissions, sessions, etc.) separate from application data. This can simplify access control, backups, and migrations, and helps reduce blast radius.

---

## Features

- **Predefined logger** with daily file rotation pattern and consistent log format — logs are written under `./logs/`.  
- **Centralized configuration** via `config/config.ini` + `.env` (for secrets like DB credentials).  
- **Custom user model** (`accounts_app.User`) to extend auth fields cleanly.  
- **Two Postgres schemas** in the **same database**:
  - `auth_realm` for Django auth, admin, contenttypes and `accounts_app`.
  - `application_realm` for app data.
- **Database Routers** to ensure reads/writes and migrations target the right schema in the right order.
- **JWT Authentication** using `djangorestframework-simplejwt` for secure API access.
- **Rate Limiting** protection against brute force attacks and API abuse.
- **DRF-ready endpoints** for complete user management (CRUD operations).
- **Docker support** with AWS ECR deployment instructions.

---

## Project Structure (high level)

```
knowlix/                           # Project root
├── .knowlix/                      # VS Code workspace settings
├── .local-certs/                  # Local SSL certificates
├── .pytest_cache/                 # pytest cache files
├── accounts_app/                  # Custom user management app
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── forms.py
│   └── urls.py
├── config/                        # Configuration directory
│   └── config.ini                 # Non-secret configuration
├── django_main/                   # Main Django project
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── AuthRouter.py
│   ├── ApplicationRouter.py
│   └── templates/
├── EC2_Application_directory/     # AWS deployment configs
│   ├── media/
│   ├── nginx/
│   │   ├── certs/
│   │   │   ├── nginx.conf
│   │   │   └── site.conf
│   │   └── static/
│   └── docker-compose.yml
├── helper/                        # Utility modules
│   ├── configuration.py           # Centralized config loader
│   ├── logger_setup.py           # Logging configuration
│   └── Get_Username_Object.py    # User fetching utilities
├── home_app/                      # Main application
│   ├── views.py
│   └── urls.py
├── logs/                          # Application logs (auto-created)
│   └── ...                       # Daily rotating log files
├── static/                        # Static files (collectstatic)
├── .dockerignore                  # Docker ignore patterns
├── .env                          # Environment variables (secrets)
├── Dockerfile                    # Docker image definition
├── knowlix.code-workspace        # VS Code workspace file
├── manage.py                     # Django management script
├── README.md                     # This documentation
└── requirements.txt              # Python dependencies
```

---

## Requirements

- Python 3.11+
- PostgreSQL 13+ (single database with two schemas: `auth_realm`, `application_realm`)
- Required packages (add to `requirements.txt`):

```
Django>=5.2
psycopg3
python-dotenv
djangorestframework
djangorestframework-simplejwt
django-ratelimit
```

---

## Configuration

### 1) Environment variables (`.env`)

Store secrets in `.env` at the project root:

```
db_username=postgres
db_password=postgres
```

> These are used by the configuration loader to avoid committing secrets.

### 2) App config (`config/config.ini`)

**`config/config.ini` example:**

```ini
[database_connection]
host = your-rds-instance.xxxxxxxxxx.region.rds.amazonaws.com
database_name = your_database_name
```

- The code reads this file to resolve non-secret parameters (RDS endpoint & database name).
- Secrets (username/password) come from `.env`.
- **Important:** Use your actual AWS RDS endpoint, not localhost.

---

## Database Setup (AWS RDS)

This project is configured to use **AWS RDS PostgreSQL** with two schemas. The database configuration is fetched from your AWS RDS instance.

### AWS RDS Configuration

1. **Create RDS PostgreSQL Instance** in AWS Console:
   - Choose PostgreSQL engine
   - Configure instance size based on your needs
   - Set up VPC and security groups
   - Note down the endpoint, username, and password

2. **Create Schemas in RDS**:
   Connect to your RDS instance and create the required schemas:

   ```sql
   CREATE SCHEMA IF NOT EXISTS auth_realm;
   CREATE SCHEMA IF NOT EXISTS application_realm;
   ```

3. **Grant Permissions**:
   ```sql
   GRANT ALL PRIVILEGES ON SCHEMA auth_realm TO your_rds_user;
   GRANT ALL PRIVILEGES ON SCHEMA application_realm TO your_rds_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth_realm TO your_rds_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA application_realm TO your_rds_user;
   ```

### Environment Configuration

Update your configuration files to point to AWS RDS:

**`.env` file:**
```
db_username=your_rds_username
db_password=your_rds_password
```

**`config/config.ini` file:**
```ini
[database_connection]
host = your-rds-instance.xxxxxxxxxx.region.rds.amazonaws.com
database_name = your_database_name
```

> **Note:** The `host` should be your **AWS RDS endpoint**, not `127.0.0.1`. The database and schemas should already exist in your RDS instance before running migrations.

---

## Django Settings — Key Configuration

- **Custom user model**: `AUTH_USER_MODEL = "accounts_app.User"`
- **Multiple DBs** in `DATABASES`:
  - `default`: Standard connection to the database
  - `auth_realm` uses `OPTIONS: {"options": "-c search_path=auth_realm,public"}`
  - `application_realm` uses `OPTIONS: {"options": "-c search_path=application_realm,public"}`
- **Database Routers** (order matters):
  ```python
  DATABASE_ROUTERS = [
      "django_main.AuthRouter.AuthRouter",
      "django_main.ApplicationRouter.ApplicationRouter",
  ]
  ```
- **JWT Authentication** configured with:
  - Access token lifetime: 180 minutes
  - Refresh token lifetime: 1 day
  - No token rotation for simplicity

> **Important:** All databases point to the same PostgreSQL instance (same NAME/HOST/PORT), using separate **schemas** not separate databases.

---

## Migrations (IMPORTANT — run in this exact order)

Run **exactly** in the order below to ensure auth-related tables land in `auth_realm` first, followed by application tables:

```bash
# 1) Auth & user models (admin, auth, contenttypes, accounts_app)
python manage.py migrate --database=auth_realm

# 2) Application models (home_app and other app data)
python manage.py migrate --database=application_realm

# 3) Final sync (for anything un-routed / multi-app dependencies)
python manage.py migrate
```

> **Migration Reset:** If you need to reset, clear the DB tables/schemas and delete migration files in your apps (except `__init__.py`), then re-run `makemigrations` + the sequence above.

---

## Running Locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Make sure schemas exist in Postgres, and .env + config/config.ini are in place.
python manage.py makemigrations
python manage.py migrate --database=auth_realm
python manage.py migrate --database=application_realm
python manage.py migrate

# Create an admin user (will go into auth_realm)
python manage.py createsuperuser

python manage.py runserver
```

Navigate to `http://127.0.0.1:8000/`

---

## Authentication & Security

### JWT Authentication

The project uses JWT tokens for API authentication:

- **Access tokens**: Valid for 3 hours
- **Refresh tokens**: Valid for 1 day
- Include `Authorization: Bearer <access_token>` header in API requests

### Rate Limiting

Protection against abuse with different limits:
- **HTML views**: 5-10 requests per minute per IP
- **API endpoints**: 5 requests per minute per IP
- Automatic blocking when limits exceeded

---

## API Endpoints

### User Management

All API endpoints are prefixed based on your main URL configuration. Assuming `accounts_app` URLs are included at root level:

#### 1. Create User
```http
POST /api/createuser/
Content-Type: application/json

{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe",
    "birthdate": "1990-01-15",
    "nationalid": "123456789",
    "phonenumber": "+1234567890"
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "message": "User created successfully.",
    "data": {
        "id": 1,
        "username": "newuser",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

**GET Request (to see required fields):**
```http
GET /api/createuser/
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "This endpoint creates users (POST only).",
    "data": {
        "fields_required": [
            "username", "email", "password", "first_name", 
            "last_name", "birthdate", "nationalid", "phonenumber"
        ]
    }
}
```

#### 2. Request JWT Token
```http
POST /api/requesttoken/
Content-Type: application/json

{
    "username_or_email": "newuser",
    "password": "securepassword123"
}
```

**Note:** You can use either username OR email in the `username_or_email` field.

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Token issued.",
    "data": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

**Error Response (401 Unauthorized):**
```json
{
    "success": false,
    "message": "Invalid username or password."
}
```

#### 3. Refresh JWT Token
```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 4. Update User (Authenticated)
```http
PUT /api/updateuser/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "first_name": "Jane",
    "email": "jane@example.com",
    "birthdate": "1990-05-20",
    "phonenumber": "+9876543210"
}
```

**Available fields for update:**
- `username`, `email`, `password`, `first_name`, `last_name`
- `birthdate`, `nationalid`, `phonenumber`

**Response (200 OK):**
```json
{
    "success": true,
    "message": "User updated successfully."
}
```

#### 5. Partial Update User (Authenticated)
```http
PATCH /api/updateuser/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "first_name": "Jane"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "User updated successfully."
}
```

#### 6. Delete User (Authenticated)
```http
DELETE /api/deleteuser/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "User deleted successfully."
}
```

### Error Responses

All endpoints return consistent error format:

```json
{
    "success": false,
    "message": "Error description",
    "errors": {
        "field_name": ["Specific error details"]
    }
}
```

Common HTTP status codes:
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side error

---

## HTML Views (Traditional Forms)

For non-API usage, the following HTML views are available:

- `/login/` — User login form (accepts username OR email + password)
- `/logout/` — User logout (redirects to home)  
- `/create_view/` — User registration form (includes username, email, password, birthdate, phonenumber)

### Form Fields:

**Login Form:**
- `username_or_email` - Can enter either username or email
- `password` - User password

**Registration Form:**
- `username`, `password1`, `password2` - Standard Django fields
- `email` - Unique email address
- `birthdate` - Date picker field
- `phonenumber` - Phone number field

These views include CSRF protection, Django messages for user feedback, and rate limiting (10/min for login, 5/min for registration).

---

## Logging

- Logs are written into `./logs/` automatically.
- Each logger gets a file named like `<LOGGER_NAME>_YYYYMMDD.log`.
- Default format: `'%(asctime)s - %(levelname)s - [%(module)s] - %(message)s'`

Create loggers per module:

```python
from helper.logger_setup import setup_logger
logger = setup_logger("accounts_app")
logger.info("Hello from accounts_app")
```

**Log Events Include:**
- User creation/authentication
- Token issuance
- User updates and deletions
- Error conditions and exceptions

---

## Configuration Management

The `helper/configuration.py` module provides centralized config management:

```python
from config.configuration import ConfigurationCenter

config = ConfigurationCenter()

# Get from config.ini
db_host = config.get_parameter('database_connection', 'host')

# Get from environment (.env)
db_password = config.get_environmental('db_password')
```

This approach:
- Verifies config files exist
- Provides clear error messages for missing settings
- Separates secrets from configuration
- Centralizes all config access

---

## Database Routers Explained

### AuthRouter
Routes these apps to `auth_realm`:
- `admin` - Django admin interface
- `contenttypes` - Django content types
- `auth` - Django authentication
- `accounts_app` - Custom user management

### ApplicationRouter  
Routes all other apps to `application_realm`:
- `home_app` - Main application logic
- Any future application-specific apps

> **Critical:** Router order matters — keep `AuthRouter` *before* `ApplicationRouter` in `DATABASE_ROUTERS`.

---

## Custom User Model

The custom user model (`accounts_app.User`) extends Django's `AbstractUser` with additional fields:

### Model Fields:
- **Standard Django fields**: `username`, `email`, `first_name`, `last_name`, `password`
- **Extended fields**:
  - `email` - Unique email address (required)
  - `birthdate` - Date of birth (required for registration)
  - `nationalid` - National ID number (optional)
  - `phonenumber` - Phone number (required)
  - `wallet` - Decimal field for wallet balance (default: 0)

### Required Fields:
When creating a superuser, these fields are required:
- `email`, `birthdate`, `phonenumber`

### Authentication Options:
Users can authenticate using either:
- Username + password
- Email + password

The custom `UserManager` handles user creation and ensures proper field validation.

---

## Docker Deployment

### Building the Image

1. Create `Dockerfile` and `.dockerignore` in your project root
2. Build the image:
```bash
docker build --tag base_project_aws .
```

### AWS ECR Deployment

#### Step 1: Build Docker Image (Local Computer)

On your **local development machine**:

```bash
# Navigate to your project directory (where Dockerfile is located)
cd /path/to/your/knowlix/project

# Build the Docker image
docker build --tag knowlix_app .

# Verify the image was created
docker images
```

#### Step 2: Create ECR Repository (AWS Console)

1. **Go to AWS ECR Console** (web browser)
2. **Create repository** (e.g., `knowlix-app`)
3. **Note the repository URI**: `<your-account-id>.dkr.ecr.eu-central-1.amazonaws.com/knowlix-app`

#### Step 3: Docker Authentication - Two Options

##### Option A: Using AWS CLI (If you have it installed)

On your **local computer**:
```bash
# Get the login password
aws ecr get-login-password --region eu-central-1

# This outputs a very long token - copy it, then use it in docker login:
docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.eu-central-1.amazonaws.com
# Paste the token when prompted for password

# Or combine both commands:
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.eu-central-1.amazonaws.com
```

##### Option B: Manual Authentication (Without AWS CLI)

If you **don't want to install AWS CLI** on your local machine:

1. **Get password from AWS Console**:
   - Go to ECR → Your Repository → "View push commands"
   - Copy the login password from the command shown

2. **Manual Docker Login** on your **local computer**:
   ```bash
   # Run docker login command
   docker login --username AWS <your-account-id>.dkr.ecr.eu-central-1.amazonaws.com
   
   # When prompted for password, paste the token from AWS Console
   Password: [paste the very long ECR token here]
   ```

#### Step 4: Tag and Push Image (Local Computer)

On your **local computer**:
```bash
# Tag your image for ECR
docker tag knowlix_app <your-account-id>.dkr.ecr.eu-central-1.amazonaws.com/knowlix-app:latest

# Push to ECR repository
docker push <your-account-id>.dkr.ecr.eu-central-1.amazonaws.com/knowlix-app:latest

# Verify upload in AWS ECR Console
```

#### Step 5: EC2 Setup and Deployment

##### On your EC2 Instance:

1. **Install Docker** on EC2:
   ```bash
   # For Amazon Linux 2
   sudo yum update -y
   sudo yum install -y docker
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -a -G docker ec2-user
   # Log out and log back in for group changes to take effect
   ```

2. **Setup Application Directory**:
   ```bash
   sudo mkdir -p /application
   sudo chown ec2-user:ec2-user /application
   cd /application
   
   # Copy your EC2_Application_directory contents here
   # (upload via scp, rsync, or git clone)
   ```

3. **Route 53 Domain Setup** on AWS:


## Steps to Create Domain and Route to EC2

    1. **Register Domain**: Go to AWS Route 53 → "Registered domains" → "Register domain" → Choose domain name and complete purchase
    2. **Create Hosted Zone**: Navigate to Route 53 → "Hosted zones" → "Create hosted zone" → Enter your domain name
    3. **Get EC2 Public IP**: Go to EC2 Console → Select your instance → Copy the Public IPv4 address
    4. **Create A Record**: In your hosted zone → "Create record" → Record type: "A" → Value: Your EC2 public IP
    5. **Create CNAME Record** (optional): Record name: "www" → Record type: "CNAME" → Value: your-domain.com
    6. **Update Name Servers**: Go to "Registered domains" → Select domain → "Add or edit name servers" → Copy NS records from hosted zone
    7. **Verify DNS Propagation**: Wait 24-48 hours for full propagation → Test with `nslookup your-domain.com`
    8. **Configure Security Groups**: Ensure EC2 security group allows HTTP (port 80) and HTTPS (port 443) traffic
    9. **Test Connection**: Open browser and navigate to your domain to verify routing works
    10. **Optional SSL**: Use AWS Certificate Manager to add SSL certificate for HTTPS support

3. **Generate SSL Certificates** on EC2:
   ```bash
   cd /application/nginx/certs/
   
   # Generate self-signed certificate (replace yourdomain.com with your actual domain)
   openssl req -x509 -nodes -newkey rsa:2048 \
     -keyout domain.key -out domain.crt -days 365 \
     -subj "/C=DE/ST=NRW/L=Cologne/O=Company/OU=Unit/CN=yourdomain.com" \
     -addext "subjectAltName=DNS:yourdomain.com,DNS:www.yourdomain.com"
   ```

4. **Configure Domain and Nginx** on EC2:
   ```bash
   # Edit nginx site configuration
   sudo nano /application/nginx/certs/site.conf
   
   # Replace placeholder domain names with your actual domain
   # Update server_name to match your domain
   ```

5. **Docker Authentication** on EC2:

   **Option A: With AWS CLI on EC2:**
   ```bash
   # Install AWS CLI on EC2
   sudo yum install -y awscli
   
   # Configure AWS credentials (if not using IAM roles)
   aws configure
   
   # Login to ECR
   aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.eu-central-1.amazonaws.com
   ```

   **Option B: Manual token (Recommended for EC2):**
   ```bash
   # Get the ECR password from your local machine or AWS Console
   # Then run on EC2:
   docker login --username AWS <your-account-id>.dkr.ecr.eu-central-1.amazonaws.com
   # Paste the ECR token when prompted
   ```

6. **Pull and Run Application** on EC2:
   ```bash
   # Pull your image from ECR
   docker pull <your-account-id>.dkr.ecr.eu-central-1.amazonaws.com/knowlix-app:latest
   
   # Navigate to application directory
   cd /application
   
   # Update your docker-compose.yml to use the ECR image
   # Then start the application
   docker-compose up -d
   ```
