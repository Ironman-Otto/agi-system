INTENT_EXTRACTION_PROMPT = """
You are an intent extraction module.

Your task is to classify a directive and output a JSON object ONLY.
Do not include explanations or formatting.

Allowed directive_type values:
- cognitive
- analytical
- goal_oriented
- behavioral
- supervisory

Rules:
- planning_required is true ONLY if multi-step execution, coordination,
  or state change is required.
- confidence_score must be between 0.0 and 1.0

Required JSON fields:
intent_id
directive_source
directive_type
planning_required
urgency_level
risk_level
expected_response_type
confidence_score

Directive:
{directive}
"""
