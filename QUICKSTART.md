# ⚡ Quick Start Guide - 5 Minutes to Your First Audiobook

## 🎯 Goal

Generate your first professional audiobook in 5 minutes!

---

## 📋 Prerequisites

- Python 3.10+ installed
- OpenAI API key (get at https://platform.openai.com/api-keys)
- 5 minutes of your time

---

## 🚀 Step 1: Clone & Setup (2 minutes)
```bash
# Clone repository
git clone https://github.com/rohimayaventures/rohimaya-audiobook-generator.git
cd rohimaya-audiobook-generator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# OR: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 🔑 Step 2: Add API Key (1 minute)
```bash
# Copy secrets template
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit with your key
nano .streamlit/secrets.toml
# OR open in your text editor
```

Add your OpenAI API key:
```toml
[openai]
api_key = "sk-proj-YOUR_KEY_HERE"
```

**Get API Key:** https://platform.openai.com/api-keys

---

## 🎬 Step 3: Run the App (30 seconds)
```bash
streamlit run streamlit_app.py
```

**Browser opens automatically at:** http://localhost:8501

---

## 📚 Step 4: Generate Audiobook (1.5 minutes)

1. **Upload manuscript:**
   - Click "Choose your manuscript"
   - Select `examples/sample_manuscript.txt`
   - OR upload your own .txt/.docx file

2. **Select voice:**
   - Choose from 6 professional voices
   - Recommended: "Nova" (warm female) or "Onyx" (deep male)

3. **Click "Generate Audiobook"**
   - Watch real-time progress
   - Wait ~1-2 minutes
   - Done! ✨

4. **Download & Listen:**
   - Click "Download Audiobook"
   - Play in your audio player
   - Share with the world!

---

## 🎉 Success!

You just created a professional audiobook in 5 minutes!

**Cost:** ~$0.10 for sample (687 words)  
**Quality:** ACX-ready, professional  
**Time:** Under 5 minutes start to finish

---

## 🔥 Next Steps

### **Try Different Voices:**
- Alloy (neutral)
- Echo (male, clear)
- Fable (British)
- Onyx (deep male)
- Nova (female, warm)
- Shimmer (female, soft)

### **Upload Your Book:**
- Full novels work perfectly!
- Cost: ~$6-60 depending on length
- 80,000 words = ~$60

### **Advanced Settings:**
- Adjust chunk size
- Change narration speed
- Enable ACX-ready export

---

## 💡 Tips & Tricks

### **Best Practices:**
- **Clean your manuscript first** (remove headers/footers)
- **Use .txt format** for best results
- **Test with sample first** before full book
- **Try different voices** to find perfect narrator

### **Cost Optimization:**
- Shorter chunks = more API calls = higher cost
- Use 1500 character chunks (default)
- Batch similar books together

### **Quality Tips:**
- Remove formatting codes
- Fix punctuation issues
- Check for strange characters
- Preview first chapter before full book

---

## 🐛 Troubleshooting

### **"Module not found"**
```bash
pip install -r requirements.txt --upgrade
```

### **"ffmpeg not found"**
**Mac:**
```bash
brew install ffmpeg
```

**Ubuntu:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

### **"API key invalid"**
- Check `.streamlit/secrets.toml`
- Verify key starts with `sk-proj-`
- No extra spaces or quotes

### **"Rate limit exceeded"**
- Wait 60 seconds
- Reduce chunk size
- Upgrade OpenAI plan

---

## 📊 Understanding Costs

### **OpenAI TTS Pricing:**
- $0.015 per 1,000 characters
- Average novel (80K words): ~$6
- Short story (5K words): ~$0.40

### **Example Costs:**
| Length | Words | Characters | Cost |
|--------|-------|------------|------|
| Short story | 5,000 | 25,000 | $0.38 |
| Novella | 20,000 | 100,000 | $1.50 |
| Novel | 80,000 | 400,000 | $6.00 |
| Epic novel | 150,000 | 750,000 | $11.25 |

**Compare to:** $1,500-5,000 for human narrator

---

## 🎯 What's Next?

### **Deploy to Cloud:**
See `docs/DEPLOYMENT.md` for Streamlit Cloud setup (FREE!)

### **Integrate with Platform:**
See `docs/INTEGRATION_GUIDE.md` for Rohimaya integration

### **Enhance Features:**
See `docs/ENHANCEMENTS.md` for future roadmap

---

## 📞 Need Help?

- **Documentation:** Check `/docs` folder
- **Issues:** Create GitHub issue
- **Email:** rohimayapublishing@gmail.com
- **Demo:** See `examples/DEMO_SCRIPT.md`

---

## 🦚 About Rohimaya

**Where the Phoenix Rises and the Peacock Dances**

Rohimaya Publishing empowers authors with AI-powered tools:
- AI Writing Assistant
- Manuscript Formatter
- AI Cover Designer
- **Audiobook Generator** ← You are here!
- Plot Outliner
- Character Creator
- Marketing Copy Generator

**Learn more:** https://rohimayapublishing.com

---

**Built with 🔥 and 🦚 by Prasad (Phoenix) & Hannah (Peacock)**

**Now go create amazing audiobooks!** 🎙️✨
