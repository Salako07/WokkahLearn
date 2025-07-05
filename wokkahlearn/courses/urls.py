from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'categories', views.CourseCategoryViewSet, basename='course-category')
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'modules', views.ModuleViewSet, basename='module')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'exercises', views.ExerciseViewSet, basename='exercise')
router.register(r'enrollments', views.CourseEnrollmentViewSet, basename='enrollment')
router.register(r'lesson-progress', views.LessonProgressViewSet, basename='lesson-progress')
router.register(r'exercise-submissions', views.ExerciseSubmissionViewSet, basename='exercise-submission')
router.register(r'ratings', views.CourseRatingViewSet, basename='course-rating')
router.register(r'bulk', views.BulkOperationsViewSet, basename='bulk-operations')
router.register(r'search', views.AdvancedSearchViewSet, basename='advanced-search')

urlpatterns = [
    path('', include(router.urls)),
]

"""
COMPLETE ENDPOINT MAPPING FOR COURSES APP:

========================================================================
COURSE CATEGORIES
========================================================================
GET     /api/courses/categories/                    - List all categories
POST    /api/courses/categories/                    - Create category (admin/instructor)
GET     /api/courses/categories/{id}/               - Get category details
PUT     /api/courses/categories/{id}/               - Update category (admin/instructor)
PATCH   /api/courses/categories/{id}/               - Partial update category (admin/instructor)
DELETE  /api/courses/categories/{id}/               - Delete category (admin/instructor)
GET     /api/courses/categories/{id}/courses/       - Get courses in category
GET     /api/courses/categories/tree/               - Get category tree structure

========================================================================
COURSES
========================================================================
GET     /api/courses/courses/                       - List all published courses
POST    /api/courses/courses/                       - Create course (instructor)
GET     /api/courses/courses/{id}/                  - Get course details
PUT     /api/courses/courses/{id}/                  - Update course (instructor)
PATCH   /api/courses/courses/{id}/                  - Partial update course (instructor)
DELETE  /api/courses/courses/{id}/                  - Delete course (instructor)

# Course Actions
POST    /api/courses/courses/{id}/enroll/           - Enroll in course
DELETE  /api/courses/courses/{id}/unenroll/         - Unenroll from course
POST    /api/courses/courses/{id}/rate/             - Rate and review course
GET     /api/courses/courses/my_courses/            - Get user's enrolled courses
GET     /api/courses/courses/teaching/              - Get instructor's courses
GET     /api/courses/courses/{id}/reviews/          - Get course reviews

# Analytics & Reporting
GET     /api/courses/courses/{id}/analytics/        - Get course analytics
GET     /api/courses/courses/{id}/engagement/       - Get engagement metrics
GET     /api/courses/courses/{id}/performance/      - Get performance insights
GET     /api/courses/courses/{id}/export/           - Export analytics report

# Course Management
GET     /api/courses/courses/{id}/students/         - Get enrolled students (instructor)
POST    /api/courses/courses/{id}/publish/          - Publish course (instructor)
POST    /api/courses/courses/{id}/unpublish/        - Unpublish course (instructor)
GET     /api/courses/courses/{id}/structure/        - Get complete course structure

========================================================================
MODULES
========================================================================
GET     /api/courses/modules/                       - List modules (filtered by access)
POST    /api/courses/modules/                       - Create module (instructor)
GET     /api/courses/modules/{id}/                  - Get module details
PUT     /api/courses/modules/{id}/                  - Update module (instructor)
PATCH   /api/courses/modules/{id}/                  - Partial update module (instructor)
DELETE  /api/courses/modules/{id}/                  - Delete module (instructor)
GET     /api/courses/modules/{id}/lessons/          - Get lessons in module

========================================================================
LESSONS
========================================================================
GET     /api/courses/lessons/                       - List lessons (filtered by access)
POST    /api/courses/lessons/                       - Create lesson (instructor)
GET     /api/courses/lessons/{id}/                  - Get lesson details
PUT     /api/courses/lessons/{id}/                  - Update lesson (instructor)
PATCH   /api/courses/lessons/{id}/                  - Partial update lesson (instructor)
DELETE  /api/courses/lessons/{id}/                  - Delete lesson (instructor)

# Lesson Actions
POST    /api/courses/lessons/{id}/mark_completed/   - Mark lesson as completed
POST    /api/courses/lessons/{id}/bookmark/         - Toggle lesson bookmark
GET     /api/courses/lessons/{id}/exercises/        - Get exercises in lesson

========================================================================
EXERCISES
========================================================================
GET     /api/courses/exercises/                     - List exercises (filtered by access)
POST    /api/courses/exercises/                     - Create exercise (instructor)
GET     /api/courses/exercises/{id}/                - Get exercise details
PUT     /api/courses/exercises/{id}/                - Update exercise (instructor)
PATCH   /api/courses/exercises/{id}/                - Partial update exercise (instructor)
DELETE  /api/courses/exercises/{id}/                - Delete exercise (instructor)

# Exercise Actions
POST    /api/courses/exercises/{id}/submit/         - Submit exercise solution
GET     /api/courses/exercises/{id}/submissions/    - Get user's submissions
POST    /api/courses/exercises/{id}/get_hint/       - Get AI-powered hint
POST    /api/courses/exercises/{id}/provide_feedback/ - Provide instructor feedback

========================================================================
ENROLLMENTS
========================================================================
GET     /api/courses/enrollments/                   - List user's enrollments
GET     /api/courses/enrollments/{id}/              - Get enrollment details
GET     /api/courses/enrollments/{id}/progress_detail/ - Get detailed progress

========================================================================
LESSON PROGRESS
========================================================================
GET     /api/courses/lesson-progress/               - List lesson progress
POST    /api/courses/lesson-progress/               - Create progress entry
GET     /api/courses/lesson-progress/{id}/          - Get progress details
PUT     /api/courses/lesson-progress/{id}/          - Update progress
PATCH   /api/courses/lesson-progress/{id}/          - Partial update progress
DELETE  /api/courses/lesson-progress/{id}/          - Delete progress

========================================================================
EXERCISE SUBMISSIONS
========================================================================
GET     /api/courses/exercise-submissions/          - List submissions (filtered)
GET     /api/courses/exercise-submissions/{id}/     - Get submission details
POST    /api/courses/exercise-submissions/{id}/provide_feedback/ - Provide feedback

========================================================================
COURSE RATINGS & REVIEWS
========================================================================
GET     /api/courses/ratings/                       - List ratings (filtered)
POST    /api/courses/ratings/                       - Create rating/review
GET     /api/courses/ratings/{id}/                  - Get rating details
PUT     /api/courses/ratings/{id}/                  - Update rating (owner only)
PATCH   /api/courses/ratings/{id}/                  - Partial update rating (owner only)
DELETE  /api/courses/ratings/{id}/                  - Delete rating (owner only)
POST    /api/courses/ratings/{id}/reply/            - Reply to review (instructor)

========================================================================
BULK OPERATIONS
========================================================================
POST    /api/courses/bulk/bulk_create_modules/      - Bulk create modules
POST    /api/courses/bulk/bulk_import_lessons/      - Bulk import lessons

========================================================================
ADVANCED SEARCH
========================================================================
GET     /api/courses/search/courses/                - Advanced course search

========================================================================
CUSTOM FILTERS AVAILABLE:
========================================================================

Courses:
- programming_languages (JSONField contains)
- skills_gained (JSONField contains)
- tags (JSONField contains)
- min_duration, max_duration (duration range)
- min_rating (rating threshold)
- min_enrollments (enrollment threshold)
- max_price (price range)
- created_after, created_before (date range)
- instructor_username (instructor search)

Lessons:
- module_course (filter by course ID)
- duration_min, duration_max (duration range)
- lesson_type (video, text, interactive, etc.)
- is_required, is_preview (boolean filters)

Exercises:
- lesson_module (filter by module ID)
- lesson_course (filter by course ID)
- points_min, points_max (points range)
- programming_language (exact match)
- difficulty (easy, medium, hard, expert)
- ai_hints_enabled, allow_collaboration (boolean filters)

Enrollments:
- course (filter by course)
- status (enrolled, completed, dropped, suspended)
- enrollment_source (direct, invitation, bulk, api, admin)

Exercise Submissions:
- exercise (filter by exercise)
- status (submitted, passed, failed, partial, error)
- auto_graded (boolean filter)
- is_final_submission (boolean filter)

========================================================================
WEBSOCKET ENDPOINTS (for real-time features):
========================================================================
ws://localhost:8000/ws/courses/{course_id}/          - Course real-time updates
ws://localhost:8000/ws/lessons/{lesson_id}/          - Lesson real-time updates
ws://localhost:8000/ws/exercises/{exercise_id}/      - Exercise real-time updates

========================================================================
FRONTEND COMPONENT MAPPING:
========================================================================

InstructorDashboard        -> GET /courses/teaching/
                          -> GET /courses/{id}/analytics/

CourseCreatorForm         -> POST /courses/
                          -> PUT /courses/{id}/
                          -> GET /categories/

LiveLessonManager         -> GET /courses/{id}/structure/
                          -> POST /modules/
                          -> PUT /modules/{id}/
                          -> POST /lessons/
                          -> PUT /lessons/{id}/

ExerciseCreator           -> POST /exercises/
                          -> PUT /exercises/{id}/
                          -> GET /exercises/{id}/

StudentProgressTracker    -> GET /courses/{id}/students/
                          -> GET /enrollments/{id}/progress_detail/
                          -> GET /exercise-submissions/
                          -> POST /exercise-submissions/{id}/provide_feedback/

CourseAnalyticsDashboard  -> GET /courses/{id}/analytics/
                          -> GET /courses/{id}/engagement/
                          -> GET /courses/{id}/performance/
                          -> GET /courses/{id}/export/

All frontend API examples are fully supported by these endpoints!
"""