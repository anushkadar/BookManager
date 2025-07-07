import flet as ft
from db import create_user_tables, get_users_paginated, get_total_users_count, insert_user, update_user, delete_user, search_users

def create_users_tab(page, show_snack_bar):
    selected_user_id = None
    current_page = 1
    page_size = 100
    total_users = get_total_users_count()
    show_form = False
    filtered_users = None

    # Form fields for user data input
    fields = {
        'user_id': ft.TextField(label="User ID", read_only=True),
        'name': ft.TextField(label="Full Name"),
        'email': ft.TextField(label="Email"),
        'phone': ft.TextField(label="Phone"),
        'membership_type': ft.Dropdown(
            label="Membership Type",
            options=[
                ft.dropdown.Option("Regular"),
                ft.dropdown.Option("Premium"),
                ft.dropdown.Option("Student"),
                ft.dropdown.Option("Staff")
            ],
            value="Regular"
        ),
        'status': ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Active"),
                ft.dropdown.Option("Inactive"),
                ft.dropdown.Option("Suspended")
            ],
            value="Active"
        )
    }

    def clear_fields(e=None):
        nonlocal selected_user_id
        selected_user_id = None
        for k, f in fields.items():
            f.value = "" if isinstance(f, ft.TextField) else fields[k].options[0].key
        page.update()

    def fill_form(user):
        nonlocal selected_user_id, show_form
        selected_user_id = user[0]
        show_form = True
        form_section.visible = True
        for key, value in zip(fields.keys(), user[1:]):
            if key in fields:
                fields[key].value = str(value or "")
        page.update()

    def parse_user_form():
        data = {}
        errors = []
        for k, f in fields.items():
            val = f.value
            if k == "user_id":
                try:
                    data[k] = int(val.strip()) if val and str(val).strip().isdigit() else None
                except:
                    data[k] = None
            else:
                data[k] = val.strip() if isinstance(val, str) else ""

        if not data["name"]:
            errors.append("name")
        if not data["email"]:
            errors.append("email")

        return data, errors

    def highlight_errors(errors):
        for k in fields:
            fields[k].border_color = None
        for k in errors:
            fields[k].border_color = ft.Colors.RED_400
        page.update()

    def handle_add_or_update(e):
        data, errors = parse_user_form()
        if errors:
            highlight_errors(errors)
            show_snack_bar("Please fill all required fields.")
            return

        try:
            if selected_user_id:
                update_user(selected_user_id, data)
            else:
                insert_user(data)

            clear_fields()
            refresh_users()

        except Exception as ex:
            show_snack_bar(f"Error: {ex}")

    def delete_user_action(user_id):
        def confirm_delete(e):
            delete_user(user_id)
            refresh_users()
            page.dialog.open = False
            page.update()
            show_snack_bar("User deleted successfully!", ft.Colors.GREEN_100)

        def cancel_delete(e):
            page.dialog.open = False
            page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this user?"),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("No", on_click=cancel_delete),
            ],
        )

        page.dialog = confirm_dialog
        page.dialog.open = True
        page.update()

    def update_table():
        user_table.rows.clear()

        if filtered_users is not None:
            total_users = len(filtered_users)
            users = filtered_users[(current_page - 1) * page_size: current_page * page_size]
        else:
            total_users = get_total_users_count()
            users = get_users_paginated(current_page, page_size)

        total_pages = max(1, (total_users + page_size - 1) // page_size)

        for index, user in enumerate(users):
            user_id = user[0]
            status = user[5]
            status_Colors = {
                "Active": ft.Colors.GREEN_400,
                "Inactive": ft.Colors.AMBER_600,
                "Suspended": ft.Colors.RED_500,
            }
            colored_status = ft.Text(status, color=status_Colors.get(status, ft.Colors.GREY_600))

            data_cells = [ft.DataCell(ft.Text(str(cell))) for cell in user[0:5]]
            data_cells.append(ft.DataCell(colored_status))
            data_cells.append(ft.DataCell(ft.Row([
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Edit",
                    on_click=lambda e, u=user: fill_form(u),
                    icon_color=ft.Colors.ORANGE_400
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    tooltip="Delete",
                    on_click=lambda e, uid=user_id: delete_user_action(uid),
                    icon_color=ft.Colors.RED_400
                )
            ], spacing=5, wrap=False)))

            row_color = ft.Colors.GREY_100 if index % 2 == 0 else ft.Colors.WHITE
            user_table.rows.append(ft.DataRow(cells=data_cells, color=row_color))

        page_label.value = f"Page {current_page} of {total_pages} | Total: {total_users}"
        page.update()

    def refresh_users(filtered=None):
        nonlocal filtered_users, current_page
        current_page = 1
        filtered_users = filtered
        update_table()

    def handle_search(e):
        term = search_input.value.strip()
        is_exact = exact_search_toggle.value

        if term:
            results = search_users(term, exact=is_exact)
            refresh_users(results)
        else:
            refresh_users(None)

    def go_to_page(e):
        nonlocal current_page
        try:
            req = int(page_input.value.strip())
            max_pages = max(1, (total_users + page_size - 1) // page_size)
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
        if current_page < max(1, (total_users + page_size - 1) // page_size):
            current_page += 1
            update_table()

    def toggle_form(e):
        nonlocal show_form
        show_form = not show_form
        form_section.visible = show_form
        if not show_form:
            clear_fields()
        page.update()

    # UI elements
    search_input = ft.TextField(label="Search by name, email, or phone", expand=True, on_submit=handle_search)
    exact_search_toggle = ft.Checkbox(label="Exact match", value=False)
    page_input = ft.TextField(label="Go to page", width=150, on_submit=go_to_page)
    page_size_dropdown = ft.Dropdown(
        label="Page size",
        width=120,
        value=str(page_size),
        options=[ft.dropdown.Option(str(n)) for n in [50, 100, 250]],
        on_change=change_page_size
    )

    user_table = ft.DataTable(
        columns=[ft.DataColumn(label=ft.Text(h)) for h in
                 ["ID", "Name", "Email", "Phone", "Membership Type", "Status", "Actions"]],
        rows=[],
        expand=True
    )

    table_container = ft.Container(
        content=ft.Column([user_table], scroll=ft.ScrollMode.ALWAYS, expand=True),
        bgcolor=ft.Colors.GREY_100,
        expand=True
    )
    page_label = ft.Text()

    column1 = ft.Column([
        fields['name'], fields['email'], fields['phone']
    ], expand=True)

    column2 = ft.Column([
        fields['membership_type'], fields['status'],
        ft.Row([
            ft.ElevatedButton("Save", on_click=handle_add_or_update, bgcolor=ft.Colors.GREEN_100),
            ft.ElevatedButton("Clear", on_click=clear_fields, bgcolor=ft.Colors.GREY_200),
        ], spacing=10)
    ], expand=True)

    form_section = ft.Column([ft.Row([column1, column2], vertical_alignment=ft.CrossAxisAlignment.START)])
    form_section.visible = False

    layout = ft.Column([
        ft.Row([
            ft.Text("\ud83d\udc64 User Management", size=20, weight=ft.FontWeight.BOLD, expand=True),
            ft.ElevatedButton("\u2795 Add User", on_click=toggle_form, bgcolor=ft.Colors.BLUE_100)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        form_section,
        ft.Divider(),
        ft.Row([
            search_input,
            exact_search_toggle,
            ft.ElevatedButton("Search", on_click=handle_search, bgcolor=ft.Colors.GREY_200),
            ft.ElevatedButton("Clear", on_click=lambda e: (setattr(search_input, 'value', ''), refresh_users()),
                              bgcolor=ft.Colors.GREY_200)
        ], spacing=10),
        table_container,
        ft.Row([
            ft.ElevatedButton("Previous", on_click=prev_page, bgcolor=ft.Colors.GREY_200),
            ft.ElevatedButton("Next", on_click=next_page, bgcolor=ft.Colors.GREY_200),
            page_label,
            page_input,
            ft.ElevatedButton("Go", on_click=go_to_page, bgcolor=ft.Colors.GREY_200),
            page_size_dropdown
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    ], expand=True)

    layout.refresh_users = refresh_users
    return layout