"""
Tests for the DroneWorker class
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from drone_worker import DroneWorker, DroneWorkerSignals


class TestDroneWorkerSignals:
    """Test the DroneWorkerSignals class"""
    
    def test_signals_initialization(self):
        """Test that signals are properly initialized"""
        signals = DroneWorkerSignals()
        
        # Check that all expected signals exist
        assert hasattr(signals, 'frame_ready')
        assert hasattr(signals, 'telemetry_updated')
        assert hasattr(signals, 'status_message')
        assert hasattr(signals, 'mission_finished')
        assert hasattr(signals, 'connection_status')
        assert hasattr(signals, 'mission_started')


class TestDroneWorker:
    """Test the DroneWorker class"""
    
    def test_worker_initialization(self):
        """Test that DroneWorker initializes correctly"""
        worker = DroneWorker()
        
        # Check that required attributes are set
        assert worker.path_model_path == "epoch50.pt"
        assert worker.pad_model_path == "best_pad_new.pt"
        assert worker.target_pad_id == 5
        assert hasattr(worker, 'signals')
        assert hasattr(worker, 'control_loop_timer')
    
    def test_worker_with_custom_paths(self):
        """Test DroneWorker with custom model paths"""
        custom_path = "custom_path.pt"
        custom_pad = "custom_pad.pt"
        
        worker = DroneWorker(
            path_model_path=custom_path,
            pad_model_path=custom_pad
        )
        
        assert worker.path_model_path == custom_path
        assert worker.pad_model_path == custom_pad
    
    def test_worker_flags_initialization(self):
        """Test that worker flags are properly initialized"""
        worker = DroneWorker()
        
        assert worker._start_segmentation is False
        assert worker._pad_mode is False
        assert worker._is_running is True
        assert worker._no_path_counter == 0
        assert worker._pad_height_adjusted is False
    
    def test_worker_methods_exist(self):
        """Test that all required methods exist"""
        worker = DroneWorker()
        
        # Check that all required methods exist
        assert hasattr(worker, 'run')
        assert hasattr(worker, 'start_drone_mission')
        assert hasattr(worker, 'land_drone')
        assert hasattr(worker, 'emergency_land')
        assert hasattr(worker, 'stop_worker')
        assert hasattr(worker, 'get_drone')
        assert hasattr(worker, 'get_path_model')
        assert hasattr(worker, 'get_pad_model')


if __name__ == "__main__":
    pytest.main([__file__]) 