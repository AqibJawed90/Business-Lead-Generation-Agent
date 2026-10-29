from graph import lead_generation_graph


def main():
    print("=== Business Lead Generation Agent ===")

    niche = input(
        "Business niche (e.g. restaurants): "
    ).strip()

    country = input(
        "Country (e.g. Germany): "
    ).strip()

    city = input(
        "City (e.g. Berlin): "
    ).strip()

    target_text = input(
        "Target results (default 10): "
    ).strip()

    try:
        target = int(target_text) if target_text else 10

        if target < 1:
            raise ValueError

    except ValueError:
        print("Target positive whole number hona chahiye.")
        return

    if not niche or not country or not city:
        print("Niche, country aur city enter karna zaroori hai.")
        return

    try:
        # Initial state LangGraph ko dena
        initial_state = {
            "niche": niche,
            "country": country,
            "city": city,
            "target": target,
        }

        # Complete workflow run karna
        result = lead_generation_graph.invoke(initial_state)

        qualified_leads = result.get("qualified_leads", [])

        print("\n========== FINAL SUMMARY ==========")
        print(f"Search results: {len(result.get('leads', []))}")
        print(f"Valid unique URLs: {len(result.get('valid_leads', []))}")
        print(f"Potential businesses: {len(qualified_leads)}")

        if result.get("csv_path"):
            print(f"CSV file: {result['csv_path']}")

        for index, lead in enumerate(qualified_leads, start=1):
            print(f"\n{index}. {lead.get('business_name', lead.get('title', 'Unknown'))}")
            print(f"Website: {lead.get('url', '')}")

        print("\nWorkflow completed!")

    except Exception as error:
        print(f"\nWorkflow failed: {error}")


if __name__ == "__main__":
    main()
