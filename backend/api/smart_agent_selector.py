"""
Smart Agent Selection Service
Selects relevant personas based on demographics and industry/interests alignment
Uses OpenAI for intelligent semantic matching
"""
from typing import List, Dict, Any, Optional
import random
import json
from db.supabase_client import supabase_client
from utils.openai_client import openai_client


class SmartAgentSelector:
    """
    Selects 50 relevant personas for ad analysis based on:
    - Age range alignment with target audience
    - 40% industry/interests match
    - Diversity in the remaining 60%
    """

    def __init__(self):
        self.supabase = supabase_client

    def select_relevant_personas(
        self,
        target_age_range: Optional[str] = None,  # e.g., "18-24", "25-34", "35-44", "45+"
        industry_keywords: Optional[List[str]] = None,  # e.g., ["fitness", "health"]
        num_personas: int = 50,
        industry_match_ratio: float = 0.4  # 40% should match industry
    ) -> List[Dict[str, Any]]:
        """
        Select personas matching criteria

        Args:
            target_age_range: Target age cohort (e.g., "18-24")
            industry_keywords: List of industry/interest keywords to match
            num_personas: Total number of personas to select (default 50)
            industry_match_ratio: Ratio of personas that should match industry (default 0.4 = 40%)

        Returns:
            List of selected persona records
        """
        # Calculate split
        num_industry_match = int(num_personas * industry_match_ratio)
        num_age_diverse = num_personas - num_industry_match

        # Step 1: Get personas matching age range
        age_matched_personas = self._get_personas_by_age(target_age_range) if target_age_range else []

        # Step 2: From age-matched personas, get those that also match industry
        industry_matched = []
        if industry_keywords and age_matched_personas:
            industry_matched = self._filter_by_industry(age_matched_personas, industry_keywords)

        # Step 3: Build final selection
        selected_personas = []

        # Add industry-matched personas (up to 40%)
        if industry_matched:
            selected_count = min(len(industry_matched), num_industry_match)
            selected_personas.extend(random.sample(industry_matched, selected_count))

        # Fill remaining slots with age-matched but diverse industry
        remaining_slots = num_personas - len(selected_personas)
        if remaining_slots > 0 and age_matched_personas:
            # Remove already selected personas
            selected_ids = {p['id'] for p in selected_personas}
            diverse_pool = [p for p in age_matched_personas if p['id'] not in selected_ids]

            if diverse_pool:
                diverse_count = min(len(diverse_pool), remaining_slots)
                selected_personas.extend(random.sample(diverse_pool, diverse_count))

        # If we still don't have 50, fill with random personas
        if len(selected_personas) < num_personas:
            remaining_slots = num_personas - len(selected_personas)
            selected_ids = {p['id'] for p in selected_personas}

            # Get all personas not yet selected
            all_personas = self._get_all_personas()
            remaining_pool = [p for p in all_personas if p['id'] not in selected_ids]

            if remaining_pool:
                fill_count = min(len(remaining_pool), remaining_slots)
                selected_personas.extend(random.sample(remaining_pool, fill_count))

        return selected_personas[:num_personas]

    def _get_personas_by_age(self, age_range: str) -> List[Dict[str, Any]]:
        """
        Fetch personas matching the age range
        """
        try:
            # Query personas where demographics->age_range matches
            response = self.supabase.from_("personas").select(
                "id, name, summary, demographics, psychographics, pain_points, motivations"
            ).execute()

            if not response.data:
                return []

            # Filter by age range in demographics JSONB
            matched = []
            for persona in response.data:
                demographics = persona.get('demographics', {})
                if isinstance(demographics, dict):
                    persona_age = demographics.get('age_range', '')
                    if persona_age == age_range:
                        matched.append(persona)
                elif isinstance(demographics, str):
                    # Handle string-encoded JSON
                    import json
                    try:
                        demographics_dict = json.loads(demographics)
                        persona_age = demographics_dict.get('age_range', '')
                        if persona_age == age_range:
                            matched.append(persona)
                    except:
                        pass

            return matched

        except Exception as e:
            print(f"Error fetching personas by age: {e}")
            return []

    def _filter_by_industry(
        self,
        personas: List[Dict[str, Any]],
        industry_keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Use OpenAI to intelligently filter personas based on industry/interests alignment
        Returns personas ranked by relevance to the industry keywords
        """
        if not personas or not industry_keywords:
            return []

        # Build a concise description of each persona
        persona_descriptions = []
        for persona in personas:
            # Parse JSON fields if needed
            psychographics = persona.get('psychographics', {})
            if isinstance(psychographics, str):
                try:
                    psychographics = json.loads(psychographics)
                except:
                    psychographics = {}

            pain_points = persona.get('pain_points', [])
            motivations = persona.get('motivations', [])

            # Build compact persona description
            desc = f"{persona.get('name', 'Unknown')}: {persona.get('summary', '')} | "
            desc += f"Values: {psychographics.get('values', [])} | "
            desc += f"Pain Points: {', '.join(pain_points[:3]) if pain_points else 'None'} | "
            desc += f"Motivations: {', '.join(motivations[:3]) if motivations else 'None'}"

            persona_descriptions.append({
                'id': persona['id'],
                'description': desc,
                'full_data': persona
            })

        # Use OpenAI to rank personas by relevance
        industry_str = ', '.join(industry_keywords)

        system_prompt = f"""You are an expert audience analyst. Given a list of personas and industry keywords, select the personas most relevant to those industries.

Industry Keywords: {industry_str}

Return a JSON array of persona IDs ranked by relevance (most relevant first). Only include personas with clear alignment to the industry keywords.

Format: {{"relevant_persona_ids": ["id1", "id2", ...]}}

Be selective - only include personas with strong industry alignment."""

        # Build user prompt with persona list
        user_prompt = "Personas:\n\n"
        for i, p in enumerate(persona_descriptions[:100], 1):  # Limit to 100 to avoid token limits
            user_prompt += f"{i}. ID: {p['id']}\n   {p['description']}\n\n"

        try:
            # Call OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            relevant_ids = result.get('relevant_persona_ids', [])

            # Return personas in order of relevance
            matched = []
            for persona_id in relevant_ids:
                for p in persona_descriptions:
                    if p['id'] == persona_id:
                        matched.append(p['full_data'])
                        break

            print(f"✓ OpenAI selected {len(matched)} industry-matched personas from {len(personas)} candidates")
            return matched

        except Exception as e:
            print(f"Error using OpenAI for persona selection: {e}")
            # Fallback to keyword matching
            return self._filter_by_industry_fallback(personas, industry_keywords)

    def _filter_by_industry_fallback(
        self,
        personas: List[Dict[str, Any]],
        industry_keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fallback keyword-based filtering if OpenAI fails
        """
        matched = []

        for persona in personas:
            # Check psychographics, pain_points, motivations for keyword matches
            text_to_search = []

            # Add summary
            if persona.get('summary'):
                text_to_search.append(persona['summary'].lower())

            # Add psychographics
            psychographics = persona.get('psychographics', {})
            if isinstance(psychographics, dict):
                text_to_search.append(str(psychographics).lower())
            elif isinstance(psychographics, str):
                text_to_search.append(psychographics.lower())

            # Add pain_points and motivations
            pain_points = persona.get('pain_points', [])
            motivations = persona.get('motivations', [])

            if isinstance(pain_points, list):
                text_to_search.extend([str(p).lower() for p in pain_points])
            if isinstance(motivations, list):
                text_to_search.extend([str(m).lower() for m in motivations])

            # Check if any keyword matches
            combined_text = ' '.join(text_to_search)
            if any(keyword.lower() in combined_text for keyword in industry_keywords):
                matched.append(persona)

        return matched

    def _get_all_personas(self) -> List[Dict[str, Any]]:
        """
        Fetch all personas from database
        """
        try:
            response = self.supabase.from_("personas").select(
                "id, name, summary, demographics, psychographics, pain_points, motivations"
            ).execute()

            return response.data if response.data else []

        except Exception as e:
            print(f"Error fetching all personas: {e}")
            return []


# Singleton instance
smart_selector = SmartAgentSelector()
