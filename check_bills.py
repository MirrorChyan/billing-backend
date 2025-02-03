from datetime import datetime, timedelta

from src.database import Bill, Plan, CheckIn


def monthly_bill(year: int, month: int):
    print(f"Checking {year}-{month} bills...")

    bills = Bill.select().where(
        Bill.created_at.year == year,
        Bill.created_at.month == month,
    )

    print("\n==== Orders ====\n")

    all_plans = Plan.select().order_by(Plan.valid_days)
    plans = {}
    for plan in all_plans:
        plans[plan.plan_id] = (plan.title, 0, 0) # name, order, item

    order_count = 0
    item_count = 0
    bill_amount = 0
    for bill in bills:
        if bill.plan_id not in plans:
            print(f"Plan not found: {bill.plan_id}, bill: {bill}")
            continue

        plans[bill.plan_id] = (
            plans[bill.plan_id][0],
            plans[bill.plan_id][1] + 1,
            plans[bill.plan_id][2] + bill.buy_count,
        )

        order_count += 1
        item_count += bill.buy_count
        bill_amount += float(bill.actually_paid)

    for plan_id, (name, order, item) in plans.items():
        print(f"{name}: {order} orders, {item} items")

    print(f"\nTotal: orders: {order_count}, items: {item_count}, amount: {bill_amount:.2f}")

    print("\n==== Checkins ====\n")

    app_uas = {}

    checkins = CheckIn.select().where(
        CheckIn.activated_at.year == year,
        CheckIn.activated_at.month == month,
    )

    # 有可能订单在上个月，但是激活在这个月
    bills = Bill.select().where(
        Bill.created_at < datetime(year, month, 1) + timedelta(days=31),
    )

    invalid_checkins = 0
    for checkin in checkins:
        app = checkin.application
        ua = checkin.user_agent
        app_ua = f"{app} - {ua}"
        if app_ua not in app_uas:
            app_uas[app_ua] = (0, 0) # count, amount

        count = 0
        amount = 0
        for bill in bills:
            if bill.cdk == checkin.cdk:
                count += 1
                amount += float(bill.actually_paid)

        if count == 0:
            invalid_checkins += 1
            continue

        app_uas[app_ua] = (
            app_uas[app_ua][0] + 1,
            app_uas[app_ua][1] + amount,
        )

    checkin_count = len(checkins) - invalid_checkins
    checkin_amount = sum(amount for _, (_, amount) in app_uas.items())

    print(f"Invalid checkins: {invalid_checkins}")
    for app_ua, (count, amount) in app_uas.items():
        print(f"{app_ua}: {count} checkins, amount: {amount:.2f}")

    print(f"\nTotal: checkins: {checkin_count}, amount: {checkin_amount:.2f}")

    not_checkin_count = order_count - checkin_count
    not_checkin_amount = bill_amount - checkin_amount
    print(f"\nOrders not checkin: {not_checkin_count}, amount: {not_checkin_amount:.2f}")



if __name__ == "__main__":
    monthly_bill(datetime.now().year, datetime.now().month)
