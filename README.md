# 🎙️ Rohimaya Audiobook Generator

**Professional audiobook generation powered by AI**

Built on [Prasad Pagade's audiobook-producer](https://github.com/prasadpagade/audiobook-producer) foundation with enhancements for the Rohimaya Publishing platform.

---

## 🎯 What This Is

Transform written manuscripts into professional-quality audiobooks using cutting-edge AI text-to-speech technology.

### ✨ Features

**Original Core (by Prasad Pagade):**
- ✅ Intelligent text chunking (preserves sentence boundaries)
- ✅ Smart text cleaning (removes artifacts)
- ✅ Automatic audio merging
- ✅ Error recovery and fallbacks
- ✅ Production-ready pipeline

**Enhancements (by Rohimaya Team):**
- 🆕 Multi-provider TTS support (Inworld, ElevenLabs, OpenAI)
- 🆕 Beautiful Streamlit UI with Rohimaya branding
- 🆕 Rate limiting and cost optimization
- 🆕 Parallel processing (5x faster generation)
- 🆕 Real-time progress tracking
- 🆕 Cost estimation before generation
- 🆕 ACX-ready export formatting

---

## 🏗️ Architecture
```
Input Manuscript (.txt, .docx, .pdf)
         ↓
   Text Cleaner (Prasad's)
         ↓
   Smart Chunker (Prasad's)
         ↓
   TTS Manager (Enhanced - Multi-provider)
         ↓
   Audio Merger (Prasad's)
         ↓
   Final Audiobook (MP3/M4B)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- API key for at least one TTS provider (Inworld/ElevenLabs/OpenAI)

### Installation
```bash
# Clone repository
git clone https://github.com/rohimayaventures/rohimaya-audiobook-generator.git
cd rohimaya-audiobook-generator

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your API keys

# Run Streamlit app
streamlit run streamlit_app.py
```

### Command-Line Usage (Prasad's Original)
```bash
# Place manuscript in input/
python src/main.py
```

---

## 📊 Cost Comparison

| Method | Cost | Time | Quality |
|--------|------|------|---------|
| Professional Narrator | $1,500-5,000 | 2-4 weeks | Excellent |
| **Rohimaya AI** | **$6-60** | **30 minutes** | **Excellent** |

*80,000-word novel example*

---

## 🎨 Branding

**Rohimaya Publishing Colors:**
- Phoenix Orange: #FF8C42
- Peacock Teal: #4A9B9B
- Midnight Navy: #1A1A2E
- Cream: #FFF8E7

*"Where the Phoenix Rises and the Peacock Dances"*

---

## 📖 Documentation

- [ENHANCEMENTS.md](docs/ENHANCEMENTS.md) - What we added
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Complete technical design
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - How to deploy
- [INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) - Integration into Rohimaya platform

---

## 🤝 Contributing

This project is built on Prasad Pagade's excellent foundation. We welcome contributions!

**Special thanks to:**
- **Prasad Pagade** - Original audiobook-producer architecture
- **Hannah Kraulik Pagade** - Product vision and Rohimaya integration

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details

**Original work:** https://github.com/prasadpagade/audiobook-producer (MIT License)

---

## 📞 Contact

- **Email:** rohimayapublishing@gmail.com
- **Website:** https://rohimayapublishing.com
- **GitHub:** [@RohimayaPublishing](https://github.com/RohimayaPublishing)

---

**Built with 🔥 and 🦚 by the Rohimaya Publishing Team**

*Ascend • Flourish • Enlighten*