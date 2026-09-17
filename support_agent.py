"""Small support-triage agent used as the system under evaluation."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TriageResult:
    category: str
    priority: str
    action: str
    steps: int
    input_tokens: int
    output_tokens: int


class SupportTriageAgent:
    """Classify a support message and recommend a next action.

    The deliberately compact rules make the example runnable offline. The
    evaluation report exposes the limitations rather than hiding them.
    """

    RULES = (
        ("security", ("hacked", "unauthorized", "stolen", "phishing", "breach")),
        ("billing", ("charged", "refund", "invoice", "payment", "subscription", "bill")),
        ("account_access", ("login", "password", "locked", "sign in", "2fa", "verification code")),
        ("technical", ("error", "crash", "broken", "not loading", "bug", "timeout", "sync")),
        ("cancellation", ("cancel", "close my account", "terminate")),
        ("general", ()),
    )

    ACTIONS = {
        "security": "escalate_security",
        "billing": "route_billing",
        "account_access": "start_account_recovery",
        "technical": "collect_diagnostics",
        "cancellation": "start_cancellation",
        "general": "request_more_information",
    }

    def run(self, text: str) -> TriageResult:
        if not isinstance(text, str):
            raise TypeError("message must be a string")
        cleaned = re.sub(r"\s+", " ", text.strip().lower())
        if not cleaned:
            category = "general"
        else:
            category = next(
                name for name, words in self.RULES
                if not words or any(word in cleaned for word in words)
            )

        urgent_markers = ("urgent", "immediately", "asap", "fraud", "hacked", "cannot work")
        priority = "high" if category == "security" or any(x in cleaned for x in urgent_markers) else "normal"
        action = self.ACTIONS[category]

        # Transparent approximation: one token is roughly four characters.
        input_tokens = max(1, (len(text) + 3) // 4)
        output_text = f"{category} {priority} {action}"
        output_tokens = max(1, (len(output_text) + 3) // 4)
        return TriageResult(category, priority, action, 3, input_tokens, output_tokens)

