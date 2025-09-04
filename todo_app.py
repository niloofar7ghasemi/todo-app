import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
DATA_FILE = "todo_data.json"
class ToDoApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.master.title("Aufgabenliste – To-Do App")
        self.master.minsize(540, 420)
        self.pack(fill="both", expand=True)
        self.tasks = []  
        self.filter_var = tk.StringVar(value="alle")  
        self.entry_var = tk.StringVar()
        self.current_path = DATA_FILE  
        self._build_ui()
        self._load(self.current_path)
    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        entry = ttk.Entry(top, textvariable=self.entry_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.add_task())
        entry.focus_set() 
        ttk.Button(top, text="Hinzufügen", command=self.add_task).pack(side="left", padx=(8, 0))
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(filter_frame, text="Filter:").pack(side="left")
        for val, label in [("alle", "Alle"), ("offen", "Offen"), ("erledigt", "Erledigt")]:
            ttk.Radiobutton(
                filter_frame, text=label, value=val, variable=self.filter_var, command=self.refresh_list
            ).pack(side="left", padx=6)
        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(mid, activestyle="dotbox")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Double-1>", lambda e: self.toggle_done())
        self.listbox.bind("<Delete>", lambda e: self.delete_selected())
        sb = ttk.Scrollbar(mid, command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=sb.set)
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Als erledigt/offen (Enter)", command=self.toggle_done).pack(side="left")
        ttk.Button(btns, text="Bearbeiten", command=self.edit_selected).pack(side="left", padx=6)
        ttk.Button(btns, text="Löschen (Entf)", command=self.delete_selected).pack(side="left", padx=6)
        ttk.Button(btns, text="Erledigte löschen", command=self.clear_done).pack(side="left", padx=6)
        self.status = ttk.Label(self, anchor="w")
        self.status.pack(fill="x", pady=(8, 0))
        menubar = tk.Menu(self.master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Öffnen…\tCtrl+O", command=self.open_file)
        filemenu.add_command(label="Speichern\tCtrl+S", command=self._save)
        filemenu.add_command(label="Export als CSV…", command=self.export_csv)
        filemenu.add_separator()
        filemenu.add_command(label="Beenden", command=self.master.destroy)
        menubar.add_cascade(label="Datei", menu=filemenu)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(
            label="Über",
            command=lambda: messagebox.showinfo(
                "Über", "To-Do App (Tkinter)\nAutor: Niloofar Ghasemi\nPython-Projekt für Lebenslauf"
            ),
        )
        menubar.add_cascade(label="Hilfe", menu=helpmenu)
        self.master.config(menu=menubar)

        self.master.bind_all("<Control-s>", lambda e: self._save())
        self.master.bind_all("<Control-o>", lambda e: self.open_file())
        self.master.bind_all("<Control-n>", lambda e: self.add_task())
        self.master.bind(
            "<Return>",
            lambda e: self.toggle_done() if self.listbox.focus_get() == self.listbox else None,
        )
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    def _load(self, path: str):
        self.current_path = path
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = [
                        {"text": str(t.get("text", "")).strip(), "done": bool(t.get("done", False))}
                        for t in (data if isinstance(data, list) else [])
                        if isinstance(t, dict) and str(t.get("text", "")).strip()
                    ]
                    self._update_status(f"Geladen: {os.path.basename(path)}")
            except Exception:
                messagebox.showwarning("Warnung", "Konnte gespeicherte Daten nicht laden.")
                self.tasks = []
                self._update_status("Leere Liste geladen.")
        else:
            self.tasks = []
        self.refresh_list()
    def _save(self, path: str | None = None):
        path = path or self.current_path
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            self._update_status(f"Gespeichert: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")
    def add_task(self):
        text = self.entry_var.get().strip()
        if not text:
            self._update_status("Kein Text eingegeben.")
            return
        self.tasks.append({"text": text, "done": False})
        self.entry_var.set("")
        self.refresh_list()
        self._save()
    def _visible_tasks(self):
        mode = self.filter_var.get()
        if mode == "offen":
            return [t for t in self.tasks if not t["done"]]
        if mode == "erledigt":
            return [t for t in self.tasks if t["done"]]
        return self.tasks
    def refresh_list(self):
        self.listbox.delete(0, "end")
        for t in self._visible_tasks():
            prefix = "✓ " if t["done"] else "• "
            self.listbox.insert("end", prefix + t["text"])
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["done"])
        self._update_status(f"Gesamt: {total} | Erledigt: {done} | Offen: {total - done}")
        self.master.title(f"Aufgabenliste – {done}/{total} erledigt")
    def _selected_global_index(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        visible = self._visible_tasks()
        target = visible[sel[0]]
        for i, t in enumerate(self.tasks):
            if t is target:
                return i
        return None
    def toggle_done(self):
        idx = self._selected_global_index()
        if idx is None:
            return
        self.tasks[idx]["done"] = not self.tasks[idx]["done"]
        self.refresh_list()
        self._save()
    def edit_selected(self):
        idx = self._selected_global_index()
        if idx is None:
            return
        new_text = simpledialog.askstring("Bearbeiten", "Neuer Text:", initialvalue=self.tasks[idx]["text"])
        if new_text is not None:
            new_text = new_text.strip()
            if new_text:
                self.tasks[idx]["text"] = new_text
                self.refresh_list()
                self._save()
    def delete_selected(self):
        idx = self._selected_global_index()
        if idx is None:
            return
        if messagebox.askyesno("Löschen", "Eintrag wirklich löschen?"):
            self.tasks.pop(idx)
            self.refresh_list()
            self._save()
    def clear_done(self):
        self.tasks = [t for t in self.tasks if not t["done"]]
        self.refresh_list()
        self._save()
    def open_file(self):
        path = filedialog.askopenfilename(
            title="Datei öffnen",
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")],
        )
        if path:
            self._load(path)
    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Als CSV speichern",
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv")],
        )
        if not path:
            return
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["text", "done"])
                for t in self.tasks:
                    writer.writerow([t["text"], "1" if t["done"] else "0"])
            self._update_status("CSV exportiert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"CSV-Export fehlgeschlagen:\n{e}")
    def _update_status(self, msg):
        self.status.config(text=msg)
def main():
    root = tk.Tk()
    if sys.platform.startswith("win"):
        try:
            root.call("tk", "scaling", 1.25)
        except Exception:
            pass
    ToDoApp(root)
    root.mainloop()
if __name__ == "__main__":
    main()
