#!/usr/bin/env python3
"""
Convert religious_perspectives_on_political_compass.json to JavaScript format
for use in GitHub Pages website.
"""

import json
from pathlib import Path

def convert_json_to_js():
    """Convert JSON data to JavaScript module format."""
    
    # Read the JSON file
    json_path = Path("religious_perspectives_on_political_compass.json")
    
    if not json_path.exists():
        print(f"Error: {json_path} not found!")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to JavaScript format
    js_content = f"""// Religious Perspectives on Political Compass Data
// Generated from religious_perspectives_on_political_compass.json
// Total questions: {len(data)}

const RELIGIOUS_DATA = {json.dumps(data, indent=2, ensure_ascii=False)};

// Helper function to get question by ID
function getQuestionById(questionId) {{
    return RELIGIOUS_DATA.find(q => q.question_id === questionId);
}}

// Helper function to get all questions
function getAllQuestions() {{
    return RELIGIOUS_DATA;
}}

// Helper function to get all religions
function getAllReligions() {{
    const religions = new Set();
    RELIGIOUS_DATA.forEach(question => {{
        question.religious_perspectives.forEach(perspective => {{
            religions.add(perspective.religion);
        }});
    }});
    return Array.from(religions).sort();
}}

// Helper function to get choice label
function getChoiceLabel(choice) {{
    const labels = {{
        'sa': 'Strongly Agree',
        'a': 'Agree', 
        'd': 'Disagree',
        'sd': 'Strongly Disagree'
    }};
    return labels[choice] || choice;
}}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = {{ RELIGIOUS_DATA, getQuestionById, getAllQuestions, getAllReligions, getChoiceLabel }};
}}
"""
    
    # Write JavaScript file
    output_path = Path("data.js")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"✅ Successfully converted {len(data)} questions to {output_path}")
    print(f"📊 Data includes {len(data[0]['religious_perspectives'])} religious perspectives per question")

if __name__ == "__main__":
    convert_json_to_js()