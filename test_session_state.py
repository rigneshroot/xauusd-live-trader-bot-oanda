"""
Live Trading System for OANDA
Copyright (c) 2026 Rignesh
Licensed under the MIT License - see LICENSE file for details
"""

"""
Test suite for SessionStateMachine
Tests the mid-day startup fix and other state transitions
"""

import datetime
from unittest.mock import patch, MagicMock

from session_state import SessionStateMachine, SessionState
from candle_buffer import CandleBuffer


class TestMidDayStartup:
    """Test cases for mid-day startup behavior."""
    
    def test_startup_after_or_window_skips_session(self):
        """Test that starting after OR window (9:35 AM) skips the session."""
        # Mock time to be 3:33 PM EST (after OR window)
        mock_ny_time = datetime.datetime(2026, 1, 9, 15, 33, 0, 
                                         tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        
        with patch('session_state.get_ny_time') as mock_time:
            mock_time.return_value = mock_ny_time
            
            session = SessionStateMachine()
            buffer = CandleBuffer()
            
            # First update should skip to SESSION_CLOSED
            session.update(buffer)
            
            assert session.state == SessionState.SESSION_CLOSED
            assert session.can_trade() == False
            print("✅ Test passed: Bot correctly skips session when starting at 3:33 PM")
    
    def test_startup_at_or_lock_time_skips_session(self):
        """Test that starting exactly at OR lock time (9:35 AM) skips the session."""
        # Mock time to be exactly 9:35 AM EST
        mock_ny_time = datetime.datetime(2026, 1, 9, 9, 35, 0,
                                         tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        
        with patch('session_state.get_ny_time') as mock_time:
            mock_time.return_value = mock_ny_time
            
            session = SessionStateMachine()
            buffer = CandleBuffer()
            
            session.update(buffer)
            
            assert session.state == SessionState.SESSION_CLOSED
            assert session.can_trade() == False
            print("✅ Test passed: Bot correctly skips session when starting at 9:35 AM")
    
    def test_startup_before_or_window_works_normally(self):
        """Test that starting before OR window works normally."""
        # Mock time to be 8:00 AM EST (before session start)
        mock_ny_time = datetime.datetime(2026, 1, 9, 8, 0, 0,
                                         tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        
        with patch('session_state.get_ny_time') as mock_time:
            mock_time.return_value = mock_ny_time
            
            session = SessionStateMachine()
            buffer = CandleBuffer()
            
            session.update(buffer)
            
            # Should be in PRE_OR state
            assert session.state == SessionState.PRE_OR
            assert session.can_trade() == False
            print("✅ Test passed: Bot correctly stays in PRE_OR when starting at 8:00 AM")
    
    def test_startup_during_or_building_works_normally(self):
        """Test that starting during OR building (9:30-9:34) works normally."""
        # Mock time to be 9:32 AM EST (during OR building)
        mock_ny_time = datetime.datetime(2026, 1, 9, 9, 32, 0,
                                         tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        
        with patch('session_state.get_ny_time') as mock_time:
            mock_time.return_value = mock_ny_time
            
            session = SessionStateMachine()
            buffer = CandleBuffer()
            
            session.update(buffer)
            
            # Should be in OR_BUILDING state
            assert session.state == SessionState.OR_BUILDING
            assert session.can_trade() == False
            print("✅ Test passed: Bot correctly enters OR_BUILDING when starting at 9:32 AM")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Running Mid-Day Startup Fix Tests")
    print("="*70 + "\n")
    
    test_suite = TestMidDayStartup()
    
    try:
        test_suite.test_startup_after_or_window_skips_session()
        test_suite.test_startup_at_or_lock_time_skips_session()
        test_suite.test_startup_before_or_window_works_normally()
        test_suite.test_startup_during_or_building_works_normally()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
