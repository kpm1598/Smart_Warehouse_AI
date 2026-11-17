"""Terminal formatting helpers."""


def print_inventory(rows, summary=None):
    print("\nWAREHOUSE INVENTORY\n")
    print("-" * 52)
    print(f"{'Product Name':<22}{'Location':<12}{'Available Qty':>13}")
    print("-" * 52)
    if not rows:
        print("(inventory is empty)")
    for row in rows:
        print(f"{row['product']:<22}{row['location']:<12}{row['quantity']:>13}")
    print("-" * 52)
    if summary is not None:
        print(f"Unique Products: {summary['unique_products']}")
        print(f"Total Units: {summary['total_stock_units']}")
        print(f"Occupied Locations: {summary['occupied_locations']}")


def print_locations(locations):
    print("\nWAREHOUSE LOCATIONS\n")
    print("-" * 68)
    print(f"{'Code':<11}{'Capacity':>10}{'Occupied':>10}{'Remaining':>11}  Status")
    print("-" * 68)
    for loc in locations:
        status = "storage" if loc["is_storage"] else "non-storage"
        if not loc["is_active"]:
            status = "inactive"
        print(
            f"{loc['location_code']:<11}{loc['max_capacity']:>10}"
            f"{loc['occupied_capacity']:>10}{loc['remaining_capacity']:>11}  {status}"
        )
    print("-" * 68)
