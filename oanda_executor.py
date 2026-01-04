"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

"""
OANDA order executor and position manager.
Handles market order placement, SL/TP attachment, and position monitoring.
"""

import oandapyV20
from oandapyV20.endpoints import orders, positions, accounts
import logging
import json

from config import OANDA_ACCESS_TOKEN, OANDA_ACCOUNT_ID, INSTRUMENT, UNITS, RISK_REWARD

logger = logging.getLogger(__name__)


class OandaExecutor:
    """
    Executes trades and manages positions via OANDA API.
    """
    
    def __init__(self, dry_run=False):
        """
        Initialize executor.
        
        Args:
            dry_run (bool): If True, log orders but don't execute
        """
        self.client = oandapyV20.API(access_token=OANDA_ACCESS_TOKEN)
        self.account_id = OANDA_ACCOUNT_ID
        self.instrument = INSTRUMENT
        self.units = UNITS
        self.dry_run = dry_run
        
        self.current_position = None
        self.order_id = None
        
        logger.info(f"OandaExecutor initialized (dry_run={dry_run})")
    
    def place_order(self, signal):
        """
        Place market order with SL and TP attached.
        
        Args:
            signal (dict): Entry signal from detector
                - direction: 'long' or 'short'
                - entry_price: Expected entry price
                - sl: Stop loss price
                - tp: Take profit price
                
        Returns:
            bool: True if order placed successfully
        """
        direction = signal['direction']
        entry_price = signal['entry_price']
        sl = signal['sl']
        tp = signal['tp']
        
        # Calculate units (positive for long, negative for short)
        units_signed = self.units if direction == 'long' else -self.units
        
        # Build order request
        order_data = {
            "order": {
                "instrument": self.instrument,
                "units": str(units_signed),
                "type": "MARKET",
                "stopLossOnFill": {
                    "price": f"{sl:.2f}"
                },
                "takeProfitOnFill": {
                    "price": f"{tp:.2f}"
                }
            }
        }
        
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Placing {direction.upper()} order:")
        logger.info(f"  Entry: {entry_price:.2f}")
        logger.info(f"  SL: {sl:.2f}")
        logger.info(f"  TP: {tp:.2f}")
        logger.info(f"  Units: {units_signed}")
        
        if self.dry_run:
            # Simulate successful order
            self.current_position = {
                'direction': direction,
                'entry': entry_price,
                'sl': sl,
                'tp': tp,
                'units': units_signed
            }
            logger.info("[DRY RUN] Order simulated successfully")
            return True
        
        try:
            # Place real order
            r = orders.OrderCreate(accountID=self.account_id, data=order_data)
            response = self.client.request(r)
            
            # Extract order details
            order_fill = response.get('orderFillTransaction', {})
            self.order_id = order_fill.get('id')
            
            # Store position info
            self.current_position = {
                'direction': direction,
                'entry': float(order_fill.get('price', entry_price)),
                'sl': sl,
                'tp': tp,
                'units': units_signed,
                'order_id': self.order_id
            }
            
            logger.info(f"✅ Order placed successfully! Order ID: {self.order_id}")
            logger.info(f"   Fill price: {self.current_position['entry']:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Order placement failed: {e}")
            return False
    
    def get_position(self):
        """
        Query current position from OANDA.
        
        Returns:
            dict or None: Position info or None if no position
        """
        if self.dry_run:
            return self.current_position
        
        try:
            r = positions.PositionDetails(
                accountID=self.account_id,
                instrument=self.instrument
            )
            response = self.client.request(r)
            
            position = response.get('position', {})
            long_units = float(position.get('long', {}).get('units', 0))
            short_units = float(position.get('short', {}).get('units', 0))
            
            # Check if we have an open position
            if long_units != 0 or short_units != 0:
                return {
                    'long_units': long_units,
                    'short_units': short_units,
                    'pl': float(position.get('pl', 0))
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error querying position: {e}")
            return None
    
    def has_position(self):
        """
        Check if we have an open position.
        
        Returns:
            bool: True if position is open
        """
        return self.current_position is not None
    
    def monitor_position(self, current_price):
        """
        Monitor position for exit conditions.
        Note: With SL/TP attached, OANDA handles exits automatically.
        This is mainly for logging and state tracking.
        
        Args:
            current_price (float): Current market price
            
        Returns:
            str or None: 'win', 'loss', or None if still open
        """
        if not self.has_position():
            return None
        
        direction = self.current_position['direction']
        sl = self.current_position['sl']
        tp = self.current_position['tp']
        
        # Check if TP hit
        if direction == 'long' and current_price >= tp:
            logger.info(f"🎯 TP HIT at {current_price:.2f}")
            self._close_position('win')
            return 'win'
        elif direction == 'short' and current_price <= tp:
            logger.info(f"🎯 TP HIT at {current_price:.2f}")
            self._close_position('win')
            return 'win'
        
        # Check if SL hit
        if direction == 'long' and current_price <= sl:
            logger.info(f"🛑 SL HIT at {current_price:.2f}")
            self._close_position('loss')
            return 'loss'
        elif direction == 'short' and current_price >= sl:
            logger.info(f"🛑 SL HIT at {current_price:.2f}")
            self._close_position('loss')
            return 'loss'
        
        return None
    
    def check_if_closed(self):
        """
        Check if position was closed by OANDA (SL/TP hit).
        
        Returns:
            bool: True if position is closed
        """
        if self.dry_run:
            return False
        
        position = self.get_position()
        
        # If we think we have a position but OANDA says no, it was closed
        if self.current_position is not None and position is None:
            logger.info("Position closed by OANDA (SL/TP hit)")
            self._close_position('closed')
            return True
        
        return False
    
    def _close_position(self, reason):
        """
        Mark position as closed.
        
        Args:
            reason (str): Reason for closure
        """
        logger.info(f"Position closed: {reason}")
        self.current_position = None
        self.order_id = None
    
    def force_close_position(self):
        """
        Force close current position (emergency use).
        
        Returns:
            bool: True if closed successfully
        """
        if not self.has_position():
            logger.warning("No position to close")
            return False
        
        logger.warning("⚠️ FORCE CLOSING POSITION")
        
        if self.dry_run:
            self._close_position('force_closed')
            return True
        
        try:
            # Close position via OANDA
            data = {
                "longUnits": "ALL" if self.current_position['direction'] == 'long' else "NONE",
                "shortUnits": "ALL" if self.current_position['direction'] == 'short' else "NONE"
            }
            
            r = positions.PositionClose(
                accountID=self.account_id,
                instrument=self.instrument,
                data=data
            )
            response = self.client.request(r)
            
            logger.info(f"Position force closed: {response}")
            self._close_position('force_closed')
            return True
            
        except Exception as e:
            logger.error(f"Error force closing position: {e}")
            return False
    
    def get_account_summary(self):
        """
        Get account balance and summary.
        
        Returns:
            dict: Account summary
        """
        if self.dry_run:
            return {'balance': 'N/A (dry run)', 'pl': 'N/A'}
        
        try:
            r = accounts.AccountSummary(accountID=self.account_id)
            response = self.client.request(r)
            
            account = response.get('account', {})
            return {
                'balance': float(account.get('balance', 0)),
                'pl': float(account.get('pl', 0)),
                'unrealized_pl': float(account.get('unrealizedPL', 0))
            }
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}
