
from database import get_all_leads


def main():
    print("\n===== SAVED BUSINESS LEADS =====")

    leads = get_all_leads()

    if not leads:
        print("Database mein koi leads nahi hain.")
        return

    print(f"Total saved leads: {len(leads)}")

    for index, lead in enumerate(leads, start=1):
        print(f"\n{index}. {lead.get('business_name', 'Unknown')}")
        print(f"Website: {lead.get('url', '')}")
        print(f"Email: {lead.get('email') or 'Not found'}")
        print(f"Phone: {lead.get('phone') or 'Not found'}")
        print(
            f"Contact page: "
            f"{lead.get('contact_page') or 'Not found'}"
        )
        print(f"Contact status: {lead.get('contact_status', 'pending')}")
        print("-" * 45)


if __name__ == "__main__":
    main()
