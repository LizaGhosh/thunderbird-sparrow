# 🎤 Voice Processing Installation Guide

## **📋 Prerequisites**

Before installing voice processing dependencies, ensure you have:

- ✅ Python 3.8+ installed
- ✅ pip package manager
- ✅ Microphone access on your system
- ✅ Sufficient disk space (2-3GB for Whisper models)

## **🚀 Quick Installation**

### **Option 1: Single Command (Recommended)**

```bash
# From project root directory
pip install -r requirements.txt
```

### **Option 2: Manual Installation**

```bash
# Install core dependencies
pip install openai-whisper numpy torch

# Install audio recording dependencies
pip install pyaudio

# For macOS users (if pyaudio fails)
brew install portaudio
pip install pyaudio

# For Linux users (if pyaudio fails)
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio
pip install pyaudio
```

## **🔧 System-Specific Instructions**

### **macOS**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install portaudio
brew install portaudio

# Install Python packages
pip install -r requirements.txt
```

### **Ubuntu/Debian Linux**
```bash
# Update package list
sudo apt-get update

# Install system dependencies
sudo apt-get install -y portaudio19-dev python3-pyaudio ffmpeg

# Install Python packages
pip install -r requirements.txt
```

### **Windows**
```bash
# Install Python packages (pyaudio should work directly)
pip install -r requirements.txt
```

## **🧪 Testing the Installation**

After installation, test that everything works:

```bash
# Test basic imports
python -c "import whisper; print('✅ Whisper installed')"
python -c "import pyaudio; print('✅ PyAudio installed')"
python -c "import torch; print('✅ PyTorch installed')"

# Test voice processing module
cd web
python -c "from voice_processing.processor import create_voice_processor; print('✅ Voice processing module ready')"
```

## **⚠️ Common Issues & Solutions**

### **1. PyAudio Installation Fails**

**Error**: `fatal error: 'portaudio.h' file not found`

**Solution**: Install portaudio first
```bash
# macOS
brew install portaudio

# Ubuntu/Debian
sudo apt-get install portaudio19-dev
```

### **2. Whisper Model Download Issues**

**Error**: `Error downloading model`

**Solution**: Check internet connection and try again
```bash
# Force re-download
python -c "import whisper; whisper.load_model('base')"
```

### **3. Microphone Access Denied**

**Error**: `OSError: [Errno -9996] Invalid input device`

**Solution**: Check microphone permissions
- **macOS**: System Preferences → Security & Privacy → Microphone
- **Linux**: Check audio device permissions
- **Windows**: Check microphone privacy settings

### **4. Out of Memory Errors**

**Error**: `CUDA out of memory` or `RuntimeError: out of memory`

**Solution**: Use smaller Whisper model
```bash
# In the web interface, select "tiny" or "base" model instead of "large"
```

## **🔍 Verification Steps**

### **1. Check Dependencies**
```bash
pip list | grep -E "(whisper|pyaudio|torch|numpy)"
```

### **2. Test Microphone**
```bash
# Simple microphone test
python -c "
import pyaudio
p = pyaudio.PyAudio()
print('Available audio devices:')
for i in range(p.get_device_count()):
    print(f'  {i}: {p.get_device_info_by_index(i)["name"]}')
p.terminate()
"
```

### **3. Test Whisper**
```bash
# Test Whisper model loading
python -c "
import whisper
model = whisper.load_model('tiny')
print('✅ Whisper model loaded successfully')
"
```

## **📱 Using the Voice Processing System**

After successful installation:

1. **Start the web application**:
   ```bash
   python launch_web.py
   ```

2. **Navigate to Voice Recording**:
   - Go to `http://localhost:5001/voice_record`
   - Select recording options
   - Click record and speak

3. **View Results**:
   - Go to `http://localhost:5001/results`
   - See all voice processing results and metrics

## **🆘 Getting Help**

If you encounter issues:

1. **Check the error messages** in the web interface
2. **Verify dependencies** are installed correctly
3. **Check microphone permissions** on your system
4. **Try smaller Whisper models** if you have memory issues
5. **Check the logs** in the web application

## **📊 System Requirements**

- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: 2-3GB for Whisper models
- **Audio**: Working microphone with proper permissions
- **Python**: 3.8+ with pip package manager

## **🎉 Success Indicators**

You'll know the installation is successful when:

- ✅ All Python packages install without errors
- ✅ Voice processing module imports successfully
- ✅ Web application starts without import errors
- ✅ Voice recording interface loads properly
- ✅ You can record and process voice inputs
- ✅ Results are generated successfully

**Happy voice processing!** 🎤✨
