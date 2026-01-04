"""
LLM Service - Abstract interface for multiple LLM providers
Supports: OpenAI, Anthropic, Local (Ollama), with fallback to keyword-based methods
"""

import os
import json
import hashlib
import time
from typing import Dict, Optional, List, Any
from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def analyze(self, prompt: str, system_prompt: Optional[str] = None, 
                temperature: float = 0.3, max_tokens: int = 500) -> str:
        """Analyze text and return response"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("STOCK_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                pass
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    def analyze(self, prompt: str, system_prompt: Optional[str] = None,
                temperature: float = 0.3, max_tokens: int = 500) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or os.getenv("STOCK_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                pass
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    def analyze(self, prompt: str, system_prompt: Optional[str] = None,
                temperature: float = 0.3, max_tokens: int = 500) -> str:
        if not self.is_available():
            raise RuntimeError("Anthropic provider not available")
        
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are a financial analyst assistant.",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")


class LocalOllamaProvider(LLMProvider):
    """Local Ollama provider (free, runs on your machine)"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def is_available(self) -> bool:
        return self._available
    
    def analyze(self, prompt: str, system_prompt: Optional[str] = None,
                temperature: float = 0.3, max_tokens: int = 500) -> str:
        if not self.is_available():
            raise RuntimeError("Ollama provider not available")
        
        try:
            import requests
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")


class LLMService:
    """Main LLM service with caching and fallback"""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None,
                 enabled: bool = True, cache_enabled: bool = True, cache_duration: int = 3600):
        self.enabled = enabled
        self.cache_enabled = cache_enabled
        self.cache_duration = cache_duration
        self._cache: Dict[str, tuple] = {}  # hash -> (response, timestamp)
        
        # Determine provider
        provider = provider or os.getenv("STOCK_LLM_PROVIDER", "openai").lower()
        model = model or os.getenv("STOCK_LLM_MODEL", "gpt-4o-mini")
        
        # Initialize provider
        if provider == "openai":
            self.provider = OpenAIProvider(model=model)
        elif provider == "anthropic":
            self.provider = AnthropicProvider(model=model)
        elif provider == "local" or provider == "ollama":
            self.provider = LocalOllamaProvider(model=model)
        else:
            self.provider = None
        
        # Check availability
        self.available = self.enabled and self.provider is not None and self.provider.is_available()
        
        if not self.available and self.enabled:
            print("⚠️  LLM service not available - falling back to keyword-based methods")
    
    def _cache_key(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate cache key from prompt"""
        content = f"{system_prompt or ''}|{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached(self, cache_key: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        if not self.cache_enabled or cache_key not in self._cache:
            return None
        
        response, timestamp = self._cache[cache_key]
        age = time.time() - timestamp
        
        if age > self.cache_duration:
            del self._cache[cache_key]
            return None
        
        return response
    
    def _cache_response(self, cache_key: str, response: str):
        """Cache response"""
        if self.cache_enabled:
            self._cache[cache_key] = (response, time.time())
    
    def analyze(self, prompt: str, system_prompt: Optional[str] = None,
                temperature: float = 0.3, max_tokens: int = 500,
                use_cache: bool = True) -> Optional[str]:
        """
        Analyze text using LLM with caching
        
        Returns:
            LLM response string, or None if unavailable
        """
        if not self.available:
            return None
        
        # Check cache
        if use_cache:
            cache_key = self._cache_key(prompt, system_prompt)
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        try:
            response = self.provider.analyze(prompt, system_prompt, temperature, max_tokens)
            
            # Cache response
            if use_cache:
                self._cache_response(cache_key, response)
            
            return response
        except Exception as e:
            print(f"⚠️  LLM analysis error: {e}")
            return None
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()
    
    def generate_risk_assessment(self, pick: Dict) -> Optional[str]:
        """Generate risk assessment for a stock pick"""
        if not self.available:
            return None
        
        prompt = f"""Provide a concise risk assessment for this stock pick. Identify potential failure modes, key risks, and suggest mitigation strategies. Keep it under 100 words.

Pick Details:
Symbol: {pick.get('symbol', 'N/A')}
Strategy: {pick.get('strategy', 'N/A')}
Conviction Score: {pick.get('conviction_score', 0):.1f}
Entry Price: {pick.get('entry_price', 0):.2f}
Stop Loss: {pick.get('stop_loss', 0):.2f}
Target: {pick.get('target', 0):.2f}"""
        
        system_prompt = "You are a seasoned risk manager providing critical insights for a trade."
        
        try:
            return self.analyze(prompt, system_prompt, temperature=0.5, max_tokens=200)
        except Exception as e:
            print(f"⚠️  LLM risk assessment failed: {e}")
            return None
    
    def generate_market_context(self, pick: Dict, regime: str) -> Optional[str]:
        """Generate market context interpretation for a stock pick"""
        if not self.available:
            return None
        
        prompt = f"""Interpret the market context for this stock pick. How does it fit into the broader market regime ({regime})? Are there any macro factors or sector-specific trends relevant to this trade? Keep it under 100 words.

Pick Details:
Symbol: {pick.get('symbol', 'N/A')}
Strategy: {pick.get('strategy', 'N/A')}
Market Regime: {regime}"""
        
        system_prompt = "You are a macro analyst providing a concise market context for a trade."
        
        try:
            return self.analyze(prompt, system_prompt, temperature=0.5, max_tokens=200)
        except Exception as e:
            print(f"⚠️  LLM market context failed: {e}")
            return None
    
    def generate_news_impact(self, symbol: str, news_articles: List[Dict] = None) -> Optional[str]:
        """Generate news impact summary for a stock"""
        if not self.available:
            return None
        
        if not news_articles:
            return None
        
        article_texts = [f"Title: {a.get('title', '')}\nSummary: {a.get('summary', '')}" for a in news_articles[:5]]
        prompt = f"""Analyze the following news articles for {symbol} and provide a concise summary of their potential impact on the stock price. Keep it under 100 words.

Articles:
{chr(10).join(article_texts)}"""
        
        system_prompt = "You are a financial news analyst providing objective analysis of news impact on stock prices."
        
        try:
            return self.analyze(prompt, system_prompt, temperature=0.3, max_tokens=200)
        except Exception as e:
            print(f"⚠️  LLM news impact failed: {e}")
            return None

