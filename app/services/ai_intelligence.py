"""
AI Intelligence Suite

Advanced AI-powered features for competitive advantage:
- Competitor Analysis
- ROI Prediction
- Creative Scoring
- Audience Discovery
- Voice Commands
"""
import os
import json
import logging
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import httpx

from app.core.ai.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)


# =============================================================================
# COMPETITOR ANALYZER
# =============================================================================

class CompetitorAnalyzer:
    """
    AI-powered competitor analysis.

    Features:
    - Scrape competitor websites
    - Analyze their ad strategies
    - Find gaps and opportunities
    - Generate counter-strategies
    """

    ANALYSIS_PROMPT = """Analyze this competitor business information and provide strategic insights.

COMPETITOR INFO:
{competitor_info}

YOUR BUSINESS:
{your_business}

Provide a detailed JSON analysis with the following structure:
{{
    "competitor_name": "extracted name",
    "competitor_strengths": ["list of strengths"],
    "competitor_weaknesses": ["list of weaknesses"],
    "their_target_audience": "description",
    "their_key_messages": ["main marketing messages"],
    "their_pricing_strategy": "description",
    "opportunities_for_you": ["list of opportunities"],
    "recommended_counter_strategies": [
        {{
            "strategy": "strategy name",
            "description": "how to implement",
            "expected_impact": "high/medium/low"
        }}
    ],
    "ad_copy_suggestions": [
        {{
            "headline": "suggested headline",
            "text": "ad text that counters competitor",
            "angle": "what makes this effective"
        }}
    ],
    "keywords_to_target": ["keywords they might miss"],
    "overall_threat_level": "high/medium/low",
    "action_priority": ["ordered list of actions"]
}}

Be specific and actionable. Focus on Russian market specifics.
"""

    def __init__(self):
        self.orchestrator = get_orchestrator()

    async def analyze_competitor(
        self,
        competitor_url: str,
        your_business: str
    ) -> Dict[str, Any]:
        """
        Analyze a competitor and generate strategic recommendations.
        """
        # Scrape competitor website
        competitor_info = await self._scrape_website(competitor_url)

        # Generate analysis with AI
        result = await self.orchestrator.generate_text(
            prompt=self.ANALYSIS_PROMPT.format(
                competitor_info=competitor_info,
                your_business=your_business
            ),
            system_prompt="You are a strategic marketing analyst specializing in Russian digital advertising. Provide actionable competitive intelligence.",
            json_schema={"type": "object"},
            optimize_for="quality"
        )

        analysis = result.get("content", {})
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except:
                analysis = {"raw_analysis": analysis}

        analysis["analyzed_at"] = datetime.utcnow().isoformat()
        analysis["competitor_url"] = competitor_url

        return analysis

    async def analyze_multiple(
        self,
        competitor_urls: List[str],
        your_business: str
    ) -> Dict[str, Any]:
        """Analyze multiple competitors and synthesize insights."""
        analyses = []

        for url in competitor_urls[:5]:  # Limit to 5
            try:
                analysis = await self.analyze_competitor(url, your_business)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze {url}: {e}")
                continue

        # Synthesize overall strategy
        synthesis = await self._synthesize_analyses(analyses, your_business)

        return {
            "individual_analyses": analyses,
            "synthesis": synthesis,
            "competitor_count": len(analyses)
        }

    async def _scrape_website(self, url: str) -> str:
        """Scrape and extract key information from a website."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract key elements
                title = soup.title.string if soup.title else ""
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc['content'] if meta_desc else ""

                # Get main text content
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()

                text = soup.get_text(separator=' ', strip=True)[:3000]

                return f"Title: {title}\nDescription: {description}\nContent: {text}"

        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return f"URL: {url} (could not scrape, analyze based on URL pattern)"

    async def _synthesize_analyses(
        self,
        analyses: List[Dict],
        your_business: str
    ) -> Dict[str, Any]:
        """Synthesize multiple competitor analyses into actionable strategy."""
        prompt = f"""Based on these competitor analyses, create a unified competitive strategy.

ANALYSES:
{json.dumps(analyses, indent=2, ensure_ascii=False)}

YOUR BUSINESS:
{your_business}

Create a JSON strategy document:
{{
    "market_position": "where you stand",
    "main_differentiators": ["your unique advantages"],
    "priority_actions": [
        {{"action": "...", "timeline": "...", "expected_result": "..."}}
    ],
    "budget_allocation": {{
        "brand_awareness": "percentage",
        "direct_response": "percentage",
        "competitor_conquesting": "percentage"
    }},
    "messaging_framework": {{
        "primary_message": "...",
        "supporting_points": ["..."],
        "tone": "..."
    }},
    "quick_wins": ["immediate actions for fast results"]
}}
"""

        result = await self.orchestrator.generate_text(
            prompt=prompt,
            json_schema={"type": "object"},
            optimize_for="quality"
        )

        return result.get("content", {})


# =============================================================================
# ROI PREDICTOR
# =============================================================================

class ROIPredictor:
    """
    Machine learning-based ROI prediction.

    Predicts:
    - Expected conversions
    - Cost per acquisition
    - Revenue projections
    - Break-even timeline
    """

    # Industry benchmarks for Russian market (approximations)
    INDUSTRY_BENCHMARKS = {
        "ecommerce": {"avg_ctr": 0.025, "avg_cvr": 0.02, "avg_cpc": 35, "avg_order": 3500},
        "services": {"avg_ctr": 0.03, "avg_cvr": 0.05, "avg_cpc": 50, "avg_order": 5000},
        "saas": {"avg_ctr": 0.02, "avg_cvr": 0.03, "avg_cpc": 80, "avg_order": 15000},
        "education": {"avg_ctr": 0.035, "avg_cvr": 0.04, "avg_cpc": 40, "avg_order": 8000},
        "realestate": {"avg_ctr": 0.015, "avg_cvr": 0.01, "avg_cpc": 100, "avg_order": 50000},
        "auto": {"avg_ctr": 0.02, "avg_cvr": 0.015, "avg_cpc": 60, "avg_order": 25000},
        "beauty": {"avg_ctr": 0.04, "avg_cvr": 0.06, "avg_cpc": 25, "avg_order": 2500},
        "default": {"avg_ctr": 0.025, "avg_cvr": 0.03, "avg_cpc": 45, "avg_order": 4000}
    }

    def __init__(self):
        self.orchestrator = get_orchestrator()

    async def predict_roi(
        self,
        budget: float,
        industry: str,
        business_description: str,
        target_audience: str = None,
        platforms: List[str] = None,
        historical_data: Dict = None
    ) -> Dict[str, Any]:
        """
        Predict ROI for a given budget and business type.
        """
        # Get industry benchmarks
        benchmarks = self.INDUSTRY_BENCHMARKS.get(
            industry.lower(),
            self.INDUSTRY_BENCHMARKS["default"]
        )

        # Adjust based on platforms
        platform_multipliers = {
            "yandex": 1.0,
            "vk": 0.85,
            "ozon": 1.2
        }

        platforms = platforms or ["yandex", "vk"]
        avg_multiplier = sum(
            platform_multipliers.get(p, 1.0) for p in platforms
        ) / len(platforms)

        # Base calculations
        estimated_cpc = benchmarks["avg_cpc"] * avg_multiplier
        estimated_clicks = budget / estimated_cpc
        estimated_conversions = estimated_clicks * benchmarks["avg_cvr"]
        estimated_revenue = estimated_conversions * benchmarks["avg_order"]
        estimated_roi = ((estimated_revenue - budget) / budget) * 100

        # Use AI to refine predictions based on business specifics
        ai_adjustment = await self._get_ai_adjustment(
            business_description,
            target_audience,
            industry,
            benchmarks
        )

        # Apply AI adjustments
        confidence_factor = ai_adjustment.get("confidence_factor", 1.0)
        adjusted_cvr = benchmarks["avg_cvr"] * ai_adjustment.get("cvr_multiplier", 1.0)

        final_conversions = estimated_clicks * adjusted_cvr
        final_revenue = final_conversions * benchmarks["avg_order"] * ai_adjustment.get("aov_multiplier", 1.0)
        final_roi = ((final_revenue - budget) / budget) * 100

        # Calculate scenarios
        scenarios = {
            "pessimistic": {
                "conversions": int(final_conversions * 0.6),
                "revenue": final_revenue * 0.6,
                "roi": ((final_revenue * 0.6 - budget) / budget) * 100
            },
            "realistic": {
                "conversions": int(final_conversions),
                "revenue": final_revenue,
                "roi": final_roi
            },
            "optimistic": {
                "conversions": int(final_conversions * 1.5),
                "revenue": final_revenue * 1.5,
                "roi": ((final_revenue * 1.5 - budget) / budget) * 100
            }
        }

        # Break-even analysis
        break_even_conversions = budget / benchmarks["avg_order"]
        days_to_break_even = max(1, int(break_even_conversions / (final_conversions / 30)))

        return {
            "budget": budget,
            "industry": industry,
            "platforms": platforms,

            "predictions": {
                "impressions": int(estimated_clicks / benchmarks["avg_ctr"]),
                "clicks": int(estimated_clicks),
                "conversions": int(final_conversions),
                "revenue": round(final_revenue, 2),
                "roi_percent": round(final_roi, 1),
                "cpa": round(budget / max(1, final_conversions), 2),
                "roas": round(final_revenue / budget, 2)
            },

            "scenarios": scenarios,

            "break_even": {
                "conversions_needed": int(break_even_conversions),
                "estimated_days": days_to_break_even
            },

            "benchmarks_used": benchmarks,
            "confidence": round(confidence_factor * 100, 1),
            "ai_insights": ai_adjustment.get("insights", []),

            "recommendations": ai_adjustment.get("recommendations", [])
        }

    async def _get_ai_adjustment(
        self,
        business_description: str,
        target_audience: str,
        industry: str,
        benchmarks: Dict
    ) -> Dict[str, Any]:
        """Use AI to adjust predictions based on business specifics."""
        prompt = f"""Analyze this business and provide prediction adjustments.

BUSINESS: {business_description}
TARGET AUDIENCE: {target_audience or 'Not specified'}
INDUSTRY: {industry}
BASELINE BENCHMARKS: {json.dumps(benchmarks)}

Provide JSON with:
{{
    "confidence_factor": 0.0-1.0 (how confident in predictions),
    "cvr_multiplier": 0.5-2.0 (adjust conversion rate),
    "aov_multiplier": 0.5-2.0 (adjust average order value),
    "insights": ["key insights about this business"],
    "recommendations": ["specific recommendations to improve ROI"]
}}

Consider Russian market specifics, seasonality, and competitive landscape.
"""

        try:
            result = await self.orchestrator.generate_text(
                prompt=prompt,
                json_schema={"type": "object"},
                optimize_for="speed"
            )

            content = result.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)

            # Validate and clamp values
            content["confidence_factor"] = max(0.3, min(1.0, content.get("confidence_factor", 0.7)))
            content["cvr_multiplier"] = max(0.5, min(2.0, content.get("cvr_multiplier", 1.0)))
            content["aov_multiplier"] = max(0.5, min(2.0, content.get("aov_multiplier", 1.0)))

            return content

        except Exception as e:
            logger.warning(f"AI adjustment failed: {e}")
            return {
                "confidence_factor": 0.7,
                "cvr_multiplier": 1.0,
                "aov_multiplier": 1.0,
                "insights": [],
                "recommendations": []
            }


# =============================================================================
# CREATIVE SCORER
# =============================================================================

class CreativeScorer:
    """
    AI-powered creative quality scoring.

    Evaluates:
    - Headline effectiveness
    - Call-to-action strength
    - Emotional appeal
    - Clarity and readability
    - Platform compliance
    """

    SCORING_PROMPT = """Score this advertisement creative on multiple dimensions.

AD CREATIVE:
Title: {title}
Text: {text}
Platform: {platform}
Landing URL: {landing_url}

Score each dimension 1-10 and provide specific feedback.
Return JSON:
{{
    "overall_score": 1-10,
    "dimensions": {{
        "headline_power": {{"score": 1-10, "feedback": "..."}},
        "clarity": {{"score": 1-10, "feedback": "..."}},
        "emotional_appeal": {{"score": 1-10, "feedback": "..."}},
        "call_to_action": {{"score": 1-10, "feedback": "..."}},
        "urgency": {{"score": 1-10, "feedback": "..."}},
        "benefit_focus": {{"score": 1-10, "feedback": "..."}},
        "credibility": {{"score": 1-10, "feedback": "..."}},
        "platform_fit": {{"score": 1-10, "feedback": "..."}}
    }},
    "strengths": ["list of strengths"],
    "weaknesses": ["list of weaknesses"],
    "improvement_suggestions": [
        {{"issue": "...", "suggestion": "...", "improved_version": "..."}}
    ],
    "predicted_ctr_range": "X.X% - X.X%",
    "a_b_test_variants": [
        {{"title": "...", "text": "...", "hypothesis": "..."}}
    ]
}}

Be specific to Russian advertising market and {platform} platform requirements.
"""

    def __init__(self):
        self.orchestrator = get_orchestrator()

    async def score_creative(
        self,
        title: str,
        text: str,
        platform: str = "yandex",
        landing_url: str = None
    ) -> Dict[str, Any]:
        """Score a single creative and provide improvement suggestions."""
        result = await self.orchestrator.generate_text(
            prompt=self.SCORING_PROMPT.format(
                title=title,
                text=text,
                platform=platform,
                landing_url=landing_url or "not provided"
            ),
            system_prompt="You are an expert advertising copywriter and creative director specializing in Russian digital marketing.",
            json_schema={"type": "object"},
            optimize_for="quality"
        )

        score = result.get("content", {})
        if isinstance(score, str):
            try:
                score = json.loads(score)
            except:
                score = {"overall_score": 5, "error": "Failed to parse"}

        score["scored_at"] = datetime.utcnow().isoformat()

        return score

    async def score_batch(
        self,
        creatives: List[Dict[str, str]],
        platform: str = "yandex"
    ) -> Dict[str, Any]:
        """Score multiple creatives and rank them."""
        scores = []

        for creative in creatives:
            score = await self.score_creative(
                title=creative.get("title", ""),
                text=creative.get("text", ""),
                platform=platform,
                landing_url=creative.get("landing_url")
            )
            score["creative"] = creative
            scores.append(score)

        # Rank by overall score
        scores.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        return {
            "ranked_creatives": scores,
            "best_creative": scores[0] if scores else None,
            "average_score": sum(s.get("overall_score", 0) for s in scores) / len(scores) if scores else 0,
            "recommendations": self._generate_batch_recommendations(scores)
        }

    def _generate_batch_recommendations(self, scores: List[Dict]) -> List[str]:
        """Generate overall recommendations from batch scoring."""
        recommendations = []

        avg_score = sum(s.get("overall_score", 0) for s in scores) / len(scores) if scores else 0

        if avg_score < 6:
            recommendations.append("Consider rewriting creatives - average score is below acceptable threshold")

        # Find common weaknesses
        weakness_counts = {}
        for score in scores:
            for weakness in score.get("weaknesses", []):
                weakness_counts[weakness] = weakness_counts.get(weakness, 0) + 1

        common_weaknesses = [w for w, c in weakness_counts.items() if c >= len(scores) / 2]
        if common_weaknesses:
            recommendations.append(f"Address common issues across all creatives: {', '.join(common_weaknesses[:3])}")

        return recommendations


# =============================================================================
# AUDIENCE FINDER
# =============================================================================

class AudienceFinder:
    """
    AI-powered audience discovery.

    Features:
    - Find look-alike audiences
    - Discover hidden segments
    - Generate targeting suggestions
    - Expand keyword ideas
    """

    AUDIENCE_PROMPT = """Analyze this business and discover target audiences.

BUSINESS: {business_description}
CURRENT TARGETING: {current_targeting}
PLATFORMS: {platforms}

Find audiences that would be interested in this business.
Return JSON:
{{
    "primary_audience": {{
        "description": "main target audience",
        "demographics": {{
            "age_range": "XX-XX",
            "gender": "all/male/female",
            "income_level": "low/medium/high/premium",
            "locations": ["cities or regions"]
        }},
        "interests": ["list of interests"],
        "behaviors": ["behavioral patterns"],
        "pain_points": ["what problems they have"],
        "motivations": ["what drives them"]
    }},
    "secondary_audiences": [
        {{
            "name": "segment name",
            "description": "...",
            "potential_size": "small/medium/large",
            "expected_conversion_rate": "low/medium/high"
        }}
    ],
    "hidden_opportunities": [
        {{
            "audience": "unexpected audience",
            "reasoning": "why they might convert",
            "targeting_approach": "how to reach them"
        }}
    ],
    "platform_specific_targeting": {{
        "yandex": {{
            "keywords": ["keyword suggestions"],
            "audiences": ["Yandex Audience segments"],
            "retargeting": ["retargeting strategies"]
        }},
        "vk": {{
            "interests": ["VK interest categories"],
            "communities": ["types of communities to target"],
            "look_alike": ["seed audience suggestions"]
        }}
    }},
    "negative_audiences": ["who to exclude"],
    "expansion_keywords": ["keywords to test for expansion"],
    "seasonal_considerations": ["timing recommendations"]
}}

Focus on Russian market and platform-specific features.
"""

    def __init__(self):
        self.orchestrator = get_orchestrator()

    async def find_audiences(
        self,
        business_description: str,
        current_targeting: str = None,
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """Discover target audiences for a business."""
        result = await self.orchestrator.generate_text(
            prompt=self.AUDIENCE_PROMPT.format(
                business_description=business_description,
                current_targeting=current_targeting or "None specified",
                platforms=", ".join(platforms or ["yandex", "vk"])
            ),
            system_prompt="You are a digital marketing strategist specializing in audience research for Russian market.",
            json_schema={"type": "object"},
            optimize_for="quality"
        )

        audiences = result.get("content", {})
        if isinstance(audiences, str):
            try:
                audiences = json.loads(audiences)
            except:
                audiences = {"error": "Failed to parse"}

        return audiences

    async def expand_keywords(
        self,
        seed_keywords: List[str],
        business_type: str
    ) -> Dict[str, Any]:
        """Expand a list of seed keywords using AI."""
        prompt = f"""Expand these seed keywords for {business_type} business.

SEED KEYWORDS: {', '.join(seed_keywords)}

Return JSON:
{{
    "expanded_keywords": [
        {{"keyword": "...", "search_intent": "informational/transactional/navigational", "competition": "low/medium/high", "priority": 1-10}}
    ],
    "long_tail_keywords": ["long tail variations"],
    "negative_keywords": ["keywords to exclude"],
    "keyword_clusters": [
        {{"theme": "...", "keywords": ["..."]}}
    ]
}}
"""

        result = await self.orchestrator.generate_text(
            prompt=prompt,
            json_schema={"type": "object"},
            optimize_for="speed"
        )

        return result.get("content", {})


# =============================================================================
# VOICE ASSISTANT
# =============================================================================

class VoiceAssistant:
    """
    Voice command processing for hands-free advertising management.

    Commands:
    - "Покажи статистику за сегодня"
    - "Увеличь бюджет на 20%"
    - "Создай новую кампанию"
    - "Останови рекламу"
    """

    INTENT_PROMPT = """Parse this voice command for an advertising platform.

COMMAND: {command}
CONTEXT: {context}

Identify the intent and extract parameters.
Return JSON:
{{
    "intent": "get_stats|adjust_budget|create_campaign|pause_campaign|resume_campaign|get_recommendations|unknown",
    "parameters": {{
        "time_period": "today/yesterday/week/month/custom",
        "campaign_id": null or ID,
        "budget_change": null or percentage/amount,
        "platform": null or platform name,
        "other_params": {{}}
    }},
    "confidence": 0.0-1.0,
    "clarification_needed": null or "question to ask",
    "response_preview": "what the assistant should say"
}}
"""

    def __init__(self):
        self.orchestrator = get_orchestrator()

    async def process_command(
        self,
        command: str,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Process a voice command and return structured intent."""
        result = await self.orchestrator.generate_text(
            prompt=self.INTENT_PROMPT.format(
                command=command,
                context=json.dumps(context or {}, ensure_ascii=False)
            ),
            system_prompt="You are a voice assistant for a Russian advertising platform. Parse commands accurately.",
            json_schema={"type": "object"},
            optimize_for="speed"
        )

        intent = result.get("content", {})
        if isinstance(intent, str):
            try:
                intent = json.loads(intent)
            except:
                intent = {"intent": "unknown", "confidence": 0}

        return intent

    async def generate_response(
        self,
        intent: Dict,
        data: Dict = None
    ) -> str:
        """Generate a natural language response for the user."""
        prompt = f"""Generate a natural Russian response for this advertising assistant action.

INTENT: {json.dumps(intent, ensure_ascii=False)}
DATA: {json.dumps(data or {}, ensure_ascii=False)}

The response should be:
- Concise (1-2 sentences)
- Natural Russian
- Include key numbers if relevant
- Friendly but professional

Return just the response text, no JSON.
"""

        result = await self.orchestrator.generate_text(
            prompt=prompt,
            optimize_for="speed"
        )

        return result.get("content", "Команда выполнена.")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def get_competitor_analyzer() -> CompetitorAnalyzer:
    return CompetitorAnalyzer()

def get_roi_predictor() -> ROIPredictor:
    return ROIPredictor()

def get_creative_scorer() -> CreativeScorer:
    return CreativeScorer()

def get_audience_finder() -> AudienceFinder:
    return AudienceFinder()

def get_voice_assistant() -> VoiceAssistant:
    return VoiceAssistant()
