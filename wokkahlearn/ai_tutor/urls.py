# ai_tutor/urls.py - FIXED VERSION with explicit basenames
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AITutorSessionViewSet, AIMessageViewSet, LearningPathRecommendationViewSet,
    CodeAnalysisResultViewSet
    #, PersonalizedQuizViewSet
)

router = DefaultRouter()

# Register viewsets with explicit basenames (fixes the router error)
router.register(r'sessions', AITutorSessionViewSet, basename='aitutorsession')
router.register(r'messages', AIMessageViewSet, basename='aimessage')
router.register(r'recommendations', LearningPathRecommendationViewSet, basename='learningpathrecommendation')
router.register(r'code-analysis', CodeAnalysisResultViewSet, basename='codeanalysisresult')
#router.register(r'quizzes', PersonalizedQuizViewSet, basename='personalizedquiz')

urlpatterns = [
    path('', include(router.urls)),
]