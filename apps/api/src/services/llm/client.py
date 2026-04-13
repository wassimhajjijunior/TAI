"""Groq LLM client for generating tender responses."""

import logging
import os
from typing import Any

from ...core.env import load_local_env_if_present


logger = logging.getLogger(__name__)


# Multilingual system prompt for tender responses
TENDER_SYSTEM_PROMPT_FR = """Vous êtes un assistant expert en réponse aux appels d'offres (AO) et consultations.
Votre rôle est de rédiger des réponses professionnelles, claires et précises basées sur les extraits fournis du document de consultation.

Instructions:
1. Analysez attentivement les extraits du document fournis
2. Rédigez une réponse structurée et complète
3. Utilisez un langage professionnel et technique approprié
4. Incluez des citations aux extraits utilisés [Excerpt X]
5. Organisez la réponse en sections claires
6. Adaptez le ton selon le type de réponse demandée

Les réponses doivent être en français sauf indication contraire."""

TENDER_SYSTEM_PROMPT_AR = """أنت مساعد خبير في الرد على المناقصات والاستشارات.
دورك هو صياغة ردود احترافية وواضحة ودقيقة بناءً على المقتطفات المقدمة من وثيقة المناقصة.

التعليمات:
1. حلل المقتطفات المقدمة بعناية
2. اكتب رداً منظمًا وشاملاً
3. استخدم لغة احترافية وتقنية مناسبة
4. أدرج اقتباسات للمقتطفات المستخدمة [Excerpt X]
5. نظم الرد في أقسام واضحة
6. كيّف النبرة حسب نوع الرد المطلوب

الردود يجب أن تكون بالعربية ما لم يُذكر خلاف ذلك."""

TENDER_SYSTEM_PROMPT_EN = """You are an expert tender/RFQ response assistant.
Your role is to write professional, clear, and precise responses based on the provided tender document excerpts.

Instructions:
1. Carefully analyze the provided document excerpts
2. Write a well-structured and complete response
3. Use appropriate professional and technical language
4. Include citations to the excerpts used [Excerpt X]
5. Organize the response in clear sections
6. Adapt the tone according to the requested response type

Responses should be in English unless otherwise specified."""


def _load_langchain_groq_chat_model(
    model: str,
    temperature: float,
    max_tokens: int,
) -> Any:
    load_local_env_if_present()
    from importlib import import_module

    module = import_module("langchain_groq")
    ChatGroq = getattr(module, "ChatGroq")
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable not set")
    return ChatGroq(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _load_langchain_messages() -> tuple[Any, Any]:
    from importlib import import_module

    module = import_module("langchain_core.messages")
    SystemMessage = getattr(module, "SystemMessage")
    HumanMessage = getattr(module, "HumanMessage")
    return SystemMessage, HumanMessage


def _detect_language(text: str) -> str:
    """Detect the primary language of text."""
    # Simple detection based on character ranges
    ar_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    total_chars = len([c for c in text if c.isalpha()])
    
    if total_chars > 0 and ar_chars / total_chars > 0.3:
        return "ar"
    
    # Check for French indicators
    fr_indicators = ["le", "la", "les", "un", "une", "des", "et", "ou", "appel", "offre", "consultation"]
    text_lower = text.lower()
    fr_count = sum(1 for word in fr_indicators if word in text_lower)
    if fr_count >= 3:
        return "fr"
    
    return "en"


def _get_system_prompt(language: str = "fr") -> str:
    """Get system prompt based on language."""
    prompts = {
        "fr": TENDER_SYSTEM_PROMPT_FR,
        "ar": TENDER_SYSTEM_PROMPT_AR,
        "en": TENDER_SYSTEM_PROMPT_EN,
    }
    return prompts.get(language, TENDER_SYSTEM_PROMPT_FR)


def _build_prompt(
    query: str,
    context: str,
    sections: list[str] | None = None,
    company_info: dict[str, Any] | None = None,
) -> str:
    """Build the full prompt for tender response generation.
    
    Args:
        query: The specific query or requirement
        context: The formatted context from RAG
        sections: Specific sections to cover (technical, financial, administrative)
        company_info: Optional company profile information
        
    Returns:
        The complete prompt for the LLM
    """
    language = _detect_language(query + " " + context)
    
    sections_str = ""
    if sections:
        sections_str = f"\nSections à couvrir / Sections to cover: {', '.join(sections)}\n"
    
    company_str = ""
    if company_info:
        company_str = f"\nInformations sur l'entreprise / Company Profile:\n{company_info}\n"
    
    prompt = f"""{query}

Contexte du document de consultation / Tender Document Context:
{context}
{sections_str}
{company_str}

Instructions:
1. Rédigez une réponse complète et professionnelle
2. Basez votre réponse UNIQUEMENT sur les extraits fournis ci-dessus
3. Citez les extraits utilisés avec [Excerpt X] dans votre réponse
4. Structurez votre réponse de manière claire et professionnelle

Votre réponse:"""
    
    return prompt


def generate_response(
    query: str,
    context: str,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    sections: list[str] | None = None,
    company_info: dict[str, Any] | None = None,
) -> str:
    """Generate a tender response using Groq LLM.
    
    Args:
        query: The query or requirement to address
        context: The RAG context from document chunks
        model: The Groq model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        sections: Specific sections to cover
        company_info: Optional company information
        
    Returns:
        The generated response text
    """
    language = _detect_language(query + " " + context)
    system_prompt = _get_system_prompt(language)
    user_prompt = _build_prompt(query, context, sections, company_info)
    chat_model = _load_langchain_groq_chat_model(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    SystemMessage, HumanMessage = _load_langchain_messages()
    
    try:
        response = chat_model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        raw_content = getattr(response, "content", "")
        if isinstance(raw_content, str):
            content = raw_content
        elif isinstance(raw_content, list):
            parts: list[str] = []
            for item in raw_content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            content = "\n".join(parts)
        else:
            content = str(raw_content)

        if not content.strip():
            raise RuntimeError("Empty LLM response content")
        logger.info("Generated response using model=%s, tokens=%d", model, len(content.split()))
        return content
        
    except Exception as error:
        logger.exception("LLM generation failed")
        raise RuntimeError(f"Failed to generate response: {error}") from error


def generate_response_streaming(
    query: str,
    context: str,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    sections: list[str] | None = None,
    company_info: dict[str, Any] | None = None,
) -> Any:
    """Generate a tender response with streaming support.
    
    Yields chunks of the response as they are generated.
    """
    language = _detect_language(query + " " + context)
    system_prompt = _get_system_prompt(language)
    user_prompt = _build_prompt(query, context, sections, company_info)
    chat_model = _load_langchain_groq_chat_model(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    SystemMessage, HumanMessage = _load_langchain_messages()
    
    try:
        stream = chat_model.stream(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

        for chunk in stream:
            raw_content = getattr(chunk, "content", "")
            if isinstance(raw_content, str) and raw_content:
                yield raw_content
            elif isinstance(raw_content, list):
                for item in raw_content:
                    if isinstance(item, str) and item:
                        yield item
                    elif isinstance(item, dict):
                        text = item.get("text")
                        if isinstance(text, str) and text:
                            yield text
                
    except Exception as error:
        logger.exception("LLM streaming generation failed")
        raise RuntimeError(f"Failed to generate streaming response: {error}") from error


def extract_citations(response_text: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract citations from response text and match to chunks.
    
    Args:
        response_text: The generated response
        chunks: The source chunks
        
    Returns:
        List of citation objects with chunk references
    """
    import re
    
    citations: list[dict[str, Any]] = []
    pattern = r'\[Excerpt\s*(\d+)\]'
    matches = re.finditer(pattern, response_text)
    
    for match in matches:
        excerpt_num = int(match.group(1))
        # Find matching chunk (1-indexed in prompt)
        if 1 <= excerpt_num <= len(chunks):
            chunk = chunks[excerpt_num - 1]
            citations.append({
                "excerpt_number": excerpt_num,
                "chunk_id": chunk.get("id", ""),
                "position": chunk.get("position", 0),
                "content": chunk.get("content", "")[:200] + "..." if len(str(chunk.get("content", ""))) > 200 else chunk.get("content", ""),
            })
    
    return citations


class LLMClient:
    """Convenience wrapper for LLM operations."""
    
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        self._client: Any | None = None
    
    def generate(self, query: str, context: str, **kwargs: Any) -> str:
        """Generate response."""
        return generate_response(query, context, model=self.model, **kwargs)
    
    def generate_stream(self, query: str, context: str, **kwargs: Any) -> Any:
        """Generate response with streaming."""
        yield from generate_response_streaming(query, context, model=self.model, **kwargs)
