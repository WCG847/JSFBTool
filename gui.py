import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os

from cjsfb import Jsfb

class JSFBGui:
    def __init__(self, master):
        self.master = master
        master.title("JSFBTool")
        master.geometry("500x400")

        self.jsfb = Jsfb()
        self.file_path = None

        # File selection
        self.file_button = tk.Button(master, text="Open .jsfb File", command=self.open_file)
        self.file_button.pack(pady=10)

        # Info label
        self.info_label = tk.Label(master, text="No file loaded.")
        self.info_label.pack()

        # Listbox for index selection
        self.index_listbox = tk.Listbox(master, width=60)
        self.index_listbox.pack(pady=10)

        # Export filename entry
        self.name_label = tk.Label(master, text="Export Filename (without extension):")
        self.name_label.pack()
        self.name_entry = tk.Entry(master)
        self.name_entry.pack()

        # Export button
        self.export_button = tk.Button(master, text="Export Selected Index", command=self.export_index)
        self.export_button.pack(pady=10)

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("JSFB Files", "*.jsfb"), ("All Files", "*.*")])
        if not self.file_path:
            return

        try:
            with open(self.file_path, 'rb') as f:
                self.jsfb.ReadHeader(f)
                self.jsfb.ResolveVTable()

            self.info_label.config(text=f"Loaded: {os.path.basename(self.file_path)} | Header: {self.jsfb.Header}")
            self.populate_index_listbox()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def populate_index_listbox(self):
        self.index_listbox.delete(0, tk.END)
        for entry in self.jsfb.Info:
            self.index_listbox.insert(tk.END, f"Index {entry['Index']} | Offset: {entry['Offset']} | Size: {entry['Size']}")

    def export_index(self):
        selected = self.index_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an index from the list.")
            return

        index = selected[0]
        output_name = self.name_entry.get().strip()
        if not output_name:
            output_name = f"output_index_{index}"

        try:
            self.jsfb.ExportPointer(index, self.file_path, name=output_name)
            messagebox.showinfo("Success", f"Exported to {output_name}.json")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = JSFBGui(root)
    root.mainloop()
