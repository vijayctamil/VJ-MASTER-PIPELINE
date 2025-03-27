# 🎬 VJPipeline – VFX Pipeline Tool

VJPipeline is a standalone desktop application (built with PySide6 and packaged via PyInstaller) designed to streamline and manage key parts of a VFX production pipeline. It currently supports batch file caching for Houdini scenes and offers a render management system for organizing shots and render layers within projects.

---

## 🚀 Features

### 1. 🔷 **Batch Caching for Houdini**
Manage and automate the execution of File Cache nodes in multiple Houdini `.hip` files through a simple UI and CSV pipeline.

#### ➤ **CSV Creator**
- Extracts all `filecache` nodes from Houdini `.hip` files.
- Lets users select which cache nodes to include and define execution type:
  - **Sequential** (one-by-one)
  - **Parallel** (simultaneously)
- Exports the configuration as a CSV file.

#### ➤ **Batch Caching Executor**
- Loads CSV files containing batching instructions.
- Executes file caches using Houdini's Python (`hython`) interpreter.
- Includes progress tracking and real-time logs.
- Auto-detects installed Houdini versions for easy setup.

---

### 2. 🎬 **Render Manager Tool** *(Work-in-Progress)*
An early prototype UI to manage render projects in a hierarchical view:

- Select Shows ➝ Shots ➝ Render Layers.
- Interactive UI with thumbnails and metadata.
- Designed for future integration with render farm tools.

---

## 🖥️ How to Use

1. **Launch the App**
   - Use the packaged `.exe` or run directly via Python if needed.

2. **Batch Cache Workflow**
   - Go to **Houdini → Batch Caching** tab.
   - Use the **Create CSV** tab to browse `.hip` files and select file cache nodes.
   - Export as `.csv`.
   - Switch to **Run Batch Caching** to import the `.csv` and start execution.

3. **Render Manager**
   - Navigate to **Render Manager** from the sidebar.
   - View current UI prototype for projects and shots.

---

## 🛠️ Build as Executable

To package the project into a standalone `.exe`, use the following PyInstaller command:

```bash
pyinstaller --windowed --name VJPipeline ^
    --add-data "extract_filecaches.py;." ^
    --add-data "batch_cache_from_csv_v002.py;." ^
    --add-data "icons;icons" ^
    --add-data "images;images" ^
    VJ_Pipeline_UI.py
```

> ✅ Ensure all resource folders (`icons/`, `images/`) are in the same directory when running this command.

---

## 📁 File Structure

```
VJPipeline/
├── VJ_Pipeline_UI.py                # Main UI script
├── batch_cache_from_csv_v002.py    # Houdini batch caching processor
├── extract_filecaches.py           # Houdini cache node extractor
├── icons/                          # UI icons
├── images/                         # Project thumbnails for Render Manager
├── settings.ini                    # Configurations saved via UI
```

---

## 📌 Requirements

- Houdini (for `hython`)
- Python 3.9+
- PySide6
- tqdm

Install dependencies via pip:
```bash
pip install PySide6 tqdm
```

---

## 📍 Roadmap

- [ ] Render Manager full pipeline integration (scene loading, render dispatch)
- [ ] Deadline or Tractor integration
- [ ] Progress and analytics tracking
- [ ] User login and version control features

---

## 🙌 Contributing

Feel free to fork and contribute! Whether it's UI improvement, render farm integration, or caching logic – contributions are welcome.

---

## 📄 License

MIT License – use freely, but attribution is appreciated!
```
