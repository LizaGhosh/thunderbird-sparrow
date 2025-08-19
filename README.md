# Voice Note Parser - Industrial Maintenance

An AI-powered voice note parsing system designed for industrial maintenance workflows. This application processes voice recordings and converts them into structured maintenance requests, work orders, and closing comments.

## 🚀 Features

- **Voice Recording & Transcription**: Record voice notes using your microphone
- **AI-Powered Analysis**: Process voice inputs using Claude or Gemini AI models
- **Dual Processing Modes**: 
  - **Work Item Triaging**: Convert voice notes to maintenance requests
  - **Closing Comments**: Generate completion reports from voice notes
- **Web Interface**: User-friendly Flask-based web application
- **Test Mode**: Run quick tests with limited data (3 entries per category)
- **Real-time Progress Tracking**: Monitor processing status with live updates
- **Results Dashboard**: View metrics, comparison tables, and detailed outputs

## 🏗️ Project Structure

```
sparrrow/
├── backend/                 # Python backend logic
│   ├── config/             # Configuration management
│   ├── core/               # Core AI processing modules
│   ├── data/               # Data storage (inputs, outputs, logs)
│   ├── logs/               # Application logs
│   ├── test/               # Test framework
│   ├── voice/              # Voice processing modules
│   ├── main.py             # CLI execution entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # Web interface
│   ├── templates/          # HTML templates
│   ├── app.py              # Flask application
│   └── start_web.py        # Web server launcher
├── instructions/            # Reference data
├── venv/                   # Python virtual environment (ignored by git)
├── .env                    # Environment variables (ignored by git)
├── .gitignore             # Git ignore rules
├── env.example             # Environment variables template
├── launch_web.py           # Alternative web launcher
├── requirements.txt         # Root-level Python dependencies
└── README.md               # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Microphone access (for voice recording)

### Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sparrrow
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   # For Claude AI
   CLAUDE_API_KEY=your_claude_api_key_here
   
   # For Gemini AI
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## 🚀 Usage

### Web Interface (Recommended)

1. **Start the web server**
   ```bash
   # Option 1: Using the frontend launcher
   python frontend/start_web.py
   
   # Option 2: Using the root launcher
   python launch_web.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5001`

3. **Configure AI settings**
   - Go to the "Configure" tab
   - Select AI provider (Claude or Gemini)
   - Set model and temperature parameters

4. **Run tests or process voice notes**
   - **Run Tests**: Execute quick tests with limited data (3 entries per category)
   - **Voice Recording**: Record and process voice notes

### Command Line

1. **Process full dataset**
   ```bash
   python backend/main.py
   ```

2. **Run test mode (3 entries)**
   ```bash
   python backend/test/test_first_three.py
   ```

### Project Structure Overview

- **`backend/`**: Contains all Python logic, AI processing, and data management
- **`frontend/`**: Web interface with Flask templates
- **`instructions/`**: Reference data for expected outputs
- **Root level**: Configuration files, launchers, and documentation

## ⚙️ Configuration

### AI Model Settings
- **Provider**: Choose between Claude and Gemini
- **Model**: Select specific model variant
- **Temperature**: Control response creativity (0.0 = deterministic, 1.0 = creative)

### Data Paths
- **Inputs**: `backend/data/inputs/inputs_only.json`
- **Outputs**: `backend/data/outputs/`
- **Test Inputs**: `backend/test/inputs/inputs_only.json`
- **Test Outputs**: `backend/test/outputs/`

## 📊 Output Format

The system generates structured JSON outputs with:
- **Work Item Triaging**: Maintenance request details, urgency, asset information
- **Closing Comments**: Completion reports, time tracking, parts used
- **Comparison Tables**: CSV files for analysis and reporting
- **Raw LLM Outputs**: Detailed AI processing logs

## 🧪 Testing

### Test Mode
- Processes only 3 entries from each category
- Faster execution for development and testing
- Automatically restores configuration after completion

### Test Data
- **Work Triaging**: 3 sample maintenance requests
- **Closing Comments**: 3 sample completion reports

## 🔧 Development

### Project Architecture
- **Modular Design**: Clear separation of concerns
- **Frontend/Backend**: Web interface separate from processing logic
- **Configuration Management**: YAML-based configuration with environment overrides
- **Error Handling**: Comprehensive error handling and logging

### Key Components
- **MaintenanceParser**: Core AI processing engine
- **MetricsCalculator**: Performance evaluation and comparison
- **VoiceProcessor**: Audio recording and transcription
- **Flask App**: Web interface and API endpoints

## 📝 Logging

- **Application Logs**: `backend/logs/app.log`
- **Processing Logs**: Real-time progress tracking
- **Error Logs**: Detailed error information and stack traces

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the logs in `backend/logs/`
2. Review the configuration in `backend/config/`
3. Ensure API keys are properly set in `.env`
4. Check that all dependencies are installed

## 🔄 Version History

- **v2.0**: Modular architecture with frontend/backend separation
- **v1.0**: Initial implementation with basic voice processing

---

**Note**: This project requires valid API keys for AI providers. Ensure your `.env` file is properly configured before running.

