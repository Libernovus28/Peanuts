# Novel Narrator - Windows Edition

**Professional Audiobook Generator with GPU Acceleration**

Transform your books into high-quality audiobooks with natural-sounding AI voices.

---

## 🚀 Quick Start

### For Users (Non-Technical)

1. **Extract** the ZIP file to a folder
2. **Double-click** `NovelNarrator.exe`
3. **Select your book** (.txt, .docx, or .odt file)
4. **Choose a voice** (Emma is recommended)
5. **Click "Generate Audiobook"**
6. **Wait** for processing to complete
7. **Find your audiobook** in the `output` folder

### For Developers (Building from Source)

1. **Install Python 3.9-3.11** from https://python.org (check "Add to PATH")
2. **Run** `build_windows.bat`
3. **Choose option 2** to build the executable
4. **Find executable** in `dist\NovelNarrator\`

---

## 📋 System Requirements

### Minimum
- Windows 10 (64-bit) or Windows 11
- 4 GB RAM
- 5 GB free disk space
- Dual-core processor

### Recommended
- 8 GB RAM or more
- NVIDIA GPU with CUDA support (10x faster!)
- 10 GB free disk space

---

## 📖 Features

- ✅ **Natural AI Voices** - 8 professional voices (US & UK accents)
- ✅ **GPU Acceleration** - Automatic NVIDIA CUDA support with CPU fallback
- ✅ **Multiple Formats** - Supports .txt, .docx, and .odt files
- ✅ **Smart Text Processing** - Handles abbreviations, pronunciations, emphasis
- ✅ **Parallel Processing** - Multi-threaded for maximum speed
- ✅ **Progress Tracking** - Real-time progress bar and status updates
- ✅ **Voice Testing** - Preview voices before generating full audiobook
- ✅ **Adjustable Speed** - Slow (0.75x), Normal (1.0x), or Fast (1.25x)
- ✅ **High Quality** - 24kHz audio output

---

## 🎤 Available Voices

| Voice | Description | Accent |
|-------|-------------|--------|
| **Emma** ⭐ | Warm, Professional (Best) | UK Female |
| **George** | Classic, Authoritative | UK Male |
| **Bella** | Warm, Friendly | US Female |
| **Adam** | Warm, Engaging | US Male |
| **Sarah** | Energetic | US Female |
| **Michael** | Deep | US Male |
| **Nicole** | Professional | US Female |
| **Sky** | Bright | US Female |

**Recommended**: Emma (UK Female) - Best overall quality

---

## 📂 File Support

### Supported Input Formats
- `.txt` - Plain text files
- `.docx` - Microsoft Word documents
- `.odt` - OpenDocument text files

### Output Format
- `.wav` - Uncompressed audio (24kHz, high quality)

---

## ⚡ Performance

| Hardware | Speed | Time for 300-page Book |
|----------|-------|------------------------|
| **NVIDIA RTX 3060+** | 8-10x realtime | 8-12 minutes |
| **NVIDIA GTX 1060+** | 5-7x realtime | 15-20 minutes |
| **Modern CPU (8 cores)** | 1-2x realtime | 40-60 minutes |
| **Basic CPU (4 cores)** | 0.5-1x realtime | 90-120 minutes |

*"Realtime" = 1 hour of audio generated per 1 hour of processing*

---

## 🛠️ Building from Source

### Prerequisites
```bash
# Python 3.9-3.11 (NOT 3.12)
python --version

# Git (optional)
git --version
```

### Build Steps

1. **Clone or download** this repository
2. **Open Command Prompt** in the project folder
3. **Run the build script**:
   ```batch
   build_windows.bat
   ```
4. **Choose option**:
   - `1` - Run in development mode (test first)
   - `2` - Build standalone executable
   - `3` - Exit

### Manual Build (Advanced)

```batch
# Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

# Install dependencies
pip install PyQt6 kokoro python-docx odfpy pyinstaller

# Install PyTorch (choose one):
# For NVIDIA GPU:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CPU only:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Build executable
pyinstaller --name=NovelNarrator --onedir --windowed --icon=icon.ico novel_narrator_gui.py
```

---

## 🔒 Code Signing (Optional)

### Free Self-Signed Certificate

**Creates a signature but triggers Windows SmartScreen warnings**

```powershell
# Open PowerShell as Administrator
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=YourName" -CertStoreLocation "Cert:\CurrentUser\My"
$password = ConvertTo-SecureString -String "YourPassword" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath "certificate.pfx" -Password $password

# Install Windows SDK for SignTool
winget install Microsoft.WindowsSDK

# Sign the executable
signtool sign /f certificate.pfx /p YourPassword /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 "dist\NovelNarrator\NovelNarrator.exe"
```

### Trusted Certificate (No Warnings)

- **Free for Open Source**: SignPath.io
- **Commercial**: DigiCert, Sectigo ($200-500/year)
- **Extended Validation**: $500/year (immediate trust)

---

## 🆘 Troubleshooting

### "Python is not recognized..."
- Python not installed or not in PATH
- **Fix**: Reinstall Python, CHECK "Add Python to PATH"

### "Failed to install Kokoro"
- Network issue or PyPI timeout
- **Fix**: Manual install: `pip install kokoro`

### Application won't start
- Missing dependencies or corrupted build
- **Fix**: Run `build_windows.bat` again with option 1 to test

### Windows SmartScreen warning
- Normal for self-signed or unsigned apps
- **Users can bypass**: Click "More info" → "Run anyway"
- **Long-term fix**: Get trusted certificate

### GPU not detected
- CUDA not installed or incompatible GPU
- **Fix**: App automatically falls back to CPU
- **Optional**: Install CUDA Toolkit from NVIDIA

### Very slow processing
- Running on CPU (no GPU detected)
- **Expected**: CPU is 5-10x slower than GPU
- **Fix**: Reduce book length or wait longer

### Large file size (2GB+ build)
- CUDA PyTorch is very large (~2GB)
- **Fix**: Build with CPU-only PyTorch (smaller but still supports GPU at runtime)

---

## 📁 Project Structure

```
novel-narrator-windows/
├── novel_narrator_gui.py      # Main GUI application
├── build_windows.bat           # Automated build script
├── debug_kokoro.bat            # Dependency testing script
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── icon.ico                    # Application icon (optional)
├── certificate.pfx             # Code signing cert (don't commit!)
├── venv/                       # Virtual environment (auto-created)
├── logs/                       # Application logs (auto-created)
├── output/                     # Generated audiobooks (auto-created)
├── dist/                       # Built application (after build)
│   └── NovelNarrator/
│       ├── NovelNarrator.exe   # Main executable
│       ├── _internal/          # Dependencies (required!)
│       ├── output/             # User audiobooks
│       └── logs/               # Runtime logs
└── build/                      # Build cache (can delete)
```

---

## 🔧 Configuration

### Changing Default Voice
Edit `novel_narrator_gui.py` line ~50:
```python
KOKORO_VOICE = "bf_emma"  # Change to: af_bella, am_adam, etc.
```

### Adjusting Performance
Edit `Config` class in `novel_narrator_gui.py`:
```python
MAX_WORKERS = 4      # Parallel threads (2-8 recommended)
CHUNK_SIZE = 250     # Text chunk size (100-500)
```

### Custom Pronunciations
Add to `PRONUNCIATION_MAP` in `TextProcessor` class:
```python
r'\bYOURWORD\b': 'pronunciation-guide',
```

---

## 📄 License

This project uses:
- **Kokoro TTS**: Apache 2.0 License (https://github.com/hexgrad/kokoro)
- **PyQt6**: GPL v3 / Commercial License
- **PyTorch**: BSD License

### Legal Notice
- Only convert books you own or have rights to
- Respect copyright laws in your jurisdiction
- This tool is for personal use and legitimate purposes

---

## 🤝 Contributing

### Bug Reports
Include:
- Windows version
- Python version
- Error message from `logs/narrator_*.log`
- Steps to reproduce

### Feature Requests
- Open an issue on GitHub
- Describe the feature and use case
- Include mockups if applicable

---

## 📊 Technical Details

### Dependencies
- **PyQt6** 6.6.0+ - GUI framework
- **PyTorch** 2.1.0+ - ML framework
- **Kokoro** 0.9.4+ - TTS engine
- **python-docx** - Word document support
- **odfpy** - OpenDocument support

### Audio Specifications
- **Sample Rate**: 24,000 Hz
- **Bit Depth**: 32-bit float (internal)
- **Channels**: Mono
- **Format**: WAV (uncompressed)

### Processing Pipeline
1. Extract text from document
2. Clean and normalize text
3. Expand abbreviations and acronyms
4. Apply pronunciation fixes
5. Split into optimized chunks
6. Parallel synthesis with Kokoro
7. Concatenate audio segments
8. Save as WAV file

---

## 🌟 Tips for Best Results

### For Better Quality
- Use UK-English voice "Emma" (highest quality)
- Keep sentences grammatically correct
- Remove excessive formatting from source
- Use plain text files when possible

### For Faster Processing
- Use GPU if available (10x faster)
- Reduce chunk size for lower memory usage
- Close other applications during processing
- Use SSD instead of HDD if possible

### For Large Books
- Split very large books into parts
- Process overnight for books over 500 pages
- Monitor RAM usage (8GB+ recommended for large books)

---

## 📞 Support

### Documentation
- Full setup guide: `COMPLETE_SETUP_GUIDE.md`
- Signing guide: See README section above
- Quick fixes: `QUICK_FIX.md`

### Logs
Check `logs/narrator_*.log` for detailed error messages

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Share tips and experiences

---

## ✅ Version History

### v3.2 (Current)
- Windows GUI version
- GPU acceleration with automatic CPU fallback
- 8 professional voices
- Multiple document formats
- Real-time progress tracking
- Voice preview feature

### v3.0 (Linux)
- Original command-line version
- Ubuntu/Debian support
- Parallel processing
- Advanced text normalization

---

## 🎯 Roadmap

### Planned Features
- [ ] MP3 export option
- [ ] Multiple voice support (character dialogue)
- [ ] Batch processing
- [ ] Cloud processing option
- [ ] Mac OS version
- [ ] Linux GUI version
- [ ] Built-in audio player
- [ ] Bookmarking/chapters
- [ ] Speed adjustment during playback

---

**Made with ❤️ - Novel Narrator Team**

*Transform your reading into listening*