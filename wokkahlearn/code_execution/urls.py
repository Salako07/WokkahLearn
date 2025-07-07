from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExecutionEnvironmentViewSet, CodeExecutionViewSet, 
    TestCaseViewSet, CodePlaygroundViewSet, CodeTemplateViewSet
)

router = DefaultRouter()

router.register(r'environments', ExecutionEnvironmentViewSet, basename='executionenvironment')
router.register(r'executions', CodeExecutionViewSet, basename='codeexecution')
router.register(r'test-cases', TestCaseViewSet, basename='testcase')
router.register(r'playground', CodePlaygroundViewSet, basename='codeplayground')
router.register(r'templates', CodeTemplateViewSet, basename='codetemplate')

urlpatterns = [
    path('', include(router.urls)),
]