#!/usr/bin/env python3
"""
Political Compass Survey from Religious Perspectives
Surveys political questions from the viewpoint of different religious traditions.
"""

import os
import json
import csv
import argparse
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
def setup_logging():
    """Configure logging to both file and console"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"political_compass_survey_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class ReligiousPoliticalCompass:
    def __init__(self, model_name: str, logger: logging.Logger):
        self.model_name = model_name
        self.logger = logger
        self.client: Optional[OpenAI] = None
        self.questions = []
        self.religions = [
            "islam", "christianity", "judaism", "hinduism", "buddhism",
            "sikhism", "zoroastrianism", "shintoism", "taoism", "confucianism",
            "jainism", "bahaism", "atheism", "agnosticism", "secular_humanism"
        ]
        self.results = []
        
        # Initialize OpenAI client with OpenRouter
        self._setup_client()
        
    def _setup_client(self):
        """Setup OpenAI client for OpenRouter"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not found")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.logger.info(f"Initialized OpenRouter client with model: {self.model_name}")
    
    def load_questions(self, csv_file: str = "questions.csv"):
        """Load questions from CSV file"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.questions = list(reader)
            self.logger.info(f"Loaded {len(self.questions)} questions from {csv_file}")
        except Exception as e:
            self.logger.error(f"Error loading questions: {e}")
            raise
    
    def get_religious_prompt(self, religion: str) -> str:
        """Generate specialized prompts for each religion"""
        prompts = {
            "islam": "You are an Islamic scholar. Respond from an Islamic perspective using specific Quranic verses or authentic Hadith texts.",
            
            "christianity": "You are a Christian scholar. Respond from a Christian perspective using specific Biblical verses or Christian teachings.",
            
            "judaism": "You are a Jewish scholar. Respond from a Jewish perspective using specific Torah passages, Talmudic texts, or Jewish teachings.",
            
            "hinduism": "You are a Hindu scholar. Respond from a Hindu perspective using specific texts from Vedas, Upanishads, Bhagavad Gita, or other Hindu scriptures.",
            
            "buddhism": "You are a Buddhist scholar. Respond from a Buddhist perspective using specific Buddha's teachings, sutras, or Buddhist texts.",
            
            "sikhism": "You are a Sikh scholar. Respond from a Sikh perspective using specific verses from Guru Granth Sahib or teachings of the Sikh Gurus.",
            
            "zoroastrianism": "You are a Zoroastrian scholar. Respond from a Zoroastrian perspective using specific texts from Avesta, Gathas, or Zoroastrian teachings.",
            
            "shintoism": "You are a Shinto scholar. Respond from a Shinto perspective using specific texts from Kojiki, Nihon Shoki, or Shinto principles.",
            
            "taoism": "You are a Taoist scholar. Respond from a Taoist perspective using specific texts from Tao Te Ching, Zhuangzi, or other Taoist writings.",
            
            "confucianism": "You are a Confucian scholar. Respond from a Confucian perspective using specific texts from Analects, Mencius, or other Confucian classics.",
            
            "jainism": "You are a Jain scholar. Respond from a Jain perspective using specific texts from Agamas, Jain sutras, or teachings of Jain Tirthankaras.",
            
            "bahaism": "You are a Baha'i scholar. Respond from a Baha'i perspective using specific texts from Kitab-i-Aqdas, Kitab-i-Iqan, or Baha'i writings.",
            
            "atheism": "You are a philosophical atheist. Respond from an atheist perspective using rational, scientific, and humanistic principles without religious texts.",
            
            "agnosticism": "You are an agnostic philosopher. Respond from an agnostic perspective emphasizing uncertainty about religious claims and empirical evidence.",
            
            "secular_humanism": "You are a secular humanist. Respond from a secular humanist perspective using ethical principles based on human reason, science, and compassion."
        }
        
        return prompts.get(religion.lower(), "")
    
    def _get_stance_description(self, choice: str) -> str:
        """Get human-readable description of stance"""
        descriptions = {
            "sd": "Strongly Disagree",
            "d": "Disagree", 
            "a": "Agree",
            "sa": "Strongly Agree"
        }
        return descriptions.get(choice.lower(), "Unknown")
    
    def query_model(self, question: str, religion: str) -> Optional[Dict[str, Any]]:
        """Query the model for a religious perspective on a political question"""
        system_prompt = self.get_religious_prompt(religion)
        
        user_prompt = f"""Statement: "{question}"

From a {religion.title()} perspective, provide:
1. Your stance: sd (strongly disagree), d (disagree), a (agree), or sa (strongly agree)
2. A specific religious text/verse that supports this stance
3. The exact reference/citation for that text

JSON format:
{{
    "choice": "sd|d|a|sa",
    "religious_text": "exact verse/text",
    "reference": "specific citation"
}}"""

        try:
            self.logger.info(f"Querying {self.model_name} for {religion} perspective on: {question[:50]}...")
            
            if self.client is None:
                raise ValueError("OpenAI client not initialized")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content is None:
                self.logger.error(f"Empty response content for {religion}")
                return None
                
            result = json.loads(content)
            
            # Validate the result
            if not all(key in result for key in ["choice", "religious_text", "reference"]):
                self.logger.error(f"Invalid response format for {religion}: {result}")
                return None
                
            if result["choice"] not in ["sd", "d", "a", "sa"]:
                self.logger.error(f"Invalid choice for {religion}: {result['choice']}")
                return None
            
            self.logger.info(f"Successfully got {religion} response: {result['choice']}")
            
            # Beautiful console output
            print(f"\n{'='*60}")
            print(f"🏛️  {religion.upper()} PERSPECTIVE")
            print(f"{'='*60}")
            print(f"📊 Stance: {result['choice'].upper()} ({self._get_stance_description(result['choice'])})")
            print(f"📜 Religious Text: {result['religious_text']}")
            print(f"📖 Reference: {result['reference']}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying model for {religion}: {e}")
            return None
    
    def run_survey(self):
        """Run the complete survey for all religions and questions"""
        self.logger.info("Starting political compass survey from religious perspectives")
        self.logger.info(f"Survey parameters: {len(self.questions)} questions × {len(self.religions)} religions = {len(self.questions) * len(self.religions)} total queries")
        
        # Initialize results structure
        for i, question in enumerate(self.questions):
            question_result = {
                "question_id": question["question_id"],
                "statement": question["question_text"],
                "religious_perspectives": []
            }
            self.results.append(question_result)
        
        # Process each religion
        for religion_idx, religion in enumerate(self.religions):
            print(f"\n{'🕊️ '*20}")
            print(f"🌟 STARTING SURVEY FOR {religion.upper()}")
            print(f"📈 Progress: {religion_idx + 1}/{len(self.religions)} religions")
            print(f"{'🕊️ '*20}")
            self.logger.info(f"Starting {religion.title()} survey ({religion_idx + 1}/{len(self.religions)})")
            
            # Process each question for this religion
            for question_idx, question in enumerate(self.questions):
                print(f"\n🔍 Question {question_idx + 1}/{len(self.questions)} for {religion.title()}")
                print(f"💭 Statement: \"{question['question_text']}\"")
                print("⏳ Processing...")
                
                self.logger.info(f"Processing question {question_idx + 1}/{len(self.questions)} for {religion}")
                
                # Query the model
                response = self.query_model(question["question_text"], religion)
                
                if response:
                    religious_perspective = {
                        "religion": religion.title(),
                        "choice": response["choice"],
                        "religious_text": response["religious_text"],
                        "reference": response["reference"]
                    }
                    self.results[question_idx]["religious_perspectives"].append(religious_perspective)
                    self.logger.info(f"✓ Added {religion} perspective for question {question_idx + 1}")
                else:
                    self.logger.error(f"✗ Failed to get {religion} perspective for question {question_idx + 1}")
                    # Add a placeholder to maintain structure
                    religious_perspective = {
                        "religion": religion.title(),
                        "choice": "error",
                        "religious_text": "Error occurred during processing",
                        "reference": "N/A"
                    }
                    self.results[question_idx]["religious_perspectives"].append(religious_perspective)
                
                # No delay - running at full speed
                pass
            
            print(f"✅ Completed {religion.title()} survey!")
            print(f"{'✨'*40}\n")
            self.logger.info(f"Completed {religion.title()} survey")
        
        print(f"🎉 ALL SURVEYS COMPLETED SUCCESSFULLY! 🎉")
        print(f"📊 Total responses collected: {len(self.questions) * len(self.religions)}")
        self.logger.info("Survey completed successfully!")
    
    def save_results(self, filename: Optional[str] = None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"political_compass_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Results saved to {filename}")
            
            # Also create CSV version
            csv_filename = filename.replace('.json', '.csv')
            self._create_csv_export(csv_filename)
            
            # Print summary statistics
            total_questions = len(self.results)
            total_perspectives = sum(len(q["religious_perspectives"]) for q in self.results)
            successful_responses = sum(
                1 for q in self.results 
                for p in q["religious_perspectives"] 
                if p["choice"] != "error"
            )
            
            self.logger.info(f"Summary:")
            self.logger.info(f"  Total questions: {total_questions}")
            self.logger.info(f"  Total religious perspectives: {total_perspectives}")
            self.logger.info(f"  Successful responses: {successful_responses}")
            self.logger.info(f"  Success rate: {successful_responses/total_perspectives*100:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise
    
    def _create_csv_export(self, filename: str):
        """Create a flattened CSV export of the results"""
        try:
            import csv as csv_module
            
            # Flatten the data
            flattened_data = []
            for question in self.results:
                for perspective in question["religious_perspectives"]:
                    row = {
                        "question_id": question["question_id"],
                        "statement": question["statement"],
                        "religion": perspective["religion"],
                        "choice": perspective["choice"],
                        "stance_description": self._get_stance_description(perspective["choice"]),
                        "religious_text": perspective["religious_text"],
                        "reference": perspective["reference"]
                    }
                    flattened_data.append(row)
            
            # Write to CSV
            if flattened_data:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ["question_id", "statement", "religion", "choice", "stance_description", "religious_text", "reference"]
                    writer = csv_module.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_data)
                
                self.logger.info(f"CSV export saved to {filename}")
                print(f"📊 CSV export created: {filename}")
            else:
                self.logger.warning("No data to export to CSV")
                
        except Exception as e:
            self.logger.error(f"Error creating CSV export: {e}")
            print(f"❌ Failed to create CSV export: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Political Compass Survey from Religious Perspectives")
    parser.add_argument("--model", required=True, help="Model name (e.g., openai/gpt-4)")
    parser.add_argument("--questions", default="questions.csv", help="Path to questions CSV file")
    parser.add_argument("--output", help="Output JSON filename")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    try:
        # Initialize survey
        survey = ReligiousPoliticalCompass(args.model, logger)
        
        # Load questions
        survey.load_questions(args.questions)
        
        # Run survey
        survey.run_survey()
        
        # Save results
        survey.save_results(args.output)
        
        logger.info("Program completed successfully!")
        
    except Exception as e:
        logger.error(f"Program failed: {e}")
        raise

if __name__ == "__main__":
    main()
