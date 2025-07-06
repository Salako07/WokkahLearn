# ai_tutor/views.py - Updated with Service Integration

import asyncio
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from asgiref.sync import sync_to_async
from django.core.cache import cache

from .models import (
    AIModel, AITutorSession, AIMessage, LearningPathRecommendation,
    CodeAnalysisResult, PersonalizedQuiz, AITutorFeedback
)
from .serializers import (
    AIModelSerializer, AITutorSessionSerializer, AIMessageSerializer,
    LearningPathRecommendationSerializer, CodeAnalysisResultSerializer,
    PersonalizedQuizSerializer, AITutorFeedbackSerializer
)
from .services import ai_tutor_service, AIServiceError

import logging
logger = logging.getLogger(__name__)


class AIModelViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for AI models"""
    queryset = AIModel.objects.filter(is_active=True)
    serializer_class = AIModelSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available AI models for different tasks"""
        model_type = request.query_params.get('type', None)
        queryset = self.get_queryset()
        
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AITutorSessionViewSet(viewsets.ModelViewSet):
    """API endpoints for AI tutor sessions"""
    serializer_class = AITutorSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AITutorSession.objects.filter(student=self.request.user).order_by('-started_at')
    
    def create(self, request):
        """Create a new AI tutor session"""
        try:
            session_type = request.data.get('session_type', 'help_request')
            initial_query = request.data.get('initial_query', '')
            context_data = request.data.get('context_data', {})
            
            if not initial_query:
                return Response(
                    {'error': 'initial_query is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Run async service method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                session = loop.run_until_complete(
                    ai_tutor_service.start_session(
                        user=request.user,
                        session_type=session_type,
                        initial_query=initial_query,
                        context=context_data
                    )
                )
            finally:
                loop.close()
            
            serializer = self.get_serializer(session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except AIServiceError as e:
            logger.error(f"AI service error: {str(e)}")
            return Response(
                {'error': f'AI service error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in the session and get AI response"""
        session = self.get_object()
        content = request.data.get('content', '').strip()
        context = request.data.get('context', {})
        
        if not content:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Run async service method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                ai_message = loop.run_until_complete(
                    ai_tutor_service.send_message(session, content)
                )
            finally:
                loop.close()
            
            # Return both user message and AI response
            user_message = {
                'id': f"user_{timezone.now().timestamp()}",
                'messageType': 'user',
                'content': content,
                'createdAt': timezone.now().isoformat()
            }
            
            ai_response = AIMessageSerializer(ai_message).data
            
            return Response({
                'user_message': user_message,
                'ai_response': ai_response,
                'session_updated': True
            })
            
        except AIServiceError as e:
            logger.error(f"AI service error: {str(e)}")
            return Response(
                {'error': f'AI service error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error sending message: {str(e)}")
            return Response(
                {'error': 'Failed to send message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages in a session"""
        session = self.get_object()
        messages = session.messages.order_by('created_at')
        serializer = AIMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End the AI tutor session"""
        session = self.get_object()
        feedback_data = request.data.get('feedback', {})
        
        # Update session status
        session.status = AITutorSession.SessionStatus.COMPLETED
        session.ended_at = timezone.now()
        session.save()
        
        # Create feedback if provided
        if feedback_data:
            AITutorFeedback.objects.create(
                session=session,
                overall_rating=feedback_data.get('rating', 3),
                helpfulness_rating=feedback_data.get('helpfulness', 3),
                clarity_rating=feedback_data.get('clarity', 3),
                feedback_text=feedback_data.get('comment', ''),
                improvement_suggestions=feedback_data.get('suggestions', [])
            )
        
        return Response({
            'message': 'Session ended successfully',
            'session_id': str(session.id),
            'duration': (session.ended_at - session.started_at).total_seconds()
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get the current active session"""
        active_session = self.get_queryset().filter(
            status=AITutorSession.SessionStatus.ACTIVE
        ).first()
        
        if not active_session:
            return Response({'message': 'No active session'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(active_session)
        return Response(serializer.data)


class AIMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for AI messages"""
    serializer_class = AIMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AIMessage.objects.filter(
            session__student=self.request.user
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate an AI response"""
        message = self.get_object()
        
        if message.message_type != AIMessage.MessageType.ASSISTANT:
            return Response(
                {'error': 'Can only regenerate AI messages'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the previous user message
            previous_messages = AIMessage.objects.filter(
                session=message.session,
                created_at__lt=message.created_at
            ).order_by('-created_at')
            
            user_message = previous_messages.filter(
                message_type=AIMessage.MessageType.USER
            ).first()
            
            if not user_message:
                return Response(
                    {'error': 'No user message found to regenerate response'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Delete the old AI message
            message.delete()
            
            # Generate new response
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                new_message = loop.run_until_complete(
                    ai_tutor_service.send_message(message.session, user_message.content)
                )
            finally:
                loop.close()
            
            serializer = self.get_serializer(new_message)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error regenerating message: {str(e)}")
            return Response(
                {'error': 'Failed to regenerate message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LearningPathRecommendationViewSet(viewsets.ModelViewSet):
    """API endpoints for learning path recommendations"""
    serializer_class = LearningPathRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LearningPathRecommendation.objects.filter(
            student=self.request.user
        ).order_by('-priority', '-created_at')
    
    def perform_create(self, serializer):
        # Get AI model for recommendations
        ai_model = AIModel.objects.filter(
            model_type=AIModel.ModelType.CURRICULUM,
            is_active=True
        ).first()
        
        serializer.save(
            student=self.request.user,
            generated_by=ai_model
        )
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate personalized learning recommendations"""
        try:
            # Get user's learning data
            user_context = {
                'skill_level': getattr(request.user, 'skill_level', 'beginner'),
                'preferred_languages': getattr(request.user, 'preferred_languages', []),
                'completed_courses': [],  # TODO: Get from enrollments
                'weak_areas': [],  # TODO: Get from analytics
                'learning_goals': request.data.get('goals', [])
            }
            
            # For now, create mock recommendations
            # TODO: Integrate with AI service for real recommendations
            mock_recommendations = [
                {
                    'recommendation_type': 'course',
                    'title': 'Master Python Fundamentals',
                    'description': 'Strengthen your Python basics with hands-on projects',
                    'priority': 'high',
                    'difficulty_level': 'intermediate',
                    'estimated_duration': 'P2W',  # 2 weeks
                    'reasoning': 'Based on your recent exercise submissions, focusing on Python fundamentals will help improve your coding efficiency.',
                    'metadata': {
                        'course_id': None,
                        'skills': ['python', 'functions', 'data-structures'],
                        'confidence': 0.85
                    }
                },
                {
                    'recommendation_type': 'skill',
                    'title': 'Practice Algorithm Design',
                    'description': 'Improve problem-solving with algorithm challenges',
                    'priority': 'medium',
                    'difficulty_level': 'intermediate',
                    'estimated_duration': 'P1W',
                    'reasoning': 'Algorithm practice will enhance your logical thinking and coding interview preparation.',
                    'metadata': {
                        'skills': ['algorithms', 'problem-solving', 'optimization'],
                        'confidence': 0.78
                    }
                }
            ]
            
            created_recommendations = []
            for rec_data in mock_recommendations:
                recommendation = LearningPathRecommendation.objects.create(
                    student=request.user,
                    recommendation_type=rec_data['recommendation_type'],
                    title=rec_data['title'],
                    description=rec_data['description'],
                    priority=rec_data['priority'],
                    difficulty_level=rec_data['difficulty_level'],
                    estimated_duration=rec_data['estimated_duration'],
                    reasoning=rec_data['reasoning'],
                    metadata=rec_data['metadata']
                )
                created_recommendations.append(recommendation)
            
            serializer = self.get_serializer(created_recommendations, many=True)
            return Response({
                'message': f'Generated {len(created_recommendations)} recommendations',
                'recommendations': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return Response(
                {'error': 'Failed to generate recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a learning recommendation"""
        recommendation = self.get_object()
        
        recommendation.status = LearningPathRecommendation.RecommendationStatus.ACCEPTED
        recommendation.accepted_at = timezone.now()
        recommendation.save()
        
        # TODO: Implement enrollment or skill tracking based on recommendation type
        
        return Response({
            'message': 'Recommendation accepted',
            'recommendation_id': str(recommendation.id)
        })
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss a learning recommendation"""
        recommendation = self.get_object()
        feedback = request.data.get('feedback', '')
        
        recommendation.status = LearningPathRecommendation.RecommendationStatus.DISMISSED
        recommendation.feedback = feedback
        recommendation.save()
        
        return Response({
            'message': 'Recommendation dismissed',
            'recommendation_id': str(recommendation.id)
        })


class CodeAnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for code analysis results"""
    serializer_class = CodeAnalysisResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CodeAnalysisResult.objects.filter(
            submission__student=self.request.user
        ).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def analyze_code(self, request):
        """Analyze code submission and provide AI feedback"""
        try:
            code = request.data.get('code', '')
            language = request.data.get('language', 'python')
            exercise_id = request.data.get('exercise_id', None)
            
            if not code:
                return Response(
                    {'error': 'Code is required for analysis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # For now, return mock analysis
            # TODO: Integrate with AI service for real code analysis
            mock_analysis = {
                'overall_score': 75,
                'issues_found': [
                    'Variable naming could be more descriptive',
                    'Consider adding error handling',
                    'Function could be broken into smaller parts'
                ],
                'suggestions': [
                    'Use more descriptive variable names',
                    'Add try-catch blocks for error handling',
                    'Follow single responsibility principle'
                ],
                'strengths': [
                    'Good use of functions',
                    'Clean code structure',
                    'Proper indentation'
                ],
                'summary': 'Your code demonstrates good understanding of the concepts. Focus on improving variable naming and error handling.',
                'detailed_feedback': 'The code structure is well-organized and shows good use of functions. However, there are opportunities for improvement in variable naming and error handling...',
                'improvement_suggestions': 'Consider using more descriptive variable names and adding error handling to make your code more robust.',
                'complexity_score': 60,
                'readability_score': 70,
                'maintainability_score': 65,
                'concepts_demonstrated': ['functions', 'loops', 'conditionals'],
                'missing_concepts': ['error_handling', 'documentation'],
                'next_learning_steps': ['Error handling patterns', 'Code documentation', 'Advanced functions']
            }
            
            return Response({
                'analysis': mock_analysis,
                'analyzed_code': code,
                'language': language,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return Response(
                {'error': 'Failed to analyze code'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )