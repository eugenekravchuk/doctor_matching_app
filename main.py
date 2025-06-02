import customtkinter as ctk
from tkinter import filedialog, messagebox
from algo_flow import generate_preference_schedule_from_csv
import os

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class ScheduleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Schedule Generator")
        self.geometry("500x400")
        
        self.input_csv = None
        self.input_json = None

        ctk.CTkLabel(self, text="Upload Files for Scheduling", font=("Helvetica", 18)).pack(pady=20)

        self.csv_btn = ctk.CTkButton(self, text="Select CSV", command=self.select_csv)
        self.csv_btn.pack(pady=10)

        self.json_btn = ctk.CTkButton(self, text="Select JSON", command=self.select_json)
        self.json_btn.pack(pady=10)

        self.week_var = ctk.IntVar(value=1)
        ctk.CTkLabel(self, text="Week Number (1-4)").pack(pady=5)
        ctk.CTkEntry(self, textvariable=self.week_var).pack(pady=5)

        self.gen_btn = ctk.CTkButton(self, text="Generate Schedule", command=self.generate_schedule)
        self.gen_btn.pack(pady=20)

    def select_csv(self):
        self.input_csv = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if self.input_csv:
            self.csv_btn.configure(text=f"CSV: {os.path.basename(self.input_csv)}")

    def select_json(self):
        self.input_json = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if self.input_json:
            self.json_btn.configure(text=f"JSON: {os.path.basename(self.input_json)}")

    def generate_schedule(self):
        if not self.input_csv or not self.input_json:
            messagebox.showerror("Error", "Please select both CSV and JSON files.")
            return
        
        week = self.week_var.get()
        output_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

        if output_path:
            try:
                generate_preference_schedule_from_csv(
                    self.input_csv, self.input_json, output_path, None, week
                )
                messagebox.showinfo("Success", f"Schedule saved to:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Generation Failed", str(e))

if __name__ == "__main__":
    app = ScheduleApp()
    app.mainloop()