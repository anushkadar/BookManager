import flet as ft
from db import get_books_paginated, get_total_books_count, insert_book, update_book, delete_book, \
    search_books, export_books, get_copy_summary, update_inventory, find_book_by_title


def create_books_tab(page, show_snack_bar):
    # We'll move all book-related code here
    selected_book_id = None
    current_page = 1
    page_size = 100
    total_books = get_total_books_count()
    show_form = False
    filtered_books = None

    # Form fields for book data input
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
                ft.dropdown.Option("Missing"),
                ft.dropdown.Option("Damaged")
            ],
            value="Available"
        )
    }

    def clear_fields(e=None):
        nonlocal selected_book_id
        selected_book_id = None
        for k, f in fields.items():
            f.value = "" if isinstance(f, ft.TextField) else "Available"
            f.border_color = None
        page.update()

    def fill_form(book):
        nonlocal selected_book_id, show_form
        selected_book_id = book[0]
        show_form = True
        form_section.visible = True
        for key, value in zip(fields.keys(), book[1:]):
            fields[key].value = str(value or "")
        page.update()

    def parse_book_form():
        data = {}
        errors = []
        for k, f in fields.items():
            val = f.value
            if k == "book_number":
                try:
                    data[k] = int(val.strip()) if val and str(val).strip().isdigit() else None
                except:
                    data[k] = None
            else:
                data[k] = val.strip() if isinstance(val, str) else ""

        if not data["title"]:
            errors.append("title")
        if not data["author"]:
            errors.append("author")
        if data["book_number"] is None:
            errors.append("book_number")

        return data, errors

    def highlight_errors(errors):
        for k in fields:
            fields[k].border_color = None
        for k in errors:
            fields[k].border_color = ft.Colors.RED_400
        page.update()

    def handle_add_or_update(e):
        data, errors = parse_book_form()
        if errors:
            highlight_errors(errors)
            show_snack_bar("Please fill all required fields.")
            return

        try:
            # Check title uniqueness
            existing = find_book_by_title(data["title"])
            if existing and (not selected_book_id or existing[0] != selected_book_id):
                highlight_errors(["title"])
                book_number = existing[1]
                show_snack_bar(f"⚠️ A book with this title already exists (Book Number: {book_number}).")
                return

            if selected_book_id:
                update_book(selected_book_id, data)
            else:
                insert_book(data)

            clear_fields()
            refresh_books()

        except Exception as ex:
            import sqlite3
            if isinstance(ex, sqlite3.IntegrityError):
                highlight_errors(["book_number"])
                show_snack_bar("⚠️ Book number must be unique.")
            else:
                show_snack_bar(f"Error: {ex}")

    def update_table():
        book_table.rows.clear()
        nonlocal total_books

        if filtered_books is not None:
            total_books = len(filtered_books)
            books = filtered_books[(current_page - 1) * page_size: current_page * page_size]
        else:
            total_books = get_total_books_count()
            books = get_books_paginated(current_page, page_size)

        total_pages = max(1, (total_books + page_size - 1) // page_size)

        for index, book in enumerate(books):
            book_id = book[0]
            status = book[10]
            status_colors = {
                "Available": ft.Colors.GREEN_400,
                "Not Available": ft.Colors.AMBER_600,
                "Missing": ft.Colors.RED_500,
            }
            colored_status = ft.Text(status, color=status_colors.get(status, ft.Colors.GREY_600))

            data_cells = [ft.DataCell(ft.Text(str(cell))) for cell in book[0:10]]
            data_cells[-1] = ft.DataCell(colored_status)
            data_cells.append(ft.DataCell(ft.Row([
                ft.IconButton(icon="PERSON", tooltip="Summary", on_click=create_summary_callback(book_id),
                              icon_color="green400"),
                ft.IconButton(icon="edit", tooltip="Edit", on_click=create_edit_callback(book), icon_color="orange400"),
                ft.IconButton(icon="delete", tooltip="Delete", on_click=create_delete_callback(book_id),
                              icon_color="red400")
            ], wrap=False)))

            row_color = "grey100" if index % 2 == 0 else "white"
            book_table.rows.append(ft.DataRow(cells=data_cells, color=row_color))

        page_label.value = f"Page {current_page} of {total_pages} | Total: {total_books}"
        page.update()

    def refresh_books(filtered=None):
        nonlocal filtered_books, current_page
        current_page = 1
        filtered_books = filtered
        update_table()

    def handle_search(e):
        term = search_input.value.strip()
        is_exact = exact_search_toggle.value

        if term:
            results = search_books(term, exact=is_exact)
            refresh_books(results)
        else:
            refresh_books(None)

    def create_summary_callback(book_id):
        def show_summary(e):
            summary = get_copy_summary(book_id)
            create_summary_dialog(summary)

        return show_summary

    def create_summary_dialog(summary):
        inputs = {
            k: ft.TextField(value=str(summary.get(k, 0)), width=70, text_align=ft.TextAlign.CENTER, dense=True)
            for k in ["Available", "Lent", "Missing", "Damaged"]
        }

        def save_inventory(e):
            update_inventory(selected_book_id, **{k.lower(): int(v.value or 0) for k, v in inputs.items()})
            page.dialog.open = False
            show_snack_bar("Inventory updated successfully!", ft.Colors.GREEN_100)
            refresh_books()
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("📦 Inventory Summary", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                padding=10,
                content=ft.Column([
                    ft.Row(
                        [ft.Column([ft.Text(k, size=14), v]) for k, v in inputs.items()],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        spacing=10
                    ),
                    ft.Row([
                        ft.ElevatedButton("Save", on_click=save_inventory),
                        ft.TextButton("Cancel", on_click=lambda e: setattr(page.dialog, 'open', False))
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ],
                    spacing=30
                ),
                width=500,
                height=155
            )
        )

        page.dialog = dialog
        page.dialog.open = True
        page.update()

    def create_edit_callback(book):
        return lambda e: fill_form(book)

    def create_delete_callback(book_id):
        return lambda e: (delete_book(book_id), refresh_books())

    def go_to_page(e):
        nonlocal current_page
        try:
            req = int(page_input.value.strip())
            max_pages = max(1, (total_books + page_size - 1) // page_size)
            if 1 <= req <= max_pages:
                current_page = req
                update_table()
        except:
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
        if current_page < max(1, (total_books + page_size - 1) // page_size):
            current_page += 1
            update_table()

    def handle_export(e):
        export_books()
        show_snack_bar("Books exported to Excel.", ft.Colors.BLUE_100)

    def toggle_form(e):
        nonlocal show_form
        show_form = not show_form
        form_section.visible = show_form
        page.update()

    # UI elements
    search_input = ft.TextField(label="Search by title, author, or book number", expand=True, on_submit=handle_search)
    exact_search_toggle = ft.Checkbox(label="Exact match", value=False)
    page_input = ft.TextField(label="Go to page", width=150, on_submit=go_to_page)
    page_size_dropdown = ft.Dropdown(label="Page size", width=120, value=str(page_size),
                                     options=[ft.dropdown.Option(str(n)) for n in [50, 100, 250]],
                                     on_change=change_page_size)

    book_table = ft.DataTable(
        columns=[ft.DataColumn(label=ft.Text(h)) for h in
                 ["ID", "Book Number", "Title", "Author", "Translator", "Pub Date", "ISBN", "Language", "Genre",
                  "Status", "Actions"]],
        rows=[], expand=True
    )

    table_container = ft.Container(content=ft.Column([book_table], scroll=ft.ScrollMode.ALWAYS, expand=True),
                                   bgcolor=ft.Colors.GREY_100, expand=True)
    page_label = ft.Text()

    column1 = ft.Column([
        fields['book_number'], fields['title'], fields['author'], fields['translator'], fields['pub_date']
    ], expand=True)

    column2 = ft.Column([
        fields['isbn'], fields['language'], fields['genre'], fields['edition'], fields['status'],
        ft.Row([
            ft.ElevatedButton("Save", on_click=handle_add_or_update, bgcolor=ft.Colors.GREEN_100),
            ft.ElevatedButton("Clear", on_click=clear_fields, bgcolor=ft.Colors.GREY_200),
            ft.ElevatedButton("Export", on_click=handle_export, bgcolor=ft.Colors.BLUE_100)
        ], spacing=10)
    ], expand=True)

    form_section = ft.Column([ft.Row([column1, column2], vertical_alignment=ft.CrossAxisAlignment.START)])
    form_section.visible = False

    layout = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("📚 Book Management", size=20, weight=ft.FontWeight.BOLD, expand=True),
                ft.ElevatedButton("➕ Add Book", on_click=toggle_form, bgcolor=ft.Colors.BLUE_100),
            ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.only(top=8, left=8, right=8)
        ),
        form_section,
        ft.Divider(height=2, thickness=1, color=ft.Colors.GREY_300),
        ft.Container(
        ft.Row([
            search_input,
            exact_search_toggle,
            ft.ElevatedButton(" Search ", on_click=handle_search, bgcolor=ft.Colors.GREY_200),
            ft.ElevatedButton(" Clear ", on_click=lambda e: (search_input.__setattr__('value', ''), refresh_books()),
                              bgcolor=ft.Colors.GREY_200)
        ], spacing=10),
           padding=ft.padding.only(top=8, left=8, right=8)),
        table_container,
        ft.Row([
            ft.ElevatedButton("Previous", on_click=prev_page, bgcolor=ft.Colors.GREY_200),
            ft.ElevatedButton("Next", on_click=next_page, bgcolor=ft.Colors.GREY_200),
            page_label, page_input,
            ft.ElevatedButton("Go", on_click=go_to_page, bgcolor=ft.Colors.GREY_200),
            page_size_dropdown
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    ], expand=True)

    layout.refresh_books = refresh_books
    return layout
