import tkinter as tk
from utils.helpers import (
    APP_TITLE,WIN_WIDTH, WIN_HEIGHT, SIDEBAR_W, NAV_ITEMS, COLORS,)
from gui.dashboard import DashboardPage
from gui.cpu_page import CPUPage
from gui.memory_page import MemoryPage
from gui.page_replacement_page import PageReplacementPage
from gui.sync_page import SyncPage
from gui.deadlock_page import DeadlockPage
from gui.file_management_page import FileManagementPage

class MiniOSSimulator(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.configure(bg=COLORS["content_bg"])
        self.pages = {}
        self._build_sidebar()
        self._build_content()
        self._create_pages()
        self.show_page("dashboard")

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self,bg=COLORS["sidebar_bg"]
                                ,width=SIDEBAR_W)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(
            self.sidebar,
            text="Mini OS\nSimulator",
            bg=COLORS["sidebar_bg"],
            fg="white",
            font=("Segoe UI", 16, "bold"),
            pady=20).pack(fill="x")
        self.nav_buttons = {}
        for label, icon, key in NAV_ITEMS:
            btn = tk.Button(
                self.sidebar,
                text=f"{icon}  {label}",
                anchor="w",
                relief="flat",
                bd=0,
                padx=16,
                pady=10,
                bg=COLORS["sidebar_bg"],
                fg=COLORS["sidebar_text"],
                activebackground=COLORS["sidebar_active"],
                activeforeground="white",
                command=lambda k=key: self.show_page(k))
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

    def _build_content(self):
        self.content = tk.Frame(
            self, bg=COLORS["content_bg"])

        self.content.pack(
            side="right", fill="both",expand=True)

    def _create_pages(self):
        self.pages["dashboard"] = DashboardPage(
            self.content,
            navigate_cb=self.show_page )
        self.pages["cpu"] = CPUPage(self.content)
        self.pages["memory"] = MemoryPage(self.content)
        self.pages["page_replacement"] = PageReplacementPage(
            self.content)
        self.pages["synchronization"] = SyncPage(
            self.content)
        self.pages["deadlock"] = DeadlockPage(
            self.content)
        self.pages["file"] = FileManagementPage(
            self.content)
        for page in self.pages.values():
            page.place(
                relx=0, rely=0,
                relwidth=1,
                relheight=1)
    def show_page(self, page_key):
        page = self.pages.get(page_key)
        if page:
            page.tkraise()
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(
                    bg=COLORS["sidebar_active"] )
            else:
                btn.configure(
                    bg=COLORS["sidebar_bg"] )
if __name__ == "__main__":
    app = MiniOSSimulator()
    app.mainloop()