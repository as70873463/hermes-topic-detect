from __future__ import annotations


class TopicState:
    def __init__(self):
        self.current_topic: str | None = None

        self.candidate_topic: str | None = None
        self.candidate_score: float = 0.0

    def decide(
        self,
        new_topic: str | None,
        new_conf: float,
        *,
        inertia: int = 2,
        min_conf: float = 0.45,
    ):
        # Smarter threshold for conversational switching
        threshold = max(
            1.5,
            float(inertia) * 0.8,
        )

        # Low confidence handling
        if (
            not new_topic
            or new_topic == "none"
            or new_conf < min_conf
        ):
            if self.current_topic:
                return (
                    self.current_topic,
                    False,
                    "low_conf_keep_current",
                )

            return (
                "none",
                False,
                "low_conf_no_topic",
            )

        # Initial topic
        if self.current_topic is None:
            self.current_topic = new_topic

            self.candidate_topic = None
            self.candidate_score = 0.0

            return (
                new_topic,
                True,
                "initial_topic",
            )

        # Same topic reinforcement
        if new_topic == self.current_topic:
            self.candidate_topic = None
            self.candidate_score = 0.0

            return (
                self.current_topic,
                False,
                "same_topic",
            )

        # New candidate topic
        if self.candidate_topic != new_topic:
            self.candidate_topic = new_topic
            self.candidate_score = new_conf

            return (
                self.current_topic,
                False,
                f"candidate_started:{self.candidate_score:.2f}",
            )

        # Build candidate confidence
        self.candidate_score += new_conf

        # Switch topic
        if self.candidate_score >= threshold:
            old = self.current_topic

            self.current_topic = new_topic

            self.candidate_topic = None
            self.candidate_score = 0.0

            return (
                new_topic,
                True,
                f"switch_from_{old}",
            )

        # Still building
        return (
            self.current_topic,
            False,
            f"candidate_building:{self.candidate_score:.2f}",
        )
