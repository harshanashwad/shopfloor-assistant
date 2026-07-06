from profile import OperatorProfile

PERSONALIZATION_THRESHOLD = 5  # configurable, 20-30 in production
INSTRUCTION_STYLE_THRESHOLD = 0.3 # When the operator's preference for an instruction style is above this, we will include it in the system prompt

def build_system_prompt(profile: OperatorProfile) -> str:
    base = f"""You are an AI assistant for shopfloor operators in a manufacturing facility.
    You help operators troubleshoot machine issues, retrieve relevant documentation, and escalate problems when needed.
    Always prioritize safety. If an issue poses a safety risk, recommend stopping the machine immediately.
    
    Current operator: {profile.name} (ID: {profile.operator_id})"""

    if profile.interaction_count >= PERSONALIZATION_THRESHOLD:
        base += _personalized_prompt(profile)
    else:
        base += f"\n\nThis operator has {profile.interaction_count} recorded interactions. Respond neutrally until more behavioral data is available."

    return base


def _personalized_prompt(profile: OperatorProfile) -> str:
    sections = []

    instruction_style_prompts = {
        "step_by_step": "Break down all guidance into numbered steps.",
        "visual": "Use structured formatting, tables, and clear visual hierarchy in responses.",
        "example_based": "Always include a practical example when explaining procedures.",
        "brief": "Keep responses concise. Avoid lengthy explanations unless asked."
    }

    troubleshooting_prompts = {
        "escalates_quickly": "This operator tends to escalate quickly. Proactively offer to create a ticket when issues seem complex.",
        "tries_first": "This operator tries to resolve issues independently. Acknowledge their attempts and build on what they've tried.",
        "mixed": "This operator shows mixed troubleshooting behavior. Follow their lead on whether to escalate or resolve independently."
    }

    machine_confidence_prompts = {
        "weak": "Operator has low confidence with: {machines}. Proactively retrieve documentation for these machines without being asked.",
        "strong": "Operator is experienced with: {machines}. Skip basic explanations for these."
    }

    # Instruction style
    instruction_style_preference_scores = profile.instruction_style_preference_scores
    preferred_styles = [style for style, score in instruction_style_preference_scores.items() if score > INSTRUCTION_STYLE_THRESHOLD]

    if preferred_styles:
        style_names_str = ", ".join(preferred_styles)
        style_rules_str = "\n".join([f"- {instruction_style_prompts[s]}" for s in preferred_styles])
        sections.append(f"INSTRUCTION STYLE: This operator has shown strong preference for: {style_names_str}.\n{style_rules_str}")

    # Troubleshooting behavior
    troubleshooting_scores = profile.troubleshooting_scores
    dominant_troubleshooting_behavior = max(troubleshooting_scores.keys(), key = lambda troubleshooting_pattern: troubleshooting_scores[troubleshooting_pattern])

    if profile.troubleshooting_scores[dominant_troubleshooting_behavior] > 0.3:
        sections.append(f"TROUBLESHOOTING: {troubleshooting_prompts[dominant_troubleshooting_behavior]}")
    # Machine confidence
    weak_machines = [m for m, score in profile.machine_confidence.items() if score < 0.3]
    strong_machines = [m for m, score in profile.machine_confidence.items() if score >= 0.7]

    # Explain which machines the operator is cmofortable with and which ones he needs guidance and relevant documentation for
    if weak_machines:
        sections.append(f"MACHINE CONFIDENCE: {machine_confidence_prompts['weak'].format(machines=', '.join(weak_machines))}")
    if strong_machines:
        sections.append(f"MACHINE CONFIDENCE: {machine_confidence_prompts['strong'].format(machines=', '.join(strong_machines))}")

    if not sections:
        return ""
    header = f"The following behavioral profile has been learned for this operator from {profile.interaction_count} interactions. Apply these rules consistently:"
    return f"\n\nOPERATOR PROFILE:\n {header}\n\n" + "\n".join(sections)