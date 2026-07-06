# Enterprise Knowledge Document Converter (EKDC)

Welcome to the **Enterprise Knowledge Document Converter (EKDC)**! 

As part of the Enterprise Knowledge RAG System, the EKDC serves as an intelligent background agent that continuously monitors your data ingestion folders. Its core mission is to seamlessly transform disparate file formats—ranging from Office documents and PDFs to images, audio, and video—into a unified Markdown format. This structured Markdown is essential for ensuring high-quality data ingestion for Retrieval-Augmented Generation (RAG) models.

---

## 🌟 Key Features
- **Continuous Synchronization**: Watches your `input_docs` directory 24/7. When a file is created, modified, or deleted, the output is updated instantly.
- **Universal Format Support**: Intelligently converts Documents (PDF, DOCX, PPTX), Media (Audio/Video), Images (OCR), and standard Text files.
- **Image Capture (zero loss)**: Embedded pictures in documents *and* standalone image files are carried into the Markdown (linked files by default). Configurable via `EKDC_DOCLING_IMAGE_MODE`.
- **File Metadata**: Optionally prepends a YAML metadata block (source path, size, timestamps, SHA-256, MIME) to every `.md`.
- **Optional AI Image Descriptions**: A multimodal (vision) model can describe images so their *meaning* is searchable. **Opt-in and OFF by default** so machines without a GPU are never burdened.
- **Structure Preservation**: Automatically mirrors your input folder hierarchy in the output directory.
- **Graceful Fallbacks**: Uses LibreOffice for complex DrawingML in Word documents, and handles extraction/model failures gracefully (a document always converts, even if optional enrichment is unavailable).

---

## 🛠️ Prerequisites

To ensure EKDC can convert every single file type seamlessly, you will need to install a few third-party system dependencies. **Please do not skip these if you intend to process media or complex documents.**

### 1. Python 3.10+
EKDC is built on Python. Ensure you have Python installed.
- **Download**: [python.org](https://www.python.org/downloads/)
- **Check**: Open terminal and run `python --version`

### 2. Tesseract OCR (For Image Text Extraction)
Required to extract text from images (PNG, JPG, BMP).
- **Download**: Download the Windows installer from [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
- **Install**: Run the installer. 
- **Configuration**: Ensure the installation path (usually `C:\Program Files\Tesseract-OCR`) is added to your Windows **System Environment `PATH`**.

### 3. FFmpeg (For Audio & Video Transcription)
Required by OpenAI's Whisper model and MoviePy to process media files.
- **Download**: Go to [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (the official Windows build provider) and download the `ffmpeg-release-essentials.zip` from the "release builds" section. 
  > **⚠️ IMPORTANT:** Do *not* download the "Source Code" from the main ffmpeg.org site, as it requires manual compilation and does not contain the `bin` folder.
- **Install**: 
  1. Extract the zip file. It usually creates a folder named something like `ffmpeg-2023-XX-XX-essentials_build`.
  2. Inside that folder, you will find a `bin` folder containing `ffmpeg.exe`.
  3. Move or rename that main folder to `C:\ffmpeg` so your path is clean (e.g., `C:\ffmpeg\bin\ffmpeg.exe`).
  4. Add the `C:\ffmpeg\bin` folder to your Windows **System Environment `PATH`**.
- **Check**: Open a *new* terminal and run `ffmpeg -version`.

### 4. LibreOffice (For Complex Word Documents)
Required by the `docling` engine to process DrawingML and shapes inside DOCX files.
- **Download**: [libreoffice.org](https://www.libreoffice.org/download/download-libreoffice/)
- **Install**: Run the standard installer.
- **Configuration**: We will configure this in the `.env` file in the next section.

### 5. (Optional) Multimodal Model — only if you enable AI image descriptions
**Skip this entirely if you don't have a GPU or don't need image descriptions** (`EKDC_DESCRIBE_IMAGES=false`, the default). If you do want it:
- **Ollama (recommended):** install [Ollama](https://ollama.com/), run `ollama pull qwen2.5vl`, and `pip install langchain-ollama`.
- **HuggingFace:** the `transformers` stack downloads a **vision** model on first use (e.g. `Qwen/Qwen2.5-VL-7B-Instruct`). A GPU is strongly recommended.

---

## 🚀 Installation & Setup

### Step 1: Clone or Navigate to the Directory
Ensure your terminal is in the EKDC service folder:
```bash
cd "path/to/Enterprise-Knowledge-RAG-System/services/ekdc"
```

### Step 2: Install Python Dependencies
Install the required Python packages into your environment:
```bash
pip install -r requirements.txt
```
*(Note: If you run into issues with python-magic on Windows, the requirements file handles it by installing `python-magic-bin`.)*

### Step 3: Configure the `.env` file
EKDC uses a `.env` file to manage paths. Create a `.env` file in the root of the `ekdc` folder and add the following:

```env
# --- Paths ---
# The directory you want the agent to monitor for new files
INPUT_DIRECTORY="input_docs"

# The directory where the agent will save the Markdown conversions
OUTPUT_DIRECTORY="output_md"

# Point this to your LibreOffice executable to avoid DOCX conversion warnings
DOCLING_LIBREOFFICE_CMD="C:\Program Files\LibreOffice\program\soffice.exe"

# --- Image handling (light) ---
# referenced (default) | embedded | placeholder
EKDC_DOCLING_IMAGE_MODE=referenced

# --- Optional enrichment (see "Compute & GPU/CPU Control" below) ---
EKDC_INCLUDE_METADATA=true     # metadata front-matter (free, no model)
EKDC_DESCRIBE_IMAGES=false     # AI image descriptions (OFF by default; GPU recommended)
EKDC_VLM_PROVIDER=ollama       # ollama (recommended) | huggingface
EKDC_VLM_MODEL=qwen2.5vl        # a VISION model, e.g. qwen2.5vl or Qwen/Qwen2.5-VL-7B-Instruct
EKDC_VLM_BASE_URL=http://localhost:11434
# EKDC_VLM_PROMPT=Describe this image in detail for search indexing.
EKDC_VLM_MAX_NEW_TOKENS=256     # max tokens per image description (higher = longer, slower)
# HF_TOKEN=                     # optional: silences the HF "unauthenticated" warning + faster downloads

# --- Security (safe defaults) ---
# Skip input files larger than this many MB (resource-exhaustion / DoS guard). 0 = no limit.
EKDC_MAX_FILE_SIZE_MB=1024
# Allow executing custom modeling code shipped inside a HuggingFace model repo.
# OFF by default (safe). Only enable for a trusted model that requires it.
# EKDC_VLM_TRUST_REMOTE_CODE=false

# --- Persistent local-model storage ---
# Where downloaded HuggingFace VLM weights + Whisper models are cached.
# Leave blank to use <ekdc>/models. (Ollama models are managed by the Ollama server.)
EKDC_MODEL_CACHE_DIR=
```

---

## ⚙️ How to Use the Agent

Running the agent is incredibly straightforward.

**Start the Background Process:**
```bash
python agent.py
```

**What happens next?**
1. **Initial Sync**: The agent will scan `input_docs`. If there are files there, it will convert them to `output_md`. If a file was deleted while the agent was offline, it will clean up the corresponding markdown file.
2. **Watchdog Mode**: The agent will sit in the background and wait.
3. **Drop a file**: Open your file explorer and copy a file (e.g., `company_presentation.pptx`) into the `input_docs` folder. 
4. **Magic**: Look at your terminal, and you will see the conversion happening in real-time. Navigate to `output_md` to view your ready-to-use `.md` file!

To stop the agent, simply press `Ctrl + C` in your terminal.

---

## 🧩 Conversion Features (What Gets Captured)

EKDC is built for **zero information loss**. Every `.md` can include:

- **Text & Tables** — from all documents (PDF, DOCX, PPTX, HTML, CSV).
- **Images** — embedded pictures in documents *and* standalone image files, controlled by `EKDC_DOCLING_IMAGE_MODE`:
  - `referenced` *(default)* — images saved next to the `.md` in a `<name>_artifacts/` folder and linked with clean relative paths. **Best for RAG.**
  - `embedded` — images inlined as base64 (self-contained file, heavier/noisier for RAG).
  - `placeholder` — images dropped (text/tables only).
- **Scanned PDFs** — OCR'd automatically so image-based text is recovered.
- **File Metadata** — optional YAML front-matter (source path, size, timestamps, SHA-256, MIME, image dimensions) via `EKDC_INCLUDE_METADATA`.
- **AI Image Descriptions** *(optional)* — a vision model describes each image (added as `> **Image description:** ...`) so its meaning is searchable, via `EKDC_DESCRIBE_IMAGES`.
- **Audio/Video** — transcribed to text with Whisper.

---

## 🖥️ Compute & GPU/CPU Control (Enable / Disable)

> **The most important section for low-resource deployments.** Everything heavy is **opt-in and OFF by default**, so a customer **without a GPU is never burdened** unless they explicitly enable it.

| Feature | `.env` flag | Default | Compute footprint | To disable |
| :--- | :--- | :--- | :--- | :--- |
| File metadata front-matter | `EKDC_INCLUDE_METADATA` | `true` (on) | **None** (instant) | set `false` |
| Image capture in Markdown | `EKDC_DOCLING_IMAGE_MODE` | `referenced` | **Light** (image rasterize) | set `placeholder` |
| **AI image description** | `EKDC_DESCRIBE_IMAGES` | `false` (**off**) | **Heavy — GPU strongly recommended** | keep `false` |
| Audio/Video transcription (Whisper) | *(runs on media you feed)* | on | **Heavy — CPU/GPU** | don't feed audio/video |
| Scanned-doc / image OCR | *(runs on images & scans)* | on | **Moderate CPU** | — |

### ✅ Recommended presets

**Customer WITHOUT a GPU (or low-resource):** keep the defaults — the heavy AI describer stays off; text, tables, images, OCR and metadata still work on CPU.
```env
EKDC_INCLUDE_METADATA=true
EKDC_DESCRIBE_IMAGES=false      # <-- keep OFF: no GPU load, no large model download
EKDC_DOCLING_IMAGE_MODE=referenced
```

**Customer WITH a GPU (wants image understanding):**
```env
EKDC_DESCRIBE_IMAGES=true
EKDC_VLM_PROVIDER=ollama
EKDC_VLM_MODEL=qwen2.5vl         # a VISION model (see note below)
EKDC_VLM_BASE_URL=http://localhost:11434
```
Then: `pip install langchain-ollama` and `ollama pull qwen2.5vl`.

### 🔌 Turn AI image descriptions OFF
Set `EKDC_DESCRIBE_IMAGES=false` in `.env` and restart the agent. **No model is loaded and no GPU/CPU is spent on descriptions.** Conversion is unchanged — images are still captured as files/links, you just don't get AI descriptions.

### 🔌 Turn AI image descriptions ON
1. Prefer a machine with a GPU (CPU works but is slow for a 7B vision model).
2. Pick a **provider + model in `.env`** (never hardcoded — always read from `.env`).
3. Set `EKDC_DESCRIBE_IMAGES=true` and restart.

> **Fail-safe:** if the model/server is unavailable or misconfigured, EKDC **logs a warning and skips the description** — the document still converts successfully. Descriptions are **cached by image hash**, so re-runs don't re-pay the cost.

> ⚠️ **The model MUST be a VISION (VL) model.** For HuggingFace use e.g. `Qwen/Qwen2.5-VL-7B-Instruct` — **not** `Qwen/Qwen2.5-7B-Instruct` (that is text-only and cannot see images). For Ollama use a vision tag such as `qwen2.5vl` or `llama3.2-vision`. The Qwen3-VL-**Embedding** model used by the retrieval engine is an *embedding* model and also cannot describe images.

### 📦 Where local models are stored (persistent cache)

Downloaded weights are large, so EKDC keeps them in **one persistent folder** and reuses them across restarts (no re-downloading). Configure it in `.env`:
```env
EKDC_MODEL_CACHE_DIR=D:\models\ekdc   # leave blank to use <ekdc>/models
```
A relative path (e.g. `./storage`) resolves against the **EKDC service folder**, so the location is the same no matter where you launch the agent. EKDC wires this folder into the download paths for you:
- **HuggingFace / transformers** VLM weights (`HF_HOME`, `HUGGINGFACE_HUB_CACHE`, `TRANSFORMERS_CACHE`) → `<cache>/huggingface/`
- **Whisper** audio/video models (`download_root`) → `<cache>/whisper/`
- **Torch** hub assets (`TORCH_HOME`) → `<cache>/torch/`

> **Ollama** models are **not** stored here — the Ollama server manages them (default `~/.ollama/models`; change it with the `OLLAMA_MODELS` environment variable on the Ollama side).

---

## 📂 Supported File Types

| Category | Formats | Processing Engine |
| :--- | :--- | :--- |
| **Documents** | `.pdf`, `.docx`, `.pptx`, `.html`, `.csv` | `docling` & `LibreOffice` |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp` | `pytesseract` (OCR) |
| **Audio** | `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a` | `whisper` (Local ML Transcription) |
| **Video** | `.mp4`, `.mkv`, `.avi`, `.mov` | `moviepy` & `whisper` |
| **Plain Text** | `.txt`, `.py`, `.json`, `.md`, `.log` | Native Read & Markdown Code Blocks |

---

## ❓ Troubleshooting & FAQs

**Q: I'm getting a "docling is not installed" error.**
A: Ensure you have run `pip install -r requirements.txt`. If you are using virtual environments, ensure your terminal is activated in the correct environment (e.g., `(.venv)`).

**Q: I get a warning about "Found DrawingML elements... no DOCX to PDF converters."**
A: This means LibreOffice is not configured correctly. Ensure you installed LibreOffice and correctly pointed `DOCLING_LIBREOFFICE_CMD` to the `soffice.exe` path in your `.env` file.

**Q: Video/Audio files take a long time to convert!**
A: Audio/Video transcription relies on the AI model `Whisper`. Transcribing a 1-hour video requires heavy CPU processing. This is normal behavior for local AI transcription.

**Q: What if I drop a folder containing subfolders?**
A: The EKDC agent supports recursive tracking! It will exactly replicate your folder hierarchy inside the `output_md` directory.

**Q: I don't have a GPU. Will EKDC overload my machine?**
A: No. By default the only models that run are Whisper (only when you feed it audio/video) and OCR. The heavy **AI image-description** model is **OFF by default** (`EKDC_DESCRIBE_IMAGES=false`) and loads only if you explicitly enable it. See **Compute & GPU/CPU Control** above.

**Q: I enabled `EKDC_DESCRIBE_IMAGES` but no descriptions appear.**
A: Check three things: (1) the model is a **vision** model (e.g. `Qwen/Qwen2.5-VL-7B-Instruct`, **not** the text-only `Qwen/Qwen2.5-7B-Instruct`); (2) for Ollama, the server is running and the model is pulled (`ollama pull qwen2.5vl`); (3) the client libs are installed (`pip install langchain-ollama`, or the HF/transformers stack). EKDC skips descriptions gracefully on any failure and logs a warning — it never blocks conversion.

**Q: How do I make sure images are captured in the Markdown?**
A: Keep `EKDC_DOCLING_IMAGE_MODE=referenced` (the default). Images are saved next to the `.md` in a `<name>_artifacts/` folder and linked with relative paths. Use `placeholder` only if you deliberately want to drop images.

---
*Built for the Enterprise Knowledge RAG System.*
