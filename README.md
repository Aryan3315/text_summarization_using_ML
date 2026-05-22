# 🧠 Text Summarization Using Deep Learning

An AI-powered abstractive text summarization web application built using Deep Learning and NLP techniques. This project generates concise and meaningful summaries from long text documents using Seq2Seq architecture, Attention Mechanism, and Transformer-based models.

---

## 📌 Project Overview

This project focuses on **Automatic Text Summarization** using Deep Learning. Unlike extractive summarization that copies sentences directly from the source text, this system performs **abstractive summarization**, generating entirely new and meaningful sentences while preserving the original context.

The application allows users to:
- Paste large text content
- Upload PDF/TXT documents
- Generate short, medium, or long summaries
- Copy or download generated summaries instantly

---

# 🚀 Features

✅ Deep Learning-based Text Summarization  
✅ PDF and TXT File Upload Support  
✅ Abstractive Summary Generation  
✅ Configurable Summary Length  
✅ Interactive Flask Web Application  
✅ Copy & Download Summary Option  
✅ Responsive User Interface  

---

# 🛠️ Technologies Used

## Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap

## Backend
- Python
- Flask

## Deep Learning & NLP
- PyTorch / TensorFlow
- Hugging Face Transformers
- NLTK
- Seq2Seq Architecture
- GRU Encoder-Decoder
- Bahdanau Attention
- DistilBART

## Dataset
- CNN/DailyMail Dataset

---

# 🧠 Deep Learning Concepts Used

- Artificial Neural Networks (ANN)
- Recurrent Neural Networks (RNN)
- Long Short-Term Memory (LSTM)
- Sequence-to-Sequence Learning
- Attention Mechanism
- Transformer Models

---

# ⚙️ System Workflow

1. User enters text or uploads a file  
2. Text preprocessing and tokenization  
3. Input passed into Seq2Seq/Transformer model  
4. Attention mechanism captures contextual meaning  
5. Beam Search decoding generates optimized summaries  
6. Final summarized output displayed to user  

---

# 📊 Model Performance

| Model | ROUGE-1 | ROUGE-2 | ROUGE-L |
|------|------|------|------|
| Lead-3 Baseline | 0.401 | 0.175 | 0.366 |
| Our Seq2Seq Model | 0.384 | 0.175 | 0.352 |
| DistilBART (Deployed) | 0.422 | 0.201 | 0.389 |

The model achieved stable convergence over 10 epochs with decreasing validation loss and competitive summarization performance.

---

# 📂 Project Structure

```bash
Text-Summarization-Using-Deep-Learning/
│
├── static/                 # CSS, JS, Images
├── templates/              # HTML Templates
├── model/                  # Trained Model Files
├── uploads/                # Uploaded Documents
├── app.py                  # Flask Application
├── requirements.txt        # Required Libraries
├── train.py                # Model Training Script
├── summarize.py            # Summarization Logic
└── README.md               # Project Documentation
```

---

# 💻 Installation & Setup

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/text-summarization-using-deep-learning.git
```

## 2️⃣ Navigate to Project Folder

```bash
cd text-summarization-using-deep-learning
```

## 3️⃣ Create Virtual Environment

```bash
python -m venv venv
```

## 4️⃣ Activate Virtual Environment

### Windows
```bash
venv\Scripts\activate
```

### Linux/Mac
```bash
source venv/bin/activate
```

## 5️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

## 6️⃣ Run Application

```bash
python app.py
```

## 7️⃣ Open in Browser

```bash
http://127.0.0.1:5000
```

---

# 📸 System Interface

The web application provides:
- Clean and responsive UI
- Input text area
- File upload support
- Summary length selection
- Generated summary output section

---

# 🎯 Project Outcomes

✔ Successfully developed a complete abstractive summarization system  
✔ Applied real-world Deep Learning and NLP concepts  
✔ Built an AI-powered web application  
✔ Bridged academic learning with industry deployment practices  

---

# 🔮 Future Enhancements

- Integration of larger transformer models
- Multi-document summarization
- Real-time streaming summarization
- Cloud deployment support
- User feedback-based learning system

---

# 👨‍💻 Author

**Aryan Trivedi**  


---


---

# 📜 License

This project is developed for educational and research purposes. Feel free to use and modify it for learning.

---

⭐ If you like this project, give it a star on GitHub!
