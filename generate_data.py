"""QueryPilot Phase 1: synthetic data generator (PostgreSQL).

Usage:  python generate_data.py --dsn "postgresql:///querypilot"
Run once on a freshly created schema (it refuses to run on non-empty data).

Design choices that matter for later phases:
  * Pareto-skewed customer activity -> "best customer" has a real answer.
  * ~15% of customers never order -> tests LEFT JOIN / anti-join questions.
  * Nov/Dec seasonal spike -> "last month" / trend questions are non-trivial.
  * Price changes over time -> order_items.unit_price != current_price.
  * Multi-payment, multi-shipment, partial-refund orders -> fan-out traps.
Ids rely on identity columns starting at 1 and inserting in order, so a row's
id == its position in the list. Fixed seed => reproducible dataset.
"""
import argparse
import random
from datetime import date, datetime, timedelta

import psycopg2
from faker import Faker
from psycopg2.extras import execute_values

SEED = 42
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

START = datetime(2024, 1, 1)
END = datetime(2026, 10, 28)
N_CUSTOMERS, N_PRODUCTS, N_ORDERS = 2000, 150, 12000
MONTH_WEIGHT = {1: .8, 2: .7, 3: .9, 4: .9, 5: 1, 6: 1, 7: .9, 8: .9, 9: 1, 10: 1.1, 11: 1.8, 12: 2.0}


class Table:
    """Collects rows in memory; add() returns the id the DB will assign."""
    def __init__(self, name, cols):
        self.name, self.cols, self.rows = name, cols, []

    def add(self, *row):
        self.rows.append(row)
        return len(self.rows)

    def flush(self, cur):
        if not self.rows:
            return
        sql = f"INSERT INTO {self.name} ({', '.join(self.cols)}) VALUES %s"
        execute_values(cur, sql, self.rows, page_size=2000)


def rand_between(a, b):
    return a + timedelta(seconds=random.randint(0, max(1, int((b - a).total_seconds()))))


def seasonal_date(after):
    """Random datetime in [max(after, START), END], biased by month weight (rejection sampling)."""
    lo = max(after, START)
    for _ in range(60):
        d = rand_between(lo, END)
        if random.random() < MONTH_WEIGHT[d.month] / 2.0:
            return d
    return rand_between(lo, END)


def main(dsn):
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM customers")
    if cur.fetchone()[0]:
        raise SystemExit("customers is not empty - run on a fresh schema.")

    T = {}
    def table(name, *cols):
        T[name] = Table(name, cols)
        return T[name]

    # ---------- employees / ops ----------
    depts = table("departments", "name")
    dept_names = ["Customer Support", "Sales", "Warehouse", "Marketing", "Engineering", "Finance"]
    for n in dept_names:
        depts.add(n)
    emps = table("employees", "department_id", "manager_id", "first_name", "last_name",
                 "email", "job_title", "hired_at", "is_active")
    emp_dept = {}
    for i in range(1, 46):
        dept = 1 + (i % 6) if i > 1 else 2
        mgr = None if i == 1 else random.randint(1, min(i - 1, 8))
        eid = emps.add(dept, mgr, fake.first_name(), fake.last_name(), f"emp{i}@querypilot.test",
                       random.choice(["Associate", "Specialist", "Lead", "Manager"]),
                       fake.date_between(date(2019, 1, 1), date(2026, 6, 1)), random.random() > .08)
        emp_dept[eid] = dept
    sales_emps = [e for e, d in emp_dept.items() if d == 2]
    support_emps = [e for e, d in emp_dept.items() if d == 1]
    store_emps = [e for e, d in emp_dept.items() if d in (2, 3)]

    stores = table("stores", "name", "city", "country", "manager_id", "opened_at")
    for city, ctry in [("Mumbai", "India"), ("Delhi", "India"), ("Kolkata", "India"),
                       ("Dubai", "UAE"), ("Singapore", "Singapore")]:
        stores.add(f"QP {city}", city, ctry, random.choice(sales_emps),
                   fake.date_between(date(2018, 1, 1), date(2023, 1, 1)))
    n_stores = len(stores.rows)
    asg = table("employee_store_assignments", "employee_id", "store_id", "started_at", "ended_at")
    for e in store_emps:
        s = random.randint(1, n_stores)
        st = fake.date_between(date(2022, 1, 1), date(2025, 1, 1))
        asg.add(e, s, st, None if random.random() < .75 else st + timedelta(days=random.randint(90, 600)))

    # ---------- catalog ----------
    cats = table("categories", "parent_category_id", "name")
    tree = {"Electronics": ["Phones", "Laptops", "Audio"], "Clothing": ["Men", "Women", "Kids"],
            "Home": ["Kitchen", "Furniture", "Decor"], "Sports": ["Fitness", "Outdoor", "Team Sports"],
            "Beauty": ["Skincare", "Haircare", "Fragrance"], "Books": ["Fiction", "Non-fiction", "Education"]}
    leaf_cats = []
    for parent, kids in tree.items():
        pid = cats.add(None, parent)
        for k in kids:
            leaf_cats.append(cats.add(pid, k))

    sups = table("suppliers", "name", "country", "contact_email", "is_active")
    for i in range(20):
        sups.add(fake.company(), random.choice(["India", "China", "Vietnam", "Germany", "USA"]),
                 f"sales{i}@supplier.test", random.random() > .1)

    prods = table("products", "category_id", "supplier_id", "name", "description", "brand",
                  "created_at", "is_discontinued")
    variants = table("product_variants", "product_id", "sku", "size", "color", "current_price", "unit_cost")
    hist = table("price_history", "variant_id", "price", "effective_from", "effective_to")
    price_lookup = {}  # variant_id -> [(from_dt, to_dt|None, price)]
    adjectives = ["Classic", "Pro", "Eco", "Ultra", "Smart", "Essential", "Premium", "Compact"]
    brands = ["Nova", "Zenith", "Urbana", "Kiro", "Aster", "Veda", "Lumo"]
    for p in range(N_PRODUCTS):
        cat = random.choice(leaf_cats)
        pid = prods.add(cat, random.randint(1, 20), f"{random.choice(adjectives)} {fake.word().title()}",
                        fake.sentence(), random.choice(brands),
                        rand_between(datetime(2023, 1, 1), datetime(2025, 6, 1)), random.random() < .07)
        base = round(random.lognormvariate(3.8, .8), 2) + 5
        for v in range(random.randint(2, 4)):
            # price history: 1-3 periods, last one open-ended
            n_per = random.randint(1, 3)
            cuts = sorted(rand_between(datetime(2023, 6, 1), END) for _ in range(n_per - 1))
            bounds = [datetime(2023, 1, 1)] + cuts
            price, periods = base * random.uniform(.95, 1.05), []
            for i, b in enumerate(bounds):
                to = bounds[i + 1] - timedelta(days=1) if i + 1 < len(bounds) else None
                periods.append((b, to, round(price, 2)))
                price *= random.uniform(.9, 1.15)
            cur_price = periods[-1][2]
            vid = variants.add(pid, f"SKU-{pid:04d}-{v}", random.choice(["S", "M", "L", "XL", None]),
                               random.choice(["black", "white", "blue", "red", "green", None]),
                               cur_price, round(cur_price * random.uniform(.4, .7), 2))
            price_lookup[vid] = periods
            for b, to, pr in periods:
                hist.add(vid, pr, b.date(), to.date() if to else None)
    n_variants = len(variants.rows)

    wh = table("warehouses", "name", "city", "country")
    for city, ctry in [("Bhiwandi", "India"), ("Gurgaon", "India"), ("Jebel Ali", "UAE"), ("Jurong", "Singapore")]:
        wh.add(f"WH {city}", city, ctry)
    inv = table("inventory_stock", "warehouse_id", "variant_id", "quantity_on_hand", "reorder_level", "updated_at")
    for w in range(1, len(wh.rows) + 1):
        for v in range(1, n_variants + 1):
            if random.random() < .7:
                lvl = random.choice([10, 20, 50])
                inv.add(w, v, random.choice([0, 3, 8]) if random.random() < .12 else random.randint(lvl, 400),
                        lvl, rand_between(datetime(2026, 6, 1), END))

    # ---------- customers ----------
    custs = table("customers", "first_name", "last_name", "email", "phone", "signed_up_at",
                  "acquisition_channel", "is_active")
    addrs = table("customer_addresses", "customer_id", "line1", "line2", "city", "state",
                  "postal_code", "country", "is_default")
    signup, default_addr = {}, {}
    for i in range(1, N_CUSTOMERS + 1):
        su = rand_between(datetime(2023, 6, 1), datetime(2026, 8, 31))
        cid = custs.add(fake.first_name(), fake.last_name(), f"cust{i}@mail.test", fake.msisdn()[:10], su,
                        random.choices(["organic", "paid_search", "referral", "social", "email"],
                                       [35, 25, 15, 15, 10])[0], random.random() > .1)
        signup[cid] = su
        for k in range(random.choice([1, 1, 2])):
            a = addrs.add(cid, fake.street_address(), None, fake.city(), fake.state(),
                          fake.postcode(), random.choice(["India", "India", "India", "UAE", "Singapore"]), k == 0)
            if k == 0:
                default_addr[cid] = a

    carriers = table("shipping_carriers", "name")
    for n in ["BlueDart", "Delhivery", "DHL", "FedEx", "EcomExpress"]:
        carriers.add(n)

    # ---------- marketing (before orders so redemptions can reference) ----------
    camps = table("marketing_campaigns", "name", "channel", "budget", "start_date", "end_date")
    for i in range(12):
        s = rand_between(START, END - timedelta(days=30)).date()
        camps.add(f"Campaign {i+1}: {fake.catch_phrase()[:30]}", random.choice(["email", "social", "search", "display"]),
                  round(random.uniform(500, 20000), 2), s, s + timedelta(days=random.randint(7, 45)))
    promos = table("promotions", "campaign_id", "code", "discount_type", "discount_value", "valid_from", "valid_to")
    promo_windows = []
    for i in range(15):
        s = rand_between(START, END - timedelta(days=20)).date()
        e = s + timedelta(days=random.randint(5, 40))
        dt = random.choice(["percent", "fixed"])
        val = random.choice([5, 10, 15, 20]) if dt == "percent" else random.choice([5, 10, 25])
        pid = promos.add(random.randint(1, 12) if random.random() < .7 else None, f"PROMO{i+1:02d}", dt, val, s, e)
        promo_windows.append((pid, s, e, dt, val))
    ccust = table("campaign_customers", "campaign_id", "customer_id", "sent_at", "opened", "clicked")
    for c in range(1, 13):
        start_dt = datetime.combine(camps.rows[c - 1][3], datetime.min.time())
        for cid in random.sample(range(1, N_CUSTOMERS + 1), random.randint(150, 400)):
            opened = random.random() < .4
            ccust.add(c, cid, start_dt, opened, opened and random.random() < .3)

    # ---------- orders and everything hanging off them ----------
    # Skewed activity: Pareto weights, ~15% of customers never order.
    weights = [0 if random.random() < .15 else min(random.paretovariate(1.2), 60) for _ in range(N_CUSTOMERS)]
    order_custs = random.choices(range(1, N_CUSTOMERS + 1), weights=weights, k=N_ORDERS)
    var_weights = [min(random.paretovariate(1.3), 40) for _ in range(n_variants)]

    def price_at(vid, dt):
        for b, to, pr in price_lookup[vid]:
            if dt >= b and (to is None or dt <= to + timedelta(days=1)):
                return pr
        return price_lookup[vid][0][2]

    orders = table("orders", "customer_id", "store_id", "shipping_address_id", "status", "ordered_at", "shipping_fee")
    items = table("order_items", "order_id", "variant_id", "quantity", "unit_price", "discount_amount")
    pays = table("payments", "order_id", "method", "amount", "status", "paid_at")
    refs = table("refunds", "payment_id", "order_item_id", "amount", "reason", "refunded_at")
    ships = table("shipments", "order_id", "carrier_id", "warehouse_id", "tracking_number", "shipped_at", "delivered_at")
    sitems = table("shipment_items", "shipment_id", "order_item_id", "quantity")
    revs = table("reviews", "customer_id", "product_id", "order_item_id", "rating", "title", "body", "created_at")
    tickets = table("support_tickets", "customer_id", "order_id", "assigned_employee_id", "subject",
                    "status", "priority", "opened_at", "resolved_at")
    msgs = table("support_ticket_messages", "ticket_id", "sender_type", "body", "sent_at")
    redeem = table("promotion_redemptions", "promotion_id", "order_id", "customer_id", "redeemed_at")

    prod_of_variant = {i + 1: variants.rows[i][0] for i in range(n_variants)}

    for cid in order_custs:
        ordered_at = seasonal_date(signup[cid])
        age_days = (END - ordered_at).days
        if age_days < 14:
            status = random.choice(["pending", "paid", "shipped"])
        else:
            status = random.choices(["pending", "paid", "shipped", "delivered", "cancelled", "returned"],
                                    [2, 3, 3, 76, 9, 7])[0]
        store = None if random.random() < .6 else random.randint(1, n_stores)
        ship_fee = 0 if store else random.choice([0, 0, 49, 99])
        oid = orders.add(cid, store, None if store else default_addr[cid], status, ordered_at, ship_fee)

        order_items = []
        total = ship_fee
        for _ in range(random.choices([1, 2, 3, 4, 5], [45, 28, 15, 8, 4])[0]):
            vid = random.choices(range(1, n_variants + 1), weights=var_weights)[0]
            qty = random.choices([1, 2, 3], [80, 15, 5])[0]
            up = price_at(vid, ordered_at)
            disc = round(up * qty * random.choice([.05, .1, .2]), 2) if random.random() < .15 else 0
            iid = items.add(oid, vid, qty, up, disc)
            order_items.append((iid, vid, qty, round(up * qty - disc, 2)))
            total += up * qty - disc
        total = round(total, 2)

        # payments
        pay_id = None
        if status == "pending":
            pays.add(oid, random.choice(["card", "upi", "cod"]), total, "pending", None)
        elif status == "cancelled":
            if random.random() < .5:
                pays.add(oid, random.choice(["card", "upi"]), total, "failed", None)
        else:
            if random.random() < .08:
                pays.add(oid, "card", total, "failed", ordered_at + timedelta(minutes=2))
            pay_id = pays.add(oid, random.choices(["card", "upi", "paypal", "bank_transfer", "cod"],
                                                  [45, 30, 10, 5, 10])[0], total, "succeeded",
                              ordered_at + timedelta(minutes=random.randint(1, 30)))

        # shipments
        delivered_at = None
        if status in ("shipped", "delivered", "returned"):
            split = len(order_items) > 1 and random.random() < .12
            groups = [order_items[:1], order_items[1:]] if split else [order_items]
            for g in groups:
                sh_at = ordered_at + timedelta(days=random.randint(1, 3), hours=random.randint(0, 20))
                dl_at = sh_at + timedelta(days=random.randint(2, 8)) if status != "shipped" else None
                sid = ships.add(oid, random.randint(1, 5), random.randint(1, 4), f"TRK{random.randint(10**9, 10**10-1)}",
                                sh_at, dl_at)
                delivered_at = dl_at or delivered_at
                for iid, vid, qty, _ in g:
                    sitems.add(sid, iid, qty)

        # refunds
        if pay_id and status == "returned":
            if random.random() < .5:
                refs.add(pay_id, None, total, random.choice(["defective", "wrong item", "changed mind"]),
                         (delivered_at or ordered_at) + timedelta(days=random.randint(2, 10)))
            else:
                for iid, vid, qty, line in order_items:
                    refs.add(pay_id, iid, line, random.choice(["defective", "wrong item", "changed mind"]),
                             (delivered_at or ordered_at) + timedelta(days=random.randint(2, 10)))
        elif pay_id and status == "delivered" and random.random() < .04:
            iid, vid, qty, line = random.choice(order_items)
            refs.add(pay_id, iid, round(line * random.uniform(.3, 1), 2) or 1, "partial refund",
                     (delivered_at or ordered_at) + timedelta(days=random.randint(2, 15)))

        # reviews (verified purchases, 12% of delivered items; ratings skew positive)
        if status == "delivered" and delivered_at:
            for iid, vid, qty, _ in order_items:
                if random.random() < .12:
                    revs.add(cid, prod_of_variant[vid], iid, random.choices([1, 2, 3, 4, 5], [6, 6, 12, 32, 44])[0],
                             fake.sentence(nb_words=4), fake.paragraph(nb_sentences=2),
                             delivered_at + timedelta(days=random.randint(1, 30)))

        # support tickets
        if status != "pending" and random.random() < .06:
            opened = ordered_at + timedelta(days=random.randint(1, 10))
            tstatus = random.choices(["open", "in_progress", "resolved", "closed"], [10, 10, 30, 50])[0]
            resolved = opened + timedelta(hours=random.randint(2, 200)) if tstatus in ("resolved", "closed") else None
            tid = tickets.add(cid, oid, random.choice(support_emps),
                              random.choice(["Late delivery", "Wrong item", "Refund status", "Damaged product", "Payment issue"]),
                              tstatus, random.choices(["low", "medium", "high"], [40, 40, 20])[0], opened, resolved)
            t = opened
            for k in range(random.randint(2, 5)):
                t += timedelta(hours=random.randint(1, 24))
                msgs.add(tid, "customer" if k % 2 == 0 else "employee", fake.paragraph(nb_sentences=2), t)

        # promotion redemption
        if status in ("paid", "shipped", "delivered", "returned") and random.random() < .10:
            ok = [p for p in promo_windows if p[1] <= ordered_at.date() <= p[2]]
            if ok:
                redeem.add(random.choice(ok)[0], oid, cid, ordered_at)

    # unverified reviews
    for _ in range(150):
        revs.add(random.randint(1, N_CUSTOMERS), random.randint(1, N_PRODUCTS), None,
                 random.choices([1, 2, 3, 4, 5], [10, 8, 14, 30, 38])[0], fake.sentence(nb_words=4),
                 fake.paragraph(nb_sentences=2), rand_between(START, END))

    wish = table("wishlists", "customer_id", "product_id", "added_at")
    seen = set()
    while len(seen) < 1500:
        pair = (random.randint(1, N_CUSTOMERS), random.randint(1, N_PRODUCTS))
        if pair not in seen:
            seen.add(pair)
            wish.add(*pair, rand_between(signup[pair[0]], END))

    # ---------- insert in FK order ----------
    order = ["departments", "employees", "stores", "employee_store_assignments", "categories", "suppliers",
             "products", "product_variants", "warehouses", "inventory_stock", "price_history", "customers",
             "customer_addresses", "shipping_carriers", "marketing_campaigns", "campaign_customers", "promotions",
             "orders", "order_items", "payments", "refunds", "shipments", "shipment_items", "reviews",
             "support_tickets", "support_ticket_messages", "wishlists", "promotion_redemptions"]
    assert set(order) == set(T), set(T) ^ set(order)
    for name in order:
        T[name].flush(cur)
    conn.commit()
    for name in order:
        print(f"{name:28s} {len(T[name].rows):>7d}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default="postgresql:///querypilot")
    main(ap.parse_args().dsn)
