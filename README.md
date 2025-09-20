# 🕊️ Religious Political Compass

A comprehensive AI-powered analysis of political perspectives across world religions and philosophical systems. This project surveys 62 political questions from the viewpoints of 15 different religious and philosophical traditions using large language models.

## 📊 Overview

This research project explores how different religious and philosophical worldviews align on political issues by:
- Querying AI models about political statements from religious perspectives
- Analyzing responses based on sacred texts and core teachings
- Visualizing results on a traditional political compass
- Providing quantitative analysis of ideological positions

## 🌍 Covered Traditions

The project analyzes perspectives from:

**Major World Religions:**
- Islam
- Christianity  
- Judaism
- Hinduism
- Buddhism
- Sikhism

**Eastern Philosophies:**
- Taoism
- Confucianism
- Shintoism

**Other Traditions:**
- Zoroastrianism
- Jainism
- Baháʼí Faith

**Secular Worldviews:**
- Atheism
- Agnosticism
- Secular Humanism

## 🛠️ Features

- **AI-Powered Analysis**: Uses OpenRouter API to query advanced language models
- **Interactive Web Interface**: Beautiful web app to explore questions and religious perspectives
- **Structured Output**: JSON responses with political stance, religious text, and citations
- **Data Transformation**: Converts survey results to analysis-ready formats
- **Visualization**: Generates political compass plots with quadrant analysis
- **Web Validation**: Selenium-based validator to verify results against politicalcompass.github.io
- **Comprehensive Logging**: Detailed logs of all API calls and responses
- **Multiple Output Formats**: JSON, CSV, and visualization outputs for different analysis needs

## 📁 Project Structure

```
islamic_political_compass/
├── run.py                                      # Main survey execution script
├── validator.py                               # Web-based political compass validator using Selenium
├── separator.py                               # Data transformation from long to wide format
├── plot.py                                   # Political compass visualization generator
├── json_to_csv.py                            # JSON to CSV format converter
├── json_to_js.py                             # Convert JSON data to JavaScript format
├── index.html                                # Interactive web interface for GitHub Pages
├── data.js                                   # JavaScript version of survey data
├── questions.csv                             # 62 political compass questions
├── requirements.txt                          # Python dependencies
├── .env                                     # API keys (not in repo)
├── .gitignore                               # Git ignore patterns
├── README.md                                # Project documentation
├── DEPLOYMENT.md                             # GitHub Pages deployment guide
│
├── religious_perspectives_on_political_compass.json  # Raw survey results (timestamped)
├── religious_perspectives_on_political_compass.csv   # Flattened survey data (timestamped)  
├── _merged_predictions.csv                           # Wide-format analysis data
├── _pc_scores.json                                   # Political compass coordinates
├── _pc_scores.csv                                    # PC scores in CSV format
├── political_compass_survey_TIMESTAMP.log            # Detailed execution logs
│
├── .venv/                                   # Python virtual environment
└── __pycache__/                            # Python bytecode cache
```

## 🌐 Live Demo

**[View Interactive Web Interface →](https://sakhadib.github.io/Religious-Study-On-Politics/)**

Explore all 62 questions and religious perspectives through our beautiful web interface.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd islamic_political_compass

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For web validation (optional - requires Chrome browser)
pip install selenium webdriver-manager
```

### 2. Configure API Access

Create a `.env` file with your OpenRouter API key:

```env
OPENROUTER_API_KEY=your_api_key_here
```

### 3. Run the Survey

```bash
# Run complete survey (930 API calls: 62 questions × 15 traditions)
python run.py --model openai/gpt-4

# Or use a different model
python run.py --model meta-llama/llama-3.3-70b-instruct
```

### 4. Generate Analysis

```bash
# Transform results to wide format
python separator.py religious_perspectives_on_political_compass.csv

# Convert PC scores to CSV
python json_to_csv.py _pc_scores.json

# Create visualization
python plot.py

# Validate results using web-based political compass (requires Chrome)
python validator.py
```

## 📊 Output Files

The project generates several output files:

| File | Description |
|------|-------------|
| `religious_perspectives_on_political_compass.json` | Raw survey results with full responses and religious texts |
| `religious_perspectives_on_political_compass.csv` | Flattened survey data with all perspectives |
| `_merged_predictions.csv` | Wide-format data (one row per question, columns per religion) |
| `_pc_scores.json` | Political compass coordinates for each tradition |
| `_pc_scores.csv` | Compass scores in CSV format for analysis |
| `political_compass.png` | Visualization plot (generated by plot.py) |
| `political_compass_survey_TIMESTAMP.log` | Detailed execution logs with API calls |

## 🎯 Usage Examples

### Basic Survey
```bash
python run.py --model openai/gpt-4
```

### Custom Output
```bash
python run.py --model anthropic/claude-3 --output my_results.json
```

### Validation Against Web Tool
```bash
# Validate results using the official political compass website
python validator.py
```

### Data Analysis
```python
import pandas as pd

# Load results
df = pd.read_csv('_merged_predictions.csv')

# Analyze agreement patterns
agreement_by_religion = df.groupby(['religion']).apply(
    lambda x: (x == 'sa').sum() + (x == 'a').sum()
)
```

## 📈 Data Structure

### Survey Response Format
```json
{
  "question_id": "q1",
  "statement": "Economic globalization should serve humanity...",
  "religious_perspectives": [
    {
      "religion": "Islam",
      "choice": "sa",
      "religious_text": "Relevant Quranic verse or Hadith",
      "reference": "Quran 2:188"
    }
  ]
}
```

### Political Compass Coordinates
```json
{
  "responder": "islam",
  "econ_score": -5.87,
  "soc_score": -1.08
}
```

## 🔬 Methodology

1. **Question Selection**: 62 political statements covering economic and social issues
2. **Religious Prompting**: Specialized prompts for each tradition emphasizing sacred texts
3. **Structured Responses**: JSON format ensuring consistent data collection
4. **Scoring**: Traditional political compass methodology
5. **Visualization**: Standard quadrant analysis with color-coded positions

## 📊 Key Findings

Based on our analysis:
- **Economic Spectrum**: Most traditions lean left (-8.49 to -4.99)
- **Social Spectrum**: Strong libertarian tendency (-8.72 to -1.08)
- **Quadrant Distribution**: All traditions fall in Left-Libertarian quadrant
- **Most Liberal**: Secular Humanism (-8.24, -8.72)
- **Most Conservative**: Islam (-5.87, -1.08)

## 🛡️ Limitations & Considerations

- **AI Interpretation**: Results reflect AI understanding of religious texts, not official doctrine
- **Model Bias**: Different AI models may produce varying results
- **Simplification**: Complex theological positions reduced to 4-point scale
- **Contemporary Context**: Modern political questions applied to ancient traditions
- **Single Perspective**: One AI interpretation per tradition per question

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-analysis`)  
3. Make changes and test
4. Commit with clear messages
5. Push and create a Pull Request

## 📜 License

This project is for research and educational purposes. Please cite appropriately if used in academic work.

## 🙏 Acknowledgments

- OpenRouter for API access
- Religious scholars and texts that inform the AI responses
- The open-source Python ecosystem
- Political compass methodology pioneers

## 📧 Contact

For questions, suggestions, or collaboration opportunities, please open an issue in the repository.

---

*This project aims to foster understanding across religious and philosophical traditions through data-driven analysis. Results should be interpreted as AI-assisted academic exploration rather than authoritative religious positions.*