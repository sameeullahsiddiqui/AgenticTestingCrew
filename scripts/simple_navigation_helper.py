#!/usr/bin/env python3
"""
Simple Navigation Structure Helper
Extract navigation hints from seed_navigation.js to help LLM with page exploration.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class SimpleNavigationHelper:
    def __init__(self, seed_file_path: str = "scripts/seed_navigation.js"):
        self.seed_file = Path(seed_file_path)
        self.output_dir = Path("backend/fs_files/navigation_hints")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_navigation_hints(self) -> Dict:
        """Extract simple navigation hints from seed_navigation.js"""
        if not self.seed_file.exists():
            return {"error": "seed_navigation.js not found", "pages": [], "actions": []}
        
        try:
            with open(self.seed_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Could not read seed file: {e}", "pages": [], "actions": []}
        
        # Extract page.getByText() clicks - these are navigation elements
        text_clicks = re.findall(r"page\.getByText\(['\"]([^'\"]+)['\"](?:,\s*{\s*exact:\s*\w+\s*})?\)\.click\(\)", content)
        
        # Extract page.locator() clicks - these might be buttons/links
        locator_clicks = re.findall(r"page\.locator\(['\"]([^'\"]+)['\"](?:\.nth\(\d+\))?\)\.click\(\)", content)
        
        # Extract getByRole clicks
        role_clicks = re.findall(r"page\.getByRole\(['\"](\w+)['\"](?:,\s*{\s*name:\s*['\"]([^'\"]+)['\"].*?})?\)\.click\(\)", content)
        
        # Clean and organize the data
        pages = []
        actions = []
        
        # Process text-based navigation (likely menu items)
        for text in text_clicks:
            text = text.strip()
            if self._looks_like_navigation(text):
                pages.append({
                    "name": text,
                    "type": "menu_item", 
                    "selector": f"page.getByText('{text}').click()"
                })
            else:
                actions.append({
                    "name": text,
                    "type": "action_button",
                    "selector": f"page.getByText('{text}').click()"
                })
        
        # Process role-based clicks
        for role, name in role_clicks:
            if name:
                name = name.strip()
                if self._looks_like_navigation(name):
                    pages.append({
                        "name": name,
                        "type": "role_element",
                        "role": role,
                        "selector": f"page.getByRole('{role}', {{ name: '{name}' }}).click()"
                    })
                else:
                    actions.append({
                        "name": name,
                        "type": "role_action", 
                        "role": role,
                        "selector": f"page.getByRole('{role}', {{ name: '{name}' }}).click()"
                    })
        
        # Process locator-based clicks (buttons, specific elements)
        for locator in locator_clicks:
            actions.append({
                "name": locator,
                "type": "locator_click",
                "selector": f"page.locator('{locator}').click()"
            })
        
        # Remove duplicates
        pages = self._remove_duplicates(pages, "name")
        actions = self._remove_duplicates(actions, "name")
        
        return {
            "total_pages": len(pages),
            "total_actions": len(actions),
            "pages": pages,
            "actions": actions,
            "extracted_from": str(self.seed_file)
        }
    
    def _looks_like_navigation(self, text: str) -> bool:
        """Simple heuristic to determine if text looks like navigation"""
        # Skip obvious action words
        action_words = ['add', 'save', 'cancel', 'close', 'edit', 'delete', 'search', 'filter', 'export', 'import']
        if any(word in text.lower() for word in action_words):
            return False
        
        # Skip single characters and short text
        if len(text.strip()) <= 2:
            return False
        
        # Skip common UI elements
        ui_elements = ['×', 'ok', 'yes', 'no']
        if text.lower().strip() in ui_elements:
            return False
        
        # Assume it's navigation if it passed the above filters
        return True
    
    def _remove_duplicates(self, items: List[Dict], key: str) -> List[Dict]:
        """Remove duplicate items based on a key"""
        seen = set()
        result = []
        for item in items:
            if item[key] not in seen:
                seen.add(item[key])
                result.append(item)
        return result
    
    def save_navigation_hints(self) -> str:
        """Extract and save navigation hints to JSON file"""
        hints = self.extract_navigation_hints()
        
        output_file = self.output_dir / "navigation_hints.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(hints, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Navigation hints saved to: {output_file}")
            print(f"   📄 Pages found: {hints['total_pages']}")
            print(f"   🎯 Actions found: {hints['total_actions']}")
            
            return str(output_file)
            
        except Exception as e:
            print(f"❌ Failed to save navigation hints: {e}")
            return ""
    
    def get_navigation_summary_for_llm(self) -> str:
        """Get a simple text summary for LLM prompts"""
        hints = self.extract_navigation_hints()
        
        if hints.get("error"):
            return f"Navigation hints error: {hints['error']}"
        
        summary_parts = []
        
        if hints["pages"]:
            page_names = [p["name"] for p in hints["pages"]]
            summary_parts.append(f"Main navigation pages: {', '.join(page_names)}")
        
        if hints["actions"]:
            action_names = [a["name"] for a in hints["actions"][:10]]  # Limit to first 10
            summary_parts.append(f"Common actions: {', '.join(action_names)}")
        
        return " | ".join(summary_parts) if summary_parts else "No navigation hints available"


def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract navigation hints from seed_navigation.js")
    parser.add_argument("--seed-file", default="scripts/seed_navigation.js", 
                       help="Path to seed_navigation.js file")
    parser.add_argument("--summary-only", action="store_true",
                       help="Only print summary for LLM")
    
    args = parser.parse_args()
    
    helper = SimpleNavigationHelper(args.seed_file)
    
    if args.summary_only:
        print(helper.get_navigation_summary_for_llm())
    else:
        output_file = helper.save_navigation_hints()
        if output_file:
            print(f"\n📋 Summary for LLM:")
            print(helper.get_navigation_summary_for_llm())


if __name__ == "__main__":
    main()
