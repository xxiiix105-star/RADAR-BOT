from anthropic import Anthropic
from config import Config
from typing import List, Dict
import asyncio

class AnthropicAI:
    """Wrapper for Anthropic Claude API"""
    
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.conversations = {}  # Store conversation context per user/chat
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
        self.max_tokens = 1024
    
    async def get_response(self, user_input: str, chat_id: int = None, system_prompt: str = None) -> str:
        """
        Get response from Claude API
        
        Args:
            user_input: User's message
            chat_id: Chat ID for conversation context
            system_prompt: Custom system prompt
        
        Returns:
            Claude's response
        """
        try:
            # Build messages list with conversation history
            messages = self.conversations.get(chat_id, []) if chat_id else []
            messages.append({"role": "user", "content": user_input})
            
            # Default system prompt
            if not system_prompt:
                system_prompt = "You are a helpful Telegram bot assistant. Be concise and friendly in your responses."
            
            # Call Anthropic API
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )
            
            assistant_message = response.content[0].text
            
            # Store conversation history (limit to last 10 exchanges)
            if chat_id:
                messages.append({"role": "assistant", "content": assistant_message})
                self.conversations[chat_id] = messages[-20:]  # Keep last 10 exchanges (20 messages)
            
            return assistant_message
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def get_code_review(self, code: str, language: str = "python") -> str:
        """Get code review from Claude"""
        system_prompt = f"You are a {language} code reviewer. Provide constructive feedback on the code quality, security, and performance."
        return await self.get_response(f"Please review this {language} code:\n\n```{language}\n{code}\n```", system_prompt=system_prompt)
    
    async def get_summary(self, text: str) -> str:
        """Get text summary from Claude"""
        system_prompt = "You are a summarization expert. Provide a concise summary of the given text."
        return await self.get_response(f"Please summarize this text:\n\n{text}", system_prompt=system_prompt)
    
    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text using Claude"""
        system_prompt = f"You are a translator. Translate the given text to {target_lang}. Only return the translated text."
        return await self.get_response(f"Translate this text to {target_lang}:\n\n{text}", system_prompt=system_prompt)
    
    def clear_conversation(self, chat_id: int):
        """Clear conversation history for a chat"""
        if chat_id in self.conversations:
            del self.conversations[chat_id]

# Initialize global instance
ai_helper = AnthropicAI()
