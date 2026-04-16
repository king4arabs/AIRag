import logging

import openai

from src.config import config

logger = logging.getLogger(__name__)


class LLMProvider:
    """Provider for LLM-based text generation using OpenAI-compatible APIs."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or config.LLM_MODEL
        self.client: openai.OpenAI | None = None
        if config.OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

    def generate_response(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate a response from the LLM for the given prompt.

        Args:
            prompt: The user message / question.
            system_prompt: Optional system-level instruction for the model.

        Returns:
            The model's response text, or an error message when the API
            key is missing or a request fails.
        """
        if not self.client:
            logger.error("OpenAI client not initialised – OPENAI_API_KEY is missing")
            return "Error: OPENAI_API_KEY is not configured. Please set it in your .env file."

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except openai.APIError as exc:
            logger.exception("OpenAI API error")
            return f"Error communicating with OpenAI: {exc}"

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a list of texts.

        Args:
            texts: Texts to embed.

        Returns:
            A list of embedding vectors (one per input text).

        Raises:
            RuntimeError: If the OpenAI client is not initialised.
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialised – OPENAI_API_KEY is missing")

        try:
            response = self.client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except openai.APIError as exc:
            logger.exception("OpenAI embeddings error")
            raise RuntimeError(f"Failed to generate embeddings: {exc}") from exc