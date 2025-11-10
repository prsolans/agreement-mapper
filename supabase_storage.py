"""
Supabase Storage Manager for Agreement Map
Provides persistent storage for company analyses using Supabase PostgreSQL + JSONB
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import json


class SupabaseStorageManager:
    """Manages storage of company analyses in Supabase"""

    def __init__(self):
        """Initialize Supabase connection"""
        self.client = None
        self.table_name = "analyses"

        try:
            # Try to get Supabase credentials from Streamlit secrets
            if hasattr(st, 'secrets') and 'supabase' in st.secrets:
                from supabase import create_client

                url = st.secrets['supabase']['url']
                key = st.secrets['supabase']['key']

                self.client = create_client(url, key)
                print("Supabase storage initialized successfully")
            else:
                print("Supabase credentials not found in secrets")

        except Exception as e:
            print(f"Supabase initialization failed: {e}")
            self.client = None

    def is_configured(self) -> bool:
        """Check if Supabase is properly configured"""
        return self.client is not None

    def save_analysis(self, company_name: str, analysis_data: Dict) -> bool:
        """
        Save analysis to Supabase

        Args:
            company_name: Name of the company
            analysis_data: Complete analysis dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            print("Supabase not configured - cannot save")
            return False

        try:
            # Prepare data for insertion
            record = {
                "company_name": company_name,
                "timestamp": datetime.now().isoformat(),
                "analysis_json": analysis_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Insert into Supabase
            response = self.client.table(self.table_name).insert(record).execute()

            if response.data:
                print(f"Successfully saved analysis for {company_name}")
                return True
            else:
                print(f"Failed to save analysis: {response}")
                return False

        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return False

    def list_analyses(self) -> List[Dict]:
        """
        List all saved analyses

        Returns:
            List of dicts with analysis metadata:
            [
                {
                    "id": "uuid",
                    "company_name": "Company Name",
                    "timestamp": "2024-01-01T00:00:00",
                    "display_name": "Company Name (Jan 01, 2024)"
                },
                ...
            ]
        """
        if not self.is_configured():
            return []

        try:
            # Query all analyses, ordered by most recent first
            response = self.client.table(self.table_name)\
                .select("id, company_name, timestamp, created_at")\
                .order("created_at", desc=True)\
                .execute()

            if not response.data:
                return []

            # Format results
            analyses = []
            for row in response.data:
                # Parse timestamp for display
                try:
                    ts = datetime.fromisoformat(row['timestamp'])
                    date_str = ts.strftime("%b %d, %Y")
                except:
                    date_str = "Unknown date"

                analyses.append({
                    "id": row['id'],
                    "company_name": row['company_name'],
                    "timestamp": row['timestamp'],
                    "display_name": f"{row['company_name']} ({date_str})"
                })

            return analyses

        except Exception as e:
            print(f"Error listing analyses from Supabase: {e}")
            return []

    def load_analysis(self, analysis_id: str) -> Optional[Dict]:
        """
        Load a specific analysis by ID

        Args:
            analysis_id: UUID of the analysis to load

        Returns:
            Analysis dictionary or None if not found
        """
        if not self.is_configured():
            return None

        try:
            # Query by ID
            response = self.client.table(self.table_name)\
                .select("analysis_json")\
                .eq("id", analysis_id)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['analysis_json']
            else:
                print(f"Analysis not found: {analysis_id}")
                return None

        except Exception as e:
            print(f"Error loading analysis from Supabase: {e}")
            return None

    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete an analysis by ID

        Args:
            analysis_id: UUID of the analysis to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            return False

        try:
            # Delete by ID
            response = self.client.table(self.table_name)\
                .delete()\
                .eq("id", analysis_id)\
                .execute()

            print(f"Deleted analysis: {analysis_id}")
            return True

        except Exception as e:
            print(f"Error deleting analysis from Supabase: {e}")
            return False

    def search_analyses(self, search_term: str) -> List[Dict]:
        """
        Search analyses by company name

        Args:
            search_term: Company name to search for

        Returns:
            List of matching analyses
        """
        if not self.is_configured():
            return []

        try:
            # Search by company name (case insensitive)
            response = self.client.table(self.table_name)\
                .select("id, company_name, timestamp, created_at")\
                .ilike("company_name", f"%{search_term}%")\
                .order("created_at", desc=True)\
                .execute()

            if not response.data:
                return []

            # Format results
            analyses = []
            for row in response.data:
                try:
                    ts = datetime.fromisoformat(row['timestamp'])
                    date_str = ts.strftime("%b %d, %Y")
                except:
                    date_str = "Unknown date"

                analyses.append({
                    "id": row['id'],
                    "company_name": row['company_name'],
                    "timestamp": row['timestamp'],
                    "display_name": f"{row['company_name']} ({date_str})"
                })

            return analyses

        except Exception as e:
            print(f"Error searching analyses in Supabase: {e}")
            return []

    def update_analysis(self, analysis_id: str, analysis_data: Dict) -> bool:
        """
        Update an existing analysis

        Args:
            analysis_id: UUID of the analysis to update
            analysis_data: Updated analysis dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            return False

        try:
            # Update record
            response = self.client.table(self.table_name)\
                .update({
                    "analysis_json": analysis_data,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("id", analysis_id)\
                .execute()

            if response.data:
                print(f"Successfully updated analysis: {analysis_id}")
                return True
            else:
                print(f"Failed to update analysis: {response}")
                return False

        except Exception as e:
            print(f"Error updating analysis in Supabase: {e}")
            return False
