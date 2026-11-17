"""Smart Warehouse AI — terminal interface (menu per TDD section 9.1).

Run from the project root:  py -m terminal.main
The backend must already be running:  py -m uvicorn backend.main:app
"""
from terminal import api_client
from terminal.api_client import ApiError, ApiUnavailable
from terminal.display import print_inventory, print_locations

MENU = """
========================================
          SMART WAREHOUSE AI
========================================

1. Place / Store an Object
2. Display Stored Items
3. Find / Locate an Object
4. Remove / Dispatch Stock
5. View Warehouse Locations
6. Compare AI Search Algorithms
7. View Warehouse Summary
0. Exit

========================================"""


def _ask_quantity(prompt):
    raw = input(prompt).strip()
    try:
        value = int(raw)
    except ValueError:
        print("Please enter a whole number.")
        return None
    if value <= 0:
        print("Quantity must be greater than zero.")
        return None
    return value


def _ask_product(prompt="Enter product name: "):
    name = input(prompt).strip()
    if not name:
        print("Product name must not be empty.")
        return None
    return name


def do_store():
    name = _ask_product()
    if name is None:
        return
    quantity = _ask_quantity("Enter quantity: ")
    if quantity is None:
        return
    print("\nProcessing storage request...")
    print("AI allocation started (Greedy Best-First Search).")
    data = api_client.store_product(name, quantity)
    print("\nSTORAGE SUCCESSFUL\n")
    print(f"Product: {data['product']}")
    print(f"Quantity: {data['quantity_stored']}")
    print(f"Assigned Location: {data['assigned_location']}")
    print(f"Remaining Capacity: {data['remaining_capacity']}")
    print(f"Path: {' -> '.join(data['path'])}")


def do_display():
    rows = api_client.list_inventory()
    summary = api_client.dashboard_summary()
    print_inventory(rows, summary)


def do_locate():
    name = _ask_product()
    if name is None:
        return
    quantity = _ask_quantity("Enter requested quantity: ")
    if quantity is None:
        return
    print("\nSEARCHING INVENTORY...")
    data = api_client.locate_product(name, quantity)
    print("\nPRODUCT FOUND\n")
    print(f"Product: {data['product']}")
    for loc in data["locations"]:
        print(f"Location: {loc['location']}  Available Quantity: {loc['available_quantity']}")
    print(f"Total Available: {data['total_available']}")
    print(f"Requested Quantity: {data['requested_quantity']}")
    if data["status"] == "CAN_BE_FULFILLED":
        print("\nSTATUS: REQUEST CAN BE FULFILLED")
    else:
        print("\nSTATUS: INSUFFICIENT STOCK")
        print(f"Shortage: {data['shortage']} units")


def do_dispatch():
    name = _ask_product()
    if name is None:
        return
    quantity = _ask_quantity("Enter dispatch quantity: ")
    if quantity is None:
        return
    print("\nCHECKING STOCK...")
    data = api_client.dispatch_product(name, quantity)
    print("\nDISPATCH SUCCESSFUL\n")
    print(f"Product: {data['product']}")
    print(f"Dispatched: {data['quantity_dispatched']}")
    print(f"Remaining: {data['remaining_stock']}")
    for loc in data["locations_affected"]:
        print(f"Location: {loc['location']}  Taken: {loc['quantity_dispatched']}")


def do_locations():
    print_locations(api_client.list_locations())


def do_compare():
    goal = input("Enter goal location (e.g. C3): ").strip().upper()
    if not goal:
        print("Goal location must not be empty.")
        return
    depth = _ask_quantity("Enter DLS depth limit: ")
    if depth is None:
        return
    data = api_client.compare_search("RECEIVING", goal, depth)
    print(f"\nAI SEARCH COMPARISON  (RECEIVING -> {goal})\n")
    print("-" * 68)
    print(f"{'Metric':<22}{'DLS':<24}{'Greedy':<22}")
    print("-" * 68)
    dls, greedy = data["dls"], data["greedy"]
    print(f"{'Search type':<22}{dls['search_type']:<24}{greedy['search_type']:<22}")
    print(f"{'Status':<22}{dls['status']:<24}{greedy['status']:<22}")
    print(f"{'Nodes explored':<22}{dls['nodes_explored']:<24}{greedy['nodes_explored']:<22}")
    print(f"{'Path distance':<22}{dls['path_distance']:<24}{greedy['path_distance']:<22}")
    print(f"{'Time (ms)':<22}{dls['execution_time_ms']:<24}{greedy['execution_time_ms']:<22}")
    print("-" * 68)
    print(f"DLS path:    {' -> '.join(dls['path']) if dls['path'] else '(none)'}")
    print(f"Greedy path: {' -> '.join(greedy['path']) if greedy['path'] else '(none)'}")


def do_summary():
    data = api_client.dashboard_summary()
    print("\nWAREHOUSE SUMMARY\n")
    print(f"Unique Products: {data['unique_products']}")
    print(f"Total Stock Units: {data['total_stock_units']}")
    print(f"Total Locations: {data['total_locations']}")
    print(f"Occupied Locations: {data['occupied_locations']}")
    print(f"Total Capacity: {data['total_capacity']}")
    print(f"Remaining Capacity: {data['total_remaining_capacity']}")
    print("\nRecent activity:")
    for item in data["recent_activity"]:
        print(f"  {item['movement_type']:<3} {item['product']} x{item['quantity']} @ {item['location']}")


ACTIONS = {
    "1": do_store,
    "2": do_display,
    "3": do_locate,
    "4": do_dispatch,
    "5": do_locations,
    "6": do_compare,
    "7": do_summary,
}


def main():
    while True:
        print(MENU)
        try:
            choice = input("Enter your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if choice == "0":
            print("Goodbye.")
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid choice. Please enter a number from the menu.")
            continue
        try:
            action()
        except ApiUnavailable as exc:
            print(f"\n{exc}")
        except ApiError as exc:
            print(f"\nERROR: {exc.message}")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        try:
            input("\nPress Enter to continue.")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break


if __name__ == "__main__":
    main()
