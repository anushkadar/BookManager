import pandas as pd
from datetime import datetime

def export_books_to_excel(book_rows):
    columns = [
        "ID", "Title", "Author", "Translator", "Publisher",
        "Publication Date", "ISBN", "Language", "Genre",
        "Pages", "Edition", "Status"
    ]
    df = pd.DataFrame(book_rows, columns=columns)
    filename = f"book_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False)
    return filename
