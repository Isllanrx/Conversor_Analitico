import logging
import queue
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk  # type: ignore[import]

from application.use_cases import ConvertFilesUseCase, ValidateFilesUseCase
from domain.entities import FormatMetadata
from presentation.events import EventType, UIEvent, UIEventEmitter
from presentation.widgets import InfoTooltip

logger = logging.getLogger(__name__)

class AplicacaoConversor(ctk.CTk):
    """GUI Application for CSV file conversion."""

    def __init__(
        self,
        validate_use_case: ValidateFilesUseCase,
        convert_use_case: ConvertFilesUseCase,
        formats: list[FormatMetadata],
        ui_config: dict[str, Any]
    ) -> None:
        super().__init__()
        self.validate_use_case = validate_use_case
        self.convert_use_case = convert_use_case
        self.formats_meta = formats
        self.ui_config = ui_config

        self.title("Analytical Converter - Clean Architecture")
        self.geometry(f"{ui_config['WINDOW_WIDTH']}x{ui_config['WINDOW_HEIGHT']}")
        
        self.files: list[str] = []
        self.event_queue: queue.Queue[UIEvent] = queue.Queue()
        self.emitter = UIEventEmitter(self.event_queue)

        self._init_widgets()
        self._check_event_queue()

    def _init_widgets(self) -> None:
        """Creates and organizes all widgets."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Upper frame: Selection and List
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill="both", expand=True, pady=(0, 10))
        ctk.CTkButton(top_frame, text="Select CSV Files", command=self._select_files).pack(pady=10)
        
        self.file_list = ctk.CTkTextbox(top_frame, height=self.ui_config.get('LIST_HEIGHT', 150))
        self.file_list.pack(pady=5, fill="both", expand=True)

        # Middle frame: Conversion Buttons
        conv_frame = ctk.CTkFrame(main_frame)
        conv_frame.pack(fill="x", pady=(0, 10))
        
        # Grid-like layout for buttons
        for i, fmt in enumerate(self.formats_meta):
            row_frame = ctk.CTkFrame(conv_frame)
            row_frame.pack(pady=2, padx=5, fill="x")
            
            ctk.CTkButton(
                row_frame, 
                text=f"Convert to {fmt.name}", 
                command=lambda f=fmt: self._start_conversion(f)
            ).pack(side="left", fill="x", expand=True)
            
            info_label = ctk.CTkLabel(row_frame, text="ⓘ", cursor="question_mark")
            info_label.pack(side="left", padx=10)
            InfoTooltip(info_label, fmt.description)

        # Lower frame: Status and Progress
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(status_frame, text="Ready")
        self.status_label.pack(pady=2)
        
        self.progress_bar = ctk.CTkProgressBar(status_frame)
        self.progress_bar.pack(pady=5, fill="x", padx=10)
        self.progress_bar.set(0)

        # Footer: Credits
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.pack(fill="x", side="bottom")
        
        from config import DEV_NAME, LINKEDIN_URL
        ctk.CTkButton(
            footer_frame, 
            text=f"Developed by {DEV_NAME}", 
            command=lambda: webbrowser.open(LINKEDIN_URL),
            fg_color="transparent",
            text_color=("gray20", "gray80")
        ).pack(side="right")

    def _check_event_queue(self) -> None:
        """Consumes events from the queue to update UI in the Main Thread."""
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._handle_ui_event(event)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._check_event_queue)

    def _handle_ui_event(self, event: UIEvent) -> None:
        if event.type == EventType.PROGRESS:
            curr, total = event.payload
            self.progress_bar.set(curr / total if total > 0 else 0)
            self.status_label.configure(text=event.message)
        elif event.type == EventType.SUCCESS:
            self.status_label.configure(text="Conversion Successful!")
            self.progress_bar.set(1)
            messagebox.showinfo("Success", event.message)
        elif event.type == EventType.ERROR:
            self.status_label.configure(text="Error occurred!")
            messagebox.showerror("Error", event.message)
        elif event.type == EventType.INFO:
            self.status_label.configure(text=event.message)

    def _select_files(self) -> None:
        files = filedialog.askopenfilenames(filetypes=[("CSV Files", "*.csv")])
        if not files:
            return

        error = self.validate_use_case.execute(list(files))
        if error:
            messagebox.showerror("Validation Error", error)
            return

        self.files = list(files)
        self.file_list.delete("1.0", "end")
        self.file_list.insert("end", "".join([f"• {Path(a).name}\n" for a in self.files]))
        
        if self.convert_use_case.low_ram_mode:
            self.status_label.configure(text="Low RAM Mode Active.")

    def _start_conversion(self, format_meta: FormatMetadata) -> None:
        if not self.files:
            messagebox.showwarning("Warning", "Please select files first.")
            return
        
        self.progress_bar.set(0)
        threading.Thread(
            target=self._run_conversion, 
            args=(format_meta,), 
            daemon=True
        ).start()

    def _run_conversion(self, format_meta: FormatMetadata) -> None:
        try:
            class UIObserver:
                def __init__(self, emitter: UIEventEmitter):
                    self.emitter = emitter
                def update(self, c: int, t: int, m: str = ""):
                    self.emitter.emit_progress(c, t, m)

            self.convert_use_case.execute(self.files, format_meta, UIObserver(self.emitter))
            self.emitter.emit_success(f"Successfully converted to {format_meta.name}")
        except Exception as e:
            logger.exception("Conversion failed")
            self.emitter.emit_error(str(e))
