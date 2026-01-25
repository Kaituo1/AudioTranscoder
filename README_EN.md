# AudioConverter

A powerful, user-friendly audio format conversion tool based on PyQt5, using FFmpeg engine, supporting high-quality conversion between various audio and video formats.

## Features

- 🎵 **Multiple Format Support**: Supports almost all common audio and video format conversions
- 📊 **Tabular File Management**: Clearly displays file name, size, format and status information
- 🚀 **Batch Conversion**: Supports converting multiple files at once
- 📁 **Folder Import**: Supports batch importing files from folders
- 🔄 **High-Quality Conversion**: Uses FFmpeg engine to ensure conversion quality and speed
- 🎨 **Modern Interface**: Modern GUI design based on PyQt5, simple and intuitive operation
- 📋 **Real-time Progress**: Displays conversion progress and detailed status information
- ⚡ **Efficient Conversion**: Supports multi-threaded conversion to improve conversion speed
- 🎯 **Always on Top**: Supports keeping the window on top for convenient operation
- 📱 **High DPI Support**: Optimized for high-resolution screen display
- 📌 **Fixed Window Size**: Clean fixed size design to avoid misoperation

## Supported Formats

### Audio Formats
- **Input/Output**: MP3, WAV, FLAC, AAC, OGG, WMA, M4A, AIFF, ALAC, APE, OPUS, WV, DSF, DFF

### Video Formats
- **Input**: MP4, MKV, AVI, MOV, WMV, FLV, WEBM, MPG, MPEG, TS, M2TS, 3GP, VOB, OGV
- **Output**: Converted to audio formats

## Installation Instructions

### System Requirements
- Windows 10/11 (64-bit)

### Installation Steps

1. **Download Program**
   - Download the latest version of `AudioConverter.exe` from the release page
   - No installation required, ready to use

2. **Run Program**
   - Double-click the `AudioConverter.exe` file to run
   - The program already includes all dependency libraries and FFmpeg engine
   - Initialization may take some time on first run

## Usage Guide

### 1. Add Files

- **Add Single or Multiple Files**: Click the "Add Files" button to select files to convert
- **Add Folder**: Click the "Add Folder" button to select a folder containing audio/video files
- **Drag and Drop**: Directly drag files or folders to the program window

### 2. Select Output Format

- Select the target format to convert in the "Output Format" dropdown menu
- Supported output formats include: MP3, WAV, FLAC, AAC, OGG, M4A, OPUS
- Each format has optimized conversion parameters to ensure high-quality output

### 3. Set Output Directory

- Default output directory is `AudioOutput` folder in user's home directory
- Click the "Browse" button to customize the output directory
- Check "Open output folder after conversion" to automatically open the output folder after conversion

### 4. Start Conversion

- Click the "Start Conversion" button to begin the conversion process
- Real-time progress and status can be viewed during conversion
- Support pause/resume conversion
- Support stopping conversion at any time

### 5. Manage Files

- **Remove Selected**: Select files to delete, click "Remove Selected" button
- **Clear All**: Click "Clear All" button to delete all added files

## Interface Description

### Main Interface

1. **Title Area**
   - Displays program name
   - Contains author information and support links
   - Support author button

2. **File List Area**
   - Displays added files in a table, including file name, size, format and status
   - Supports multi-selection operations
   - Drag and drop hint area

3. **File Operation Buttons**
   - Add Files: Add single or multiple files
   - Add Folder: Add all audio/video files from a folder
   - Remove Selected: Delete selected files
   - Clear All: Delete all added files

4. **Output Settings Area**
   - Output Format: Select target format after conversion
   - Output Directory: Set the save location for converted files
   - Open output folder after conversion: Automatically open output folder after conversion

5. **Conversion Control Area**
   - Progress Bar: Displays overall conversion progress
   - Progress Text: Displays current conversion status and information
   - Start Conversion: Start the conversion process
   - Pause/Continue: Pause or continue conversion
   - Stop Conversion: Stop current conversion

6. **Options Area**
   - Open output folder after conversion: Automatically open output folder after conversion
   - Always on Top: Keep the program window on top

## Frequently Asked Questions

### 1. What to do if conversion fails?

- Check if the input file is corrupted
- Ensure write permissions for the output directory
- Try restarting the program
- Check if there is enough disk space

### 2. How to improve conversion speed?

- Close other CPU-intensive programs
- Reduce the number of files converted simultaneously

### 3. What is the quality of converted files?

- The program uses FFmpeg engine, conversion quality depends on source file and output format
- For lossless formats (such as FLAC), quality remains unchanged when converted to other lossless formats
- When converting to lossy formats, optimized parameters are used to ensure the best balance between quality and file size

### 4. Does it support batch conversion?

- Yes, it supports batch conversion of multiple files
- Multiple files or entire folders can be added at the same time
- Support drag and drop to add multiple files

### 5. Does the program require FFmpeg installation?

- No, the program has built-in FFmpeg
- Automatically finds system FFmpeg or uses the built-in version

## Technical Description

### Core Engine

- Uses FFmpeg as conversion engine to ensure conversion quality and speed
- Supports multi-threaded conversion to improve conversion efficiency
- Automatically finds and uses system or built-in FFmpeg

### Development Environment

- Development Language: Python 3.14
- GUI Framework: PyQt5
- Conversion Engine: FFmpeg
- Packaging Tool: PyInstaller
- Supported Systems: Windows 10/11

## License

- This program is open source under MIT License
- FFmpeg uses LGPL License

## Change Log

### v2.2.0 (2026-01-25)
- 🎵 **Audio Quality Optimization**: All format parameters adjusted to highest quality
- 📁 **Folder Drag & Drop Support**: Support dragging folders directly to add files
- 🗑️ **Simplified Operation**: Removed secondary confirmation dialog for clearing files
- 🔄 **Status Reset**: Automatically reset progress display to "Waiting to start" after conversion
- 🛠️ **MP3 Conversion Fix**: Fixed MP3 conversion failure issue, optimized bitrate settings
- 🎯 **AAC/M4A Optimization**: Changed to VBR mode for better quality/size ratio
- 🎼 **OPUS Optimization**: Removed fixed bitrate limitation, using optimal VBR settings
- 🔍 **Enhanced Error Messages**: Added complete FFmpeg error output capture

### v2.1.0 (2026-01-22)
- 🎨 New PyQt5 interface design
- 📊 Tabular file management
- 📱 High DPI support
- 🎯 Always on top feature
- 🔄 Pause/resume conversion feature
- 📁 Drag and drop file support
- 🔧 Optimized FFmpeg search mechanism
- 🎨 Modern color scheme

### v2.0 (2026-01-21)
- 📊 Tabular file management interface
- 🔄 Optimized conversion logic, improved conversion speed
- 🛠️ Improved error handling mechanism
- 🎨 Beautified interface design

### v1.0
- 🔊 Initial version
- 🎵 Basic audio format conversion functionality

## Contact Information

- Author: Kaituo
- Email: rzktys@qq.com
- GitHub: https://github.com/Kaituo1/AudioTranscoder
- Bilibili: https://space.bilibili.com/209568678

## Contributing

Welcome to submit Issues and Pull Requests to improve this project!

## Acknowledgments

- Thanks to the FFmpeg team for providing the powerful conversion engine
- Thanks to all developers who contributed to the project
- Thanks to the PyQt5 team for providing an excellent GUI framework

---

**Disclaimer**: This program is for learning and personal use only, please do not use it for commercial purposes. When converting copyrighted files, please ensure you have the appropriate rights.