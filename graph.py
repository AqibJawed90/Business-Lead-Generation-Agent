
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from search_agent import search_businesses
from lead_validator import validate_leads
from business_qualifier import qualify_businesses
from csv_exporter import export_leads
from database import save_leads, update_lead_contact
from contact_extractor import extract_contact_info


class LeadState(TypedDict, total=False):
    niche: str
    country: str
    city: str
    target: int
    leads: list[dict]
    valid_leads: list[dict]
    qualified_leads: list[dict]
    csv_path: str
    saved_count: int
    contacts_processed: int


# Node 1: Business search
def search_node(state: LeadState) -> dict:
    print("\n[1/5] Searching for businesses...")

    leads = search_businesses(
        niche=state["niche"],
        country=state["country"],
        city=state["city"],
        target=state["target"],
    )

    print(f"Search results found: {len(leads)}")
    return {"leads": leads}


# Node 2: Validate website URLs and remove duplicates
def validation_node(state: LeadState) -> dict:
    print("\n[2/5] Validating URLs...")

    valid_leads = validate_leads(state.get("leads", []))

    print(f"Valid unique URLs: {len(valid_leads)}")
    return {"valid_leads": valid_leads}


# Node 3: Qualify potential business websites
def qualification_node(state: LeadState) -> dict:
    print("\n[3/5] Qualifying potential businesses...")

    qualified_leads = qualify_businesses(
        state.get("valid_leads", [])
    )

    print(f"Potential businesses: {len(qualified_leads)}")
    return {"qualified_leads": qualified_leads}


# Node 4: Extract contact information
def contact_extraction_node(state: LeadState) -> dict:
    print("\n[4/5] Extracting contact information...")

    qualified_leads = state.get("qualified_leads", [])
    updated_leads = []

    for index, lead in enumerate(qualified_leads, start=1):
        website = lead.get("url", "")

        print(
            f"\n[{index}/{len(qualified_leads)}] "
            f"{lead.get('business_name', lead.get('title', 'Unknown'))}"
        )
        print(f"Website: {website}")

        contact = extract_contact_info(website)

        lead_with_contact = {
            **lead,
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "contact_page": contact.get("contact_page", ""),
            "contact_status": contact.get("status", "unknown"),
        }

        # Existing database record ko update karna.
        # Agar record abhi database mein nahi hai, to update nahi hoga.
        updated = update_lead_contact(
            url=website,
            email=lead_with_contact["email"],
            phone=lead_with_contact["phone"],
            contact_page=lead_with_contact["contact_page"],
            contact_status=lead_with_contact["contact_status"],
        )

        print(f"Email: {lead_with_contact['email'] or 'Not found'}")
        print(f"Phone: {lead_with_contact['phone'] or 'Not found'}")
        print(f"Contact page: {lead_with_contact['contact_page'] or 'Not found'}")

        if not updated:
            print("Database record abhi nahi mila; final save step isay insert karega.")

        updated_leads.append(lead_with_contact)

    return {
        "qualified_leads": updated_leads,
        "contacts_processed": len(updated_leads),
    }


# Node 5: Save leads and export CSV
def export_node(state: LeadState) -> dict:
    print("\n[5/5] Saving leads to database and CSV...")

    qualified_leads = state.get("qualified_leads", [])

    saved_count = save_leads(
        qualified_leads,
        niche=state["niche"],
        city=state["city"],
        country=state["country"],
    )

    print(f"New leads inserted into database: {saved_count}")

    if not qualified_leads:
        print("No potential businesses found.")

        return {
            "csv_path": "",
            "saved_count": saved_count,
        }

    filepath = export_leads(qualified_leads)
    print(f"CSV saved to: {filepath}")

    return {
        "csv_path": filepath,
        "saved_count": saved_count,
    }


# Build the LangGraph workflow
builder = StateGraph(LeadState)

builder.add_node("search", search_node)
builder.add_node("validate", validation_node)
builder.add_node("qualify", qualification_node)
builder.add_node("extract_contacts", contact_extraction_node)
builder.add_node("export", export_node)

builder.add_edge(START, "search")
builder.add_edge("search", "validate")
builder.add_edge("validate", "qualify")
builder.add_edge("qualify", "extract_contacts")
builder.add_edge("extract_contacts", "export")
builder.add_edge("export", END)

lead_generation_graph = builder.compile()
