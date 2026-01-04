"""
Title History Manager - Manages historical title database for cross-library deduplication.
"""

import json
import os
import difflib
from datetime import datetime
from typing import List, Tuple, Optional

# Default path for the history file
DEFAULT_HISTORY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "title_history.json")


class TitleHistoryManager:
    """
    Manages a persistent store of generated titles for cross-library deduplication.
    """
    
    def __init__(self, history_path: str = None):
        """
        Initialize the manager with a path to the history file.
        
        Args:
            history_path: Path to the JSON file storing title history.
        """
        self.history_path = history_path or DEFAULT_HISTORY_PATH
        self.titles: List[dict] = []
        self.load_history()
    
    def load_history(self) -> None:
        """Load title history from JSON file."""
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.titles = data.get('titles', [])
            except (json.JSONDecodeError, IOError):
                self.titles = []
        else:
            self.titles = []
    
    def save_history(self) -> None:
        """Save title history to JSON file."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.titles),
                'titles': self.titles
            }
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (IOError, OSError, PermissionError) as e:
            # Silently handle errors (e.g., read-only filesystem on Streamlit Cloud)
            pass
    
    def add_title(self, title: str, brand: str = "", product_id: str = "") -> None:
        """
        Add a new title to the history.
        
        Args:
            title: The generated title
            brand: Brand name (optional)
            product_id: Product identifier (optional)
        """
        self.titles.append({
            'title': title,
            'title_lower': title.lower(),  # Pre-compute for faster comparison
            'brand': brand,
            'product_id': product_id,
            'created_at': datetime.now().isoformat()
        })
    
    def add_titles(self, titles: List[str], brand: str = "", product_id: str = "") -> None:
        """
        Add multiple titles to the history.
        
        Args:
            titles: List of generated titles
            brand: Brand name (optional)
            product_id: Product identifier (optional)
        """
        for title in titles:
            self.add_title(title, brand, product_id)
    
    def get_all_titles(self) -> List[str]:
        """Get all titles as a simple list."""
        return [t['title'] for t in self.titles]
    
    def get_all_titles_lower(self) -> List[str]:
        """Get all titles in lowercase for comparison."""
        return [t.get('title_lower', t['title'].lower()) for t in self.titles]
    
    def check_similarity(self, new_title: str, threshold: float = 0.8) -> Tuple[bool, float, Optional[str]]:
        """
        Check if a new title is too similar to any existing title in the history.
        
        Args:
            new_title: The title to check
            threshold: Similarity threshold (0-1), default 0.8
            
        Returns:
            Tuple of (is_duplicate, max_similarity_score, most_similar_title)
        """
        if not self.titles:
            return False, 0.0, None
        
        new_lower = new_title.lower()
        max_score = 0.0
        most_similar = None
        
        for record in self.titles:
            existing_lower = record.get('title_lower', record['title'].lower())
            score = difflib.SequenceMatcher(None, new_lower, existing_lower).ratio()
            if score > max_score:
                max_score = score
                most_similar = record['title']
        
        return max_score > threshold, max_score, most_similar
    
    def clear_history(self) -> None:
        """Clear all title history."""
        self.titles = []
    
    def get_stats(self) -> dict:
        """Get statistics about the title history."""
        return {
            'total_titles': len(self.titles),
            'history_path': self.history_path,
            'file_exists': os.path.exists(self.history_path)
        }
    
    def import_from_csv(self, file_path: str, title_column: str = 'title') -> int:
        """
        Import titles from a CSV file.
        
        Args:
            file_path: Path to CSV file
            title_column: Name of the column containing titles
            
        Returns:
            Number of titles imported
        """
        import pandas as pd
        try:
            df = pd.read_csv(file_path)
            if title_column in df.columns:
                count = 0
                for title in df[title_column].dropna():
                    self.add_title(str(title))
                    count += 1
                return count
            return 0
        except Exception:
            return 0
    
    def import_from_excel(self, file, title_column: str = 'title') -> int:
        """
        Import titles from an Excel file (supports file-like object).
        
        Args:
            file: File path or file-like object
            title_column: Name of the column containing titles
            
        Returns:
            Number of titles imported
        """
        import pandas as pd
        try:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip().str.lower()
            
            # Try common column names
            possible_cols = [title_column.lower(), 'title', 'product name', 'product title', '标题']
            found_col = None
            for col in possible_cols:
                if col in df.columns:
                    found_col = col
                    break
            
            if found_col:
                count = 0
                for title in df[found_col].dropna():
                    self.add_title(str(title))
                    count += 1
                return count
            return 0
        except Exception:
            return 0
