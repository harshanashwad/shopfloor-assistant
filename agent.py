from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from profile import OperatorProfile
from prompt_builder import build_system_prompt
from tools import retrieve_manual_context, create_escalation_ticket, log_profile_correction
from updater import update_profile


def run_session(profile: OperatorProfile) -> OperatorProfile:
    chat_history = []
    escalation_count = 0 # Track number of escalations made by user
    system_prompt = build_system_prompt(profile)

    agent = create_agent(
        model=ChatOpenAI(model="gpt-4o-mini", temperature=0.3) ,
        tools=[retrieve_manual_context, create_escalation_ticket, log_profile_correction],
        system_prompt=system_prompt
    )

    print(f"\nSession started for {profile.name} | Shift: {profile.current_shift} | Interactions: {profile.interaction_count}\n")
    print("Type 'quit' to end the session.\n")

    while True:
        user_input = input("Operator: ").strip()
        if user_input.lower() == "quit":
            break

        chat_history.append(HumanMessage(content=user_input))
        response = agent.invoke({"messages": chat_history})
        ai_message = response["messages"][-1]

        print(f"\nAssistant: {ai_message.content}\n")
        chat_history.append(ai_message)

        # count escalations from this turn
        tool_messages = [m for m in response["messages"] if hasattr(m, 'name') and m.name == 'create_escalation_ticket']
        escalation_count += len(tool_messages)


    # Update profile at end of session
    updated_profile = update_profile(profile, chat_history, escalation_count, recent_tickets=[])
    print(f"\nSession ended. Profile updated. Interactions: {updated_profile.interaction_count}\n")
    return updated_profile