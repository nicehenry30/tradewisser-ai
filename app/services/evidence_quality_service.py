from __future__ import annotations

from app.models.evidence import EvidenceSource
from app.models.evidence_quality import EvidenceQuality


class EvidenceQualityService:
    """
    Evaluates the quality of a single evidence source.

    This service does not determine trade direction.
    It only evaluates how trustworthy/useful the supplied
    evidence is based on its strength, confidence, sample size,
    and limitations.
    """

    def evaluate(self, evidence: EvidenceSource) -> EvidenceQuality:
        reasons: list[str] = []

        if evidence.direction == "neutral":
            reasons.append("Evidence is neutral.")
            return EvidenceQuality(
                quality="neutral",
                reasons=reasons,
            )

        if evidence.strength == "strong":
            reasons.append("Evidence has strong directional strength.")
        elif evidence.strength == "moderate":
            reasons.append("Evidence has moderate directional strength.")
        else:
            reasons.append("Evidence has weak directional strength.")

        confidence = evidence.confidence

        if confidence is None:
            reasons.append("Confidence is unavailable.")
        elif confidence >= 0.75:
            reasons.append("Confidence is high.")
        elif confidence >= 0.50:
            reasons.append("Confidence is moderate.")
        else:
            reasons.append("Confidence is low.")

        if evidence.sample_size is None:
            reasons.append("Sample size is unavailable.")
        elif evidence.sample_size < 30:
            reasons.append("Sample size is limited.")
        elif evidence.sample_size < 100:
            reasons.append("Sample size is moderate.")
        else:
            reasons.append("Sample size is substantial.")

        if evidence.limitations:
            reasons.append("Evidence has documented limitations.")

        quality = self._classify(
            strength=evidence.strength,
            confidence=confidence,
            sample_size=evidence.sample_size,
            limitations=evidence.limitations,
        )

        return EvidenceQuality(
            quality=quality,
            reasons=reasons,
        )
  
    @staticmethod
    def _classify(
        *,
        strength: str | None,
        confidence: float | None,
        sample_size: int | None,
        limitations: list[str],
    ) -> str:
        # Explicitly weak evidence remains weak.
        if strength == "weak":
            return "weak"

        if confidence is not None and confidence < 0.50:
            return "weak"

        if sample_size is not None and sample_size < 30:
            return "weak"

        # If there is no quality metadata at all, do not
        # incorrectly label the evidence as weak.
        if (
            strength is None
            and confidence is None
            and sample_size is None
            and not limitations
        ):
            return "unspecified"

        if strength == "strong" and confidence is not None and confidence >= 0.75:
            if sample_size is None or sample_size >= 30:
                return "strong"

        if strength in {"strong", "moderate"}:
            if confidence is None or confidence >= 0.50:
                return "moderate"

        if limitations and strength == "moderate":
            return "moderate"

        return "unspecified"