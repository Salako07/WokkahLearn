import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from .models import AIModel, AITutorSession, AIMessage

logger = logging.getLogger(__name__)

# Import handling with proper error catching
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic library not available")

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class OpenAIService:
    """OpenAI API integration service"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.client = None
        self.available = False
        self.default_model = "gpt-4"
        
        if self.api_key and OPENAI_AVAILABLE:
            try:
                openai.api_key = os.getenv('OPENAI_API_KET')
                self.client = openai
                self.available = True
                logger.info("✅ OpenAI service initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
                self.available = False
        
    def is_available(self) -> bool:
        return self.available and self.client is not None
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate AI response using OpenAI"""
        if not self.is_available():
            logger.warning("OpenAI not available, using mock response")
            mock_service = MockAIService()
            return await mock_service.generate_response(messages, **kwargs)
        
        try:
            # Use the new OpenAI client format (v1.x)
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
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
            # Fall back to mock service on errors
            mock_service = MockAIService()
            return await mock_service.generate_response(messages, **kwargs)

class AnthropicService:
    """Anthropic Claude API integration service - FIXED VERSION"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        self.client = None
        self.available = False
        self.default_model = "claude-3-sonnet-20240229"
        
        # Safe initialization with proper error handling
        if self.api_key and ANTHROPIC_AVAILABLE:
            try:
                # Correct Anthropic client initialization
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.available = True
                logger.info("✅ Anthropic service initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Anthropic initialization failed: {e}")
                self.client = None
                self.available = False
        else:
            if not self.api_key:
                logger.info("ℹ️ Anthropic API key not provided")
            if not ANTHROPIC_AVAILABLE:
                logger.info("ℹ️ Anthropic library not available")
        
    def is_available(self) -> bool:
        return self.available and self.client is not None
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate AI response using Anthropic Claude - FIXED ASYNC IMPLEMENTATION"""
        
        # If not available, return mock response
        if not self.is_available():
            logger.warning("Anthropic not available, using mock response")
            mock_service = MockAIService()
            return await mock_service.generate_response(messages, **kwargs)
        
        try:
            # Convert messages to Anthropic format
            system_message = None
            user_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            # Prepare request parameters
            request_params = {
                'model': model or self.default_model,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': user_messages
            }
            
            # Add system message if present
            if system_message:
                request_params['system'] = system_message
            
            # Add any additional kwargs
            request_params.update(kwargs)
            
            # FIXED: Use asyncio.to_thread for proper async handling
            response = await asyncio.to_thread(
                self.client.messages.create,
                **request_params
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
            # Fall back to mock service on API errors
            mock_service = MockAIService()
            return await mock_service.generate_response(messages, **kwargs)

class MockAIService:
    """Enhanced Mock AI service for development and testing"""
    
    def is_available(self) -> bool:
        return True
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Generate contextual mock AI response"""
        # Simulate realistic API delay
        await asyncio.sleep(0.5)
        
        last_message = messages[-1]['content'].lower() if messages else ""
        
        # Generate highly contextual mock responses
        if any(keyword in last_message for keyword in ["error", "bug", "debug", "fix"]):
            content = """I can help you debug this issue! Here's my analysis:

🔍 **Common Issues to Check:**
1. **Syntax Errors**: Missing semicolons, brackets, or quotes
2. **Variable Scope**: Variables not declared or out of scope
3. **Type Mismatches**: Incorrect data types being used
4. **Logic Errors**: Check your conditional statements

💡 **Debugging Strategy:**
```python
# Add print statements to trace execution
print(f"Variable value: {your_variable}")
# Use debugger breakpoints
# Check console for error messages
```

Would you like me to review your specific code? Please share it and I'll provide targeted feedback!"""

        elif any(keyword in last_message for keyword in ["explain", "what is", "how does"]):
            content = """Great question! Let me break this concept down step by step:

📚 **Concept Overview:**
This is a fundamental programming concept that works by processing data through a series of logical steps.

🔑 **Key Points:**
• **Input Processing**: Data enters the system
• **Transformation**: Logic is applied to modify the data  
• **Output Generation**: Results are produced

📝 **Simple Example:**
```python
def explain_concept(input_data):
    # Process the input
    processed = transform_data(input_data)
    # Return meaningful result
    return processed

# Usage
result = explain_concept("learning data")
print(result)  # Transformed output
```

🎯 **Real-World Applications:**
This concept is used in web development, data analysis, machine learning, and system design.

What specific aspect would you like me to dive deeper into?"""

        elif any(keyword in last_message for keyword in ["help", "stuck", "don't understand"]):
            content = """I'm here to help you succeed! 🚀

🧠 **I can assist you with:**
• **Concept Explanations** - Breaking down complex topics into digestible pieces
• **Code Review & Debugging** - Finding issues and suggesting improvements
• **Problem-Solving Strategies** - Step-by-step guidance through challenges
• **Best Practices** - Industry-standard coding techniques
• **Learning Path Guidance** - Personalized recommendations for your journey

💬 **Let's get specific:**
- What programming language are you working with?
- What exact challenge are you facing?
- Have you tried any solutions yet?

The more details you provide, the better I can tailor my help to your needs!"""

        elif any(keyword in last_message for keyword in ["review", "check", "look at"]):
            content = """I'd be happy to review your code! 👀

🔍 **Code Review Checklist:**
✅ **Functionality**: Does it work as intended?
✅ **Readability**: Is the code clear and well-commented?
✅ **Efficiency**: Can performance be improved?
✅ **Best Practices**: Following language conventions?
✅ **Security**: Any potential vulnerabilities?

📋 **To provide the best review:**
1. Share your code (use code blocks for formatting)
2. Explain what it's supposed to do
3. Mention any specific concerns you have
4. Let me know your experience level

```python
# Example of well-formatted code sharing:
def your_function():
    # Your code here
    pass
```

Once you share your code, I'll provide detailed, constructive feedback!"""

        elif any(keyword in last_message for keyword in ["project", "build", "create"]):
            content = """Exciting! Let's build something amazing together! 🛠️

🎯 **Project Planning Approach:**
1. **Define Requirements** - What should your project do?
2. **Choose Technology Stack** - Best tools for the job
3. **Break Down Tasks** - Smaller, manageable pieces
4. **Plan Architecture** - How components will interact
5. **Start with MVP** - Minimum viable product first

💻 **Development Process:**
```
Planning → Setup → Core Features → Testing → Refinement
```

🚀 **Let's get started:**
- What type of project do you want to build?
- What's your experience level?
- Any specific technologies you want to use?
- What's the main goal or problem it should solve?

I'll help you create a step-by-step roadmap and guide you through the implementation!"""

        else:
            # Generic helpful response
            content = f"""Thanks for your question about: "{last_message[:100]}{'...' if len(last_message) > 100 else ''}"

🤖 **I understand you're exploring this topic.** Here's how I can help:

📋 **Analysis:**
Based on your question, I can see you're working on understanding core programming concepts. This is exactly the right approach for building solid foundations.

💡 **Next Steps:**
1. **Clarify the specific challenge** you're facing
2. **Break down the problem** into smaller parts  
3. **Work through examples** step by step
4. **Practice with variations** to reinforce learning

🎯 **My Recommendation:**
Let's focus on one specific aspect at a time. What's the most immediate challenge you need help with? 

Feel free to ask follow-up questions or share code - I'm here to guide you through every step of your learning journey!"""
        
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
        # Initialize all services
        self.openai = OpenAIService()
        self.anthropic = AnthropicService()
        self.mock = MockAIService()
        
        # Service registry
        self.available_services = {
            'openai': self.openai,
            'anthropic': self.anthropic,
            'mock': self.mock
        }
        
        # Set default service based on availability priority
        if self.anthropic.is_available():
            self.default_service = 'anthropic'
            logger.info("🎯 Using Anthropic as default AI service")
        elif self.openai.is_available():
            self.default_service = 'openai'
            logger.info("🎯 Using OpenAI as default AI service")
        else:
            self.default_service = 'mock'
            logger.warning("⚠️ No AI API keys configured, using mock service for development")
    
    def get_service(self, provider: str = None) -> Any:
        """Get AI service by provider name with intelligent fallback"""
        provider = provider or self.default_service
        service = self.available_services.get(provider)
        
        if not service or not service.is_available():
            logger.warning(f"Service {provider} not available, falling back to mock")
            return self.mock
        
        return service
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all AI services"""
        return {
            'openai': self.openai.is_available(),
            'anthropic': self.anthropic.is_available(),
            'mock': self.mock.is_available(),
            'default': self.default_service
        }
    
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
        
        logger.info(f"🎉 New AI session started: {session.id} for user {user.username}")
        return session
    
    async def send_message(
        self, 
        session: AITutorSession, 
        content: str,
        is_initial: bool = False
    ) -> AIMessage:
        """Send message and get AI response"""
        
        # Create user message (if not initial)
        if not is_initial:
            user_message = AIMessage.objects.create(
                session=session,
                message_type=AIMessage.MessageType.USER,
                content=content
            )
            logger.debug(f"📝 User message created for session {session.id}")
        
        # Prepare conversation history
        messages = self._prepare_messages(session, content)
        
        # Get AI service
        provider = session.ai_model.provider if session.ai_model else self.default_service
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
            
            # Update session stats
            session.total_messages = session.messages.count()
            session.save()
            
            logger.info(f"🤖 AI response generated for session {session.id} using {response_data.get('provider')}")
            return ai_message
            
        except Exception as e:
            logger.error(f"💥 Error generating AI response: {str(e)}")
            # Create error message
            error_message = AIMessage.objects.create(
                session=session,
                message_type=AIMessage.MessageType.SYSTEM,
                content=f"I'm sorry, I'm having trouble processing your request right now. Please try again in a moment. Error: {str(e)}",
                ai_model=session.ai_model
            )
            return error_message
    
    def _prepare_messages(self, session: AITutorSession, current_content: str) -> List[Dict[str, str]]:
        """Prepare conversation messages for AI with context awareness"""
        messages = []
        
        # Add system prompt based on session type
        system_prompt = self._get_system_prompt(session.session_type, session.context_data)
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add conversation history (last 10 messages to stay within context limits)
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
        """Generate enhanced system prompt based on session type"""
        
        base_prompt = """You are an expert programming tutor for WokkahLearn, an AI-powered coding education platform. 
        Your role is to help students learn programming concepts, debug code, and improve their skills.

        CORE GUIDELINES:
        - Be encouraging, patient, and supportive
        - Explain concepts clearly with practical examples
        - Break down complex problems into manageable steps
        - Provide hints and guidance rather than direct answers when possible
        - Use properly formatted code examples to illustrate points
        - Ask clarifying questions when you need more context
        - Adapt your teaching style to the student's level
        - Encourage best practices and clean code
        - Make learning interactive and engaging

        RESPONSE FORMAT:
        - Use clear headings and bullet points for readability
        - Include code examples in proper markdown format
        - Provide step-by-step explanations
        - End with follow-up questions or next steps when appropriate"""
        
        session_specific_prompts = {
            "help_request": """
            CONTEXT: The student is asking for help with a specific problem.
            APPROACH: Guide them through solving it step by step. Ask questions to understand their thought process and provide targeted hints.""",
            
            "code_review": """
            CONTEXT: The student wants their code reviewed.
            APPROACH: Provide constructive feedback on functionality, style, efficiency, and best practices. Highlight what they did well before suggesting improvements.""",
            
            "concept_explanation": """
            CONTEXT: The student wants to understand a programming concept.
            APPROACH: Explain it clearly with analogies, examples, and progressive complexity. Start simple and build up to advanced applications.""",
            
            "debugging": """
            CONTEXT: The student has a bug in their code.
            APPROACH: Help them develop debugging skills by asking guided questions. Teach them to read error messages and use debugging techniques.""",
            
            "project_guidance": """
            CONTEXT: The student needs guidance on a programming project.
            APPROACH: Help them break down the project into smaller tasks, choose appropriate technologies, and plan their development approach."""
        }
        
        session_prompt = session_specific_prompts.get(session_type, "")
        
        # Add context-specific information if available
        context_info = ""
        if context:
            if context.get('programming_language'):
                context_info += f"\nPROGRAMMING LANGUAGE: {context['programming_language']}"
            if context.get('difficulty_level'):
                context_info += f"\nSTUDENT LEVEL: {context['difficulty_level']}"
            if context.get('course_topic'):
                context_info += f"\nCOURSE TOPIC: {context['course_topic']}"
        
        return base_prompt + session_prompt + context_info
    
    def _generate_session_title(self, query: str) -> str:
        """Generate a descriptive title for the session"""
        if len(query) <= 50:
            return query
        return query[:47] + "..."

# Initialize the AI service singleton
try:
    ai_tutor_service = AITutorService()
    logger.info("🚀 AI Tutor Service successfully initialized")
    
    # Log service status
    status = ai_tutor_service.get_service_status()
    logger.info(f"📊 AI Service Status: {status}")
    
except Exception as e:
    logger.error(f"💥 Failed to initialize AI Tutor Service: {e}")
    logger.info("🔄 Creating fallback mock service")
    
    # Create a minimal fallback service
    class FallbackService:
        def __init__(self):
            self.mock = MockAIService()
            self.default_service = 'mock'
        
        async def start_session(self, user, session_type, initial_query, context=None):
            logger.warning("Using fallback service for session creation")
            return {"message": "AI service temporarily unavailable - using fallback"}
        
        async def send_message(self, session, content, is_initial=False):
            logger.warning("Using fallback service for message generation")
            return await self.mock.generate_response([{"role": "user", "content": content}])
        
        def get_service(self, provider=None):
            return self.mock
        
        def get_service_status(self):
            return {"mock": True, "openai": False, "anthropic": False, "default": "mock"}
    
    ai_tutor_service = FallbackService()
    logger.info("🛡️ Fallback service activated")