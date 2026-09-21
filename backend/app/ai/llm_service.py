import json
import logging
import os
import sys
from typing import Any

from app.analytics.models import VerifiedResult
from app.analyst.answer_builder import AnswerBuilder
from app.ai.prompt_builder import PromptBuilder
from app.ai.provider import AICompletionRequest, get_llm_provider
from app.validation.grounding_validator import GroundingValidator

logger = logging.getLogger(__name__)


def _debug_chat_failure(
    stage: str,
    raw_text: str,
    verified: VerifiedResult,
    warnings: list[str],
    user_prompt: str,
) -> None:
    msg = (
        "\n" + "=" * 80 + "\n"
        f"[DEBUG_AI_VALIDATION] AI ANALYST CHAT VALIDATION FAILURE (STAGE: {stage.upper()}):\n"
        f"--- RAW LLM RESPONSE ---\n{raw_text}\n\n"
        f"--- VERIFIED EVIDENCE / RESULT ---\n"
        f"intent: {verified.intent}\n"
        f"target_value: {verified.get_value()}\n"
        f"result: {json.dumps(verified.result, indent=2, default=str)}\n"
        f"context: {json.dumps(verified.context or {}, indent=2, default=str)}\n\n"
        f"--- REJECTION WARNINGS / REASONS ---\n{json.dumps(warnings, indent=2)}\n\n"
        f"--- USER PROMPT SENT TO LLM ---\n{user_prompt}\n"
        + "=" * 80
    )
    logger.warning("%s", msg)
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


class LLMService:
    """Coordinates external LLM text generation strictly grounded in VerifiedResult."""

    @classmethod
    async def generate_grounded_response(
        cls,
        question: str,
        verified: VerifiedResult,
        conversation_context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        # Always build baseline deterministic answer first as guaranteed fallback
        deterministic_response = AnswerBuilder.build_answer(verified)
        deterministic_response["ai_status"] = "VERIFIED_ANALYTICS_ONLY"

        # If already unavailable or clarification, return immediately without wasting LLM tokens
        if verified.verification_status in ("unavailable", "clarification") or verified.is_unavailable:
            return deterministic_response

        provider = get_llm_provider()

        # If deterministic fallback provider is active, return deterministic answer
        if provider.provider_name() == "deterministic-fallback":
            return deterministic_response

        # Execute external LLM
        try:
            req = AICompletionRequest(
                system_prompt=PromptBuilder.get_system_prompt(),
                user_prompt=PromptBuilder.build_user_prompt(question, verified, conversation_context),
                temperature=0.1,
                max_tokens=512,
            )
            completion = await provider.generate(req)
            raw_text = completion.content.strip()

            if not raw_text:
                return deterministic_response

            debug_enabled = os.getenv("DEBUG_AI_VALIDATION", "false").lower() in ("true", "1", "yes")

            # Strict numerical and factual grounding validation
            final_text, is_grounded, warnings = GroundingValidator.validate_and_ground(raw_text, verified)
            if not is_grounded:
                if debug_enabled:
                    _debug_chat_failure(
                        stage="grounding",
                        raw_text=raw_text,
                        verified=verified,
                        warnings=warnings,
                        user_prompt=req.user_prompt,
                    )
                logger.warning("Grounding validation failed; using deterministic fallback. Warnings: %s", warnings)
                return deterministic_response

            # Canonical Guardrails (Benchmark, Risk, Causation, Leaks)
            from app.ai.validation.benchmark_validator import BenchmarkValidator
            from app.ai.validation.risk_claim_validator import RiskClaimValidator
            from app.ai.validation.unsupported_inference_validator import UnsupportedInferenceValidator

            b_res = BenchmarkValidator.validate_text(final_text, has_benchmark_data=False)
            if not b_res.is_valid:
                if debug_enabled:
                    _debug_chat_failure(
                        stage="benchmark",
                        raw_text=raw_text,
                        verified=verified,
                        warnings=b_res.unsupported_claims,
                        user_prompt=req.user_prompt,
                    )
                logger.warning("Benchmark guardrail triggered: %s; using deterministic fallback.", b_res.unsupported_claims)
                return deterministic_response

            r_res = RiskClaimValidator.validate_text(final_text, has_risk_model=False)
            if not r_res.is_valid:
                if debug_enabled:
                    _debug_chat_failure(
                        stage="risk",
                        raw_text=raw_text,
                        verified=verified,
                        warnings=r_res.unsupported_risks,
                        user_prompt=req.user_prompt,
                    )
                logger.warning("Risk guardrail triggered: %s; using deterministic fallback.", r_res.unsupported_risks)
                return deterministic_response

            inf_res = UnsupportedInferenceValidator.validate_inferences(final_text, has_causal_evidence=False)
            if not inf_res.is_valid:
                if debug_enabled:
                    _debug_chat_failure(
                        stage="inference",
                        raw_text=raw_text,
                        verified=verified,
                        warnings=inf_res.violations,
                        user_prompt=req.user_prompt,
                    )
                logger.warning("Inference guardrail triggered: %s; using deterministic fallback.", inf_res.violations)
                return deterministic_response

            deterministic_response["answer"] = final_text
            deterministic_response["ai_status"] = "AI_GENERATED_GROUNDED"
            return deterministic_response

        except Exception as exc:
            logger.error("External LLM execution failed: %s; falling back to deterministic answer.", exc)
            return deterministic_response
