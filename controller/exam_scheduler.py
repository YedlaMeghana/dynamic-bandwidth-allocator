"""
Exam Mode Scheduler for Dynamic Bandwidth Allocator

This module handles time-based priority switching for exam scenarios.
During exams, lab computers get higher priority than faculty.
"""

import schedule
import time
from datetime import datetime
import json
import os

class ExamScheduler:
    """
    Manages exam mode scheduling and priority changes.
    
    Exam Mode:
    - Lab priority increases (60 Mbps)
    - Faculty priority decreases (20 Mbps)
    - Automatically reverts after exam ends
    """
    
    def __init__(self, controller):
        """
        Initialize exam scheduler.
        
        Args:
            controller: Reference to DynamicBWAllocator controller instance
        """
        self.controller = controller
        self.exam_active = False
        self.schedule_file = '/tmp/exam_schedule.json'
        self.load_schedule()
        
    def load_schedule(self):
        """Load exam schedule from file if exists."""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r') as f:
                    self.schedules = json.load(f)
            except:
                self.schedules = []
        else:
            self.schedules = []
    
    def save_schedule(self):
        """Save current schedule to file."""
        with open(self.schedule_file, 'w') as f:
            json.dump(self.schedules, f)
    
    def schedule_exam(self, start_time, end_time, name="Exam"):
        """
        Schedule an exam mode session.
        
        Args:
            start_time: Start time in "HH:MM" format (e.g., "09:00")
            end_time: End time in "HH:MM" format (e.g., "12:00")
            name: Name/description of exam (optional)
        
        Returns:
            dict: Schedule confirmation
        """
        # Validate time format
        try:
            datetime.strptime(start_time, "%H:%M")
            datetime.strptime(end_time, "%H:%M")
        except ValueError:
            return {"error": "Invalid time format. Use HH:MM"}
        
        # Add to schedule
        exam_schedule = {
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "active": False
        }
        
        self.schedules.append(exam_schedule)
        self.save_schedule()
        
        # Schedule with schedule library
        schedule.every().day.at(start_time).do(self.start_exam, name)
        schedule.every().day.at(end_time).do(self.end_exam, name)
        
        return {
            "status": "scheduled",
            "exam": name,
            "start": start_time,
            "end": end_time
        }
    
    def start_exam(self, exam_name="Exam"):
        """
        Enter exam mode: Increase lab priority, decrease faculty.
        
        Args:
            exam_name: Name of exam starting
        """
        self.exam_active = True
        
        print(f"\n{'='*60}")
        print(f"EXAM MODE ACTIVATED: {exam_name}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Update bandwidth allocations for exam mode
        exam_bandwidth = {
            'lab': 60,      # Increased from 30 to 60 Mbps
            'faculty': 20,  # Decreased from 40 to 20 Mbps
            'student': 5    # Remains same
        }
        
        # Update priorities
        exam_priority = {
            'lab': 3,       # Highest priority
            'faculty': 2,   # Medium priority
            'student': 1    # Lowest priority
        }
        
        # Update controller configuration
        if hasattr(self.controller, 'update_bandwidth_config'):
            self.controller.update_bandwidth_config(exam_bandwidth)
        
        if hasattr(self.controller, 'update_priority_config'):
            self.controller.update_priority_config(exam_priority)
        
        # Force rule reinstallation with new priorities
        if hasattr(self.controller, 'reinstall_all_flows'):
            self.controller.reinstall_all_flows()
        
        # Update status in schedule file
        for sched in self.schedules:
            if sched['name'] == exam_name:
                sched['active'] = True
        self.save_schedule()
        
        # Log to file
        self._log_mode_change("EXAM MODE START", exam_name, exam_bandwidth)
    
    def end_exam(self, exam_name="Exam"):
        """
        Exit exam mode: Restore normal priorities.
        
        Args:
            exam_name: Name of exam ending
        """
        self.exam_active = False
        
        print(f"\n{'='*60}")
        print(f"EXAM MODE DEACTIVATED: {exam_name}")
        print(f"Returning to normal mode")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Restore normal bandwidth allocations
        normal_bandwidth = {
            'faculty': 40,  # Restored to 40 Mbps
            'lab': 30,      # Restored to 30 Mbps
            'student': 5    # Unchanged
        }
        
        # Restore normal priorities
        normal_priority = {
            'faculty': 3,   # Highest priority
            'lab': 2,       # Medium priority
            'student': 1    # Lowest priority
        }
        
        # Update controller configuration
        if hasattr(self.controller, 'update_bandwidth_config'):
            self.controller.update_bandwidth_config(normal_bandwidth)
        
        if hasattr(self.controller, 'update_priority_config'):
            self.controller.update_priority_config(normal_priority)
        
        # Force rule reinstallation with normal priorities
        if hasattr(self.controller, 'reinstall_all_flows'):
            self.controller.reinstall_all_flows()
        
        # Update status in schedule file
        for sched in self.schedules:
            if sched['name'] == exam_name:
                sched['active'] = False
        self.save_schedule()
        
        # Log to file
        self._log_mode_change("EXAM MODE END", exam_name, normal_bandwidth)
    
    def activate_exam_mode_now(self):
        """Manually activate exam mode immediately (for testing/emergency)."""
        self.start_exam("Manual Activation")
    
    def deactivate_exam_mode_now(self):
        """Manually deactivate exam mode immediately."""
        self.end_exam("Manual Deactivation")
    
    def is_exam_active(self):
        """
        Check if exam mode is currently active.
        
        Returns:
            bool: True if in exam mode, False otherwise
        """
        return self.exam_active
    
    def get_current_schedule(self):
        """
        Get current exam schedule.
        
        Returns:
            list: List of scheduled exams
        """
        return self.schedules
    
    def clear_schedule(self):
        """Clear all scheduled exams."""
        self.schedules = []
        self.save_schedule()
        schedule.clear()
        return {"status": "cleared"}
    
    def _log_mode_change(self, event, exam_name, bandwidth_config):
        """
        Log mode changes to file for debugging and demo.
        
        Args:
            event: Event type (START/END)
            exam_name: Name of exam
            bandwidth_config: Current bandwidth configuration
        """
        log_file = '/tmp/exam_mode.log'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        log_entry = {
            "timestamp": timestamp,
            "event": event,
            "exam": exam_name,
            "bandwidth": bandwidth_config
        }
        
        try:
            # Append to log file
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except:
            pass  # Ignore logging errors
    
    def run_scheduler(self):
        """
        Run the scheduler loop (call this in a separate thread).
        Checks every minute if any scheduled exams should start/end.
        """
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


# Example usage (for testing)
if __name__ == "__main__":
    # Mock controller for testing
    class MockController:
        def update_bandwidth_config(self, config):
            print(f"Updated bandwidth: {config}")
        
        def update_priority_config(self, config):
            print(f"Updated priority: {config}")
        
        def reinstall_all_flows(self):
            print("Reinstalled all flows")
    
    controller = MockController()
    scheduler = ExamScheduler(controller)
    
    # Schedule an exam from 09:00 to 12:00
    result = scheduler.schedule_exam("09:00", "12:00", "Mid-term Exam")
    print(f"Schedule result: {result}")
    
    # Manual test
    print("\nTesting manual activation...")
    scheduler.activate_exam_mode_now()
    time.sleep(2)
    scheduler.deactivate_exam_mode_now()
    
    print("\nScheduler ready. Current schedule:")
    print(scheduler.get_current_schedule())
