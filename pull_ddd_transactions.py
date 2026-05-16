#!/usr/bin/env python3
"""Pull ALL DDD transactions from TastyTrade and save to JSON.
Uses credentials from secrets.env in the same directory.
"""

import asyncio
import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

# Load secrets.env
env_file = Path(__file__).parent / "secrets.env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

from tastytrade import Session, Account


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if hasattr(o, 'value'):
            return o.value
        if hasattr(o, 'name'):
            return o.name
        return super().default(o)


async def main():
    client_secret = os.environ.get("TASTYTRADE_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTYTRADE_REFRESH_TOKEN")

    if not client_secret or not refresh_token:
        print("ERROR: Missing TASTYTRADE_CLIENT_SECRET or TASTYTRADE_REFRESH_TOKEN")
        return

    print("Authenticating with TastyTrade...")
    async with Session(client_secret, refresh_token) as session:
        print("Authenticated. Fetching accounts...")
        accounts = await Account.get(session)
        print(f"Found {len(accounts)} account(s)")

        for acct in accounts:
            print(f"\nAccount: {acct.account_number}")

            # Pull ALL transactions from account inception (2024-01-01 to be safe)
            print("Fetching ALL transaction history from 2024-01-01...")
            all_history = await acct.get_history(
                session,
                start_date=date(2024, 1, 1),
            )
            print(f"Total transactions found: {len(all_history)}")

            # Filter for DDD-related transactions
            ddd_transactions = []
            all_transactions_raw = []

            for tx in all_history:
                # Build a dict of the transaction
                tx_dict = {
                    "id": tx.id,
                    "date": tx.executed_at.isoformat() if tx.executed_at else str(tx.transaction_date),
                    "transaction_date": str(tx.transaction_date) if tx.transaction_date else "",
                    "type": str(tx.transaction_type),
                    "sub_type": str(tx.transaction_sub_type),
                    "description": tx.description or "",
                    "symbol": tx.symbol or "",
                    "underlying_symbol": tx.underlying_symbol or "",
                    "instrument_type": str(tx.instrument_type) if tx.instrument_type else "",
                    "action": str(tx.action) if tx.action else "",
                    "quantity": float(tx.quantity) if tx.quantity else 0,
                    "price": float(tx.price) if tx.price else 0,
                    "value": float(tx.value) if tx.value else 0,
                    "net_value": float(tx.net_value) if tx.net_value else 0,
                    "commission": float(tx.commission) if tx.commission else 0,
                    "regulatory_fees": float(tx.regulatory_fees) if tx.regulatory_fees else 0,
                    "clearing_fees": float(tx.clearing_fees) if tx.clearing_fees else 0,
                }
                all_transactions_raw.append(tx_dict)

                # Check if related to DDD
                symbol = tx.symbol or ""
                underlying = tx.underlying_symbol or ""
                desc = tx.description or ""

                if "DDD" in symbol or "DDD" in underlying or "DDD" in desc:
                    ddd_transactions.append(tx_dict)

            # Save ALL transactions
            all_file = Path(__file__).parent / "data" / "tastytrade_all_transactions.json"
            all_file.parent.mkdir(exist_ok=True)
            with open(all_file, "w") as f:
                json.dump(all_transactions_raw, f, indent=2, cls=DecimalEncoder)
            print(f"\nSaved ALL {len(all_transactions_raw)} transactions to {all_file}")

            # Save DDD transactions
            ddd_file = Path(__file__).parent / "data" / "tastytrade_ddd_transactions.json"
            with open(ddd_file, "w") as f:
                json.dump(ddd_transactions, f, indent=2, cls=DecimalEncoder)
            print(f"Saved {len(ddd_transactions)} DDD transactions to {ddd_file}")

            # Print DDD transactions summary
            print(f"\n{'='*80}")
            print(f"DDD TRANSACTION HISTORY ({len(ddd_transactions)} transactions)")
            print(f"{'='*80}")
            
            total_premiums_collected = 0
            total_stock_cost = 0
            total_shares_bought = 0
            total_shares_sold = 0
            
            for tx in sorted(ddd_transactions, key=lambda x: x["date"]):
                desc = tx["description"]
                val = tx["net_value"]
                dt = tx["date"][:10]
                sym = tx["symbol"]
                qty = tx["quantity"]
                price = tx["price"]
                action = tx["action"]
                sub_type = tx["sub_type"]
                inst_type = tx["instrument_type"]
                
                # Track premiums and costs
                if "Option" in inst_type or "EquityOption" in inst_type:
                    # Positive net_value = credit (premium received), negative = debit (premium paid)
                    total_premiums_collected += val
                elif "Equity" in inst_type:
                    if "Buy" in action:
                        total_stock_cost += abs(val)
                        total_shares_bought += int(qty)
                    elif "Sell" in action:
                        total_stock_cost -= abs(val)
                        total_shares_sold += int(qty)

                print(f"  {dt} | {sub_type:20s} | {sym:30s} | qty:{qty:>6.0f} | ${price:>8.4f} | net: ${val:>10.2f} | {desc}")
            
            print(f"\n{'='*80}")
            print(f"DDD WHEEL SUMMARY")
            print(f"{'='*80}")
            print(f"Total premiums collected (options): ${total_premiums_collected:.2f}")
            print(f"Net stock cost:                     ${total_stock_cost:.2f}")
            print(f"Total shares bought:                {total_shares_bought}")
            print(f"Total shares sold:                  {total_shares_sold}")
            print(f"Net shares held:                    {total_shares_bought - total_shares_sold}")
            
            if total_shares_bought - total_shares_sold > 0:
                net_shares = total_shares_bought - total_shares_sold
                true_basis = (total_stock_cost - total_premiums_collected) / net_shares
                print(f"True basis per share:               ${true_basis:.4f}")

            # Also get current positions
            print(f"\n{'='*80}")
            print(f"CURRENT POSITIONS")
            print(f"{'='*80}")
            positions = await acct.get_positions(session)
            for pos in positions:
                sym = pos.symbol
                if "DDD" in sym:
                    print(f"  {sym}: qty={pos.quantity} {pos.quantity_direction}, avg_price=${float(pos.average_open_price):.4f}")

            # Get current balance
            balance = await acct.get_balances(session)
            print(f"\nNet Liquidating Value: ${float(balance.net_liquidating_value):.2f}")
            print(f"Cash Balance: ${float(balance.cash_balance):.2f}")
            print(f"Equity Buying Power: ${float(balance.equity_buying_power):.2f}")


if __name__ == "__main__":
    asyncio.run(main())
