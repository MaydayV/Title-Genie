import pandas as pd
import io

def load_file(file) -> pd.DataFrame:
    """Reads uploaded Excel or CSV file into a DataFrame."""
    try:
        filename = file.name.lower()
        if filename.endswith('.csv'):
            # Try differing encodings
            try:
                return pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                return pd.read_csv(file, encoding='latin1')
        else:
            return pd.read_excel(file)
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

def export_excel(df: pd.DataFrame) -> bytes:
    """Converts DataFrame to an Excel file in bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()
