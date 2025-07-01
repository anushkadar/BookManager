import sys
import os

# Add 'flet/' to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "flet"))

# ✅ Add current folder (project root) to sys.path
sys.path.insert(0, os.path.dirname(__file__))

import flet as ft
from flet.core import colors

# Now this works reliably
from db import create_tables, get_books, insert_book, update_book, delete_book, search_books, export_books, \
    get_copy_summary, update_inventory


def main(page: ft.Page):
    page.title = "Book Manager"
    page.window_width = 1500
    page.window_height = 1000
    page.window_full_screen = True
    page.vertical_alignment = ft.MainAxisAlignment.START
    create_tables()

    selected_book_id = None
    books_cache = []
    current_page = 1
    page_size = 100
    show_form = False

    fields = {
        'book_number': ft.TextField(label="Book Number", hint_text="e.g. 12345"),
        'title': ft.TextField(label="Title"),
        'author': ft.TextField(label="Author"),
        'translator': ft.TextField(label="Translator"),
        'pub_date': ft.TextField(label="Publication Date", hint_text="YYYY-MM-DD"),
        'isbn': ft.TextField(label="ISBN"),
        'language': ft.TextField(label="Language"),
        'genre': ft.TextField(label="Genre"),
        'edition': ft.TextField(label="Edition"),
        'status': ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Not Available"),
                ft.dropdown.Option("Missing")
            ],
            value="Available"
        )
    }

    def clear_fields(e=None):
        nonlocal selected_book_id
        selected_book_id = None

        for k, field in fields.items():
            field.value = "" if isinstance(field, ft.TextField) else "Available"
            field.border_color = None  # ✅ Clear red border

        page.update()

    def fill_form(book):
        nonlocal selected_book_id, show_form
        selected_book_id = book[0]
        show_form = True
        form_section.visible = True

        keys = list(fields.keys())
        for key, value in zip(keys, book[1:]):
            # Always convert value to string before assigning to TextField
            fields[key].value = str(value) if value is not None else ""

        page.update()


    def parse_book_form():
        data = {}
        error_fields = []

        for k, f in fields.items():
            val = f.value
            if k == "book_number":
                try:
                    data[k] = int(val.strip()) if val and str(val).strip().isdigit() else None
                except:
                    data[k] = None
            else:
                data[k] = val.strip() if isinstance(val, str) else ""

        # Validate required fields
        if not data["title"]:
            error_fields.append("title")
        if not data["author"]:
            error_fields.append("author")
        if data["book_number"] is None:
            error_fields.append("book_number")

        return data, error_fields

    def highlight_errors(field_names):
        for k in fields:
            fields[k].border_color = None  # reset
        for k in field_names:
            fields[k].border_color = "red"

    def handle_add_or_update(e):
        data, error_fields = parse_book_form()

        if error_fields:
            highlight_errors(error_fields)
            show_snack_bar("Please fill all required fields.")
            page.update()
            return

        try:
            if selected_book_id:
                update_book(selected_book_id, data)
            else:
                insert_book(data)

            clear_fields()
            highlight_errors([])  # ✅ clear red borders after success
            refresh_books()
        except Exception as ex:
            import sqlite3
            if isinstance(ex, sqlite3.IntegrityError) and "book_number" in str(ex):
                highlight_errors(["book_number"])
                show_snack_bar("⚠️ Book number must be unique.")

            else:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Error: {str(ex)}"))
                show_snack_bar(f"Error: {str(ex)}")
            page.update()

    def show_snack_bar(message: str, color: str = ft.Colors.RED_300):
        snack_bar = ft.SnackBar(
            content=ft.Text(
                message,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            ),
            bgcolor=color,
            duration=3000
        )
        page.snack_bar = snack_bar
        page.open(snack_bar)

    def handle_delete(book_id):
        nonlocal current_page
        delete_book(book_id)
        books = get_books()
        total_pages = max(1, (len(books) + page_size - 1) // page_size)
        if current_page > total_pages:
            current_page = total_pages
        books_cache.clear()
        books_cache.extend(books)
        update_table()

    def create_edit_callback(book):
        return lambda e: fill_form(book)

    def create_delete_callback(book_id):
        return lambda e: handle_delete(book_id)

    def create_summary_callback(page, book_id):
        def show_summary(e):
            summary = get_copy_summary(book_id)  # ✅ always fetch latest
            create_summary_dialog(page, book_id, summary)  # ✅ pass updated data

        return show_summary

    def create_summary_dialog(page, book_id, summary_data):
        available_input = ft.TextField(value=str(summary_data.get("Available", 0)), width=70,
                                       text_align=ft.TextAlign.CENTER, dense=True)
        lent_input = ft.TextField(value=str(summary_data.get("Lent", 0)), width=70, text_align=ft.TextAlign.CENTER,
                                  dense=True)
        missing_input = ft.TextField(value=str(summary_data.get("Missing", 0)), width=70,
                                     text_align=ft.TextAlign.CENTER, dense=True)
        damaged_input = ft.TextField(value=str(summary_data.get("Damaged", 0)), width=70,
                                     text_align=ft.TextAlign.CENTER, dense=True)

        def save_inventory(e):
            print("🚨 save_inventory called")  #
            new_data = {
                "available": int(available_input.value or 0),
                "lent": int(lent_input.value or 0),
                "missing": int(missing_input.value or 0),
                "damaged": int(damaged_input.value or 0),
            }
            update_inventory(book_id, **new_data)  # ✅ FIXED
            page.close(summary_dialog)
            page.snack_bar = ft.SnackBar(content=ft.Text("Inventory updated successfully!"))
            page.snack_bar.open = True
            refresh_books()  # ✅ This will reload and show updated values
            page.update()

        def cancel_dialog(e):
            page.close(summary_dialog)  # ✅ Use page.close()

        summary_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("📦 Inventory Summary", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([ft.Text("Available"), available_input]),
                        ft.Column([ft.Text("Lent"), lent_input]),
                        ft.Column([ft.Text("Missing"), missing_input]),
                        ft.Column([ft.Text("Damaged"), damaged_input]),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    ft.Row([
                        ft.ElevatedButton("Save", on_click=save_inventory),
                        ft.TextButton("Cancel", on_click=cancel_dialog)
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ]),
                padding=15,
                width=600,
                height=150  # ✅ Limit overall height (adjust as needed)
            )
        )

        page.dialog = summary_dialog
        page.open(summary_dialog)  # ✅ Use page.open()

    def update_table():
        book_table.rows.clear()
        total_pages = max(1, (len(books_cache) + page_size - 1) // page_size)
        start = (current_page - 1) * page_size
        end = start + page_size

        for index, book in enumerate(books_cache[start:end]):
            book_id = book[0]
            status = book[10]  # index of "status" field

            # Color logic for status
            status_colors = {
                "Available": ft.Colors.GREEN_600,
                "Not Available": ft.Colors.AMBER_700,
                "Missing": ft.Colors.RED_600,
            }
            colored_status = ft.Text(status, color=status_colors.get(status, ft.Colors.GREY_600))

            # Build 10 data cells (excluding action buttons)
            # book = (id, book_number, title, author, translator, pub_date, isbn, language, genre, edition, status)
            # We want to include all fields except `status` (replace with colored one)
            data_cells = [ft.DataCell(ft.Text(str(cell))) for cell in book[0:10]]
            data_cells[-1] = ft.DataCell(
                colored_status)  # replace last one (edition) with colored status only if needed

            # Add the 11th column: Actions
            action_buttons = ft.Row([
                ft.IconButton(icon="info", tooltip="Summary", on_click=create_summary_callback(page, book_id),
                              icon_color="green500"),
                ft.IconButton(icon="edit", tooltip="Edit", on_click=create_edit_callback(book), icon_color="orange500"),
                ft.IconButton(icon="delete", tooltip="Delete", on_click=create_delete_callback(book_id),
                              icon_color="red500")
            ])
            data_cells.append(ft.DataCell(action_buttons))  # 11th cell

            row_color = "grey100" if index % 2 == 0 else "white"

            book_table.rows.append(
                ft.DataRow(
                    cells=data_cells,
                    color=row_color
                )
            )

        page_label.value = f"Page {current_page} of {total_pages}"
        page.update()

    def refresh_books(filtered=None):
        nonlocal books_cache, current_page
        books_cache = filtered if filtered else get_books()
        current_page = 1
        update_table()

    def handle_search(e):
        term = search_input.value.strip()
        if term:
            results = search_books(term)
            refresh_books(results)
        else:
            refresh_books()

    def handle_export(e):
        export_books()
        page.snack_bar = ft.SnackBar(content=ft.Text("Books exported to Excel."))
        page.show_snack_bar(page.snack_bar)

    def go_to_page(e):
        nonlocal current_page
        try:
            requested = int(page_input.value.strip())
            total_pages = max(1, (len(books_cache) + page_size - 1) // page_size)
            if 1 <= requested <= total_pages:
                current_page = requested
                update_table()
        except ValueError:
            pass

    def change_page_size(e):
        nonlocal page_size, current_page
        try:
            page_size = int(page_size_dropdown.value)
            current_page = 1
            update_table()
        except:
            pass

    def prev_page(e):
        nonlocal current_page
        if current_page > 1:
            current_page -= 1
            update_table()

    def next_page(e):
        nonlocal current_page
        total_pages = max(1, (len(books_cache) + page_size - 1) // page_size)
        if current_page < total_pages:
            current_page += 1
            update_table()

    def toggle_form(e):
        nonlocal show_form
        show_form = not show_form
        form_section.visible = show_form
        page.update()

    search_input = ft.TextField(label="Search by title, author, or book number", expand=True, on_submit=handle_search)
    page_input = ft.TextField(label="Go to page", width=150, on_submit=go_to_page)
    page_size_dropdown = ft.Dropdown(
        label="Page size",
        width=120,
        value=str(page_size),
        options=[ft.dropdown.Option(str(n)) for n in [50, 100, 250]],
        on_change=change_page_size
    )

    book_table = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("ID")),
            ft.DataColumn(label=ft.Text("Book Number")),  # new column
            ft.DataColumn(label=ft.Text("Title")),
            ft.DataColumn(label=ft.Text("Author")),
            ft.DataColumn(label=ft.Text("Translator")),
            ft.DataColumn(label=ft.Text("Pub Date")),
            ft.DataColumn(label=ft.Text("ISBN")),
            ft.DataColumn(label=ft.Text("Language")),
            ft.DataColumn(label=ft.Text("Genre")),
            ft.DataColumn(label=ft.Text("Status")),
            ft.DataColumn(label=ft.Text("Actions"))
        ],
        rows=[],
        expand=True
    )

    table_container = ft.Container(
        content=ft.Column(
            controls=[book_table],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True
        ),
        expand=True,
        padding=0
    )

    page_label = ft.Text()

    column1 = ft.Column([
        fields['book_number'],  # Add here
        fields['title'],
        fields['author'],
        fields['translator'],
        fields['pub_date']
    ], expand=True)

    column2 = ft.Column([
        fields['isbn'],
        fields['language'],
        fields['genre'],
        fields['edition'],
        fields['status'],
        ft.Row([
            ft.ElevatedButton("Save", on_click=handle_add_or_update),
            ft.ElevatedButton("Clear", on_click=clear_fields),
            ft.ElevatedButton("Export", on_click=handle_export)
        ], spacing=10)
    ], expand=True)

    form_row = ft.Row(
        [column1, column2],
        vertical_alignment=ft.CrossAxisAlignment.START,  # Align top of both columns
    )
    form_section = ft.Column([
        form_row
    ])

    form_section.visible = False

    pagination_controls = ft.Row([
        ft.ElevatedButton("Previous", on_click=prev_page),
        ft.ElevatedButton("Next", on_click=next_page),
        page_label,
        page_input,
        ft.ElevatedButton("Go", on_click=go_to_page),
        page_size_dropdown
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    layout = ft.Column([
        ft.Row([
            ft.Text("📚 Book Manager", size=20, weight=ft.FontWeight.BOLD, expand=True),
            ft.ElevatedButton("➕ Add Book", on_click=toggle_form)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        form_section,
        ft.Divider(),
        ft.Row([
            search_input,
            ft.ElevatedButton("Search", on_click=handle_search),
            ft.ElevatedButton("Clear", on_click=lambda e: (search_input.__setattr__('value', ''), refresh_books()))
        ], spacing=10),
        table_container,
        pagination_controls
    ], expand=True)

    page.add(layout)
    refresh_books()


ft.app(target=main)
