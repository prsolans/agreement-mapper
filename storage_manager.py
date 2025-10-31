"""
Storage Manager: Local file-based storage for company analyses
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class StorageManager:
    """Manages local JSON file storage for company analyses"""

    def __init__(self, storage_dir: str = "analyses"):
        """
        Initialize storage manager

        Args:
            storage_dir: Directory to store analysis files
        """
        self.storage_dir = Path(storage_dir)
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """Create storage directory if it doesn't exist"""
        self.storage_dir.mkdir(exist_ok=True)

    def _generate_filename(self, company_name: str, timestamp: Optional[str] = None) -> str:
        """
        Generate filename for analysis

        Args:
            company_name: Name of the company
            timestamp: Optional timestamp string, defaults to now

        Returns:
            Filename string
        """
        # Clean company name for filename
        clean_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in company_name)
        clean_name = clean_name.replace(' ', '_').lower()

        # Generate timestamp
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{clean_name}_{timestamp}.json"

    def save_analysis(self, company_name: str, analysis_data: Dict) -> str:
        """
        Save analysis to JSON file

        Args:
            company_name: Name of the company
            analysis_data: Analysis data dictionary

        Returns:
            Path to saved file
        """
        filename = self._generate_filename(company_name)
        filepath = self.storage_dir / filename

        # Add storage metadata
        analysis_data['_storage'] = {
            'filename': filename,
            'saved_at': datetime.now().isoformat(),
            'version': '1.0'
        }

        with open(filepath, 'w') as f:
            json.dump(analysis_data, f, indent=2)

        return str(filepath)

    def list_analyses(self) -> List[Dict]:
        """
        List all saved analyses

        Returns:
            List of analysis metadata dicts with keys:
            - filename: File name
            - company_name: Company name
            - analysis_date: When analysis was created
            - saved_at: When file was saved
            - file_size: Size in bytes
        """
        analyses = []

        for filepath in sorted(self.storage_dir.glob("*.json"), reverse=True):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)

                meta = data.get('_meta', {})
                storage = data.get('_storage', {})

                analyses.append({
                    'filename': filepath.name,
                    'filepath': str(filepath),
                    'company_name': meta.get('company_name', 'Unknown'),
                    'analysis_date': meta.get('analysis_date', 'Unknown'),
                    'saved_at': storage.get('saved_at', 'Unknown'),
                    'file_size': filepath.stat().st_size,
                    'display_name': f"{meta.get('company_name', 'Unknown')} - {meta.get('analysis_date', 'Unknown')}"
                })
            except Exception as e:
                # Skip invalid files
                print(f"Error reading {filepath}: {e}")
                continue

        return analyses

    def load_analysis(self, filename: str) -> Optional[Dict]:
        """
        Load analysis from file

        Args:
            filename: Name of the file to load

        Returns:
            Analysis data dict or None if not found
        """
        filepath = self.storage_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None

    def update_analysis(self, filename: str, updated_data: Dict) -> bool:
        """
        Update existing analysis file

        Args:
            filename: Name of file to update
            updated_data: Updated analysis data

        Returns:
            True if successful, False otherwise
        """
        filepath = self.storage_dir / filename

        if not filepath.exists():
            return False

        try:
            # Update storage metadata
            if '_storage' not in updated_data:
                updated_data['_storage'] = {}

            updated_data['_storage']['updated_at'] = datetime.now().isoformat()
            updated_data['_storage']['filename'] = filename

            # Update _meta last_updated
            if '_meta' in updated_data:
                updated_data['_meta']['last_updated'] = datetime.now().strftime("%Y-%m-%d")

            with open(filepath, 'w') as f:
                json.dump(updated_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error updating {filepath}: {e}")
            return False

    def delete_analysis(self, filename: str) -> bool:
        """
        Delete analysis file

        Args:
            filename: Name of file to delete

        Returns:
            True if successful, False otherwise
        """
        filepath = self.storage_dir / filename

        if not filepath.exists():
            return False

        try:
            filepath.unlink()
            return True
        except Exception as e:
            print(f"Error deleting {filepath}: {e}")
            return False

    def search_analyses(self, query: str) -> List[Dict]:
        """
        Search analyses by company name

        Args:
            query: Search query string

        Returns:
            List of matching analysis metadata
        """
        all_analyses = self.list_analyses()
        query_lower = query.lower()

        return [
            analysis for analysis in all_analyses
            if query_lower in analysis['company_name'].lower()
        ]

    def get_analysis_by_company(self, company_name: str) -> List[Dict]:
        """
        Get all analyses for a specific company

        Args:
            company_name: Company name to search for

        Returns:
            List of analysis metadata for that company
        """
        return self.search_analyses(company_name)

    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics

        Returns:
            Dict with storage stats
        """
        analyses = self.list_analyses()
        total_size = sum(a['file_size'] for a in analyses)

        return {
            'total_analyses': len(analyses),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'storage_dir': str(self.storage_dir.absolute())
        }
