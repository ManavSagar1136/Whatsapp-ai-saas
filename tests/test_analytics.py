import pytest
from unittest.mock import patch, MagicMock
from backend.celery_beat import aggregate_daily_analytics
from datetime import datetime, timedelta

@patch('backend.celery_beat.supabase')
def test_analytics_aggregation_job(mock_supabase):
    """Test the nightly cron job successfully aggregates business stats."""
    
    # Mock businesses
    mock_supabase.table().select().execute.return_value = MagicMock(data=[{"id": "b-123"}])
    
    # Needs complex nested mocking for the chained supabase calls,
    # Here we mock the upsert to ensure it triggers correctly.
    mock_upsert = MagicMock()
    mock_supabase.table().upsert.return_value.execute = mock_upsert
    
    # Fire the job manually
    result = aggregate_daily_analytics()
    
    # Ensure it processes and triggers an upsert attempting loop
    assert result == "success"
    assert mock_supabase.table().upsert.called
