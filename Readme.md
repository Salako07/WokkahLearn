# WokkahLearn Accounts API Documentation

## Overview

The WokkahLearn Accounts API provides comprehensive user authentication, registration, and profile management functionality for the AI-Powered Coding Education Platform. Built with Django REST Framework, it supports JWT token-based authentication with email verification.

**Base URL:** `/api/auth/`
**Version:** 1.0
**Authentication:** JWT Bearer Token

## Table of Contents

1. [Authentication](#authentication)
2. [Registration & Email Verification](#registration--email-verification)
3. [User Management](#user-management)
4. [Password Management](#password-management)
5. [User Data](#user-data)
6. [Error Handling](#error-handling)
7. [Security](#security)

---

## Authentication

### JWT Token Configuration
- **Access Token Lifetime:** 1 hour
- **Refresh Token Lifetime:** 7 days
- **Token Rotation:** Enabled
- **Header Format:** `Authorization: Bearer <access_token>`

---

## Registration & Email Verification

### Register User
Creates a new user account with flexible verification options.

**Endpoint:** `POST /api/auth/register/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "password_confirm": "securePassword123",
  "username": "username",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student",
  "immediate_access": true
}
```

**Response (201 - Immediate Access):**
```json
{
  "message": "Registration successful! Immediate access granted.",
  "email": "user@example.com",
  "verification_required": true,
  "user": {
    "id": "uuid",
    "username": "username",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student",
    "is_verified": false
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "immediate_access": true,
  "next_step": "You can use the app now. Please verify your email when convenient."
}
```

**Response (201 - Email-First):**
```json
{
  "message": "Registration successful! Please check your email to verify your account.",
  "email": "user@example.com",
  "verification_required": true,
  "user_id": "uuid",
  "immediate_access": false,
  "next_step": "Check your email and click the verification link to get access tokens."
}
```

### Verify Email
Confirms user email address using verification token.

**Endpoint:** `POST /api/auth/verify-email/`

**Request Body:**
```json
{
  "token": "verification_token_string"
}
```

**Response (200):**
```json
{
  "message": "Email verified successfully!",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "is_verified": true
  }
}
```

### Resend Verification Email
Sends a new verification email to unverified users.

**Endpoint:** `POST /api/auth/resend-verification/`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "Verification email sent successfully!"
}
```

### Login
Authenticates user and returns JWT tokens.

**Endpoint:** `POST /api/auth/login/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "username": "username",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "student",
    "is_verified": true,
    "is_premium": false
  },
  "message": "Login successful"
}
```

**Error Response (400 - Unverified Email):**
```json
{
  "error": "Please verify your email before logging in",
  "verification_required": true,
  "code": "email_verification_required"
}
```

### Logout
Blacklists the refresh token to log out the user.

**Endpoint:** `POST /api/auth/logout/`
**Authentication:** Required

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
  "message": "Logout successful"
}
```

---

## User Management

### Get/Update User Information
Retrieve or update basic user information.

**Endpoint:** `GET/PUT/PATCH /api/auth/user/`
**Authentication:** Required

**GET Response (200):**
```json
{
  "id": "uuid",
  "username": "username",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "student",
  "bio": "Learning enthusiast",
  "avatar": "https://example.com/avatar.jpg",
  "github_username": "johndoe",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "preferred_languages": ["python", "javascript"],
  "skill_level": "beginner",
  "is_verified": true,
  "is_premium": false,
  "timezone": "UTC",
  "language": "en"
}
```

**PUT/PATCH Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "bio": "Updated bio",
  "skill_level": "intermediate",
  "preferred_languages": ["python", "javascript", "go"],
  "github_username": "johnsmith",
  "linkedin_url": "https://linkedin.com/in/johnsmith"
}
```

### Get User Profile
Extended user profile with learning statistics.

**Endpoint:** `GET /api/auth/profile/`
**Authentication:** Required

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "username": "username",
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "total_lessons_completed": 45,
  "total_exercises_completed": 120,
  "current_streak": 7,
  "longest_streak": 21,
  "programming_skills": ["python", "javascript"],
  "weekly_goal_hours": 10,
  "ai_assistance_level": "medium",
  "preferred_explanation_style": "detailed",
  "public_profile": true,
  "show_progress": true
}
```

### Upload Avatar
Upload or update user avatar image.

**Endpoint:** `POST /api/auth/user/avatar/`
**Authentication:** Required
**Content-Type:** `multipart/form-data`

**Request Body:**
```
avatar: [image file]
```

**Response (200):**
```json
{
  "message": "Avatar uploaded successfully",
  "avatar_url": "https://example.com/avatars/user_avatar.jpg"
}
```

**Delete Avatar:**
**Endpoint:** `DELETE /api/auth/user/avatar/`

**Response (200):**
```json
{
  "message": "Avatar removed successfully"
}
```

---

## Password Management

### Change Password
Change password for authenticated users.

**Endpoint:** `POST /api/auth/change-password/`
**Authentication:** Required

**Request Body:**
```json
{
  "old_password": "currentPassword123",
  "new_password": "newSecurePassword456"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

### Request Password Reset
Initiate password reset process via email.

**Endpoint:** `POST /api/auth/password-reset/`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "Password reset email sent if account exists"
}
```

### Confirm Password Reset
Complete password reset using token from email.

**Endpoint:** `POST /api/auth/password-reset/confirm/`

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "uid": "user_id",
  "new_password": "newSecurePassword456"
}
```

**Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

---

## User Data

### Get User Skills
List programming skills for the authenticated user.

**Endpoint:** `GET /api/auth/skills/`
**Authentication:** Required

**Response (200):**
```json
[
  {
    "id": 1,
    "skill_name": "Python",
    "category": "programming_language",
    "proficiency_level": "intermediate",
    "verified": true,
    "evidence_count": 5,
    "last_assessed": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "skill_name": "JavaScript",
    "category": "programming_language",
    "proficiency_level": "beginner",
    "verified": false,
    "evidence_count": 2,
    "last_assessed": "2024-01-10T14:20:00Z"
  }
]
```

### Add User Skill
Add a new skill to user profile.

**Endpoint:** `POST /api/auth/skills/`
**Authentication:** Required

**Request Body:**
```json
{
  "skill_name": "React",
  "category": "framework",
  "proficiency_level": "beginner"
}
```

### Get User Achievements
List achievements earned by the authenticated user.

**Endpoint:** `GET /api/auth/achievements/`
**Authentication:** Required

**Response (200):**
```json
[
  {
    "id": 1,
    "achievement_id": "first_lesson",
    "achievement_type": "milestone",
    "title": "First Steps",
    "description": "Completed your first lesson",
    "icon": "🎯",
    "earned_at": "2024-01-01T12:00:00Z",
    "progress_data": {
      "lesson_id": "intro-to-python"
    }
  }
]
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": "Invalid credentials",
  "code": "invalid_credentials"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to send verification email. Please try again.",
  "code": "email_send_failed"
}
```

### Validation Errors
```json
{
  "email": ["Enter a valid email address."],
  "password": ["This password is too common."],
  "non_field_errors": ["Passwords don't match"]
}
```

---

## Security

### Rate Limiting
- **API Endpoints:** 1000 requests/hour per user
- **Login Endpoint:** 1 request/second per IP
- **General API:** 10 requests/second per IP

### Security Headers
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer-when-downgrade`

### Authentication Security
- **Password Validation:** Django's built-in validators
- **Email Verification:** Required before full access
- **Token Blacklisting:** Refresh tokens are blacklisted on logout
- **Token Rotation:** Refresh tokens rotate on each use
- **CORS:** Configured for appropriate origins

### File Upload Security
- **Avatar Files:**
  - Maximum size: 5MB
  - Allowed types: Image files only
  - Content-type validation

---

## Health Check

**Endpoint:** `GET /api/health/`

**Response (200):**
```json
{
  "status": "healthy",
  "service": "WokkahLearn Authentication API",
  "version": "1.0",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

---

## API Documentation

Interactive API documentation is available at:
- **Swagger UI:** `/api/schema/swagger-ui/`
- **ReDoc:** `/api/schema/redoc/`
- **OpenAPI Schema:** `/api/schema/`

---

## Support

For additional help:
- Check the [FAQ](docs/FAQ.md)
- Submit issues on GitHub
- Contact support at support@wokkahlearn.com