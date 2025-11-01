"""
Google Sheets Storage Manager: Store and retrieve company analyses
"""
import json
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


class SheetsStorageManager:
    """Manages Google Sheets storage for company analyses"""

    def __init__(self):
        """Initialize the sheets storage manager"""
        self.connection = None
        self._init_connection()

    def _init_connection(self):
        """Initialize Google Sheets connection"""
        try:
            from st_gsheets_connection import GSheetsConnection
            self.connection = st.connection("gsheets", type=GSheetsConnection)
        except Exception as e:
            # Silently fail if not configured - this is optional
            self.connection = None

    def is_configured(self) -> bool:
        """Check if Google Sheets is properly configured"""
        return self.connection is not None

    def save_analysis(self, company_name: str, analysis_data: Dict) -> bool:
        """
        Save analysis to Google Sheets

        Args:
            company_name: Name of the company
            analysis_data: Analysis data dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            return False

        try:
            # Add metadata
            timestamp = datetime.now().isoformat()

            # Read existing data
            try:
                df = self.connection.read(worksheet="analyses")
                if df is None or df.empty:
                    df = pd.DataFrame(columns=['company_name', 'timestamp', 'analysis_json'])
            except:
                df = pd.DataFrame(columns=['company_name', 'timestamp', 'analysis_json'])

            # Create new row
            new_row = pd.DataFrame([{
                'company_name': company_name,
                'timestamp': timestamp,
                'analysis_json': json.dumps(analysis_data)
            }])

            # Append to dataframe
            df = pd.concat([df, new_row], ignore_index=True)

            # Write back to sheet
            self.connection.update(worksheet="analyses", data=df)

            return True

        except Exception as e:
            st.error(f"Error saving to Google Sheets: {str(e)}")
            return False

    def list_analyses(self) -> List[Dict]:
        """
        List all saved analyses

        Returns:
            List of analysis metadata dicts
        """
        if not self.is_configured():
            return []

        try:
            df = self.connection.read(worksheet="analyses")

            if df is None or df.empty:
                return []

            analyses = []
            for idx, row in df.iterrows():
                try:
                    # Parse the JSON to get metadata
                    analysis_data = json.loads(row['analysis_json'])
                    meta = analysis_data.get('_meta', {})

                    analyses.append({
                        'row_index': idx,
                        'company_name': row['company_name'],
                        'timestamp': row['timestamp'],
                        'analysis_date': meta.get('analysis_date', 'Unknown'),
                        'display_name': f"{row['company_name']} - {row['timestamp'][:10]}"
                    })
                except Exception as e:
                    continue

            # Sort by timestamp descending
            analyses.sort(key=lambda x: x['timestamp'], reverse=True)

            return analyses

        except Exception as e:
            st.error(f"Error listing analyses: {str(e)}")
            return []

    def load_analysis(self, row_index: int) -> Optional[Dict]:
        """
        Load analysis from Google Sheets

        Args:
            row_index: Row index in the dataframe

        Returns:
            Analysis data dict or None if not found
        """
        if not self.is_configured():
            return None

        try:
            df = self.connection.read(worksheet="analyses")

            if df is None or df.empty or row_index >= len(df):
                return None

            row = df.iloc[row_index]
            analysis_data = json.loads(row['analysis_json'])

            return analysis_data

        except Exception as e:
            st.error(f"Error loading analysis: {str(e)}")
            return None

    def delete_analysis(self, row_index: int) -> bool:
        """
        Delete analysis from Google Sheets

        Args:
            row_index: Row index in the dataframe

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            return False

        try:
            df = self.connection.read(worksheet="analyses")

            if df is None or df.empty or row_index >= len(df):
                return False

            # Drop the row
            df = df.drop(index=row_index).reset_index(drop=True)

            # Write back
            self.connection.update(worksheet="analyses", data=df)

            return True

        except Exception as e:
            st.error(f"Error deleting analysis: {str(e)}")
            return False

    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics

        Returns:
            Dict with storage stats
        """
        if not self.is_configured():
            return {
                'total_analyses': 0,
                'configured': False
            }

        try:
            df = self.connection.read(worksheet="analyses")

            if df is None or df.empty:
                return {
                    'total_analyses': 0,
                    'configured': True
                }

            return {
                'total_analyses': len(df),
                'configured': True,
                'storage_type': 'Google Sheets'
            }

        except Exception as e:
            return {
                'total_analyses': 0,
                'configured': False,
                'error': str(e)
            }
