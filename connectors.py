import json
import os


class SupportConnector:
    """
    Prototype connector for the Kohler support system.

    In the prototype, tickets are stored locally in JSON.
    In a production system, this class could call ServiceNow,
    Salesforce, or another ticketing API instead.
    """

    def __init__(self, database_path="data/tickets.json"):
        self.database_path = database_path
        os.makedirs("data", exist_ok=True)

    def _load_tickets(self):
        if not os.path.exists(self.database_path):
            return []

        with open(
            self.database_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    def _save_tickets(self, tickets):
        with open(
            self.database_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(tickets, file, indent=4)

    def create_ticket(self, customer, product, issue):
        tickets = self._load_tickets()

        ticket_number = f"KT-{1001 + len(tickets)}"

        ticket = {
            "ticket_id": ticket_number,
            "customer": customer,
            "product": product,
            "issue": issue,
            "status": "Open",
        }

        tickets.append(ticket)

        self._save_tickets(tickets)

        return ticket

    def get_ticket(self, ticket_id):
        tickets = self._load_tickets()

        for ticket in tickets:
            if ticket["ticket_id"].lower() == ticket_id.lower():
                return ticket

        return None