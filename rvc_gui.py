import sys
from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
)


class RvcGui(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VoiceLab RVC")
        self.resize(1000, 720)

        self.root_dir = Path(__file__).resolve().parent
        self.process = None

        self.model_box = QComboBox()
        self.index_box = QComboBox()

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()

        self.pitch_spin = QSpinBox()
        self.pitch_spin.setRange(-24, 24)
        self.pitch_spin.setValue(0)

        self.f0_box = QComboBox()
        self.f0_box.addItems(["pm", "harvest", "rmvpe"])
        self.f0_box.setCurrentText("harvest")

        self.index_rate_spin = QDoubleSpinBox()
        self.index_rate_spin.setRange(0.0, 1.0)
        self.index_rate_spin.setSingleStep(0.05)
        self.index_rate_spin.setValue(0.7)

        self.filter_radius_spin = QSpinBox()
        self.filter_radius_spin.setRange(0, 7)
        self.filter_radius_spin.setValue(3)

        self.resample_spin = QSpinBox()
        self.resample_spin.setRange(0, 48000)
        self.resample_spin.setValue(0)

        self.rms_spin = QDoubleSpinBox()
        self.rms_spin.setRange(0.0, 1.0)
        self.rms_spin.setSingleStep(0.05)
        self.rms_spin.setValue(1.0)

        self.protect_spin = QDoubleSpinBox()
        self.protect_spin.setRange(0.0, 0.5)
        self.protect_spin.setSingleStep(0.01)
        self.protect_spin.setValue(0.33)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)

        self.refresh_button = QPushButton("Обновить список моделей и индексов")
        self.input_button = QPushButton("Выбрать input")
        self.output_button = QPushButton("Выбрать output")
        self.run_button = QPushButton("Преобразовать")
        self.stop_button = QPushButton("Остановить")
        self.clear_console_button = QPushButton("Очистить консоль")

        self.stop_button.setEnabled(False)

        self.build_layout()
        self.connect_signals()
        self.apply_dark_theme()
        self.refresh_models_and_indexes()

    def build_layout(self):
        main_layout = QVBoxLayout(self)

        model_group = QGroupBox("Модель")
        model_layout = QGridLayout(model_group)

        model_layout.addWidget(QLabel("Желаемый голос:"), 0, 0)
        model_layout.addWidget(self.model_box, 0, 1)

        model_layout.addWidget(QLabel("Index:"), 1, 0)
        model_layout.addWidget(self.index_box, 1, 1)

        model_layout.addWidget(self.refresh_button, 2, 0, 1, 2)

        main_layout.addWidget(model_group)

        files_group = QGroupBox("Файлы")
        files_layout = QGridLayout(files_group)

        files_layout.addWidget(QLabel("Входной WAV:"), 0, 0)
        files_layout.addWidget(self.input_edit, 0, 1)
        files_layout.addWidget(self.input_button, 0, 2)

        files_layout.addWidget(QLabel("Выходной WAV:"), 1, 0)
        files_layout.addWidget(self.output_edit, 1, 1)
        files_layout.addWidget(self.output_button, 1, 2)

        self.input_button.clicked.connect(self.choose_input)
        self.output_button.clicked.connect(self.choose_output)

        main_layout.addWidget(files_group)

        settings_group = QGroupBox("Параметры")
        settings_layout = QGridLayout(settings_group)

        settings_layout.addWidget(QLabel("Pitch:"), 0, 0)
        settings_layout.addWidget(self.pitch_spin, 0, 1)

        settings_layout.addWidget(QLabel("F0 method:"), 0, 2)
        settings_layout.addWidget(self.f0_box, 0, 3)

        settings_layout.addWidget(QLabel("Index rate:"), 1, 0)
        settings_layout.addWidget(self.index_rate_spin, 1, 1)

        settings_layout.addWidget(QLabel("Filter radius:"), 1, 2)
        settings_layout.addWidget(self.filter_radius_spin, 1, 3)

        settings_layout.addWidget(QLabel("Resample sr:"), 2, 0)
        settings_layout.addWidget(self.resample_spin, 2, 1)

        settings_layout.addWidget(QLabel("RMS mix rate:"), 2, 2)
        settings_layout.addWidget(self.rms_spin, 2, 3)

        settings_layout.addWidget(QLabel("Protect:"), 3, 0)
        settings_layout.addWidget(self.protect_spin, 3, 1)

        main_layout.addWidget(settings_group)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.run_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.clear_console_button)

        main_layout.addLayout(buttons_layout)

        console_group = QGroupBox("Консоль")
        console_layout = QVBoxLayout(console_group)
        console_layout.addWidget(self.console)

        main_layout.addWidget(console_group)

    def connect_signals(self):
        self.refresh_button.clicked.connect(self.refresh_models_and_indexes)
        self.run_button.clicked.connect(self.run_inference)
        self.stop_button.clicked.connect(self.stop_inference)
        self.clear_console_button.clicked.connect(self.console.clear)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0f1722;
                color: #e6edf3;
                font-size: 14px;
            }

            QGroupBox {
                border: 1px solid #344050;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
                background-color: #1d2735;
                border: 1px solid #3a4657;
                border-radius: 6px;
                padding: 6px;
                color: #e6edf3;
            }

            QPushButton {
                background-color: #ff6a00;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #ff7f22;
            }

            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)

    def log(self, text):
        self.console.appendPlainText(text.rstrip())

    def set_controls_enabled(self, enabled: bool):
        self.model_box.setEnabled(enabled)
        self.index_box.setEnabled(enabled)

        self.input_edit.setEnabled(enabled)
        self.output_edit.setEnabled(enabled)
        self.input_button.setEnabled(enabled)
        self.output_button.setEnabled(enabled)

        self.pitch_spin.setEnabled(enabled)
        self.f0_box.setEnabled(enabled)
        self.index_rate_spin.setEnabled(enabled)
        self.filter_radius_spin.setEnabled(enabled)
        self.resample_spin.setEnabled(enabled)
        self.rms_spin.setEnabled(enabled)
        self.protect_spin.setEnabled(enabled)

        self.refresh_button.setEnabled(enabled)
        self.run_button.setEnabled(enabled)
        self.stop_button.setEnabled(not enabled)

        # Консоль можно очищать даже во время работы процесса.
        self.clear_console_button.setEnabled(True)

    def refresh_models_and_indexes(self):
        self.model_box.clear()
        self.index_box.clear()

        self.index_box.addItem("", "")

        weights_dir = self.root_dir / "assets" / "weights"
        logs_dir = self.root_dir / "logs"

        if weights_dir.exists():
            for path in sorted(weights_dir.glob("*.pth")):
                self.model_box.addItem(path.name, path.name)

        if logs_dir.exists():
            for path in sorted(logs_dir.rglob("*.index")):
                if "trained" in path.name:
                    continue

                relative_path = path.relative_to(self.root_dir)
                self.index_box.addItem(str(relative_path), str(relative_path))

        self.log("Model/index list refreshed.")

    def choose_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать входной WAV",
            str(self.root_dir),
            "Audio files (*.wav *.flac *.mp3);;All files (*.*)"
        )

        if path:
            self.input_edit.setText(path)

            output_dir = self.root_dir / "outputs"
            output_dir.mkdir(exist_ok=True)

            input_name = Path(path).stem
            self.output_edit.setText(str(output_dir / f"{input_name}_rvc.wav"))

    def choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Выбрать выходной WAV",
            str(self.root_dir / "outputs" / "output.wav"),
            "WAV files (*.wav);;All files (*.*)"
        )

        if path:
            self.output_edit.setText(path)

    def run_inference(self):
        model = self.model_box.currentData()
        index = self.index_box.currentData()
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()

        if not model:
            self.log("ERROR: Model is not selected.")
            return

        if not input_path:
            self.log("ERROR: Input file is not selected.")
            return

        if not output_path:
            self.log("ERROR: Output file is not selected.")
            return

        script_path = self.root_dir / "rvc_infer_cli.py"

        if not script_path.exists():
            self.log(f"ERROR: Script not found: {script_path}")
            return

        args = [
            str(script_path),
            "--model", model,
            "--input", input_path,
            "--output", output_path,
            "--pitch", str(self.pitch_spin.value()),
            "--f0-method", self.f0_box.currentText(),
            "--index-rate", str(self.index_rate_spin.value()),
            "--filter-radius", str(self.filter_radius_spin.value()),
            "--resample-sr", str(self.resample_spin.value()),
            "--rms-mix-rate", str(self.rms_spin.value()),
            "--protect", str(self.protect_spin.value()),
        ]

        if index:
            args.extend(["--index", index])

        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(self.root_dir))
        self.process.setProgram(sys.executable)
        self.process.setArguments(args)

        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.process_finished)

        self.set_controls_enabled(False)

        self.log("=" * 80)
        self.log("Starting RVC inference...")
        self.log(f"Model: {model}")
        self.log(f"Input: {input_path}")
        self.log(f"Output: {output_path}")
        self.log(f"F0 method: {self.f0_box.currentText()}")
        self.log(f"Index: {index}")
        self.log("=" * 80)

        self.process.start()

    def read_stdout(self):
        if self.process is None:
            return

        data = self.process.readAllStandardOutput().data().decode(
            "utf-8",
            errors="replace"
        )

        if data:
            self.log(data)

    def read_stderr(self):
        if self.process is None:
            return

        data = self.process.readAllStandardError().data().decode(
            "utf-8",
            errors="replace"
        )

        if data:
            self.log(data)

    def process_finished(self, exit_code, exit_status):
        self.log("=" * 80)
        self.log(f"Process finished. Exit code: {exit_code}")
        self.log("=" * 80)

        self.set_controls_enabled(True)
        self.process = None

    def stop_inference(self):
        if self.process is not None:
            self.log("Stopping process...")
            self.process.kill()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RvcGui()
    window.show()
    sys.exit(app.exec())