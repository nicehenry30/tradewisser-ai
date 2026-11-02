from __future__ import annotations

from typing import Any

from app.models.evidence import EvidenceObservation, EvidenceSource


class QuantitativeEvidenceService:
    """
    Synthesizes quantitative evidence from multiple timeframes.

    QuantitativeAnalytics measures historical market behavior.
    This service interprets those measurements and combines them
    into one Quantitative Evidence Family.

    It does not make trade decisions.
    """

    def synthesize(
        self,
        four_hour: dict[str, Any],
        one_hour: dict[str, Any],
    ) -> EvidenceSource:
        four_hour_direction = self._direction(four_hour)
        one_hour_direction = self._direction(one_hour)

        direction = self._family_direction(
            four_hour_direction,
            one_hour_direction,
        )

        four_hour_strength = self._strength(four_hour)
        one_hour_strength = self._strength(one_hour)

        strength = self._family_strength(
            direction=direction,
            four_hour_direction=four_hour_direction,
            one_hour_direction=one_hour_direction,
            four_hour_strength=four_hour_strength,
            one_hour_strength=one_hour_strength,
        )

        confidence = self._family_confidence(
            direction=direction,
            four_hour=four_hour,
            one_hour=one_hour,
            four_hour_direction=four_hour_direction,
            one_hour_direction=one_hour_direction,
        )

        sample_size = self._combined_sample_size(
            four_hour,
            one_hour,
        )

        observations = [
            EvidenceObservation(
                name="four_hour_direction",
                value=four_hour_direction,
                description="Directional interpretation of 4H forward behavior.",
            ),
            EvidenceObservation(
                name="one_hour_direction",
                value=one_hour_direction,
                description="Directional interpretation of 1H forward behavior.",
            ),
            EvidenceObservation(
                name="four_hour_strength",
                value=four_hour_strength,
                description="Strength of the observed 4H directional behavior.",
            ),
            EvidenceObservation(
                name="one_hour_strength",
                value=one_hour_strength,
                description="Strength of the observed 1H directional behavior.",
            ),
            EvidenceObservation(
                name="four_hour_forward_positive_rate",
                value=self._forward_positive_rate(four_hour),
                unit="probability",
            ),
            EvidenceObservation(
                name="one_hour_forward_positive_rate",
                value=self._forward_positive_rate(one_hour),
                unit="probability",
            ),
            EvidenceObservation(
                name="four_hour_volatility",
                value=self._volatility_classification(four_hour),
            ),
            EvidenceObservation(
                name="one_hour_volatility",
                value=self._volatility_classification(one_hour),
            ),
        ]

        limitations = [
            "Historical quantitative behavior is evidence, not a guarantee of future outcome."
        ]

        if four_hour_direction != one_hour_direction:
            if "neutral" in {four_hour_direction, one_hour_direction}:
                limitations.append(
                    "4H and 1H quantitative evidence are not fully aligned."
                )
            else:
                limitations.append(
                    "4H and 1H quantitative evidence conflict."
                )

        return EvidenceSource(
            source="quantitative_analytics",
            observations=observations,
            direction=direction,
            confidence=confidence,
            sample_size=sample_size,
            strength=strength,
            limitations=limitations,
        )

    @staticmethod
    def _direction(quantitative: dict[str, Any]) -> str:
        forward = quantitative.get("forward_behavior", {})

        positive_rate = float(
            forward.get("positive_rate", 0.0) or 0.0
        )
        negative_rate = float(
            forward.get("negative_rate", 0.0) or 0.0
        )

        if positive_rate > negative_rate:
            return "bullish"

        if negative_rate > positive_rate:
            return "bearish"

        return "neutral"

    @staticmethod
    def _strength(quantitative: dict[str, Any]) -> str:
        forward = quantitative.get("forward_behavior", {})

        positive_rate = float(
            forward.get("positive_rate", 0.0) or 0.0
        )
        negative_rate = float(
            forward.get("negative_rate", 0.0) or 0.0
        )

        separation = abs(positive_rate - negative_rate)

        if separation >= 0.50:
            return "strong"

        if separation >= 0.20:
            return "moderate"

        return "weak"

    @staticmethod
    def _family_direction(
        four_hour_direction: str,
        one_hour_direction: str,
    ) -> str:
        if (
            four_hour_direction != "neutral"
            and one_hour_direction != "neutral"
            and four_hour_direction != one_hour_direction
        ):
            return "neutral"

        if four_hour_direction != "neutral":
            return four_hour_direction

        if one_hour_direction != "neutral":
            return one_hour_direction

        return "neutral"

    @staticmethod
    def _family_strength(
        *,
        direction: str,
        four_hour_direction: str,
        one_hour_direction: str,
        four_hour_strength: str,
        one_hour_strength: str,
    ) -> str:
        if direction == "neutral":
            if (
                four_hour_direction != "neutral"
                and one_hour_direction != "neutral"
            ):
                return "moderate"

            return "weak"

        strengths = {four_hour_strength, one_hour_strength}

        if (
            four_hour_direction == direction
            and one_hour_direction == direction
        ):
            if "strong" in strengths:
                return "strong"

            if "moderate" in strengths:
                return "moderate"

            return "weak"

        if four_hour_direction == direction:
            return four_hour_strength

        return "weak"

    @classmethod
    def _family_confidence(
        cls,
        *,
        direction: str,
        four_hour: dict[str, Any],
        one_hour: dict[str, Any],
        four_hour_direction: str,
        one_hour_direction: str,
    ) -> float:
        four_hour_confidence = cls._timeframe_confidence(four_hour)
        one_hour_confidence = cls._timeframe_confidence(one_hour)

        if direction == "neutral":
            return round(
                min(four_hour_confidence, one_hour_confidence) * 0.50,
                3,
            )

        if (
            four_hour_direction == direction
            and one_hour_direction == direction
        ):
            return round(
                min(four_hour_confidence, one_hour_confidence) * 0.90,
                3,
            )

        return round(
            four_hour_confidence * 0.75,
            3,
        )

    @staticmethod
    def _timeframe_confidence(
        quantitative: dict[str, Any],
    ) -> float:
        sample = quantitative.get("sample", {})
        observations = int(
            sample.get("forward_observations", 0) or 0
        )

        if observations <= 0:
            return 0.0

        return min(observations / 100.0, 1.0)

    @staticmethod
    def _combined_sample_size(
        four_hour: dict[str, Any],
        one_hour: dict[str, Any],
    ) -> int:
        four_hour_sample = int(
            four_hour.get("sample", {})
            .get("forward_observations", 0)
            or 0
        )

        one_hour_sample = int(
            one_hour.get("sample", {})
            .get("forward_observations", 0)
            or 0
        )

        return four_hour_sample + one_hour_sample

    @staticmethod
    def _forward_positive_rate(
        quantitative: dict[str, Any],
    ) -> float | None:
        value = quantitative.get(
            "forward_behavior", {}
        ).get("positive_rate")

        if value is None:
            return None

        return float(value)

    @staticmethod
    def _volatility_classification(
        quantitative: dict[str, Any],
    ) -> str | None:
        return quantitative.get(
            "volatility", {}
        ).get("classification")
