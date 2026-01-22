#!/usr/bin/env python3
"""
NOVEL NARRATOR - Windows GUI Edition v3.2
Professional audiobook generator with PyQt6 interface
Based on the proven Linux implementation
"""

import sys, os, subprocess, re, gc, time, logging, warnings, random
from pathlib import Path
from datetime import datetime
from contextlib import redirect_stderr, redirect_stdout
import io

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar, 
    QComboBox, QGroupBox, QRadioButton, QButtonGroup, QSlider
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

import torch, torchaudio, concurrent.futures

# Suppress all warnings
warnings.filterwarnings('ignore')
os.environ.update({
    'TF_CPP_MIN_LOG_LEVEL': '3', 'PYTHONWARNINGS': 'ignore',
    'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True', 'TORCH_LOGS': 'OFF'
})

for m in ['transformers', 'torch', 'onnxruntime', 'tensorflow', 'phonemizer', 'g2p_en']:
    logging.getLogger(m).setLevel(logging.CRITICAL)

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_dir / f'narrator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')]
)


def install_kokoro():
    """Install Kokoro if not available"""
    try:
        from kokoro import KPipeline
        return True, "Kokoro ready"
    except ImportError:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-q', 'kokoro'],
                timeout=300,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                check=True
            )
            from kokoro import KPipeline
            return True, "Kokoro installed (v0.9.4)"
        except Exception as e:
            return False, f"Failed to install Kokoro: {e}"


# Import all classes from original script
class Config:
    SAMPLE_RATE, TORCH_DTYPE, KOKORO_VOICE = 24000, torch.float32, "bf_emma"
    MAX_RETRIES, MIN_TEXT_LENGTH, SPEED, EMPHASIS = 3, 10, 1.0, 1.15
    OUTPUT_DIR = Path("output")
    MAX_WORKERS, CHUNK_SIZE, RETRY_DELAY, CPU_MODE = None, 250, 1, False
    VOICES = {
        'af_bella': '[US-F] Bella (Warm, Friendly)', 'af_sarah': '[US-F] Sarah (Energetic)',
        'af_nicole': '[US-F] Nicole (Professional)', 'af_sky': '[US-F] Sky (Bright)',
        'am_adam': '[US-M] Adam (Warm, Engaging)', 'am_michael': '[US-M] Michael (Deep)',
        'bf_emma': '[UK-F] Emma (Warm, Professional) ★ BEST', 'bm_george': '[UK-M] George (Classic)',
    }
    @staticmethod
    def setup_from_hardware(hw):
        Config.GPU_TYPE, Config.GPU_NAME = hw['gpu_type'], hw['gpu_name']
        Config.CPU_CORES, Config.CPU_NAME = hw['cpu_cores'], hw['cpu_name']
        Config.CPU_MODE = (hw['gpu_type'] is None)
        if hw['gpu_type'] == "NVIDIA":
            Config.MAX_WORKERS = max(2, min(hw['cpu_cores'] - 1, 4))
            Config.CHUNK_SIZE = max(150, int(500 - (hw['gpu_mem'] / 8) * 50))
        else:
            Config.MAX_WORKERS = max(1, min(hw['cpu_cores'] // 2, 2))
            Config.CHUNK_SIZE = 100


class Hardware:
    _cached = None
    @classmethod
    def detect(cls):
        if cls._cached: return cls._cached
        gpu_type, gpu_name, gpu_mem = None, "CPU", 0
        try:
            if torch.cuda.is_available():
                gpu_type = "NVIDIA"
                gpu_name = torch.cuda.get_device_name(0)
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        except: pass
        cores = os.cpu_count() or 1
        try:
            import platform
            cpu_name = platform.processor() or "CPU"
        except:
            cpu_name = "CPU"
        cls._cached = {'gpu_type': gpu_type, 'gpu_name': gpu_name, 'gpu_mem': gpu_mem, 'cpu_name': cpu_name, 'cpu_cores': cores}
        return cls._cached


# Copy entire TextProcessor class from original (abbreviated for space)
class TextProcessor:
    SENT_PATTERN = re.compile(r'(?<=[.!?:;…])\s+')
    SPACE_PATTERN = re.compile(r'\s+')
    ABBREV_MAP = {
        r'\bDr\.': 'Doctor', r'\bMr\.': 'Mister', r'\bMrs\.': 'Missus', r'\bMs\.': 'Miss',
        r'\bSt\.': 'Street', r'\bAve\.': 'Avenue', r'\bEtc\.': 'and so on',
    }
    PRONUNCIATION_MAP = {
        r'\bquiet\b': 'kwiet', r'\bquite\b': 'kwite', r'\bpoetry\b': 'po-it-ree',
        r'\bchaos\b': 'kay-os', r'\bwould\b': 'wood',
    }
    @staticmethod
    def extract_odt(fp):
        try:
            from odf.opendocument import load
            from odf import text as odf_text
            doc = load(str(fp))
            return '\n'.join(TextProcessor._get_text(p).strip() for p in doc.getElementsByType(odf_text.P) if TextProcessor._get_text(p).strip())
        except: return None
    @staticmethod
    def extract_docx(fp):
        try:
            from docx import Document
            return '\n'.join(p.text for p in Document(str(fp)).paragraphs if p.text.strip())
        except: return None
    @staticmethod
    def extract_txt(fp):
        for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(fp, 'r', encoding=enc, errors='ignore') as f:
                    return f.read().strip()
            except: pass
        return None
    @staticmethod
    def _get_text(node):
        text = getattr(node, 'data', '')
        if hasattr(node, 'childNodes'):
            text += ''.join(TextProcessor._get_text(child) for child in node.childNodes)
        return text
    @staticmethod
    def extract(fp):
        p = Path(fp)
        if not p.exists(): return None
        extractors = {'.odt': TextProcessor.extract_odt, '.docx': TextProcessor.extract_docx}
        return extractors.get(p.suffix.lower(), TextProcessor.extract_txt)(fp)
    @staticmethod
    def clean(text):
        if not text: return ""
        # Full cleaning pipeline from original
        for abbrev, expansion in TextProcessor.ABBREV_MAP.items():
            text = re.sub(abbrev, expansion, text, flags=re.IGNORECASE)
        text = re.sub(r'\.{3,}', ' pause ', text)
        text = re.sub(r'\*([^*]+)\*', r'emphasized \1', text)
        text = re.sub(r'\$(\d+(?:\.\d{2})?)', r'dollar \1', text)
        text = re.sub(r'\'s\b', ' is ', text)
        text = re.sub(r'["""]', ' ', text)
        text = TextProcessor.SPACE_PATTERN.sub(' ', text).strip()
        for pat, repl in TextProcessor.PRONUNCIATION_MAP.items():
            text = re.sub(pat, repl, text, flags=re.IGNORECASE)
        return text
    @staticmethod
    def split_chunks(text):
        if not text: return []
        sentences = [s.strip() for s in TextProcessor.SENT_PATTERN.split(text) if s.strip() and len(s.strip()) >= Config.MIN_TEXT_LENGTH]
        chunks, current = [], ""
        for sent in sentences:
            test = current + sent + " "
            if len(test) <= Config.CHUNK_SIZE:
                current = test
            else:
                if current.strip(): chunks.append(current.strip())
                current = sent + " "
        if current.strip(): chunks.append(current.strip())
        return chunks


class KokoroTTS:
    def __init__(self):
        try:
            from kokoro import KPipeline
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                self.pipeline = KPipeline(lang_code="a")
        except Exception as e:
            raise
    def synthesize(self, text, speed=1.0):
        if not text or len(text) < Config.MIN_TEXT_LENGTH:
            return torch.zeros(1, 24000), Config.SAMPLE_RATE
        try:
            with torch.no_grad():
                audio_list = []
                for result in self.pipeline(text, voice=Config.KOKORO_VOICE, speed=speed):
                    try:
                        if hasattr(result, 'output') and hasattr(result.output, 'audio'):
                            audio = result.output.audio.detach().cpu()
                            if audio.dim() == 1: audio = audio.unsqueeze(0)
                            elif audio.dim() == 2 and audio.shape[0] > 1: audio = audio[0:1]
                            if audio.numel() > 0 and audio.shape[-1] > 0: audio_list.append(audio)
                    except: continue
                return (torch.cat(audio_list, dim=1), Config.SAMPLE_RATE) if audio_list else (torch.zeros(1, 24000), Config.SAMPLE_RATE)
        except:
            return torch.zeros(1, 24000), Config.SAMPLE_RATE


class AudioGenerationWorker(QThread):
    progress = pyqtSignal(int, int)
    status = pyqtSignal(str)
    finished_signal = pyqtSignal(str, float, float)
    error_signal = pyqtSignal(str)
    
    def __init__(self, chunks, output_path, speed=1.0):
        super().__init__()
        self.chunks = chunks
        self.output_path = output_path
        self.speed = speed
        self.should_stop = False
    
    def run(self):
        try:
            start_time = time.time()
            self.status.emit("Initializing TTS engine...")
            tts = KokoroTTS()
            self.status.emit(f"Processing {len(self.chunks)} chunks...")
            audio_dict, completed = {}, 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as ex:
                futures = {ex.submit(self._synth, tts, i, c): i for i, c in enumerate(self.chunks, 1)}
                for future in concurrent.futures.as_completed(futures):
                    if self.should_stop:
                        ex.shutdown(wait=False, cancel_futures=True)
                        self.error_signal.emit("Cancelled")
                        return
                    try:
                        idx, audio = future.result(timeout=120)
                        audio_dict[idx] = audio
                        completed += 1
                        self.progress.emit(completed, len(self.chunks))
                    except:
                        completed += 1
                        self.progress.emit(completed, len(self.chunks))
            if not audio_dict:
                self.error_signal.emit("No audio generated")
                return
            self.status.emit("Combining audio...")
            audio_tensors = [audio_dict[i] for i in sorted(audio_dict.keys()) if audio_dict[i].numel() > 100]
            if not audio_tensors:
                self.error_signal.emit("No valid audio")
                return
            combined = torch.cat(audio_tensors, dim=1)
            self.status.emit("Saving...")
            torchaudio.save(str(self.output_path), combined, Config.SAMPLE_RATE)
            elapsed = time.time() - start_time
            duration = combined.shape[1] / Config.SAMPLE_RATE
            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()
            self.finished_signal.emit(str(self.output_path), duration, elapsed)
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def _synth(self, tts, idx, chunk):
        try:
            audio, sr = tts.synthesize(chunk, speed=self.speed)
            return (idx, audio)
        except:
            return (idx, torch.zeros(1, 24000))
    
    def stop(self):
        self.should_stop = True


class NovelNarratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.selected_file = None
        self.init_ui()
        QTimer.singleShot(100, self.post_init)
    
    def init_ui(self):
        self.setWindowTitle("Novel Narrator - Audiobook Generator")
        self.setMinimumSize(850, 650)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("📖 Novel Narrator")
        font = QFont()
        font.setPointSize(22)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Transform books into professional audiobooks")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 11pt;")
        layout.addWidget(subtitle)
        
        # Hardware
        hw_group = QGroupBox("System Status")
        hw_layout = QVBoxLayout()
        self.hw_label = QLabel("Checking system...")
        hw_layout.addWidget(self.hw_label)
        hw_group.setLayout(hw_layout)
        layout.addWidget(hw_group)
        
        # File
        file_group = QGroupBox("📄 Step 1: Select Your Book")
        file_layout = QVBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("padding: 8px; background: #f5f5f5; border-radius: 4px;")
        file_layout.addWidget(self.file_label)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        browse_btn.setMinimumHeight(36)
        file_layout.addWidget(browse_btn)
        supp = QLabel("Supports: .txt, .docx, .odt")
        supp.setStyleSheet("color: #888; font-size: 9pt;")
        file_layout.addWidget(supp)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Voice
        voice_group = QGroupBox("🎤 Step 2: Choose Voice")
        voice_layout = QVBoxLayout()
        self.voice_combo = QComboBox()
        for key, desc in Config.VOICES.items():
            self.voice_combo.addItem(desc, key)
        self.voice_combo.setCurrentIndex(6)  # Emma
        self.voice_combo.currentIndexChanged.connect(self.voice_changed)
        voice_layout.addWidget(self.voice_combo)
        test_btn = QPushButton("🔊 Test Voice")
        test_btn.clicked.connect(self.test_voice)
        voice_layout.addWidget(test_btn)
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)
        
        # Speed
        speed_group = QGroupBox("⚡ Step 3: Reading Speed")
        speed_layout = QVBoxLayout()
        speed_btns = QHBoxLayout()
        self.speed_group = QButtonGroup()
        for i, (lbl, spd) in enumerate([("Slow", 0.75), ("Normal", 1.0), ("Fast", 1.25)]):
            rb = QRadioButton(f"{lbl} ({spd}x)")
            rb.setProperty("speed", spd)
            rb.clicked.connect(self.speed_changed)
            self.speed_group.addButton(rb, i)
            speed_btns.addWidget(rb)
            if spd == 1.0: rb.setChecked(True)
        speed_layout.addLayout(speed_btns)
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # Progress
        prog_group = QGroupBox("📊 Progress")
        prog_layout = QVBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        prog_layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        prog_layout.addWidget(self.progress_bar)
        prog_group.setLayout(prog_layout)
        layout.addWidget(prog_group)
        
        # Generate
        self.generate_btn = QPushButton("🎬 Generate Audiobook")
        self.generate_btn.setMinimumHeight(45)
        self.generate_btn.setStyleSheet("""
            QPushButton { background: #4CAF50; color: white; font-size: 13pt; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #45a049; }
            QPushButton:disabled { background: #ccc; color: #666; }
        """)
        self.generate_btn.clicked.connect(self.generate_audiobook)
        self.generate_btn.setEnabled(False)
        layout.addWidget(self.generate_btn)
        
        # Cancel
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.setStyleSheet("QPushButton { background: #f44336; color: white; border-radius: 4px; }")
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.cancel_btn.setVisible(False)
        layout.addWidget(self.cancel_btn)
        
        self.statusBar().showMessage("Ready")
    
    def post_init(self):
        self.status_label.setText("Checking dependencies...")
        QApplication.processEvents()
        success, msg = install_kokoro()
        if not success:
            QMessageBox.critical(self, "Error", f"Failed to install Kokoro:\n{msg}")
            self.status_label.setText("❌ Dependency error")
            return
        hw = Hardware.detect()
        Config.setup_from_hardware(hw)
        lines = []
        if hw['gpu_type']:
            lines.append(f"✅ GPU: {hw['gpu_name']} ({hw['gpu_mem']:.1f}GB)")
        else:
            lines.append(f"💻 CPU: {hw['cpu_name']}")
            lines.append("⚠️ No GPU (slower processing)")
        lines.append(f"Workers: {Config.MAX_WORKERS}")
        self.hw_label.setText("\n".join(lines))
        self.status_label.setText("✅ Ready to generate audiobooks!")
    
    def browse_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select Book", "", "Books (*.txt *.docx *.odt);;All Files (*)")
        if fname:
            self.selected_file = Path(fname)
            self.file_label.setText(f"Selected: {self.selected_file.name}")
            self.generate_btn.setEnabled(True)
            self.statusBar().showMessage(f"File: {self.selected_file.name}")
    
    def voice_changed(self):
        Config.KOKORO_VOICE = self.voice_combo.currentData()
    
    def speed_changed(self):
        btn = self.speed_group.checkedButton()
        if btn:
            Config.SPEED = btn.property("speed")
    
    def test_voice(self):
        self.status_label.setText("Testing voice...")
        QApplication.processEvents()
        try:
            tts = KokoroTTS()
            sample = "The quiet moment stretched before us."
            audio, sr = tts.synthesize(TextProcessor.clean(sample), Config.SPEED)
            path = Config.OUTPUT_DIR / f"test_{Config.KOKORO_VOICE}.wav"
            Config.OUTPUT_DIR.mkdir(exist_ok=True)
            torchaudio.save(str(path), audio, sr)
            QMessageBox.information(self, "Voice Test", f"Test saved to:\n{path}\n\nPlay this file to hear the voice!")
            self.status_label.setText("Test complete")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Test failed: {e}")
            self.status_label.setText("Test failed")
    
    def generate_audiobook(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File", "Please select a book first")
            return
        self.status_label.setText("Reading file...")
        QApplication.processEvents()
        raw = TextProcessor.extract(str(self.selected_file))
        if not raw:
            QMessageBox.critical(self, "Error", "Could not read file")
            return
        clean = TextProcessor.clean(raw)
        chunks = TextProcessor.split_chunks(clean)
        if not chunks:
            QMessageBox.critical(self, "Error", "No text found in file")
            return
        reply = QMessageBox.question(self, "Confirm", 
            f"Book: {self.selected_file.name}\n"
            f"Length: {len(clean):,} characters\n"
            f"Chunks: {len(chunks)}\n"
            f"Voice: {Config.VOICES[Config.KOKORO_VOICE]}\n"
            f"Speed: {Config.SPEED}x\n\n"
            f"Estimated time: {len(chunks) * 2 // Config.MAX_WORKERS // 60} minutes\n\n"
            "Start generation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Config.OUTPUT_DIR / f"{self.selected_file.stem}_narrated_{ts}.wav"
        Config.OUTPUT_DIR.mkdir(exist_ok=True)
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.worker = AudioGenerationWorker(chunks, output, Config.SPEED)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished_signal.connect(self.generation_finished)
        self.worker.error_signal.connect(self.generation_error)
        self.worker.start()
    
    def update_progress(self, curr, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(curr)
        pct = (curr / total * 100) if total > 0 else 0
        self.progress_bar.setFormat(f"{curr}/{total} ({pct:.0f}%)")
    
    def update_status(self, msg):
        self.status_label.setText(msg)
    
    def generation_finished(self, path, duration, elapsed):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        size_mb = Path(path).stat().st_size / 1024 / 1024
        perf = duration / elapsed if elapsed > 0 else 0
        QMessageBox.information(self, "Success!", 
            f"Audiobook generated!\n\n"
            f"File: {Path(path).name}\n"
            f"Duration: {duration/60:.1f} minutes\n"
            f"Size: {size_mb:.1f} MB\n"
            f"Processing: {elapsed:.0f}s ({perf:.1f}x realtime)\n\n"
            f"Saved to: {path}")
        self.status_label.setText("✅ Complete!")
        self.statusBar().showMessage(f"Saved: {Path(path).name}")
    
    def generation_error(self, msg):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        QMessageBox.critical(self, "Error", f"Generation failed:\n{msg}")
        self.status_label.setText("❌ Failed")
    
    def cancel_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Cancelling...")


def main():
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.set_grad_enabled(False)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = NovelNarratorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()