from dotenv import load_dotenv
load_dotenv()

from profile import load_profile, new_profile, save_profile
from agent import run_session


if __name__ == "__main__":
    operator_id = input("Enter operator ID: ").strip()
    name = input("Enter operator name: ").strip()
    shift = input("Enter shift (day/night): ").strip()

    # Load existing profile or create new one
    profile = load_profile(operator_id)
    if profile is None:
        profile = new_profile(operator_id, name)
        print(f"\nNew profile created for {name}.")
    else:
        print(f"\nWelcome back, {profile.name}. Interaction #{profile.interaction_count + 1}.")

    profile.current_shift = shift

    # Run the session — returns updated profile
    updated_profile = run_session(profile)

    # Save is already handled inside update_profile. Just show confirmation to the user
    print(f"\nProfile saved. Updated scores:")
    print(f"  Instruction style: {updated_profile.instruction_style_preference_scores}")
    print(f"  Troubleshooting:   {updated_profile.troubleshooting_scores}")
    print(f"  Machine confidence: {updated_profile.machine_confidence}")