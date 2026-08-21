import re
from rapidfuzz import fuzz

def normalize_text(text: str) -> str:
    """Lowercase and strip excessive whitespace/punctuation for comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())

def verify_grounding(quote: str, transcript_segments: list[dict], threshold: float = 82.0) -> tuple[bool, float, str | None]:
    """
    Verifies if a candidate quote is genuinely grounded in the diarized transcript.
    Returns: (is_grounded, confidence_score, matched_segment_id)
    """
    if not quote or not transcript_segments:
        return False, 0.0, None

    clean_quote = normalize_text(quote)
    if not clean_quote:
        return False, 0.0, None

    # Full concatenated transcript for exact check
    full_transcript_text = " ".join([normalize_text(s.get("text", "")) for s in transcript_segments])

    # Stage 1: Exact Substring Check (100% confidence)
    if clean_quote in full_transcript_text:
        for seg in transcript_segments:
            if clean_quote in normalize_text(seg.get("text", "")):
                return True, 100.0, str(seg.get("id"))
        return True, 100.0, str(transcript_segments[0].get("id"))

    # Stage 2: Stricter Fuzzy Matching via token_set_ratio & token_sort_ratio
    best_score = 0.0
    best_segment_id = None

    for seg in transcript_segments:
        seg_text = normalize_text(seg.get("text", ""))
        if not seg_text:
            continue

        score_set = fuzz.token_set_ratio(clean_quote, seg_text)
        score_sort = fuzz.token_sort_ratio(clean_quote, seg_text)
        combined_score = max(score_set, score_sort)

        if combined_score > best_score:
            best_score = combined_score
            best_segment_id = str(seg.get("id"))

    is_verified = best_score >= threshold
    return is_verified, round(best_score, 2), (best_segment_id if is_verified else None)

class GroundingVerifier:
    @staticmethod
    def verify_action_items(action_items: list[dict], transcript_segments: list[dict], threshold: float = 82.0) -> list[dict]:
        verified_items = []
        for item in action_items:
            quote = (
                item.get("source_quote") 
                or item.get("grounding_quote") 
                or item.get("quote") 
                or ""
            )
            is_grounded, score, segment_id = verify_grounding(quote, transcript_segments, threshold)
            
            updated_item = dict(item)
            updated_item["source_quote"] = quote
            updated_item["is_grounded"] = is_grounded
            updated_item["grounding_score"] = score
            updated_item["matched_segment_id"] = segment_id
            verified_items.append(updated_item)
        return verified_items

# Export instances for all import styles
grounding_verifier = GroundingVerifier()
grounding_filter = GroundingVerifier.verify_action_items