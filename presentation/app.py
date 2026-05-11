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
from presentation.widgets import DicaTooltip


class AplicacaoConversor(ctk.CTk):
    """Aplicação GUI para conversão de arquivos CSV."""

    def __init__(
        self,
        validate_use_case: ValidateFilesUseCase,
        convert_use_case: ConvertFilesUseCase,
        formatos: list[FormatMetadata],
        config_ui: dict[str, int]
    ) -> None:
        super().__init__()
        self.validate_use_case = validate_use_case
        self.convert_use_case = convert_use_case
        self.formatos_meta = formatos
        self.config_ui = config_ui

        self.title("Conversor CSV Inteligente - Clean Architecture")
        self.geometry(f"{config_ui['largura']}x{config_ui['altura']}")
        
        self.arquivos: list[str] = []
        self.event_queue: queue.Queue[UIEvent] = queue.Queue()
        self.emitter = UIEventEmitter(self.event_queue)

        self._init_widgets()
        self._check_event_queue()

    def _init_widgets(self) -> None:
        """Cria e organiza todos os widgets."""
        quadro_principal = ctk.CTkFrame(self)
        quadro_principal.pack(fill="both", expand=True, padx=10, pady=10)

        quadro_sup = ctk.CTkFrame(quadro_principal)
        quadro_sup.pack(fill="both", expand=True, pady=(0, 10))
        ctk.CTkButton(quadro_sup, text="Selecionar Arquivos", command=self._selecionar_arquivos).pack(pady=10)
        self.lista = ctk.CTkTextbox(quadro_sup, height=self.config_ui.get('altura_lista', 100))
        self.lista.pack(pady=5, fill="both", expand=True)

        quadro_conv = ctk.CTkFrame(quadro_principal)
        quadro_conv.pack(fill="x", pady=(0, 10))
        for fmt in self.formatos_meta:
            q = ctk.CTkFrame(quadro_conv)
            q.pack(pady=2, padx=5, fill="x")
            ctk.CTkButton(
                q, 
                text=f"Converter para {fmt.name}", 
                command=lambda f=fmt: self._iniciar_conversao(f)
            ).pack(side="left")
            label_info = ctk.CTkLabel(q, text="i")
            label_info.pack(side="left", padx=5)
            DicaTooltip(label_info, fmt.description)

        quadro_inf = ctk.CTkFrame(quadro_principal)
        quadro_inf.pack(fill="x", pady=(0, 10))
        self.label_status = ctk.CTkLabel(quadro_inf, text="Pronto")
        self.label_status.pack(pady=5)
        self.progresso = ctk.CTkProgressBar(quadro_inf)
        self.progresso.pack(pady=5, fill="x", padx=10)
        self.progresso.set(0)

        quadro_cred = ctk.CTkFrame(quadro_principal)
        quadro_cred.pack(fill="x", side="bottom")
        ctk.CTkButton(
            quadro_cred, 
            text="Desenvolvido por Isllan Toso", 
            command=self._abrir_linkedin
        ).pack(side="right", padx=10, pady=5)

    def _check_event_queue(self) -> None:
        """Consome eventos da queue e atualiza a UI (Main Thread safe)."""
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
            self.progresso.set(curr / total)
            self.label_status.configure(text=event.message)
        elif event.type == EventType.SUCCESS:
            self.label_status.configure(text=event.message)
            self.progresso.set(1)
            messagebox.showinfo("Sucesso", event.message)
        elif event.type == EventType.ERROR:
            self.label_status.configure(text="Erro!")
            messagebox.showerror("Erro", event.message)
        elif event.type == EventType.INFO:
            self.label_status.configure(text=event.message)

    def _selecionar_arquivos(self) -> None:
        files = filedialog.askopenfilenames(filetypes=[("CSV", "*.csv")])
        if not files:
            return

        erro = self.validate_use_case.execute(list(files))
        if erro:
            messagebox.showerror("Erro", erro)
            return

        self.arquivos = list(files)
        self.lista.delete("1.0", "end")
        self.lista.insert("end", "".join([f"{Path(a).name}\n" for a in self.arquivos]))
        
        if self.convert_use_case.low_ram_mode:
            self.label_status.configure(text="Modo Baixo Consumo ativado.")

    def _iniciar_conversao(self, format_meta: FormatMetadata) -> None:
        if not self.arquivos:
            messagebox.showwarning("Aviso", "Selecione arquivos primeiro.")
            return
        
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

            self.convert_use_case.execute(self.arquivos, format_meta, UIObserver(self.emitter))
            self.emitter.emit_success(f"Conversão para {format_meta.name} concluída!")
        except Exception as e:
            self.emitter.emit_error(str(e))

    def _abrir_linkedin(self) -> None:
        webbrowser.open("https://www.linkedin.com/in/isllantoso/")
