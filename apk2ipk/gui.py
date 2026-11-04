"""Beginner-friendly offline desktop workflow. Workers never touch widgets."""
from pathlib import Path
import hashlib
import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .analyze import inspect_apk, markdown
from .convert import convert


def next_output(apk_path):
    source = Path(apk_path)
    base = source.parent / (source.stem + "-webos")
    result, n = base, 2
    while result.exists():
        result = base.with_name(base.name + f"-{n}")
        n += 1
    return result


def suggested_settings(apk_path, report):
    """Stable TV identity and usable metadata without asking users to code."""
    manifest = report["manifest"]
    label = manifest.get("label", "")
    title = label if label and not label.startswith("@") else Path(apk_path).stem
    title = "".join(c for c in title if ord(c) >= 32).strip()[:80] or "My TV App"
    version = manifest.get("version_name", "")
    if re.fullmatch(r"\d{1,9}(\.\d{1,9}){0,2}", version):
        parts = [str(int(p)) for p in version.split(".")]
        version = ".".join((parts + ["0", "0"])[:3])
    else:
        version = "1.0.0"
    candidates = sorted(report["web_candidates"], key=lambda c: (
        c["root"] not in ("assets/www", "assets/public"), len(c["root"]), c["root"]))
    chosen = candidates[0] if candidates else {"root": "", "entry": "index.html"}
    identity = hashlib.sha256(manifest.get("package", "").encode()).hexdigest() if manifest.get("package") else report["sha256"]
    return dict(title=title, app_id="org.apk2ipk.app" + identity[:16],
                version=version, asset_root=chosen["root"], entry=chosen["entry"])


class App:
    def __init__(self, root):
        self.root, self.report, self.last_output = root, None, None
        self.events = queue.Queue()
        self.busy = False
        self.details_text = "Choose an APK to see its compatibility details."
        root.title("APK2IPK Studio — LG TV converter")
        root.geometry("940x760")
        root.minsize(800, 690)
        root.configure(bg="#101820")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#101820")
        style.configure("TLabel", background="#101820", foreground="#e4edf5", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 28, "bold"), foreground="#42dec1")
        style.configure("TButton", font=("Segoe UI", 11), padding=10)
        style.configure("Primary.TButton", background="#42dec1", foreground="#10251f", font=("Segoe UI", 12, "bold"))
        main = ttk.Frame(root, padding=28)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        ttk.Label(main, text="APK → IPK", style="Title.TLabel").grid(row=0, sticky="w")
        ttk.Label(main, text="Choose an Android app. Create a package for your LG TV.").grid(row=1, sticky="w", pady=(4, 18))
        ttk.Label(main, text="1. Choose your APK file").grid(row=2, sticky="w")
        source = ttk.Frame(main)
        source.grid(row=3, sticky="ew", pady=(7, 18))
        source.columnconfigure(0, weight=1)
        self.apk = tk.StringVar()
        ttk.Entry(source, textvariable=self.apk, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.choose_button = ttk.Button(source, text="Choose APK…", command=self.pick_apk)
        self.choose_button.grid(row=0, column=1)
        self.title = tk.StringVar(value="My TV App")
        ttk.Label(main, text="2. Name your TV app").grid(row=4, sticky="w")
        title_entry = ttk.Entry(main, textvariable=self.title)
        title_entry.grid(row=5, sticky="ew", pady=(7, 18))
        self.output = tk.StringVar()
        ttk.Label(main, text="3. Save your converted app").grid(row=6, sticky="w")
        destination = ttk.Frame(main)
        destination.grid(row=7, sticky="ew", pady=(7, 14))
        destination.columnconfigure(0, weight=1)
        ttk.Entry(destination, textvariable=self.output, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.location_button = ttk.Button(destination, text="Change folder…", command=self.pick_output)
        self.location_button.grid(row=0, column=1)
        self.advanced_button = ttk.Button(main, text="Advanced settings ▸", command=self.toggle_advanced)
        self.advanced_button.grid(row=8, sticky="w", pady=(0, 8))
        self.advanced = ttk.Frame(main)
        self.advanced.grid(row=9, sticky="ew")
        self.advanced.columnconfigure(1, weight=1)
        self.app_id = tk.StringVar(value="org.apk2ipk.tvapp")
        self.version = tk.StringVar(value="1.0.0")
        self.asset_root = tk.StringVar()
        self.entry = tk.StringVar(value="index.html")
        self.web = tk.StringVar()
        self.inputs = [title_entry]
        for row, (label, var) in enumerate((("TV application ID", self.app_id), ("Version", self.version),
                                            ("APK web folder", self.asset_root), ("HTML entry", self.entry))):
            ttk.Label(self.advanced, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=3)
            field = ttk.Entry(self.advanced, textvariable=var)
            field.grid(row=row, column=1, sticky="ew", pady=3)
            self.inputs.append(field)
        ttk.Label(self.advanced, text="Rebuilt web app (optional)").grid(row=4, column=0, sticky="w", padx=(0, 12))
        ttk.Entry(self.advanced, textvariable=self.web, state="readonly").grid(row=4, column=1, sticky="ew")
        self.web_button = ttk.Button(self.advanced, text="Choose web folder…", command=self.pick_web)
        self.web_button.grid(row=4, column=2, padx=(8, 0))
        self.clear_web_button = ttk.Button(self.advanced, text="Clear", command=lambda: self.web.set(""))
        self.clear_web_button.grid(row=5, column=2, sticky="e")
        self.advanced.grid_remove()
        actions = ttk.Frame(main)
        actions.grid(row=10, sticky="ew", pady=(8, 12))
        self.convert_button = ttk.Button(actions, text="Convert to IPK", style="Primary.TButton", command=self.build, state="disabled")
        self.convert_button.pack(side="left", padx=(0, 12))
        self.open_button = ttk.Button(actions, text="Open output folder", command=self.open_output, state="disabled")
        self.open_button.pack(side="left")
        self.details_button = ttk.Button(actions, text="View details", command=self.view_details)
        self.details_button.pack(side="right")
        self.progress = ttk.Progressbar(main, mode="indeterminate")
        self.progress.grid(row=11, sticky="ew", pady=(0, 12))
        self.status = tk.StringVar(value="Ready — choose an APK to get started.")
        ttk.Label(main, textvariable=self.status, wraplength=830).grid(row=12, sticky="w")
        self.summary = tk.StringVar(value="No terminal commands. No Python installation needed in the Windows .exe.\n\nSome Android apps require a separate webOS version; the app will explain when conversion is unavailable.")
        ttk.Label(main, textvariable=self.summary, wraplength=830).grid(row=13, sticky="nw", pady=(14, 0))
        main.rowconfigure(13, weight=1)
        self.controls = [self.choose_button, self.location_button, self.web_button, self.clear_web_button] + self.inputs
        root.after(100, self.poll)

    def toggle_advanced(self):
        if self.advanced.winfo_ismapped():
            self.advanced.grid_remove()
            self.advanced_button.configure(text="Advanced settings ▸")
            self.root.geometry("940x760")
        else:
            self.advanced.grid()
            self.advanced_button.configure(text="Advanced settings ▾")
            self.root.geometry("940x960")

    def select_apk(self, path):
        """Shared by the file picker and UI smoke tests."""
        self.apk.set(str(path))
        self.output.set(str(next_output(path)))
        self.report, self.last_output = None, None
        self.web.set("")
        self.asset_root.set("")
        self.open_button.configure(state="disabled")
        self.work("Reading your APK…", lambda: ("analysis", inspect_apk(path)))

    def pick_apk(self):
        path = filedialog.askopenfilename(title="Choose the Android app you want to convert", filetypes=[("Android app", "*.apk")])
        if path:
            self.select_apk(path)

    def pick_output(self):
        parent = filedialog.askdirectory(title="Choose where to save the converted app")
        if parent:
            source = Path(parent) / (Path(self.apk.get()).name or "My-TV-App.apk")
            self.output.set(str(next_output(source)))

    def pick_web(self):
        path = filedialog.askdirectory(title="Choose a rebuilt web app folder")
        if path:
            self.web.set(path)
            self.asset_root.set("")
            if not self.apk.get():
                self.output.set(str(next_output(Path(path).with_suffix(".apk"))))
            self.convert_button.configure(state="normal")

    def work(self, label, operation):
        if self.busy:
            return
        self.busy = True
        self.status.set(label)
        self.convert_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        for control in self.controls:
            control.configure(state="disabled")
        self.progress.start(12)
        def run():
            try:
                self.events.put(("ok", operation()))
            except Exception as e:
                self.events.put(("error", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def build(self):
        if not self.apk.get() and not self.web.get():
            messagebox.showinfo("Choose an app", "Choose an APK file first.")
            return
        if not self.output.get():
            self.pick_output()
            if not self.output.get():
                return
        if self.report and not self.report["web_candidates"] and not self.web.get() and not self.asset_root.get():
            self.status.set("This Android app needs a webOS version.")
            self.summary.set("This APK has no web app that LG webOS can run. Its Android screens and features need to be rebuilt for webOS.\n\nThe inspector has not disabled any features. Packaging cannot supply the missing Android runtime.")
            return
        if Path(self.output.get()).exists():
            if self.last_output and Path(self.output.get()) == self.last_output:
                self.output.set(str(next_output(self.last_output.parent / Path(self.apk.get() or "My-TV-App.apk").name)))
        args = dict(apk_path=self.apk.get() or None, web_dir=self.web.get() or None,
                    asset_root=None if self.web.get() else (self.asset_root.get() or None),
                    entry=self.entry.get(), app_id=self.app_id.get(), title=self.title.get(),
                    version=self.version.get(), output=self.output.get())
        self.work("Converting your app…", lambda: ("build", convert(**args)))

    def open_output(self):
        if self.last_output and self.last_output.is_dir():
            try:
                if sys.platform == "win32":
                    os.startfile(self.last_output)
                else:
                    subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(self.last_output)])
            except OSError as e:
                messagebox.showerror("Cannot open folder", str(e))

    def view_details(self):
        window = tk.Toplevel(self.root)
        window.title("APK2IPK — conversion details")
        window.geometry("900x650")
        text = tk.Text(window, wrap="word", padx=18, pady=18)
        scrollbar = ttk.Scrollbar(window, command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        text.configure(yscrollcommand=scrollbar.set)
        text.insert("1.0", self.details_text)
        text.configure(state="disabled")

    def poll(self):
        try:
            state, value = self.events.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll)
            return
        self.busy = False
        self.progress.stop()
        for control in self.controls:
            control.configure(state="normal")
        self.convert_button.configure(state="normal" if self.report or self.web.get() else "disabled")
        if self.last_output:
            self.open_button.configure(state="normal")
        if state == "error":
            self.status.set("Could not finish. Your original APK has not been changed.")
            self.summary.set(value + "\n\nYou can choose another APK or change the Advanced settings.")
            self.details_text = value
        else:
            kind, result = value
            if kind == "analysis":
                self.report = result
                self.convert_button.configure(state="normal")
                for key, val in suggested_settings(self.apk.get(), result).items():
                    getattr(self, key).set(val)
                self.details_text = markdown(result)
                count = len(result["web_candidates"])
                self.status.set("APK ready — click Convert to IPK." if count else "APK read — this app needs a webOS version.")
                if count:
                    extra = " Multiple web folders were found; Advanced settings lets you choose another." if count > 1 else ""
                    self.summary.set("Your app's web files can be packaged. The name, TV app ID, version and output folder have been filled in for you." + extra + "\n\nFeature findings are informational. Android-specific features still need compatible implementations on the TV.")
                else:
                    self.summary.set("This app uses Android's own screens/runtime and contains no detected web app. It cannot be automatically converted to a working LG TV app.\n\nNo features were blocked. A webOS-compatible version must be built first.")
            else:
                self.last_output = Path(result["output"]).resolve()
                self.open_button.configure(state="normal")
                self.status.set("Done — your IPK file is ready.")
                self.summary.set(Path(result["ipk"]).name + "\n\nSaved in: " + str(self.last_output) + "\n\nClick Open output folder to find your file. Install and test it on your LG TV; original Android functionality is not automatically preserved.")
                self.details_text = self.summary.get() + "\n\nDependency findings:\n" + "\n".join(f["title"] + ": " + f["action"] for f in result["web_findings"])
        self.root.after(100, self.poll)


def launch():
    root = tk.Tk()
    App(root)
    root.mainloop()


def smoke_test():
    """Exercise the bundled Tk runtime and full click-to-convert path in CI."""
    import tempfile
    import time
    import zipfile
    from .package import verify_ipk
    with tempfile.TemporaryDirectory() as directory:
        apk = Path(directory) / "Sample App.apk"
        with zipfile.ZipFile(apk, "w") as archive:
            archive.writestr("AndroidManifest.xml", '<manifest package="org.example.smoketest"><application/></manifest>')
            archive.writestr("assets/www/index.html", "<!doctype html><html><body>GUI test</body></html>")
        root = tk.Tk()
        root.withdraw()
        try:
            app = App(root)
            app.select_apk(apk)
            def wait():
                deadline = time.monotonic() + 20
                while app.busy and time.monotonic() < deadline:
                    root.update()
                    time.sleep(0.02)
                if app.busy:
                    raise RuntimeError("GUI worker timed out")
            wait()
            if app.report is None or not app.asset_root.get():
                raise RuntimeError("Automatic APK selection/analysis failed")
            app.convert_button.invoke()
            wait()
            if not app.last_output:
                raise RuntimeError("GUI conversion failed: " + app.summary.get())
            verify_ipk(next(app.last_output.glob("*.ipk")))
        finally:
            root.destroy()
