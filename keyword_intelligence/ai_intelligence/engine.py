"""Main engine orchestrating the AI classification process."""

from __future__ import annotations

import time
from typing import Any, cast

from loguru import logger

from keyword_intelligence.ai_intelligence.cache import AICache, InMemoryAICache
from keyword_intelligence.ai_intelligence.components.parsing import (
    ResponseParser,
    ResponseValidator,
)
from keyword_intelligence.ai_intelligence.components.prompts import (
    PromptBuilder,
    PromptRegistry,
    PromptRenderer,
    PromptTemplate,
)
from keyword_intelligence.ai_intelligence.components.scoring import (
    ConfidenceScorer,
    ResultAggregator,
)
from keyword_intelligence.ai_intelligence.config import AIEngineConfig
from keyword_intelligence.ai_intelligence.executor import (
    AIBatchExecutor,
    SequentialAIBatchExecutor,
)
from keyword_intelligence.ai_intelligence.models import (
    AIClassificationResult,
    AIEngineStatistics,
    AIProviderMetrics,
)
from keyword_intelligence.ai_intelligence.registry import (
    AIProviderRegistry,
    AIProviderResolver,
)
from keyword_intelligence.config.settings import Settings
from keyword_intelligence.pipeline.context import PipelineContext


class AIEngine:
    """High-level facade for fetching AI classifications.

    Responsibilities:
    - Enforce provider capabilities
    - Check cache using SHA256 deterministic keys
    - Coordinate pipeline components (Renderer, Executor, Parser, Validator, Scorer, Aggregator)
    - Collect robust execution statistics
    """

    def __init__(
        self,
        settings: Settings,
        cache: AICache | None = None,
        registry: AIProviderRegistry | None = None,
        prompt_registry: PromptRegistry | None = None,
        executor: AIBatchExecutor | None = None,
    ) -> None:
        self.settings = settings
        self.config = AIEngineConfig.from_settings(settings)

        self.cache = cache or InMemoryAICache()

        if registry is None:
            raise ValueError(
                "AIProviderRegistry must be provided. Providers should not be instantiated in the engine."
            )

        self.resolver = AIProviderResolver(registry)

        if prompt_registry is None:
            prompt_registry = PromptRegistry()
            # Register a default prompt template for providers
            for p in ["mock", "ollama", "openai", "gemini"]:
                prompt_registry.register(
                    PromptTemplate(
                        prompt_name="default_classifier",
                        prompt_version="1.0.0",
                        provider=p,
                        schema_version="1.0",
                        system_prompt=(
                            "You are an expert AI Business & SEO analyst. "
                            "Respond ONLY with a JSON array of objects. Do not output markdown blocks or conversational text. "
                            "Each object must STRICTLY follow this schema:\n"
                            "{{\n"
                            '  "keyword": "...",\n'
                            '  "relevant": true or false,\n'
                            '  "classification": "RELEVANT" or "IRRELEVANT",\n'
                            '  "confidence": <int 0-100>,\n'
                            '  "reasoning": "...",\n'
                            '  "matched_business_fact": "...",\n'
                            '  "matched_category": "...",\n'
                            '  "matched_brand": "...",\n'
                            '  "matched_product": "..."\n'
                            "}}\n"
                            "For semantic relevance detection, answer: 'Would a knowledgeable employee of this retailer consider this keyword relevant to the retailer's products, services, customer intent, or business domain?'\n"
                            "Use BOTH Business Facts and Business Knowledge to reason. The website data is supporting evidence, not the only source of truth. Semantically related keywords should be accepted even if missing from the website.\n\n"
                            "Examples (Retailer: Lenovo):\n"
                            "Relevant: gaming laptop, usb hub, wireless mouse, developer workstation, business laptop, server rack, thinkpad x1.\n"
                            "Not Relevant: running shoes, gold ring, diamond necklace, football boots, lipstick, dog food, washing machine.\n"
                            "For irrelevant keywords, set relevant=false, classification=IRRELEVANT, provide semantic reasoning explaining why it is unrelated to the business domain, and set matched fields to null."
                        ),
                        user_prompt_template="{{business_context}}\n\nClassify these keywords: {{keywords}}",
                    )
                )

        self.prompt_builder = PromptBuilder(prompt_registry)
        self.prompt_renderer = PromptRenderer()

        self.executor = executor or SequentialAIBatchExecutor()
        self.parser = ResponseParser()
        self.validator = ResponseValidator()
        self.scorer = ConfidenceScorer()
        self.aggregator = ResultAggregator()

    @staticmethod
    def _is_retryable_error(e: Exception) -> bool:
        err_str = str(e).lower()
        retry_keywords = ["429", "402", "500", "502", "503", "504", "quota", "rate limit", "timeout", "payment required"]
        return any(k in err_str for k in retry_keywords)

    def process(self, context: PipelineContext) -> None:
        """Process the context DataFrame through the AI engine."""
        logger.info("Starting AI Keyword Intelligence Engine.")
        start_time = time.perf_counter()

        if not context.has_data:
            logger.warning("No data found in context. Skipping AI Classification.")
            return

        # 1. Filter keywords to only those that are UNCERTAIN or missing relevance from BusinessContextStage
        df = context.data
        if "business_relevance" in df.columns:
            # We only send to AI if deterministic filter couldn't resolve it
            mask = df["business_relevance"].isna() | (
                df["business_relevance"] == "UNCERTAIN"
            )
            keywords = df.loc[mask, "keyword"].tolist()
        else:
            keywords = df["keyword"].tolist()

        total_kws = len(keywords)
        if total_kws == 0:
            logger.info(
                "All keywords were deterministically resolved. Skipping AI Classification."
            )
            # We still need to record stage metrics for reporting
            from keyword_intelligence.models.pipeline import StageMetrics

            context.stage_metrics.append(
                StageMetrics(stage_name="AI_CLASSIFICATION", processing_time_ms=0.0)
            )
            return

        logger.info("AI Classification")
        logger.info(f"Received: {total_kws} keywords")

        # 2. Resolve Provider and Prompt
        provider = self.resolver.resolve(self.config.provider)
        template = self.prompt_builder.build(
            provider.provider_name, "default_classifier", "1.0.0"
        )

        # 2. Enforce Capabilities (Max Batch Size)
        actual_batch_size = min(
            self.config.batch_size, provider.capabilities.max_batch_size
        )
        if actual_batch_size < self.config.batch_size:
            logger.warning(
                f"Configured AI batch size ({self.config.batch_size}) exceeds provider "
                f"limit ({provider.capabilities.max_batch_size}). Enforcing provider limit."
            )

        # 3. Cache Check
        keywords_to_fetch: list[str] = []
        final_results: list[AIClassificationResult] = []

        company_name = (
            context.business_profile.company_name
            if hasattr(context, "business_profile") and context.business_profile
            else "unknown_company"
        )

        for kw in keywords:
            cache_key = self.cache.generate_key(
                company_name, kw, provider.provider_name, template.prompt_version
            )
            cached_res = self.cache.get(cache_key)
            if cached_res:
                final_results.append(cached_res)
            else:
                keywords_to_fetch.append(kw)

        cache_hits = len(final_results)
        cache_misses = len(keywords_to_fetch)

        # 4. Batching
        batches: list[list[str]] = []
        for i in range(0, len(keywords_to_fetch), actual_batch_size):
            batches.append(keywords_to_fetch[i : i + actual_batch_size])

        batches_processed = len(batches)
        parse_failures = 0
        validation_failures = 0

        # 5. Build Dynamic Business Context
        business_context_str = ""
        valid_cats = None
        if getattr(context, "business_profile", None):
            bp = context.business_profile
            business_context_str = (
                f"BUSINESS PROFILE:\n"
                f"Company: {bp.company_name}\n"
                f"Industry: {bp.industry}\n"
                f"Brands: {[c.entity for c in bp.business_facts.brands[:10]]}\n"
                f"Product Families: {[c.entity for c in bp.business_facts.product_families[:10]]}\n"
                f"Categories: {[c.entity for c in bp.business_facts.categories[:15]]}\n"
                f"Products: {[c.entity for c in bp.business_facts.products[:20]]}\n"
                f"Services: {[c.entity for c in bp.business_facts.services[:10]]}\n"
                f"Technologies: {[c for c in bp.technologies[:10]]}\n"
                f"Customer Segments: {[c for c in bp.customer_segments[:10]]}\n"
                f"Description: {bp.business_description[:500]}\n"
            )

            logger.debug(
                f"Injecting Business Profile into Prompt:\n{business_context_str}"
            )

        # 6. Execute Batches
        batch_start = time.perf_counter()

        # We need to inject business_context into the renderer.
        # This requires passing extra kwargs to executor or renderer.
        # For simplicity, since PromptRenderer usually accepts arbitrary kwargs,
        # we can wrap the batches execution to pass this.
        # But AIBatchExecutor.execute might not take extra kwargs. Let's see.
        # If it doesn't, we can't easily pass it. Let's look at `AIBatchExecutor` if needed,
        # or we just temporarily overwrite the template if we must.
        # Actually, looking at `PromptRenderer`, it usually accepts kwargs in `render()`.
        # I will use a hack if executor doesn't take kwargs:
        # We can just prepend it to the batches before execution? No, batches are lists of strings.
        # Let's check `SequentialAIBatchExecutor`. It probably passes kwargs.
        # To be safe, I'll temporarily override the template for this run.
        original_template = template.user_prompt_template
        template.user_prompt_template = (
            business_context_str + "\n\nClassify these keywords: {{keywords}}"
        )

        raw_responses, exec_exceptions = self.executor.execute(
            provider, template, self.prompt_renderer, batches
        )

        # 6a. Fallback Logic
        if exec_exceptions and provider.provider_name == "gemini":
            # Check if it failed after exhausting all keys or if it's retryable
            err_str = " ".join(str(e) for e in exec_exceptions).lower()
            if "exhausted" in err_str or any(self._is_retryable_error(e) for e in exec_exceptions):
                logger.warning("All Gemini keys exhausted or unavailable. Switching to OpenRouter.")

                # Determine unresolved keywords by parsing successful responses
                successful_kws = set()
                for resp in raw_responses:
                    try:
                        parsed = self.parser.parse(resp)
                        for item in parsed:
                            if isinstance(item, dict) and "keyword" in item:
                                successful_kws.add(item["keyword"])
                    except ValueError:
                        pass

                unresolved = [k for k in keywords_to_fetch if k not in successful_kws]
                if unresolved:
                    try:
                        fallback_provider = self.resolver.resolve("openrouter")
                        logger.info("Switching to OpenRouter")
                        fb_actual_batch_size = min(
                            self.config.batch_size, fallback_provider.capabilities.max_batch_size
                        )
                        fb_batches = [unresolved[i : i + fb_actual_batch_size] for i in range(0, len(unresolved), fb_actual_batch_size)]

                        fb_responses, fb_exceptions = self.executor.execute(
                            fallback_provider, template, self.prompt_renderer, fb_batches
                        )
                        raw_responses.extend(fb_responses)
                        exec_exceptions.extend(fb_exceptions)

                        if fb_exceptions:
                            logger.error("All AI providers failed")
                        else:
                            logger.info("OpenRouter succeeded")
                    except ValueError:
                        # OpenRouter not registered / unavailable
                        logger.warning("OpenRouter fallback not available.")
                    except Exception as fallback_err:
                        logger.error(f"Fallback execution failed: {fallback_err}")

        template.user_prompt_template = original_template

        batch_duration_ms = (time.perf_counter() - batch_start) * 1000

        # 6. Parse, Validate, and Score Responses
        # Build O(1) lookup to prevent O(N^2) slowdown during scoring
        lookup: dict[str, dict[str, Any]] = {}
        if not context.data.empty and "keyword" in context.data.columns:
            raw_lookup = context.data.set_index("keyword").to_dict(orient="index")
            lookup = {str(k): cast(dict[str, Any], v) for k, v in raw_lookup.items()}

        for i, raw_resp in enumerate(raw_responses, 1):
            try:
                parsed_data = self.parser.parse(raw_resp)

                logger.info(
                    f"--- AI BATCH {i} DEBUG ---\n"
                    f"1. Raw response length: {len(raw_resp)}\n"
                    f"2. Raw response: {raw_resp[:300]}...\n"
                    f"3. Parsed JSON type: {type(parsed_data).__name__}\n"
                    f"4. Number of parsed objects: {len(parsed_data)}"
                )

                valid_schemas, val_errors = self.validator.validate(parsed_data)
                validation_failures += len(val_errors)

                merged_count = 0
                for schema in valid_schemas:
                    scored_result = self.scorer.score(
                        schema, lookup, provider.provider_name, template.prompt_version
                    )
                    final_results.append(scored_result)
                    merged_count += 1

                    # Store in cache
                    cache_key = self.cache.generate_key(
                        company_name,
                        schema.keyword,
                        provider.provider_name,
                        template.prompt_version,
                    )
                    self.cache.put(cache_key, scored_result)

                logger.info(f"5. Number of merged objects: {merged_count}")

            except ValueError as e:
                parse_failures += 1
                logger.error(f"Failed to parse AI response: {e}")

        # 7. Aggregate Results into Context
        self.aggregator.aggregate(context, final_results)

        # 8. Statistics Collection
        total_time_ms = (time.perf_counter() - start_time) * 1000
        resolved_count = len(final_results)
        unresolved_count = total_kws - resolved_count
        failed_calls = len(exec_exceptions)

        avg_batch_latency = (
            batch_duration_ms / batches_processed if batches_processed > 0 else 0.0
        )
        provider_success_rate = 100.0
        if batches_processed > 0:
            provider_success_rate = (
                (batches_processed - failed_calls) / batches_processed
            ) * 100.0

        stats = AIEngineStatistics(
            total_keywords=total_kws,
            resolved_keywords=resolved_count,
            unresolved_keywords=unresolved_count,
            batches_processed=batches_processed,
            provider_calls=batches_processed,
            successful_responses=batches_processed - failed_calls,
            failed_responses=failed_calls,
            validation_failures=validation_failures,
            parse_failures=parse_failures,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            retries=0,  # Retries handled in transport layer (future)
            average_batch_latency_ms=avg_batch_latency,
            average_provider_latency_ms=avg_batch_latency,
            execution_time_ms=total_time_ms,
        )

        hit_ratio = (cache_hits / total_kws * 100.0) if total_kws > 0 else 0.0

        metrics = AIProviderMetrics(
            provider_name=provider.provider_name,
            provider_version=provider.provider_version,
            prompts_executed=batches_processed,
            tokens_estimated=0,  # Could be added with a tokenizer later
            average_latency_ms=avg_batch_latency,
            cache_hit_ratio=hit_ratio,
            success_rate=provider_success_rate,
        )

        # We attach stats to context for the pipeline layer to access
        from keyword_intelligence.models.pipeline import StageMetrics

        context.stage_metrics.append(
            StageMetrics(
                stage_name="AI_CLASSIFICATION",
                processing_time_ms=total_time_ms,
            )
        )

        logger.info(
            f"AI Engine finished in {total_time_ms:.2f}ms. "
            f"Resolved {resolved_count}/{total_kws} keywords."
        )
        if unresolved_count > 0:
            context.add_warning(
                "AI_CLASSIFICATION",
                "UNRESOLVED_KEYWORDS",
                f"Failed to classify {unresolved_count} keywords.",
            )

        # Print Requested Summary
        logger.info("\n--- Classification Summary ---")
        det_matches = 0
        if "business_relevance" in context.data.columns:
            det_matches = (context.data["business_relevance"] == "RELEVANT").sum()

        ai_classified = resolved_count
        ai_rejected = sum(1 for res in final_results if not res.relevant)

        total_relevant = det_matches + (ai_classified - ai_rejected)
        total_irrelevant = (
            (context.data["business_relevance"] == "IRRELEVANT").sum() + ai_rejected
            if "business_relevance" in context.data.columns
            else ai_rejected
        )

        reduction = (
            (det_matches / len(context.data) * 100) if len(context.data) > 0 else 0
        )

        logger.info(f"Deterministic Matches: {det_matches}")
        logger.info(f"AI Classified: {ai_classified}")
        logger.info(f"AI Rejected: {ai_rejected}")
        logger.info(f"Total Relevant: {total_relevant}")
        logger.info(f"Total Irrelevant: {total_irrelevant}")
        logger.info(f"Reduction in AI workload: {reduction:.1f}%")

        if self.settings.debug:
            logger.debug(f"[DEBUG] Number of AI Calls: {batches_processed}")
            logger.debug(f"[DEBUG] Processing Time: {total_time_ms:.0f}ms")
            logger.debug(
                f"[DEBUG] Prompt Length: {len(business_context_str)} characters"
            )

        # Log every rejected keyword with reasoning
        for res in final_results:
            if not res.relevant:
                logger.info(f"[Rejected] {res.keyword} - Reason: {res.reasoning}")
