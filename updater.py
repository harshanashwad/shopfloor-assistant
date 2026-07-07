from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field
from profile import OperatorProfile, save_profile
from datetime import datetime

class InstructionStylePreferenceScores(BaseModel):
    step_by_step: float = Field(description="Score 0-10", ge=0, le=10)
    visual: float = Field(description="Score 0-10", ge=0, le=10)
    example_based: float = Field(description="Score 0-10", ge=0, le=10)
    brief: float = Field(description="Score 0-10", ge=0, le=10)


class TroubleshootingScores(BaseModel):
    tries_first: float = Field(description="Score 0-10", ge=0, le=10)
    escalates_quickly: float = Field(description="Score 0-10", ge=0, le=10)
    mixed: float = Field(description="Score 0-10", ge=0, le=10)


class SessionSignals(BaseModel):
    instruction_style_preference_scores: InstructionStylePreferenceScores = Field(
        description="Observed preference scores for each instruction style this session. Keys: step_by_step, visual, example_based, brief."
    )

    troubleshooting_scores: TroubleshootingScores = Field(
        description="Observed tendency scores for each troubleshooting behavior this session. Keys: tries_first, escalates_quickly, mixed."
    )

    machine_confidence: dict[str, float] = Field(
        description="Confidence scores for machines or processes discussed this session. Machine name as key, score as value. Empty if no machines discussed."
    )



def extract_signals(chat_transcript: list[HumanMessage | AIMessage]) -> SessionSignals:
    system_prompt = """You are a behavioral analyst evaluating a conversation between a shopfloor operator and an AI assistant.

    Your task is to score the operator's behavioral patterns based solely on signals observed in this conversation transcript.

    INSTRUCTION STYLE — score each 0-10:
    - step_by_step: Operator asked for numbered steps, sequential guidance, or ordered procedures
    - visual: Operator requested diagrams, images, visual aids, or asked to "show" rather than "explain"
    - example_based: Operator asked for examples, analogies, or "how would this look in practice"
    - brief: Operator preferred short answers, showed impatience with long responses, asked to summarize

    TROUBLESHOOTING TENDENCY — score each 0-10:
    - tries_first: Operator described steps they already attempted before asking for help
    - escalates_quickly: Operator requested escalation or ticket creation without attempting resolution
    - mixed: Operator showed both independent attempts and escalation within the same session

    MACHINE CONFIDENCE — score 0-10 for each machine discussed:
    - High scores (7-10): Operator used technical terminology correctly, diagnosed issues accurately, needed minimal guidance
    - Mid scores (4-6): Operator had partial understanding, needed some clarification
    - Low scores (0-3): Operator was confused, used vague descriptions, needed step-by-step guidance throughout
    - Use the machine name as the key (e.g. "hydraulic press", "cnc lathe", "conveyor belt") not alarm codes.

    IMPORTANT RULES:
    - Score only what is explicitly observable in the transcript. Do not infer or assume.
    - If a dimension has no observable signal, score it 0.
    - Explicit preferences mentioned by the operator / corrections to their own profile carry higher weight than inferred signals.
    - Do not include machines not discussed in this session.

    {format_instructions}"""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = PydanticOutputParser[SessionSignals](pydantic_object=SessionSignals)

    prompt_template = ChatPromptTemplate(
        [
            ("system", system_prompt),
            (MessagesPlaceholder(variable_name="chat_transcript"))
        ],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt_template | llm | parser

    response = chain.invoke({"chat_transcript": chat_transcript})
    return response


def aggregate(profile: OperatorProfile, chat_transcript: list[HumanMessage | AIMessage], escalation_count: int, signals: SessionSignals) -> OperatorProfile:
    weight_new = 1 / (profile.interaction_count + 1)
    weight_existing = 1 - weight_new

    for key in profile.instruction_style_preference_scores:
        session_score = getattr(signals.instruction_style_preference_scores, key, 0.0) / 10
        profile.instruction_style_preference_scores[key] = round(
            profile.instruction_style_preference_scores[key] * weight_existing + session_score * weight_new, 3
        )

    for key in profile.troubleshooting_scores:
        session_score = getattr(signals.troubleshooting_scores, key, 0.0) / 10
        profile.troubleshooting_scores[key] = round(
            profile.troubleshooting_scores[key] * weight_existing + session_score * weight_new, 3
        )

    for machine, score in signals.machine_confidence.items():
        existing = profile.machine_confidence.get(machine, 0.0)
        profile.machine_confidence[machine] = round(
            existing * weight_existing + (score / 10) * weight_new, 3
        )

    # Shift pattern updates
    human_messages = [m for m in chat_transcript if isinstance(m, HumanMessage)]

    shift = profile.current_shift
    current_avg_questions = profile.shift_patterns[shift]["avg_questions"]
    current_avg_escalations = profile.shift_patterns[shift]["avg_escalations"]

    # Basically maintaining a running average of questions and escalations raised every interaction grouped by shift type
    profile.shift_patterns[shift]["avg_questions"] = round(
        current_avg_questions * weight_existing + len(human_messages) * weight_new, 2
    )
    profile.shift_patterns[shift]["avg_escalations"] = round(
        current_avg_escalations * weight_existing + escalation_count * weight_new, 2
    )
    profile.interaction_count += 1
    profile.last_updated = datetime.now()

    return profile

def update_profile(profile: OperatorProfile, chat_transcript: list[HumanMessage | AIMessage], escalation_count: int) -> OperatorProfile:
    signals = extract_signals(chat_transcript)
    updated = aggregate(profile, chat_transcript, escalation_count, signals)
    save_profile(updated)
    return updated