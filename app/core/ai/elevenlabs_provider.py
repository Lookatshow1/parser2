"""
ElevenLabs Voice AI Provider

Text-to-speech generation for ad voiceovers.
https://docs.elevenlabs.io/api-reference
"""
import os
import logging
import hashlib
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


# Popular Russian-friendly voices on ElevenLabs
ELEVENLABS_VOICES = {
    # Russian voices
    "ru_male_deep": "pNInz6obpgDQGcFmaJgB",  # Adam - deep male
    "ru_male_young": "TxGEqnHWrfWFTfGW9XjX",  # Josh - young male
    "ru_female_warm": "EXAVITQu4vr4xnSDxMaL",  # Bella - warm female
    "ru_female_pro": "21m00Tcm4TlvDq8ikWAM",  # Rachel - professional female

    # Multilingual voices
    "narrator_male": "pNInz6obpgDQGcFmaJgB",
    "narrator_female": "EXAVITQu4vr4xnSDxMaL",

    # Energetic for ads
    "energetic_male": "VR6AewLTigWG4xSOukaG",
    "energetic_female": "jBpfuIE2acCO8z3wKNLl",

    # Calm and trustworthy
    "calm_male": "yoZ06aMxZJJ28mfd3POQ",
    "calm_female": "ThT5KcBeYPX3keUQqHPh",
}


class ElevenLabsProvider:
    """
    ElevenLabs text-to-speech provider.

    Features:
    - Multiple voice options
    - Emotional control
    - Russian language support
    - Audio file generation for ads
    """

    API_URL = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_voice: str = "ru_female_pro",
        proxy_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.default_voice_id = ELEVENLABS_VOICES.get(default_voice, default_voice)
        self.proxy_url = proxy_url or os.getenv("ELEVENLABS_PROXY_URL")

        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not set - ElevenLabs provider will not work")

    def _get_http_client(self) -> httpx.AsyncClient:
        """Creates HTTP client with optional proxy."""
        kwargs = {
            "timeout": 60.0,
            "headers": {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
        }

        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url

        return httpx.AsyncClient(**kwargs)

    async def generate_speech(
        self,
        text: str,
        voice: str = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.5,
        output_format: str = "mp3_44100_128"
    ) -> bytes:
        """
        Generate speech audio from text.

        Args:
            text: Text to convert to speech
            voice: Voice ID or preset name
            stability: Voice stability (0-1)
            similarity_boost: Voice clarity (0-1)
            style: Expressiveness (0-1)
            output_format: Audio format

        Returns:
            Audio file bytes
        """
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")

        voice_id = ELEVENLABS_VOICES.get(voice, voice) if voice else self.default_voice_id

        url = f"{self.API_URL}/text-to-speech/{voice_id}"

        request_body = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True
            }
        }

        try:
            async with self._get_http_client() as client:
                response = await client.post(
                    url,
                    json=request_body,
                    params={"output_format": output_format}
                )

                if response.status_code == 401:
                    raise ValueError("Invalid ElevenLabs API key")
                if response.status_code == 429:
                    raise Exception("ElevenLabs rate limit exceeded")

                response.raise_for_status()

                logger.info(f"Generated speech: {len(text)} chars -> {len(response.content)} bytes")
                return response.content

        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.exception("ElevenLabs request failed")
            raise

    async def generate_ad_voiceover(
        self,
        ad_text: str,
        style: str = "energetic"
    ) -> Dict[str, Any]:
        """
        Generate voiceover for an advertisement.

        Args:
            ad_text: The ad copy to voice
            style: Voice style (energetic, calm, professional)

        Returns:
            Dict with audio_url and metadata
        """
        # Select voice based on style
        voice_mapping = {
            "energetic": "energetic_female",
            "calm": "calm_male",
            "professional": "ru_female_pro",
            "narrator": "narrator_male",
            "young": "ru_male_young",
            "warm": "ru_female_warm"
        }

        voice = voice_mapping.get(style, "ru_female_pro")

        # Adjust settings based on style
        settings = {
            "energetic": {"stability": 0.3, "similarity_boost": 0.8, "style": 0.8},
            "calm": {"stability": 0.7, "similarity_boost": 0.7, "style": 0.3},
            "professional": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.5},
        }

        params = settings.get(style, settings["professional"])

        try:
            audio_bytes = await self.generate_speech(
                text=ad_text,
                voice=voice,
                **params
            )

            # Generate a unique filename
            text_hash = hashlib.md5(ad_text.encode()).hexdigest()[:8]

            return {
                "audio_bytes": audio_bytes,
                "filename": f"ad_voiceover_{text_hash}.mp3",
                "voice": voice,
                "style": style,
                "text_length": len(ad_text),
                "audio_size": len(audio_bytes)
            }

        except Exception as e:
            logger.error(f"Failed to generate ad voiceover: {e}")
            return {
                "error": str(e),
                "audio_bytes": None
            }

    async def list_voices(self) -> List[Dict[str, Any]]:
        """Get available voices from ElevenLabs."""
        if not self.api_key:
            return []

        try:
            async with self._get_http_client() as client:
                response = await client.get(f"{self.API_URL}/voices")
                response.raise_for_status()
                data = response.json()

                return [
                    {
                        "voice_id": v["voice_id"],
                        "name": v["name"],
                        "category": v.get("category", "custom"),
                        "labels": v.get("labels", {})
                    }
                    for v in data.get("voices", [])
                ]

        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []

    async def generate_batch_voiceovers(
        self,
        ads: List[Dict[str, str]],
        style: str = "professional"
    ) -> List[Dict[str, Any]]:
        """
        Generate voiceovers for multiple ads.

        Args:
            ads: List of dicts with 'title' and 'text' keys
            style: Voice style to use

        Returns:
            List of voiceover results
        """
        results = []

        for ad in ads:
            # Combine title and text for voiceover
            full_text = f"{ad.get('title', '')}. {ad.get('text', '')}"

            result = await self.generate_ad_voiceover(full_text, style)
            result["ad_title"] = ad.get("title", "")
            results.append(result)

        return results


def get_elevenlabs_provider() -> ElevenLabsProvider:
    """Factory function to get ElevenLabs provider."""
    return ElevenLabsProvider()
