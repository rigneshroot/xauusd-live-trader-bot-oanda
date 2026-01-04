"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

from utils import setup_logging
from candle_buffer import CandleBuffer
from session_state import SessionStateMachine
from entry_detector import EntryDetector
from oanda_executor import OandaExecutor
from streaming_client import StreamingClient

def main():
    logger = setup_logging()

    buffer = CandleBuffer()
    session = SessionStateMachine()
    detector = EntryDetector()
    executor = OandaExecutor(dry_run=True)

    def on_tick(ts, bid, ask):
        buffer.add_tick(ts, bid, ask)
        session.update(buffer)

        if not session.can_trade():
            return

        candles = buffer.get_latest_1m(1)
        if not candles:
            return

        candle = candles[-1]
        or_high, or_low = session.get_or_range()

        signal = detector.process_candle(candle, or_high, or_low)

        if signal and not executor.has_position():
            ok = executor.place_order(signal)
            if ok:
                session.mark_trade_taken()

    stream = StreamingClient(on_tick)
    stream.start()

    logger.info("🚀 Live trader started")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stream.stop()

if __name__ == "__main__":
    main()
