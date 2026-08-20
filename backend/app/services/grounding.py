from thefuzz import fuzz
from typing import List
from app.schemas import ActionItemCandidate

class GroundingFilter:
    def __init__(self, threshold: int = 70):
        self.threshold = threshold

    def verify_action_items(
        self, 
        action_items: List[ActionItemCandidate], 
        transcript: str
    ) -> List[ActionItemCandidate]:
        verified_items = []
        normalized_transcript = transcript.lower()

        for item in action_items:
            quote = item.source_quote.strip().lower()
            if not quote:
                continue

            match_score = fuzz.partial_ratio(quote, normalized_transcript)
            
            if match_score >= self.threshold:
                verified_items.append(item)
            else:
                print(f"[GroundingFilter] Dropped hallucinated item: '{item.task}' (Match score: {match_score})")

        return verified_items

grounding_filter = GroundingFilter(threshold=70)