import customtkinter as ctk
from db.cache import init_db
from gui.app import App

def main():
    # Ensure SQLite database and tables exist before launching
    init_db()
    
    # Instantiate and run the main application
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()