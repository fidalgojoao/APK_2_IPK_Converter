"""Offline Tk desktop interface; worker threads never touch widgets."""
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .analyze import inspect_apk, markdown, write_report
from .convert import convert


class App:
    def __init__(self, root):
        self.root = root
        self.report = None
        self.events = queue.Queue()
        root.title("APK → IPK · LG webOS Studio")
        root.geometry("1060x820")
        root.minsize(850, 680)
        root.configure(bg="#101820")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#101820")
        style.configure("TLabel", background="#101820", foreground="#e4edf5", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 25, "bold"), foreground="#42dec1")
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("TCheckbutton", background="#101820", foreground="#e4edf5")
        main = ttk.Frame(root, padding=24)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        ttk.Label(main, text="APK → IPK", style="Title.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(main, text="LG webOS Studio  /  Inspect • Review • Package").grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 14))
        ttk.Label(main, text="Packages reusable web assets. Android code and APIs require a source port.").grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 14))
        self.apk = tk.StringVar()
        self.web = tk.StringVar()
        self.asset_root = tk.StringVar()
        self.entry = tk.StringVar(value="index.html")
        self.app_id = tk.StringVar(value="com.example.tvapp")
        self.title = tk.StringVar(value="My TV App")
        self.version = tk.StringVar(value="1.0.0")
        self.output = tk.StringVar()
        self.buttons = []
        def field(row, label, variable, browse=None):
            ttk.Label(main, text=label).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=5)
            ttk.Entry(main, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=5)
            if browse:
                b = ttk.Button(main, text="Browse", command=browse)
                b.grid(row=row, column=2, padx=(10, 0))
                self.buttons.append(b)
        field(3, "APK (optional with web export)", self.apk, self.pick_apk)
        field(4, "Ported web directory (optional)", self.web, self.pick_web)
        field(5, "APK asset root (or automatic)", self.asset_root)
        field(6, "HTML entry", self.entry)
        field(7, "webOS application ID", self.app_id)
        field(8, "TV application title", self.title)
        field(9, "Version", self.version)
        field(10, "New output directory", self.output, self.pick_output)
        ttk.Label(main, text="Dependency findings are informational. All selected web assets are preserved.").grid(row=11, column=0, columnspan=3, sticky="w", pady=12)
        actions = ttk.Frame(main)
        actions.grid(row=12, column=0, columnspan=3, sticky="ew")
        for label, cmd in (("1  Analyze APK", self.analyze), ("Save report", self.save_report), ("2  Build project + IPK", self.build)):
            button = ttk.Button(actions, text=label, command=cmd)
            button.pack(side="left", padx=(0, 10))
            self.buttons.append(button)
        self.status = tk.StringVar(value="Ready. Choose an APK to inspect or a web export to package.")
        ttk.Label(main, textvariable=self.status).grid(row=13, column=0, columnspan=3, sticky="w", pady=10)
        main.rowconfigure(14, weight=1)
        self.text = tk.Text(main, bg="#192633", fg="#dce8ef", insertbackground="white", wrap="word", relief="flat", font=("Consolas", 10), padx=14, pady=12)
        self.text.grid(row=14, column=0, columnspan=3, sticky="nsew")
        self.show("Compatibility reports and build results appear here.\n\nNo uploads, no external API keys, no execution of APK code.\n\nFor native apps, rebuild a web version from source and choose its exported directory.")
        root.after(100, self.poll)

    def show(self, text):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.configure(state="disabled")

    def pick_apk(self):
        path = filedialog.askopenfilename(filetypes=[("Android package", "*.apk")])
        if path:
            self.apk.set(path)
            self.report = None
            self.asset_root.set("")

    def pick_web(self):
        path = filedialog.askdirectory()
        if path:
            self.web.set(path)
            self.asset_root.set("")

    def pick_output(self):
        path = filedialog.asksaveasfilename(title="Choose a NEW output folder name", initialfile="webos-build")
        if path:
            self.output.set(path)

    def work(self, label, operation):
        self.status.set(label)
        for b in self.buttons:
            b.configure(state="disabled")
        def run():
            try:
                self.events.put(("ok", operation()))
            except Exception as e:
                self.events.put(("error", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def analyze(self):
        path = self.apk.get()
        self.work("Analyzing APK…", lambda: ("analysis", inspect_apk(path)))

    def build(self):
        args = dict(apk_path=self.apk.get() or None, web_dir=self.web.get() or None,
                    asset_root=self.asset_root.get() or None, entry=self.entry.get(),
                    app_id=self.app_id.get(), title=self.title.get(), version=self.version.get(),
                    output=self.output.get())
        if not self.output.get():
            messagebox.showerror("Output required", "Choose a new output directory.")
            return
        self.work("Building webOS project and checking IPK structure…", lambda: ("build", convert(**args)))

    def save_report(self):
        if self.report is None:
            messagebox.showinfo("Analyze first", "Analyze an APK first.")
            return
        path = filedialog.asksaveasfilename(title="New report directory", initialfile="apk-report")
        if path:
            try:
                if Path(path).exists():
                    raise ValueError("Choose a new directory.")
                write_report(self.report, Path(path))
                self.status.set("Report saved.")
            except Exception as e:
                messagebox.showerror("Report error", str(e))

    def poll(self):
        try:
            state, value = self.events.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll)
            return
        for b in self.buttons:
            b.configure(state="normal")
        if state == "error":
            self.status.set("Action could not complete.")
            self.show(value)
        else:
            kind, result = value
            if kind == "analysis":
                self.report = result
                if len(result["web_candidates"]) == 1 and not self.web.get():
                    c = result["web_candidates"][0]
                    self.asset_root.set(c["root"])
                    self.entry.set(c["entry"])
                self.show(markdown(result))
                self.status.set("Analysis complete. Review dependencies before packaging.")
            else:
                self.show("Project and IPK created:\n" + result["output"] + "\n\n" + result["ipk"] + "\n\nStructure verified. TV functionality has not been verified.\nReview conversion.json, analysis/ and TESTING.md.\n\nWeb dependency findings:\n" + "\n".join(f["title"] + ": " + f["action"] for f in result["web_findings"]))
                self.status.set("Build complete. Install and test on your LG TV.")
        self.root.after(100, self.poll)


def launch():
    root = tk.Tk()
    App(root)
    root.mainloop()
