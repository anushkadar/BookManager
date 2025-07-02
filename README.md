# 📚 Book Manager

A simple and efficient desktop application to manage a large collection of books. Built using **Python** and **Flet**, this app offers a smooth experience for adding, editing, deleting, searching, and exporting book records, with built-in inventory tracking.

---

## ✨ Features

- ✅ Add, edit, and delete books
- 🔍 Search by title, author, or book number (exact or partial match)
- 📦 Inventory summary (Available, Lent, Missing, Damaged)
- 📄 Export to Excel
- 📊 Pagination for large datasets (50,000+ entries)
- ⚠️ Form validation with error highlights
- 🌐 Responsive and clean interface
- 💡 App info dialog (version, developer, contact)

---

## 🖥 Requirements

- Python 3.10 or later
- SQLite (built-in)
- Flet (`pip install flet`)

---

## 🔧 Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/book-manager.git
cd book-manager

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
