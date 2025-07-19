# 🎙️ PodcastPro v2.0 - AI-Powered Podcast Creation Platform

**Advanced podcast creation platform with AI voice generation, sophisticated audio processing, and professional template management.**

## ✨ New Features in v2.0

### 🎯 **Advanced Template System**
- **Sophisticated Audio Management**: Upload intro/outro music, transitions, and sound effects
- **Precise Timing Controls**: Set exact start/end points and fade controls for each segment
- **Visual Timeline Builder**: Drag-and-drop interface for arranging episode segments
- **Professional Audio Mixing**: Multi-layer audio processing with volume control

### 🤖 **ElevenLabs AI Integration**
- **AI Voice Generation**: Create dynamic content with professional voice models
- **Voice Cloning**: Clone custom voices from audio samples
- **Dynamic Prompts**: Generate episode-specific content with template variables
- **Voice Settings**: Fine-tune stability, similarity, and style parameters

### 🎵 **Advanced Audio Processing**
- **Multi-Layer Mixing**: Mix voice segments with background music
- **Precise Fade Controls**: Custom fade-in/fade-out for each segment
- **Background Music Integration**: Music with custom start/end points and looping
- **Professional Export**: High-quality MP3 output with metadata

### 🎛️ **Professional Template Features**
- **Music Track Configuration**: Background music with precise timing
- **Segment Timing**: Start/end offsets for exact control
- **Fade Controls**: Independent fade-in/fade-out for each segment
- **Volume Mixing**: Optimal levels for voice and music layers

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- FFmpeg (for audio processing)
- ElevenLabs API key (for AI voice generation)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/podcastpro.git
   cd podcastpro
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
   ```bash
   # Create .env file
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   FLASK_SECRET_KEY=your_secret_key_here
   ```

5. **Initialize database**
   ```bash
   python recreate_database.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the platform**
   - Web Interface: http://localhost:5000
   - API Documentation: http://localhost:5000/api/v1/health

## 🎨 Template System Overview

### Creating Advanced Templates

1. **Navigate to Admin → Templates → New Template**
2. **Upload Audio Files**: Add intro/outro music and sound effects
3. **Build Timeline**: Arrange segments with drag-and-drop interface
4. **Configure Music**: Set background music with precise timing
5. **Add AI Segments**: Configure ElevenLabs voice and prompts
6. **Save Template**: Ready for episode creation

### Template Structure Example

```json
{
  "version": "2.0",
  "segments": [
    {
      "type": "intro",
      "audio_file": "intro_1.mp3",
      "timing": {
        "start_offset": 0,
        "end_offset": 0
      },
      "fade": {
        "fade_in": 0,
        "fade_out": 0
      }
    }
  ],
  "music_track": {
    "type": "upload",
    "file_path": "background_music.mp3",
    "start_point": 3.0,
    "fade_in": 2.0,
    "fade_out": 3.0
  },
  "ai_segments": {
    "voice_model": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "prompts": [
      "Welcome to [PODCAST_NAME], today we're discussing [TOPIC]..."
    ]
  }
}
```

## 🤖 AI Voice Generation

### ElevenLabs Integration

PodcastPro integrates with ElevenLabs for professional AI voice generation:

- **Voice Models**: Choose from professional voices (Rachel, Domi, Bella, Josh, etc.)
- **Voice Cloning**: Clone custom voices from audio samples
- **Dynamic Content**: Generate episode-specific content with template variables
- **Voice Settings**: Adjust stability, similarity boost, and style

### Example Usage

```python
from src.core.elevenlabs_service import ElevenLabsService

# Initialize service
elevenlabs = ElevenLabsService(api_key="your_api_key")

# Generate episode segment
audio_path = elevenlabs.generate_episode_segment(
    prompt="Welcome to Tech Talk, today we're discussing AI...",
    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
    output_dir="outputs",
    stability=0.5
)
```

## 🎵 Advanced Audio Processing

### Multi-Layer Audio Mixing

The platform supports sophisticated audio processing:

- **Precise Timing**: Sub-second accuracy for segment positioning
- **Volume Control**: Independent volume levels for each layer
- **Fade Effects**: Custom fade-in/fade-out for smooth transitions
- **Background Music**: Automatic looping and fade controls

### Audio Processing Pipeline

1. **Upload Audio Files** → Duration detection, metadata extraction
2. **Template Configuration** → Visual timeline builder
3. **AI Generation** → ElevenLabs integration for dynamic content
4. **Advanced Mixing** → Multi-layer audio with precise timing
5. **Professional Export** → High-quality MP3 with metadata

## 📁 Project Structure

```
podcastpro/
├── src/
│   ├── api/                    # REST API endpoints
│   │   ├── auth.py            # Authentication
│   │   ├── podcasts.py        # Podcast management
│   │   ├── episodes.py        # Episode processing
│   │   ├── templates.py       # Template management
│   │   └── files.py           # File uploads
│   ├── core/                  # Core processing
│   │   ├── elevenlabs_service.py      # AI voice generation
│   │   ├── advanced_audio_processor.py # Audio processing
│   │   └── podcast_processor.py       # Episode processing
│   ├── database/              # Database models
│   │   ├── models.py          # Production models
│   │   └── models_dev.py      # Development models
│   └── web/                   # Web interface
│       ├── templates/         # HTML templates
│       └── static/            # CSS, JS, images
├── uploads/                   # User uploaded files
├── outputs/                   # Processed episodes
├── docs/                      # Documentation
└── tests/                     # Test files
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
ELEVENLABS_API_KEY=your_elevenlabs_api_key
FLASK_SECRET_KEY=your_secret_key

# Optional
FLASK_ENV=development
DATABASE_URL=sqlite:///podcastpro_dev.db
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
```

### Audio Processing Settings

```python
# Audio file limits
MAX_AUDIO_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_AUDIO_FORMATS = ['mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg']

# Processing settings
AUDIO_BITRATE = '192k'
TARGET_DBFS = -20.0
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest test_real_world.py

# Run with coverage
python -m pytest --cov=src
```

### Test Templates

```bash
# Test template creation
python test_real_world.py

# Test audio processing
python test_audio_processing_real.py
```

## 📚 API Documentation

### Authentication

```bash
# Register
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "password123",
  "username": "username"
}

# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Templates

```bash
# Create template
POST /api/v1/templates
{
  "name": "Professional Show",
  "description": "Professional podcast template",
  "content": {
    "version": "2.0",
    "segments": [...],
    "music_track": {...},
    "ai_segments": {...}
  }
}

# Get templates
GET /api/v1/templates

# Get specific template
GET /api/v1/templates/{template_id}
```

### Episodes

```bash
# Create episode
POST /api/v1/episodes
{
  "podcast_id": "podcast_uuid",
  "title": "Episode Title",
  "template_id": "template_uuid",
  "audio_files": [...]
}

# Process episode
POST /api/v1/episodes/{episode_id}/process
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t podcastpro .
docker run -p 5000:5000 podcastpro
```

### Production Setup

1. **Set production environment variables**
2. **Configure database (PostgreSQL recommended)**
3. **Set up reverse proxy (nginx)**
4. **Configure SSL certificates**
5. **Set up monitoring and logging**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ElevenLabs** for AI voice generation
- **Librosa** for audio processing
- **Pydub** for audio manipulation
- **Flask** for the web framework

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/podcastpro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/podcastpro/discussions)

---

**PodcastPro v2.0** - Professional podcast creation made simple with AI! 🎙️✨
