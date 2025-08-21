#!/usr/bin/env python3
"""
Simple Recording Handler
Handles initial recording when URL is provided for the first time.
"""

import os
import subprocess
import sys
from pathlib import Path
import json


class SimpleRecordingHandler:
    def __init__(self, url: str):
        self.url = url
        self.output_file = Path("scripts/seed_navigation.js")
        self.auth_file = Path("scripts/auth_state.json")
    
    def needs_recording(self) -> bool:
        """Check if recording is needed (no existing seed file)"""
        return not self.output_file.exists()
    
    def start_recording(self) -> bool:
        """Start Playwright recording session"""
        if not self.needs_recording():
            print(f"✅ Recording already exists: {self.output_file}")
            return True
        
        print(f"🎬 Starting recording for: {self.url}")
        print("📝 Navigate through the application, then close the recorder window")
        
        try:
            # Use Playwright codegen to record interactions
            cmd = [
                sys.executable, "-m", "playwright", "codegen",
                "--target=javascript",
                f"--output={self.output_file}",
                f"--save-storage={self.auth_file}",
                self.url
            ]
            
            # Try to use Edge on Windows
            if os.name == "nt":
                cmd.insert(-1, "--channel=msedge")
            
            result = subprocess.run(cmd, capture_output=False)
            
            if result.returncode == 0 and self.output_file.exists():
                print(f"✅ Recording saved to: {self.output_file}")
                return True
            else:
                print(f"❌ Recording failed or no interactions recorded")
                return False
                
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get recording status"""
        return {
            "needs_recording": self.needs_recording(),
            "recording_exists": self.output_file.exists(),
            "auth_exists": self.auth_file.exists(),
            "recording_file": str(self.output_file),
            "auth_file": str(self.auth_file)
        }


def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Handle Playwright recording for URL")
    parser.add_argument("url", help="URL to record interactions for")
    parser.add_argument("--force", action="store_true", 
                       help="Force recording even if file exists")
    parser.add_argument("--status", action="store_true",
                       help="Show recording status only")
    
    args = parser.parse_args()
    
    handler = SimpleRecordingHandler(args.url)
    
    if args.status:
        status = handler.get_status()
        print(f"Recording Status:")
        print(f"  Needs recording: {status['needs_recording']}")
        print(f"  Recording file: {status['recording_file']}")
        print(f"  Auth file: {status['auth_file']}")
        return
    
    if args.force:
        # Remove existing files to force new recording
        handler.output_file.unlink(missing_ok=True)
        handler.auth_file.unlink(missing_ok=True)
    
    success = handler.start_recording()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
