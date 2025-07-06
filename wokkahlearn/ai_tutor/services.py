# ai_tutor/services.py - Complete AI Service Integration Layer

import os
import openai
import anthropic
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from .models import AIModel, AITutorSession, AIMessage

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class OpenAIService:
    """OpenAI API integration service"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if self.api_key:
            openai.api_key = self.api_key
        self.default_model = "gpt-4"
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate AI response using OpenAI"""
        try:
            if not self.is_available():
                raise AIServiceError("OpenAI API key not configured")
            
            response = await openai.ChatCompletion.acreate(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return {
                'content': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason,
                'provider': 'openai'
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise AIServiceError(f"OpenAI API error: {str(e)}")

class AnthropicService:
    """Anthropic Claude API integration service"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
        self.default_model = "claude-3-sonnet-20240229"
        
    def is_available(self) -> bool:
        return bool(self.client)
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate AI response using Anthropic Claude"""
        try:
            if not self.is_available():
                raise AIServiceError("Anthropic API key not configured")
            
            # Convert messages to Anthropic format
            system_message = None
            user_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append(msg)
            
            response = await self.client.messages.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=user_messages,
                **kwargs
            )
            
            return {
                'content': response.content[0].text,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                'model': response.model,
                'finish_reason': response.stop_reason,
                'provider': 'anthropic'
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise AIServiceError(f"Anthropic API error: {str(e)}")

class MockAIService:
    """Mock AI service for development and testing"""
    
    def is_available(self) -> bool:
        return True
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock AI response"""
        import asyncio
        await asyncio.sleep(0.5)  # Simulate API delay
        
        last_message = messages[-1]['content'] if messages else ""
        
        # Generate contextual mock responses
        if "error" in last_message.lower() or "bug" in last_message.lower():
            content = """I can help you debug this issue! Here's what I notice:

1. **Check your variable names**: Make sure they're spelled correctly
2. **Verify syntax**: Look for missing parentheses or brackets
3. **Review logic flow**: Step through your code line by line

Would you like me to review your specific code and provide more targeted feedback?"""
        
        elif "explain" in last_message.lower():
            content = """Great question! Let me break this down step by step:

**Concept Overview:**
This is a fundamental programming concept that works by...

**Key Points:**
- Point 1: Explanation here
- Point 2: More details
- Point 3: Advanced considerations

**Example:**
```python
# Simple example demonstrating the concept
def example_function():
    return "Understanding achieved!"
```

Would you like me to dive deeper into any specific aspect?"""
        
        elif "help" in last_message.lower():
            content = """I'm here to help! I can assist you with:

🧠 **Concept Explanations** - Breaking down complex topics
🔍 **Code Review** - Finding bugs and improvements  
💡 **Problem Solving** - Step-by-step guidance
📚 **Learning Paths** - Personalized recommendations

What specific challenge are you facing today?"""
        
        else:
            content = f"""Thanks for your question! I understand you're asking about: "{last_message[:100]}..."

Here's my response:
- I've analyzed your question carefully
- Based on the context, I recommend focusing on the fundamental concepts first
- Let's work through this step by step together

Is there a specific part you'd like me to explain further?"""
        
        return {
            'content': content,
            'tokens_used': len(content.split()) * 1.3,  # Rough token estimate
            'model': 'mock-ai-v1',
            'finish_reason': 'stop',
            'provider': 'mock'
        }

class AITutorService:
    """Main AI tutor service that orchestrates different AI providers"""
    
    def __init__(self):
        self.openai = OpenAIService()
        self.anthropic = AnthropicService()
        self.mock = MockAIService()
        
        # Determine available services
        self.available_services = {
            'openai': self.openai,
            'anthropic': self.anthropic,
            'mock': self.mock
        }
        
        # Set default service based on availability
        if self.openai.is_available():
            self.default_service = 'openai'
        elif self.anthropic.is_available():
            self.default_service = 'anthropic'
        else:
            self.default_service = 'mock'
            logger.warning("No AI API keys configured, using mock service")
    
    def get_service(self, provider: str = None) -> Any:
        """Get AI service by provider name"""
        provider = provider or self.default_service
        service = self.available_services.get(provider)
        
        if not service or not service.is_available():
            logger.warning(f"Service {provider} not available, falling back to mock")
            return self.mock
        
        return service
    
    async def start_session(
        self, 
        user, 
        session_type: str, 
        initial_query: str,
        context: Dict = None
    ) -> AITutorSession:
        """Start a new AI tutoring session"""
        
        # Get appropriate AI model
        ai_model = AIModel.objects.filter(
            model_type=AIModel.ModelType.TUTOR,
            is_active=True,
            is_default=True
        ).first()
        
        if not ai_model:
            ai_model = AIModel.objects.filter(
                model_type=AIModel.ModelType.TUTOR,
                is_active=True
            ).first()
        
        # Create session
        session = AITutorSession.objects.create(
            student=user,
            session_type=session_type,
            ai_model=ai_model,
            title=self._generate_session_title(initial_query),
            initial_query=initial_query,
            context_data=context or {}
        )
        
        # Generate initial AI response
        await self.send_message(session, initial_query, is_initial=True)
        
        return session
    
    async def send_message(
        self, 
        session: AITutorSession, 
        content: str,
        is_initial: bool = False
    ) -> AIMessage:
        """Send message and get AI response"""
        
        # Create user message
        if not is_initial:
            user_message = AIMessage.objects.create(
                session=session,
                message_type=AIMessage.MessageType.USER,
                content=content
            )
        
        # Prepare conversation history
        messages = self._prepare_messages(session, content)
        
        # Get AI service
        provider = session.ai_model.provider if session.ai_model else 'mock'
        service = self.get_service(provider)
        
        try:
            # Generate AI response
            response_data = await service.generate_response(
                messages=messages,
                model=session.ai_model.model_id if session.ai_model else None,
                temperature=session.ai_model.temperature if session.ai_model else 0.7,
                max_tokens=session.ai_model.max_tokens if session.ai_model else 2000
            )
            
            # Create AI message
            ai_message = AIMessage.objects.create(
                session=session,
                message_type=AIMessage.MessageType.ASSISTANT,
                content=response_data['content'],
                ai_model=session.ai_model,
                tokens_used=int(response_data.get('tokens_used', 0)),
                confidence_score=0.9,  # You can implement confidence scoring
                metadata={
                    'model': response_data.get('model'),
                    'finish_reason': response_data.get('finish_reason'),
                    'provider': response_data.get('provider')
                }
            )
            
            # Update session
            session.total_messages = session.messages.count()
            session.save()
            
            return ai_message
            
        except AIServiceError as e:
            # Create error message
            error_message = AIMessage.objects.create(
                session=session,
                message_type=AIMessage.MessageType.SYSTEM,
                content=f"I'm sorry, I'm having trouble processing your request right now. Error: {str(e)}",
                ai_model=session.ai_model
            )
            return error_message
    
    def _prepare_messages(self, session: AITutorSession, current_content: str) -> List[Dict[str, str]]:
        """Prepare conversation messages for AI"""
        messages = []
        
        # Add system prompt based on session type
        system_prompt = self._get_system_prompt(session.session_type, session.context_data)
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add conversation history (last 10 messages)
        recent_messages = session.messages.order_by('created_at')[-10:]
        
        for msg in recent_messages:
            if msg.message_type == AIMessage.MessageType.USER:
                messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.message_type == AIMessage.MessageType.ASSISTANT:
                messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
        
        # Add current message if not already included
        if current_content and (not recent_messages or recent_messages.last().content != current_content):
            messages.append({
                "role": "user",
                "content": current_content
            })
        
        return messages
    
    def _get_system_prompt(self, session_type: str, context: Dict) -> str:
        """Generate system prompt based on session type"""
        
        base_prompt = """You are an expert programming tutor for WokkahLearn, an AI-powered coding education platform. 
        Your role is to help students learn programming concepts, debug code, and improve their skills.

        Guidelines:
        - Be encouraging and supportive
        - Explain concepts clearly with examples
        - Break down complex problems into steps
        - Provide hints rather than direct answers when possible
        - Use code examples to illustrate points
        - Ask clarifying questions when needed"""
        
        if session_type == "help_request":
            return base_prompt + "\n\nThe student is asking for help with a specific problem. Guide them through solving it step by step."
        
        elif session_type == "code_review":
            return base_prompt + "\n\nThe student wants their code reviewed. Provide constructive feedback on style, efficiency, and best practices."
        
        elif session_type == "concept_explanation":
            return base_prompt + "\n\nThe student wants to understand a programming concept. Explain it clearly with examples and analogies."
        
        elif session_type == "debugging":
            return base_prompt + "\n\nThe student has a bug in their code. Help them identify and fix the issue through guided questioning."
        
        return base_prompt
    
    def _generate_session_title(self, query: str) -> str:
        """Generate a descriptive title for the session"""
        if len(query) <= 50:
            return query
        return query[:47] + "..."

ai_tutor_service = AITutorService()