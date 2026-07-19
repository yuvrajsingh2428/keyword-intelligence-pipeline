"""Parser and Validator components for AI responses."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger
from pydantic import ValidationError

from keyword_intelligence.ai_intelligence.models import KeywordResponseSchema


class ResponseParser:
    """Parses raw text strings from providers into JSON dictionaries."""

    def parse(self, raw_response: str) -> list[dict[str, Any]]:
        """Parse raw response string into a list of dictionaries."""
        if not raw_response or not raw_response.strip():
            raise ValueError("Empty response from AI provider.")

        text = raw_response.strip()
        objects = []

        # 1. Try standard JSON load
        try:
            data = json.loads(text)
            return self._normalize(data)
        except json.JSONDecodeError:
            pass

        # 2. Try parsing line-by-line (line-delimited JSON)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    objects.append(obj)
                elif isinstance(obj, list):
                    objects.extend(obj)
            except json.JSONDecodeError:
                continue

        if objects:
            return objects

        # 3. Try parsing multiple concatenated JSON objects via brace counting
        extracted = []
        brace_level = 0
        current_obj = []
        in_string = False
        escape = False

        for char in text:
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                if brace_level > 0:
                    current_obj.append(char)
            else:
                if char == '"':
                    in_string = True
                    if brace_level > 0:
                        current_obj.append(char)
                elif char == "{":
                    brace_level += 1
                    current_obj.append(char)
                elif char == "}":
                    if brace_level > 0:
                        current_obj.append(char)
                        brace_level -= 1
                        if brace_level == 0:
                            obj_str = "".join(current_obj)
                            try:
                                parsed = json.loads(obj_str)
                                if isinstance(parsed, dict):
                                    extracted.append(parsed)
                            except json.JSONDecodeError:
                                pass
                            current_obj = []
                else:
                    if brace_level > 0:
                        current_obj.append(char)

        if extracted:
            # We found multiple JSON objects. Normalize each if needed.
            # But usually they are the individual results.
            # E.g. {"keyword": "a"}
            # Return them directly if they look like keywords.
            return extracted

        # 4. Try extracting an array with regex
        import re

        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return self._normalize(data)
            except json.JSONDecodeError:
                pass

        logger.error(
            f"Failed to extract any JSON objects from AI response.\nRaw output: {text[:200]}..."
        )
        raise ValueError("Could not extract valid JSON from response.")

    def _normalize(self, data: Any) -> list[dict[str, Any]]:
        """Normalize a parsed JSON payload into a list of dicts."""
        # 1. Resiliency: Column-oriented format
        if isinstance(data, dict):
            lists = [v for v in data.values() if isinstance(v, list)]
            if lists and len(lists) == len(data.values()):
                first_len = len(lists[0])
                if all(len(lst) == first_len for lst in lists):
                    keys = list(data.keys())
                    return [{k: data[k][i] for k in keys} for i in range(first_len)]

        # 2. Resiliency: Dict-of-dicts format
        if isinstance(data, dict):
            dicts = [v for v in data.values() if isinstance(v, dict)]
            if dicts and len(dicts) == len(data.values()):
                res = []
                for k, v in data.items():
                    if "keyword" not in v:
                        v["keyword"] = k
                    res.append(v)
                return res

        # 3. Resiliency: Extractor Fallback
        if isinstance(data, dict):
            lists = [v for v in data.values() if isinstance(v, list)]
            if len(lists) == 1:
                data = lists[0]
            elif "keywords" in data and isinstance(data["keywords"], list):
                data = data["keywords"]
            elif "results" in data and isinstance(data["results"], list):
                data = data["results"]
            else:
                data = [data]

        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array, got {type(data).__name__}.")

        # Filter out non-dict items (like random strings)
        data = [item for item in data if isinstance(item, dict)]

        # Unwrap {"keywords": {...}} if present
        unwrapped = []
        for item in data:
            if (
                len(item) == 1
                and "keywords" in item
                and isinstance(item["keywords"], dict)
            ):
                unwrapped.append(item["keywords"])
            else:
                unwrapped.append(item)

        return unwrapped


class ResponseValidator:
    """Validates parsed dictionaries against strict Pydantic schemas."""

    def validate(
        self,
        parsed_data: list[dict[str, Any]],
        valid_categories: set[str] | None = None,
    ) -> tuple[list[KeywordResponseSchema], list[Exception]]:
        """Validate dictionaries and convert them into KeywordResponseSchema instances.

        Args:
            parsed_data: List of dictionaries from the parser.
            valid_categories: Optional set of allowed categories from the BusinessProfile.

        Returns:
            A tuple containing:
            1. List of successfully validated KeywordResponseSchema models.
            2. List of validation exceptions encountered.
        """
        valid_responses: list[KeywordResponseSchema] = []
        validation_failures: list[Exception] = []

        for item in parsed_data:
            try:
                model = KeywordResponseSchema.model_validate(item)
                if (
                    valid_categories
                    and model.category.lower() not in valid_categories
                    and model.category.lower() != "unknown"
                ):
                    raise ValueError(
                        f"Category '{model.category}' is not in the allowed business profile categories."
                    )
                valid_responses.append(model)
            except (ValidationError, ValueError) as e:
                logger.warning(
                    f"Validation failed for AI response item: {item}. Error: {e}"
                )
                validation_failures.append(e)

        return valid_responses, validation_failures
