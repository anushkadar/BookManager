import sys
import os

# Add 'flet/' to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "flet"))
sys.path.insert(0, os.path.dirname(__file__))

import flet as ft
from db import create_tables
from books import create_books_tab
from users import create_users_tab


def main(page: ft.Page):
    page.title = "Book Manager | Andaraz"
    page.window_width = 1500
    page.window_height = 1000
    page.window_full_screen = True
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.bgcolor = ft.Colors.GREY_50
    page.padding = 0  # ❗️Removes outer whitespace

    create_tables()

    def show_snack_bar(message, color=ft.Colors.RED_300):
        snack_bar = ft.SnackBar(
            content=ft.Text(message, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            bgcolor=color,
            duration=3000
        )
        page.snack_bar = snack_bar
        page.open(snack_bar)

    # Create tab content views
    books_tab = create_books_tab(page, show_snack_bar)
    users_tab = create_users_tab(page, show_snack_bar)

    # Handle tab change events
    def on_tab_change(e):
        selected_index = e.control.selected_index
        if selected_index == 0 and hasattr(books_tab, "refresh_books"):
            books_tab.refresh_books()
        elif selected_index == 1 and hasattr(users_tab, "refresh_users"):
            users_tab.refresh_users()

    # Tabs widget with consistent style
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        on_change=on_tab_change,
        tabs=[
            ft.Tab(
                # REMOVED: padding=ft.padding.all(0), margin=ft.margin.all(0) from ft.Tab
                tab_content=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.BOOK),
                        ft.Text("Books")
                    ], spacing=5),
                    width=140,
                    alignment=ft.alignment.center,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=ft.border_radius.all(6),
                    bgcolor=ft.Colors.GREY_100,
                    padding=10,
                    margin=0 # Keep this margin=0 on the Container
                ),
                content=books_tab
            ),
            ft.Tab(
                # REMOVED: padding=ft.padding.all(0), margin=ft.margin.all(0) from ft.Tab
                tab_content=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PEOPLE),
                        ft.Text("Users")
                    ], spacing=5),
                    width=140,
                    alignment=ft.alignment.center,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=ft.border_radius.all(6),
                    bgcolor=ft.Colors.GREY_100,
                    padding=10,
                    margin=0 # Keep this margin=0 on the Container
                ),
                content=users_tab
            )
        ],
        expand=True,
        divider_color=ft.Colors.TRANSPARENT,
        # --- NEW ATTEMPTS TO REMOVE GAP ---
        label_padding=ft.padding.all(0), # Try removing padding around the label area
        indicator_padding=ft.padding.all(0), # Try removing padding from the indicator
        # Potentially try a negative margin on the tab content, though this can be tricky
        # tab_content_margin=ft.margin.only(left=-1, right=-1) # Example, could cause overlap
    )

    # Wrap tabs in container to fully control layout
    tab_container = ft.Container(
        content=tabs,
        padding=0,
        margin=0,
        expand=True
    )

    def show_about_dialog(e):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(name="info_outline", color=ft.Colors.BLUE_400),
                ft.Text("About This App", size=18, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Column([
                ft.Text("📚 Book Manager", size=16, weight=ft.FontWeight.W_600),
                ft.Text("Version 1.0.0", size=14, italic=True),
                ft.Divider(),
                ft.Text("Developed by: Andaraz"),
                ft.Text("Contact: anushkadarr@gmail.com"),
                ft.Text("Powered by Python + Flet", size=12, color=ft.Colors.GREY_600),
            ], tight=True),
            actions=[
                ft.TextButton("Close", on_click=lambda e: page.close(dialog)),
            ],
        )
        page.dialog = dialog
        page.open(dialog)

    page.add(tab_container)

    # Trigger initial book load
    if hasattr(books_tab, "refresh_books"):
        books_tab.refresh_books()


ft.app(target=main)