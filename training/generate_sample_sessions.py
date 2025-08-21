#!/usr/bin/env python3
"""
Generate Sample Discovery Sessions for Real Data Training
Creates sample discovery sessions to demonstrate real data training
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

async def generate_sample_sessions():
    """Generate sample discovery sessions for real data training"""
    
    print("🎯 Generating Sample Discovery Sessions for Real Data Training")
    print("=" * 65)
    
    try:
        from backend.crew_orchestrator import CrewOrchestrator
        
        # Sample applications to test
        test_applications = [
            {
                "url": "https://www.saucedemo.com/",
                "description": "E-commerce demo application"
            },
            {
                "url": "https://petstore.swagger.io/",
                "description": "API documentation site"  
            },
            {
                "url": "https://httpbin.org/",
                "description": "HTTP testing service"
            }
        ]
        
        print(f"📋 Will generate {len(test_applications)} sample sessions:")
        for i, app in enumerate(test_applications, 1):
            print(f"   {i}. {app['url']} - {app['description']}")
        
        print("\n🚀 Starting sample session generation...")
        
        results = []
        
        for i, app in enumerate(test_applications, 1):
            print(f"\n📍 Session {i}/{len(test_applications)}: {app['url']}")
            
            # Create unique test run ID
            test_run_id = f"sample_session_{datetime.now():%Y%m%d_%H%M%S}_{i}"
            
            # Initialize orchestrator
            orchestrator = CrewOrchestrator(test_run_id=test_run_id)
            
            # Test inputs
            inputs = {
                "BASE_URL": app["url"],
                "INSTRUCTIONS": f"Discover and map {app['description']} for real data training",
                "FORCE": False,
                "HEADLESS": False,
                "TEST_RUN_ID": test_run_id,
                "PHASES": ["exploration"]  # Just exploration for training data
            }
            
            print(f"   🔍 Starting discovery of {app['url']}...")
            
            try:
                # Run discovery session
                result = await orchestrator.run_pipeline(inputs, False)
                
                if result:
                    print(f"   ✅ Session completed: {test_run_id}")
                    results.append({
                        "test_run_id": test_run_id,
                        "url": app["url"],
                        "status": "completed",
                        "result": result
                    })
                else:
                    print(f"   ⚠️  Session completed with issues: {test_run_id}")
                    results.append({
                        "test_run_id": test_run_id,
                        "url": app["url"], 
                        "status": "completed_with_issues",
                        "result": None
                    })
                    
            except Exception as e:
                print(f"   ❌ Session failed: {e}")
                results.append({
                    "test_run_id": test_run_id,
                    "url": app["url"],
                    "status": "failed", 
                    "error": str(e)
                })
                
            print(f"   📁 Session data saved to: backend/fs_files/{test_run_id}/")
        
        # Summary
        print(f"\n📊 Session Generation Summary:")
        completed = [r for r in results if r["status"] == "completed"]
        issues = [r for r in results if r["status"] == "completed_with_issues"]
        failed = [r for r in results if r["status"] == "failed"]
        
        print(f"   ✅ Successful sessions: {len(completed)}")
        print(f"   ⚠️  Sessions with issues: {len(issues)}")
        print(f"   ❌ Failed sessions: {len(failed)}")
        
        if completed or issues:
            print(f"\n🎉 Generated {len(completed + issues)} sessions for real data training!")
            print("\n🚀 Next Steps:")
            print("1. Run real data collection: python real_data_training.py")
            print("2. Analyze the collected data quality")
            print("3. Run enhanced training: python enhanced_real_data_training.py")
            print("4. Deploy the improved model")
            
            return True
        else:
            print(f"\n❌ No successful sessions generated")
            print("Check your network connection and try again")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the correct directory")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def quick_discovery_test():
    """Quick test to verify discovery system is working"""
    
    print("🔍 Quick Discovery System Test")
    print("-" * 30)
    
    try:
        from backend.crew_test_explorer import ExplorationCrew
        
        test_run_id = f"quick_test_{datetime.now():%Y%m%d_%H%M%S}"
        
        print(f"Creating test crew for: {test_run_id}")
        
        # Test with a simple, fast site
        crew = await ExplorationCrew.create(test_run_id, "https://httpbin.org/")
        
        print("✅ Crew created successfully")
        print("✅ Discovery system is ready for sample sessions")
        
        return True
        
    except Exception as e:
        print(f"❌ Discovery system test failed: {e}")
        return False

def main():
    """Main function"""
    
    print("🎯 Sample Session Generator for Real Data Training")
    print("This will create sample discovery sessions for training data collection")
    print("\n" + "=" * 70)
    
    # Quick system check
    print("🔧 Checking discovery system...")
    system_ready = asyncio.run(quick_discovery_test())
    
    if not system_ready:
        print("\n❌ Discovery system check failed")
        print("Please check your configuration and try again")
        return
    
    print("\n" + "=" * 70)
    print("⚠️  IMPORTANT NOTES:")
    print("• This will generate real discovery sessions")
    print("• Each session may take 3-10 minutes to complete")
    print("• Sessions will create data in backend/fs_files/")
    print("• You can stop anytime with Ctrl+C")
    print("=" * 70)
    
    response = input("\nProceed with sample session generation? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        print("\n🚀 Starting sample session generation...")
        success = asyncio.run(generate_sample_sessions())
        
        if success:
            print("\n🎊 Sample sessions generated successfully!")
            print("You now have real data for training!")
        else:
            print("\n❌ Sample session generation failed")
    else:
        print("\n✅ Cancelled by user")
        print("\n💡 Alternative: Run manual discovery sessions:")
        print("1. Start backend: python backend/main.py")
        print("2. Use frontend to run discovery sessions") 
        print("3. Or run orchestrator directly: python backend/crew_orchestrator.py")

if __name__ == "__main__":
    main()
