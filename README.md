# Coderr Backend

Django REST Framework API Backend for the Coderr Frontend project.

A clean, optimized Django REST API following best practices with resource-oriented URLs, custom filter backends, database query optimizations, and comprehensive permission management.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Special Features](#special-features)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- Virtual Environment (highly recommended)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Coderr-Backend
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user. You can access the admin interface at `http://127.0.0.1:8000/admin/` after starting the server.

### 6. Create Test Users (Optional)

To create test users for development:

```bash
python create_test_users.py
```

This creates:
- **Customer User**: username=`andrey`, password=`asdasd`
- **Business User**: username=`kevin`, password=`asdasd24`

## Configuration

### Environment Variables

The project uses Django's default settings. For production, you should:

1. Set `DEBUG = False` in `core/settings.py`
2. Change `SECRET_KEY` to a secure random value
3. Configure proper database settings (PostgreSQL recommended for production)
4. Set up proper CORS origins in `CORS_ALLOWED_ORIGINS`

### CORS Configuration

CORS is configured for local development. Allowed origins are defined in `core/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
```

For production, update this list with your frontend domain.

## Running the Server

Start the development server:

```bash
python manage.py runserver
```

The server will run on `http://127.0.0.1:8000/`

To run on a specific port:

```bash
python manage.py runserver 8000
```

## API Endpoints

### Authentication

- `POST /api/login/` - User Login
  - Request Body: `{ "username": "string", "password": "string" }`
  - Returns: Token, user_id, username, email

- `POST /api/registration/` - User Registration
  - Request Body: `{ "username": "string", "email": "string", "password": "string", "repeated_password": "string", "type": "customer" | "business", "first_name": "string", "last_name": "string" }`
  - Returns: Token, user_id, username, email

### Profile

- `GET /api/profile/` - Get current authenticated user's profile
- `GET /api/profiles/business/` - List all business profiles (authenticated)
- `GET /api/profiles/customer/` - List all customer profiles (authenticated)
- `GET /api/profile/{pk}/` - Get profile by ID (authenticated)
- `PATCH /api/profile/{pk}/` - Update profile (owner only)

### Offers

- `GET /api/offers/` - List all offers (with filtering and pagination)
- `GET /api/offers/{id}/` - Get single offer (authenticated)
- `POST /api/offers/` - Create new offer (business users only)
- `PATCH /api/offers/{id}/` - Update offer (owner only)
- `DELETE /api/offers/{id}/` - Delete offer (owner only)

**Filter Parameters for Offers:**
- `creator_id` - Filter by creator user ID (integer)
- `search` - Search in title and description (string)
- `ordering` - Sorting (`updated_at`, `-updated_at`, `min_price`, `-min_price`)
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 6, max: 100)
- `min_price` - Minimum price filter (number, validates type)
- `max_delivery_time` - Maximum delivery time in days (integer, validates type)

**Note:** All filter parameters are validated before applying filters. Invalid types (e.g., string instead of integer) will return `400 Bad Request` with a clear error message.

**Example:**
```
GET /api/offers/?creator_id=1&search=web&ordering=min_price&page=1&page_size=6&min_price=100&max_delivery_time=7
```

### Offer Details

- `GET /api/offerdetails/{id}/` - Get single offer detail (authenticated)
- `GET /api/offers/details/{id}/` - Alternative URL for offer detail (authenticated)

### Orders

- `GET /api/orders/` - List all orders (own orders - customer or business partner)
- `GET /api/orders/{id}/` - Get single order
- `POST /api/orders/` - Create new order (customer users only)
  - Request Body: `{ "offer_detail_id": integer }`
- `PATCH /api/orders/{id}/` - Update order status (business partner only)
  - Request Body: `{ "status": "pending" | "in_progress" | "completed" | "cancelled" }`
- `DELETE /api/orders/{id}/` - Delete order (not allowed - returns 403 Forbidden)

### Reviews

- `GET /api/reviews/` - List all reviews (with filtering)
- `GET /api/reviews/{id}/` - Get single review
- `POST /api/reviews/` - Create new review (customer users only, one per business)
  - Request Body: `{ "business_user": integer, "rating": 1-5, "description": "string" }`
- `PATCH /api/reviews/{id}/` - Update review (owner only)
- `DELETE /api/reviews/{id}/` - Delete review (owner only)

**Filter Parameters for Reviews:**
- `business_user_id` - Filter by business user ID
- `reviewer_id` - Filter by reviewer (customer) ID
- `ordering` - Sorting (`updated_at`, `-updated_at`, `rating`, `-rating`)

### Additional Endpoints

- `GET /api/base-info/` - Base information for homepage
  - Returns: review_count, average_rating, business_profile_count, offer_count

- `GET /api/order-count/{business_user_id}/` - Count of in-progress orders for a business user
- `GET /api/orders/business/{business_user_id}/count/` - Alternative URL for order count
- `GET /api/completed-order-count/{business_user_id}/` - Count of completed orders for a business user
- `GET /api/orders/business/{business_user_id}/completed-count/` - Alternative URL for completed order count

## Authentication

The API uses **Token Authentication**. After successful login or registration, you will receive a token that must be sent in the request headers:

```
Authorization: Token <your-token>
```

**Example using curl:**
```bash
curl -H "Authorization: Token your-token-here" http://127.0.0.1:8000/api/profile/
```

**Example using JavaScript (fetch):**
```javascript
fetch('http://127.0.0.1:8000/api/profile/', {
  headers: {
    'Authorization': 'Token your-token-here'
  }
})
```

## Project Structure

```
Coderr-Backend/
├── accounts_app/          # User authentication and profiles
│   ├── api/               # API-specific files
│   │   ├── permissions.py # Custom permissions (IsOwnerOrReadOnly)
│   │   ├── serializers.py # User serializers
│   │   ├── urls.py        # API URL routing
│   │   └── views.py       # Authentication and profile views
│   ├── models.py          # User, BusinessProfile, CustomerProfile
│   ├── admin.py           # Django admin configuration
│   └── migrations/        # Database migrations
├── offers/                # Offers and offer details
│   ├── api/               # API-specific files
│   │   ├── filters.py     # Custom filter backends (OfferFilterBackend, OfferOrderingFilter)
│   │   ├── permissions.py # Custom permissions (IsOfferOwner, IsBusinessUser)
│   │   ├── serializers.py # Offer serializers
│   │   ├── urls.py        # API URL routing
│   │   └── views.py       # Offer ViewSet and OfferDetailView
│   ├── models.py          # Offer, OfferDetail
│   ├── pagination.py      # Custom pagination (OfferPagination)
│   ├── admin.py           # Django admin configuration
│   └── migrations/        # Database migrations
├── orders/                # Order management
│   ├── api/               # API-specific files
│   │   ├── permissions.py # Custom permissions (IsOrderOwner, IsBusinessPartner, etc.)
│   │   ├── serializers.py # Order serializers
│   │   ├── urls.py        # API URL routing
│   │   └── views.py       # Order ViewSet and count views
│   ├── models.py          # Order model
│   ├── admin.py           # Django admin configuration
│   └── migrations/        # Database migrations
├── reviews/               # Review system
│   ├── api/               # API-specific files
│   │   ├── permissions.py # Custom permissions (IsReviewOwner, IsCustomerUser)
│   │   ├── serializers.py # Review serializers
│   │   ├── urls.py        # API URL routing
│   │   └── views.py       # Review ViewSet
│   ├── models.py          # Review model
│   ├── admin.py           # Django admin configuration
│   └── migrations/        # Database migrations
├── core/                  # Main project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Central URL routing
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── create_test_users.py   # Script to create test users
└── README.md              # This file
```

## Development

### Admin Interface

The Django Admin interface is available at:
`http://127.0.0.1:8000/admin/`

Login with the superuser credentials created during setup.

### Media Files

Uploaded images (profile pictures, offer images) are stored in the `media/` folder. This folder is automatically created when the first file is uploaded.

**Important:** The `media/` folder is excluded from Git via `.gitignore`. Make sure to handle media files properly in production (e.g., using cloud storage like AWS S3).

### Database

The project uses SQLite by default for development. The database file (`db.sqlite3`) is excluded from Git.

**For Production:**
- Use PostgreSQL, MySQL, or another production-ready database
- Update `DATABASES` in `core/settings.py`
- Never commit database files to version control

### Code Style

The project follows Django REST Framework best practices and clean code principles:
- Uses `ModelViewSet` for CRUD operations
- Uses `APIView` for individual endpoints
- Resource-oriented URLs (not action-based)
- Clear separation of concerns (Models, Serializers, Views, Permissions)
- Custom filter backends for complex filtering logic
- Database-level calculations using `annotate()` and `aggregate()`
- Optimized queries using `prefetch_related()` and `select_related()`
- No redundant code or duplicate validations
- Clean, compact code without unnecessary documentation

## Testing

Run the test suite:

```bash
python manage.py test
```

Run tests for a specific app:

```bash
python manage.py test accounts_app
python manage.py test offers
python manage.py test orders
python manage.py test reviews
```

## Special Features

### 1. Custom User Model

The project uses a custom User model (`accounts_app.User`) that extends Django's `AbstractUser` with:
- `user_type` field (customer or business)
- Custom profile models (BusinessProfile, CustomerProfile)
- Automatic profile creation on user registration

### 2. Token Authentication

All authenticated endpoints require a valid token in the Authorization header.

### 3. Pagination

- **Offers**: Uses custom pagination (`OfferPagination`) with configurable `page_size` (default: 6, max: 100)
- **Orders**: No pagination (returns all results via `NoPagination`)
- **Reviews**: Custom pagination (`ReviewPagination`) - all results by default, paginated if `page_size` is specified (max: 100)

### 4. Filtering and Sorting

- **Offers**: Support multiple filter parameters and custom sorting via custom filter backends
  - Filter by `creator_id`, `min_price`, `max_delivery_time`
  - Search in `title` and `description`
  - Order by `updated_at`, `min_price` (requires annotation)
  - Custom `OfferFilterBackend` validates query parameters before filtering
  - Custom `OfferOrderingFilter` handles `min_price` ordering with database annotations
- **Reviews**: Support filtering by `business_user_id` and `reviewer_id`
- All filter parameters are optional

### 5. File Uploads

- Profile pictures and offer images are handled via Django's FileField/ImageField
- Uses Pillow for image processing
- Files are stored in `media/` directory

### 6. CORS Configuration

CORS is configured to allow requests from frontend development servers. The allowed origins are:
- `http://localhost:5500`
- `http://127.0.0.1:5500`
- `http://localhost:8000`
- `http://127.0.0.1:8000`

Update `CORS_ALLOWED_ORIGINS` in `core/settings.py` for production.

### 7. Offer Details Validation

When creating an offer, exactly 3 offer details are required with types: `basic`, `standard`, and `premium`. The validation ensures type safety and prevents invalid data.

### 8. Database Query Optimization

The codebase uses Django ORM optimizations to prevent N+1 query problems:
- `prefetch_related('details')` for loading related OfferDetail objects efficiently
- `select_related('creator')` for loading creator User in the same query
- `annotate()` for calculating `min_price` and `min_delivery_time` directly in the database
- These optimizations significantly improve performance for large datasets

### 9. Review Uniqueness

Each customer can only create one review per business user.

### 10. Order Deletion Protection

Orders cannot be deleted once created. The `DELETE` endpoint returns `403 Forbidden` to prevent data loss.

### 11. Deleted Offer Handling

When an offer is deleted, associated orders are preserved (not deleted). However, new orders cannot be created for deleted offers. The `offer` and `offer_detail` fields in orders are set to `NULL` when the related offer is deleted.

## Troubleshooting

### Database Migration Issues

If you encounter migration errors:

```bash
python manage.py makemigrations
python manage.py migrate
```

If issues persist, you may need to reset migrations (development only):

```bash
# WARNING: This will delete all data
python manage.py flush
python manage.py makemigrations
python manage.py migrate
```

### Port Already in Use

If port 8000 is already in use:

```bash
python manage.py runserver 8001
```

### Import Errors

Make sure your virtual environment is activated and dependencies are installed:

```bash
pip install -r requirements.txt
```

### CORS Errors

If you encounter CORS errors:
1. Check that your frontend URL is in `CORS_ALLOWED_ORIGINS`
2. Ensure `CORS_ALLOW_CREDENTIALS = True` in settings
3. Verify CORS middleware is in `MIDDLEWARE` list

### Token Authentication Not Working

1. Verify the token is correctly formatted: `Authorization: Token <token>`
2. Check that the token hasn't expired (tokens don't expire by default in DRF)
3. Ensure the user account is active

### Media Files Not Serving

In development, media files are served automatically. If they don't appear:
1. Check that `MEDIA_URL` and `MEDIA_ROOT` are configured in settings
2. Verify the URL pattern in `urls.py` includes media file serving
3. Ensure the `media/` folder exists and has proper permissions

## License

This project is intended for students of the Developer Academy.

## Support

For issues or questions, please contact the project maintainer or create an issue in the repository.
