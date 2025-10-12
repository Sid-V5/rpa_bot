# src/gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import logging
import os
from typing import Callable, List

logger = logging.getLogger(__name__)

class InvoiceBotGUI:
    """
    A Tkinter-based GUI for the RPA Invoice Processing Bot.
    Allows users to select invoice files, start processing, and view progress.
    """
    def __init__(self, master: tk.Tk, start_processing_callback: Callable[[List[str], bool, Callable[[int, int, str], None]], None], initial_ocr_enabled: bool):
        self.master = master
        self.master.title("RPA Invoice Processing Bot")
        self.master.geometry("600x450") # Increased height for new widget
        self.master.resizable(False, False)

        self.start_processing_callback = start_processing_callback
        self.invoice_files = []
        self.ocr_enabled_var = tk.BooleanVar(value=initial_ocr_enabled)

        self._create_widgets()

    def _create_widgets(self):
        """
        Creates and arranges the GUI widgets.
        """
        # Frame for file selection
        file_frame = ttk.LabelFrame(self.master, text="Invoice File Selection", padding="10")
        file_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(file_frame, text="Selected Files:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.file_listbox = tk.Listbox(file_frame, height=4)
        self.file_listbox.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        browse_button = ttk.Button(file_frame, text="Browse Files", command=self._browse_files)
        browse_button.grid(row=1, column=2, padx=5, pady=5, sticky="s")

        file_frame.columnconfigure(1, weight=1)

        # Frame for controls
        control_frame = ttk.Frame(self.master, padding="10")
        control_frame.pack(pady=5, padx=10, fill="x")

        self.ocr_checkbutton = ttk.Checkbutton(
            control_frame,
            text="Enable EasyOCR Fallback (for scanned PDFs)",
            variable=self.ocr_enabled_var
        )
        self.ocr_checkbutton.pack(pady=5)

        self.start_button = ttk.Button(control_frame, text="Start Processing", command=self._start_bot_thread)
        self.start_button.pack(pady=10)

        # Progress bar
        self.progress_label = ttk.Label(control_frame, text="Progress: 0/0 invoices processed")
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(control_frame, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.pack(pady=5)

        # Log output area
        log_frame = ttk.LabelFrame(self.master, text="Bot Log", padding="10")
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=10, state="disabled", wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Redirect logging to GUI
        self.log_handler = GUILogHandler(self.log_text)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO) # Set default logging level for GUI

    def _browse_files(self):
        """
        Opens a dialog to select one or more PDF invoice files.
        """
        files_selected = filedialog.askopenfilenames(
            title="Select PDF Invoices",
            filetypes=[("PDF Files", "*.pdf")],
            initialdir=os.path.join(os.getcwd(), "sample_invoices")
        )
        if files_selected:
            self.invoice_files = files_selected
            self.file_listbox.delete(0, tk.END)
            for f in self.invoice_files:
                self.file_listbox.insert(tk.END, os.path.basename(f))
            logger.info(f"{len(self.invoice_files)} invoice files selected.")

    def _start_bot_thread(self):
        """
        Starts the bot processing in a separate thread to keep the GUI responsive.
        """
        if not self.invoice_files:
            messagebox.showerror("Error", "No invoice files selected.")
            logger.error("No invoice files selected to process.")
            return

        self.start_button.config(state="disabled", text="Processing...")
        self.progress_bar["value"] = 0
        self.progress_label.config(text="Progress: 0/0 invoices processed")
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        logger.info("Bot processing started.")

        # Start the processing in a new thread
        use_ocr = self.ocr_enabled_var.get()
        logger.info(f"Starting processing with OCR enabled: {use_ocr}")
        processing_thread = threading.Thread(target=self.start_processing_callback,
                                             args=(self.invoice_files, use_ocr, self._update_progress))
        processing_thread.daemon = True # Allow the thread to exit with the main program
        processing_thread.start()

    def _update_progress(self, current: int, total: int, message: str):
        """
        Updates the GUI progress bar and label.
        This method is called from the processing thread and must be marshaled to the main Tkinter thread.
        """
        self.master.after(0, self.__update_progress_gui, current, total, message)

    def __update_progress_gui(self, current: int, total: int, message: str):
        """
        Actual GUI update function, run in the main Tkinter thread.
        """
        if total > 0:
            self.progress_bar["maximum"] = total
            self.progress_bar["value"] = current
            self.progress_label.config(text=f"Progress: {current}/{total} invoices processed - {message}")
        else:
            self.progress_label.config(text=f"Progress: {message}")

        if current == total and total > 0:
            self.start_button.config(state="normal", text="Start Processing")
            messagebox.showinfo("Processing Complete", "Invoice processing finished!")
            logger.info("Bot processing finished.")
        elif total == 0 and current == 0 and "finished" in message.lower(): # Case for no PDFs found
            self.start_button.config(state="normal", text="Start Processing")
            messagebox.showinfo("Processing Complete", "No PDF invoices found to process.")
            logger.info("Bot processing finished (no PDFs found).")


class GUILogHandler(logging.Handler):
    """
    A custom logging handler that redirects log messages to a Tkinter Text widget.
    """
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.after(0, self._insert_log_message, msg)

    def _insert_log_message(self, msg):
        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, msg + "\n")
        self.text_widget.see(tk.END) # Auto-scroll to the end
        self.text_widget.config(state="disabled")
