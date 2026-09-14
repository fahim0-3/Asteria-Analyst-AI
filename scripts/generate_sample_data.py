"""Generate deterministic synthetic Asteria Retail Labs data. Never real customer data."""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OUT = Path("sample_data")


def main(scale: float = 1.0) -> None:
    rng = np.random.default_rng(SEED)
    OUT.mkdir(exist_ok=True)
    n_customers, n_products, n_orders = int(5000 * scale), int(500 * scale), int(20000 * scale)
    start = pd.Timestamp("2024-07-01")
    end = pd.Timestamp("2026-06-30")
    days = (end - start).days
    customers = pd.DataFrame({
        "customer_id": [f"C{i:05d}" for i in range(n_customers)],
        "signup_date": start + pd.to_timedelta(rng.integers(0, days, n_customers), unit="D"),
        "region": rng.choice(["North", "South", "East", "West", "Central"], n_customers, p=[.23, .19, .21, .25, .12]),
        "age_group": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], n_customers),
        "acquisition_channel": rng.choice(["Organic", "Paid Search", "Social", "Email", "Referral"], n_customers),
        "loyalty_tier": rng.choice(["Bronze", "Silver", "Gold", "Platinum"], n_customers, p=[.55, .28, .14, .03]),
    })
    categories = ["Electronics", "Home", "Fitness", "Beauty", "Office", "Outdoors"]
    products = pd.DataFrame({
        "product_id": [f"P{i:04d}" for i in range(n_products)],
        "product_name": [f"Asteria {categories[i % len(categories)]} {i + 1}" for i in range(n_products)],
        "category": [categories[i % len(categories)] for i in range(n_products)],
        "subcategory": rng.choice(["Essentials", "Premium", "Accessories", "Portable"], n_products),
        "unit_cost": np.round(rng.uniform(4, 180, n_products), 2),
        "list_price": np.round(rng.uniform(12, 480, n_products), 2),
        "launch_date": start - pd.to_timedelta(rng.integers(0, 800, n_products), unit="D"),
    })
    products["list_price"] = np.maximum(products["list_price"], products["unit_cost"] * 1.25).round(2)
    order_dates = start + pd.to_timedelta(rng.integers(0, days, n_orders), unit="D")
    seasonal = np.where(pd.Series(order_dates).dt.month.isin([11, 12]), 1.22, 1.0)
    amounts = np.round(rng.gamma(2.2, 58, n_orders) * seasonal, 2)
    orders = pd.DataFrame({
        "order_id": [f"O{i:06d}" for i in range(n_orders)], "customer_id": rng.choice(customers.customer_id, n_orders),
        "order_date": order_dates, "order_status": rng.choice(["completed", "shipped", "cancelled"], n_orders, p=[.86, .1, .04]),
        "payment_method": rng.choice(["Card", "Wallet", "Bank Transfer", "COD"], n_orders),
        "discount_amount": np.round(rng.choice([0, 5, 10, 20, 35], n_orders, p=[.45, .2, .18, .12, .05]), 2),
        "shipping_amount": rng.choice([0, 4.99, 8.99, 12.99], n_orders), "total_amount": amounts,
        "region": rng.choice(["North", "South", "East", "West", "Central"], n_orders, p=[.23, .19, .21, .25, .12]),
    })
    item_count = int(45000 * scale)
    picked_orders = rng.choice(orders.order_id, item_count)
    picked_products = rng.choice(products.product_id, item_count)
    price_map = products.set_index("product_id").list_price
    order_items = pd.DataFrame({
        "order_item_id": [f"I{i:07d}" for i in range(item_count)], "order_id": picked_orders,
        "product_id": picked_products, "quantity": rng.choice([1, 2, 3, 4], item_count, p=[.7, .2, .08, .02]),
        "unit_price": [float(price_map[x]) for x in picked_products],
        "discount_amount": rng.choice([0, 3, 8, 15], item_count, p=[.6, .2, .15, .05]),
    })
    session_count = int(30000 * scale)
    sessions = pd.DataFrame({
        "session_id": [f"S{i:06d}" for i in range(session_count)],
        "customer_id": rng.choice(np.append(customers.customer_id.values, None), session_count),
        "session_date": start + pd.to_timedelta(rng.integers(0, days, session_count), unit="D"),
        "channel": rng.choice(["Organic", "Paid Search", "Social", "Email", "Referral"], session_count),
        "device": rng.choice(["Mobile", "Desktop", "Tablet"], session_count, p=[.58, .36, .06]),
        "pages_viewed": rng.poisson(5, session_count) + 1, "added_to_cart": rng.random(session_count) < .28,
        "purchased": rng.random(session_count) < .11,
    })
    campaigns = pd.DataFrame({
        "campaign_id": [f"M{i:03d}" for i in range(20)], "campaign_name": [f"Campaign {i + 1}" for i in range(20)],
        "channel": rng.choice(["Paid Search", "Social", "Email", "Referral"], 20),
        "start_date": start + pd.to_timedelta(rng.integers(0, days - 60, 20), unit="D"),
        "budget": np.round(rng.uniform(2500, 25000, 20), 2),
    })
    return_count = int(2000 * scale)
    return_orders = rng.choice(orders.order_id, return_count, replace=False)
    return_dates = pd.to_datetime(orders.set_index("order_id").loc[return_orders].order_date.values) + pd.to_timedelta(rng.integers(2, 40, return_count), unit="D")
    returns = pd.DataFrame({
        "return_id": [f"R{i:05d}" for i in range(return_count)], "order_id": return_orders,
        "product_id": rng.choice(products.product_id, return_count), "return_date": return_dates,
        "reason": rng.choice(["Changed mind", "Damaged", "Wrong size", "Not as described", "Late delivery"], return_count),
        "refund_amount": np.round(rng.gamma(2, 35, return_count), 2),
    })
    review_count = int(5000 * scale)
    reviews = pd.DataFrame({
        "review_id": [f"V{i:05d}" for i in range(review_count)], "customer_id": rng.choice(customers.customer_id, review_count),
        "product_id": rng.choice(products.product_id, review_count), "rating": rng.choice([1, 2, 3, 4, 5], review_count, p=[.04, .07, .16, .31, .42]),
        "review_date": start + pd.to_timedelta(rng.integers(0, days, review_count), unit="D"),
    })
    # Controlled quality cases: nulls, duplicates, inconsistent labels, and a sales spike.
    customers.loc[rng.choice(n_customers, max(1, n_customers // 100), replace=False), "age_group"] = None
    orders.loc[:4, "region"] = "north"
    orders.loc[orders.order_date.between("2025-11-24", "2025-11-30"), "total_amount"] *= 2.2
    sessions = pd.concat([sessions, sessions.iloc[:max(1, int(10 * scale))]], ignore_index=True)
    for name, frame in {"customers": customers, "products": products, "orders": orders, "order_items": order_items, "sessions": sessions, "marketing_campaigns": campaigns, "returns": returns, "reviews": reviews}.items():
        frame.to_csv(OUT / f"{name}.csv", index=False)
    print(f"Generated {sum(map(len, [customers, products, orders, order_items, sessions, campaigns, returns, reviews])):,} synthetic records in {OUT}")


if __name__ == "__main__":
    main()

