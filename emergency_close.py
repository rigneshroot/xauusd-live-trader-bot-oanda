"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

#!/usr/bin/env python3
"""
Emergency position closer for OANDA.
Use this to immediately close all positions if needed.
"""

import oandapyV20
from oandapyV20.endpoints import positions
import sys

from config import OANDA_ACCESS_TOKEN, OANDA_ACCOUNT_ID, INSTRUMENT


def close_all_positions():
    """Force close all positions on the account."""
    client = oandapyV20.API(access_token=OANDA_ACCESS_TOKEN)
    
    print("=" * 60)
    print("⚠️  EMERGENCY POSITION CLOSER")
    print("=" * 60)
    print(f"Account: {OANDA_ACCOUNT_ID}")
    print(f"Instrument: {INSTRUMENT}")
    print()
    
    # Confirm
    response = input("Are you sure you want to close ALL positions? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    try:
        # Close position
        data = {
            "longUnits": "ALL",
            "shortUnits": "ALL"
        }
        
        r = positions.PositionClose(
            accountID=OANDA_ACCOUNT_ID,
            instrument=INSTRUMENT,
            data=data
        )
        
        result = client.request(r)
        
        print("✅ Positions closed successfully!")
        print()
        print("Response:")
        print(result)
        
    except Exception as e:
        print(f"❌ Error closing positions: {e}")
        sys.exit(1)


if __name__ == "__main__":
    close_all_positions()
