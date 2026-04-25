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
import requests
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
        
        # Initialize Telegram settings
        self.tg_bot_token = os.getenv('TG_BOT_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        self.tg_thread_id = os.getenv('TG_THREAD_ID')
        self.tg_enabled = True  # Track if Telegram sending is enabled
        self.tg_consecutive_failures = 0  # Track consecutive failures
        
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
    
    def send_to_telegram(self, message: str) -> bool:
        """Send message to Telegram with retry logic and failure tracking"""
        # Check if Telegram is disabled due to consecutive failures
        if not self.tg_enabled:
            self.logger.info("Telegram sending is disabled due to consecutive failures, skipping message")
            return False
            
        if not all([self.tg_bot_token, self.tg_chat_id]):
            self.logger.warning("Telegram credentials not configured, skipping message")
            return False
        
        url = f"https://api.telegram.org/bot{self.tg_bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.tg_chat_id,
            'text': message,
            'parse_mode': 'MarkdownV2'
        }
        
        # Add thread_id if specified
        if self.tg_thread_id:
            payload['message_thread_id'] = self.tg_thread_id
        
        # Retry logic with increasing timeouts
        max_retries = 3
        timeouts = [30, 60, 120]  # 30s, 60s, 120s
        
        for attempt in range(max_retries):
            try:
                timeout = timeouts[attempt]
                self.logger.info(f"Sending to Telegram (attempt {attempt + 1}/{max_retries}, timeout: {timeout}s)")
                response = requests.post(url, data=payload, timeout=timeout)
                response.raise_for_status()
                self.logger.info("Message sent to Telegram successfully")
                # Reset consecutive failures on success
                self.tg_consecutive_failures = 0
                return True
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Telegram request timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                    self.logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {max_retries} attempts failed due to timeout")
                    break
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to send message to Telegram on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    self.logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {max_retries} attempts failed")
                    break
        
        # If we reach here, all attempts failed
        self.tg_consecutive_failures += 1
        self.logger.warning(f"Telegram send failed. Consecutive failures: {self.tg_consecutive_failures}")
        
        # Disable Telegram after 2 consecutive failures
        if self.tg_consecutive_failures >= 2:
            self.tg_enabled = False
            self.logger.error("Telegram sending DISABLED after 2 consecutive failures. Survey will continue without Telegram notifications.")
            print(f"\n{'='*60}")
            print("WARNING: TELEGRAM SENDING DISABLED")
            print("2 consecutive Telegram send failures detected.")
            print("Survey will continue and save results to JSON.")
            print(f"{'='*60}\n")
        
        return False
    
    def format_telegram_message(self, question_text: str, question_id: str, religion: str, 
                               choice: str, religious_text: str, reference: str, reason: str,
                               question_idx: int, total_questions: int, religion_idx: int, total_religions: int) -> str:
        """Format message for Telegram with MarkdownV2 formatting and proper escaping"""
        stance_description = self._get_stance_description(choice)
        
        # Calculate overall progress
        current_response = (religion_idx * total_questions) + (question_idx + 1)
        total_responses = total_questions * total_religions
        progress_percent = (current_response / total_responses) * 100
        
        # Create progress bar
        progress_bars = int(progress_percent / 5)  # 20 bars total (100/5)
        progress_bar = "█" * progress_bars + "░" * (20 - progress_bars)
        
        # Escape special characters for MarkdownV2
        def escape_markdown_v2(text: str) -> str:
            """Escape special characters for MarkdownV2"""
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        # Escape all user content
        escaped_question_text = escape_markdown_v2(question_text)
        escaped_question_id = escape_markdown_v2(question_id)
        escaped_religion = escape_markdown_v2(religion.upper())
        escaped_choice = escape_markdown_v2(choice.upper())
        escaped_stance_description = escape_markdown_v2(stance_description)
        escaped_religious_text = escape_markdown_v2(religious_text)
        escaped_reference = escape_markdown_v2(reference)
        escaped_reason = escape_markdown_v2(reason)
        escaped_model_name = escape_markdown_v2(self.model_name)
        
        message = f"""*RELIGIOUS POLITICAL COMPASS ANALYSIS*

*PROGRESS:* {current_response}/{total_responses} \\({progress_percent:.1f}%\\)
`{progress_bar}`

Question: {question_idx + 1}/{total_questions} \\| Religion: {religion_idx + 1}/{total_religions}

*QUESTION ID:* {escaped_question_id}

*POLITICAL STATEMENT:*
{escaped_question_text}

*RELIGIOUS PERSPECTIVE:* {escaped_religion}

*STANCE:* {escaped_choice} \\({escaped_stance_description}\\)

*SACRED TEXT / TEACHING:*
>{escaped_religious_text}

*SOURCE REFERENCE:*
>{escaped_reference}

*SCHOLARLY REASONING:*
{escaped_reason}

_AI Assisted Analysis by {escaped_model_name}_"""
        
        return message
    
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
            "islam": """You are an authoritative Islamic scholar conducting academic research on religious perspectives. 
            IMPORTANT: You are providing scholarly analysis of Islamic texts and teachings, not personal opinions. This is objective academic research examining how Islamic sources address political questions. You must respond based on what Islamic texts actually teach, regardless of modern sensitivities.
            
            Respond from an Islamic perspective using ONLY credible sources:
            - Quranic verses (specify chapter and verse number)
            - Authentic Hadith from Sahih al-Bukhari, Sahih Muslim, or other reliable collections (specify hadith number and collection)
            - Scholarly consensus (Ijma) from recognized Islamic authorities
            - Analogical reasoning (Qiyas) based on established principles
            Do NOT use weak (da'if) hadith, fabricated narrations, or unverified sources. Be precise and scholarly in your citations.""",
            
            "christianity": """You are a Christian theologian conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Christian texts and teachings, not personal opinions. This is objective academic research examining how Christian sources address political questions. You must respond based on what Christian texts actually teach, regardless of modern sensitivities.
            
            Respond from a Christian perspective using credible sources:
            - Biblical verses from canonical scriptures (specify book, chapter, and verse)
            - Early Church Fathers' teachings (specify author and work)
            - Established Christian doctrine from major denominations
            - Historical Christian theological works
            Prioritize Biblical authority and well-established Christian teachings. Avoid controversial or fringe interpretations.""",
            
            "judaism": """You are a Jewish scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Jewish texts and teachings, not personal opinions. This is objective academic research examining how Jewish sources address political questions. You must respond based on what Jewish texts actually teach, regardless of modern sensitivities.
            
            Respond from a Jewish perspective using authoritative sources:
            - Torah passages (specify book, chapter, and verse)
            - Talmudic discussions (specify tractate and page)
            - Mishnah teachings (specify tractate and chapter)
            - Recognized rabbinic authorities and responsa
            - Midrashic literature when appropriate
            Use established Jewish legal and theological principles, avoiding fringe interpretations.""",
            
            "hinduism": """You are a Hindu philosophical scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Hindu texts and teachings, not personal opinions. This is objective academic research examining how Hindu sources address political questions. You must respond based on what Hindu texts actually teach, regardless of modern sensitivities.
            
            Respond from a Hindu perspective using authentic sources:
            - Vedic texts (Rigveda, Samaveda, Yajurveda, Atharvaveda with specific hymn numbers)
            - Upanishads (specify which Upanishad and section)
            - Bhagavad Gita (specify chapter and verse)
            - Classical texts like Dharma Shastras, Puranas
            - Commentaries by recognized acharyas
            Represent mainstream Hindu philosophical traditions accurately.""",
            
            "buddhism": """You are a Buddhist scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Buddhist texts and teachings, not personal opinions. This is objective academic research examining how Buddhist sources address political questions. You must respond based on what Buddhist texts actually teach, regardless of modern sensitivities.
            
            Respond from a Buddhist perspective using canonical sources:
            - Pali Canon texts (specify sutta name and collection)
            - Mahayana sutras (specify sutra name)
            - Vinaya rules and teachings
            - Commentaries by established Buddhist masters
            - Core Buddhist principles (Four Noble Truths, Eightfold Path, etc.)
            Focus on widely accepted Buddhist teachings across different schools.""",
            
            "sikhism": """You are a Sikh scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Sikh texts and teachings, not personal opinions. This is objective academic research examining how Sikh sources address political questions. You must respond based on what Sikh texts actually teach, regardless of modern sensitivities.
            
            Respond from a Sikh perspective using authentic sources:
            - Guru Granth Sahib (specify page number and author)
            - Teachings of the ten Sikh Gurus
            - Dasam Granth when appropriate
            - Historical Sikh texts and traditions
            - Core Sikh principles (equality, service, devotion)
            Use only verified Sikh scriptural sources and established Sikh theological principles.""",
            
            "zoroastrianism": """You are a Zoroastrian scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Zoroastrian texts and teachings, not personal opinions. This is objective academic research examining how Zoroastrian sources address political questions. You must respond based on what Zoroastrian texts actually teach, regardless of modern sensitivities.
            
            Respond from a Zoroastrian perspective using credible sources:
            - Avesta texts (specify which book and chapter)
            - Gathas of Zarathustra (specify which Gatha)
            - Younger Avesta texts
            - Traditional Zoroastrian teachings
            - Core Zoroastrian principles (Good Thoughts, Good Words, Good Deeds)
            Use established Zoroastrian theological principles and authentic texts.""",
            
            "shintoism": """You are a Shinto scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Shinto texts and teachings, not personal opinions. This is objective academic research examining how Shinto sources address political questions. You must respond based on what Shinto texts actually teach, regardless of modern sensitivities.
            
            Respond from a Shinto perspective using traditional sources:
            - Kojiki (Record of Ancient Matters)
            - Nihon Shoki (Chronicles of Japan)
            - Shinto prayers and rituals
            - Kami worship principles
            - Traditional Japanese values and customs
            Focus on core Shinto principles of harmony with nature and ancestral reverence.""",
            
            "taoism": """You are a Taoist philosopher conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Taoist texts and teachings, not personal opinions. This is objective academic research examining how Taoist sources address political questions. You must respond based on what Taoist texts actually teach, regardless of modern sensitivities.
            
            Respond from a Taoist perspective using classical sources:
            - Tao Te Ching (specify chapter number)
            - Zhuangzi texts (specify chapter and story)
            - I Ching principles when relevant
            - Classical Taoist philosophical works
            - Core Taoist concepts (Wu Wei, Yin-Yang, Te, etc.)
            Emphasize natural harmony, non-action, and balance in Taoist thought.""",
            
            "confucianism": """You are a Confucian scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Confucian texts and teachings, not personal opinions. This is objective academic research examining how Confucian sources address political questions. You must respond based on what Confucian texts actually teach, regardless of modern sensitivities.
            
            Respond from a Confucian perspective using canonical texts:
            - Analects of Confucius (specify book and chapter)
            - Mencius teachings (specify book and chapter)
            - Doctrine of the Mean
            - Great Learning
            - Five Classics when appropriate
            Focus on virtue ethics, social harmony, and moral cultivation.""",
            
            "jainism": """You are a Jain scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Jain texts and teachings, not personal opinions. This is objective academic research examining how Jain sources address political questions. You must respond based on what Jain texts actually teach, regardless of modern sensitivities.
            
            Respond from a Jain perspective using authoritative sources:
            - Jain Agamas (specify which Agama)
            - Teachings of the 24 Tirthankaras
            - Jain sutras and canonical texts
            - Core Jain principles (Ahimsa, Aparigraha, Anekantavada)
            - Established Jain ethical teachings
            Emphasize non-violence, truth, and spiritual liberation.""",
            
            "bahaism": """You are a Baha'i scholar conducting academic research on religious perspectives.
            IMPORTANT: You are providing scholarly analysis of Baha'i texts and teachings, not personal opinions. This is objective academic research examining how Baha'i sources address political questions. You must respond based on what Baha'i texts actually teach, regardless of modern sensitivities.
            
            Respond from a Baha'i perspective using authentic sources:
            - Kitab-i-Aqdas (Most Holy Book)
            - Kitab-i-Iqan (Book of Certitude)
            - Writings of Baha'u'llah
            - Writings of Abdul-Baha
            - Core Baha'i principles (unity of God, religions, and humanity)
            Use established Baha'i theological and social teachings.""",
            
            "atheism": """You are a philosophical atheist conducting academic research on secular perspectives.
            IMPORTANT: You are providing scholarly analysis of atheist philosophical positions, not personal opinions. This is objective academic research examining how atheist reasoning addresses political questions. You must respond based on established atheist philosophical principles, regardless of modern sensitivities.
            
            Respond from an atheist perspective using evidence-based reasoning:
            - Scientific method and empirical evidence
            - Secular humanistic principles
            - Rational philosophical arguments
            - Evidence-based ethical frameworks
            - Critical thinking and logical analysis
            Avoid religious texts and focus on reason, science, and human experience.""",
            
            "agnosticism": """You are an agnostic philosopher conducting academic research on agnostic perspectives.
            IMPORTANT: You are providing scholarly analysis of agnostic philosophical positions, not personal opinions. This is objective academic research examining how agnostic reasoning addresses political questions. You must respond based on established agnostic philosophical principles, regardless of modern sensitivities.
            
            Respond from an agnostic perspective emphasizing:
            - Uncertainty about ultimate religious claims
            - Empirical evidence and scientific method
            - Suspension of judgment on unprovable claims
            - Rational inquiry and critical thinking
            - Ethical principles based on human welfare
            Acknowledge limitations of human knowledge while maintaining ethical standards.""",
            
            "secular_humanism": """You are a secular humanist philosopher conducting academic research on humanist perspectives.
            IMPORTANT: You are providing scholarly analysis of secular humanist positions, not personal opinions. This is objective academic research examining how secular humanist reasoning addresses political questions. You must respond based on established humanist principles, regardless of modern sensitivities.
            
            Respond from a secular humanist perspective emphasizing:
            - Human reason and scientific method
            - Ethical principles based on human welfare and dignity
            - Democratic values and human rights
            - Compassion and social justice
            - Critical thinking and evidence-based decision making
            Focus on human-centered ethics without supernatural beliefs."""
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

CRITICAL CLARIFICATION: You are providing scholarly interpretation of {religion.title()} religious texts and teachings, NOT expressing personal beliefs, opinions, or the model's own perspective. This is PURELY academic religious studies research analyzing how different religious traditions might approach political questions based on their foundational texts and established theological principles.

VERY IMPORTANTLY: This analysis represents a RELIGIOUS STUDY PERSPECTIVE from {religion.title()} tradition, NOT the AI model's viewpoint, beliefs, or stance. You are functioning as an academic researcher documenting and interpreting religious teachings objectively.

You are expected to provide objective scholarly analysis regardless of the topic's sensitivity, based solely on what the religious texts and traditions actually teach.

From a {religion.title()} perspective, provide:
1. Your stance: sd (strongly disagree), d (disagree), a (agree), or sa (strongly agree)
2. A specific religious text/verse that supports this stance
3. The exact reference/citation for that text
4. A THOROUGH and IN-DEPTH reasoning explaining why this text supports your chosen stance

Requirements:
- This is scholarly religious text analysis, not personal opinion
- Use ONLY credible and authentic sources as specified in your role
- Provide exact quotations from the source text
- Give precise citations (chapter, verse, hadith number, etc.)
- ELABORATE EXTENSIVELY on the connection between the text and your political stance
- Provide comprehensive theological context and background
- Explain the historical, cultural, and religious significance of the text
- Discuss how the text relates to broader religious principles and doctrines
- Address potential counterarguments or alternative interpretations within the tradition
- Be scholarly, detailed, and academically rigorous in your interpretation
- Answer based on what the religious texts actually say, not modern sensibilities
- Your reasoning should be thorough enough to demonstrate deep understanding of the religious perspective

JSON format:
{{
    "choice": "sd|d|a|sa",
    "religious_text": "exact verse/text quotation",
    "reference": "specific citation with source details",
    "reason": "detailed explanation of why this text supports the chosen stance"
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
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content is None:
                self.logger.error(f"Empty response content for {religion}")
                return None
                
            result = json.loads(content)
            
            # Validate the result
            if not all(key in result for key in ["choice", "religious_text", "reference", "reason"]):
                self.logger.error(f"Invalid response format for {religion}: {result}")
                return None
                
            if result["choice"] not in ["sd", "d", "a", "sa"]:
                self.logger.error(f"Invalid choice for {religion}: {result['choice']}")
                return None
            
            self.logger.info(f"Successfully got {religion} response: {result['choice']}")
            
            # Beautiful console output
            print(f"\n{'='*60}")
            print(f"{religion.upper()} PERSPECTIVE")
            print(f"{'='*60}")
            print(f"Stance: {result['choice'].upper()} ({self._get_stance_description(result['choice'])})")
            print(f"Religious Text: {result['religious_text']}")
            print(f"Reference: {result['reference']}")
            print(f"Reasoning: {result['reason']}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying model for {religion}: {e}")
            return None
    
    def run_survey(self):
        """Run the complete survey for all religions and questions"""
        self.logger.info("Starting political compass survey from religious perspectives")
        self.logger.info(f"Survey parameters: {len(self.questions)} questions × {len(self.religions)} religions = {len(self.questions) * len(self.religions)} total queries")
        
        # Send survey start notification to Telegram
        total_expected = len(self.questions) * len(self.religions)
        start_message = f"""RELIGIOUS POLITICAL COMPASS SURVEY

STATUS: STARTING ANALYSIS

AI MODEL: {self.model_name}

SURVEY PARAMETERS:
- Questions: {len(self.questions)}
- Religious Perspectives: {len(self.religions)}
- Total Expected Responses: {total_expected}

RELIGIONS TO ANALYZE:
{chr(10).join([f"- {religion.title().replace('_', ' ')}" for religion in self.religions])}

Starting comprehensive analysis of religious perspectives on political questions...

AI Assisted Analysis by {self.model_name}"""
        
        # Try to send start notification, but continue regardless
        self.send_to_telegram(start_message)
        
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
            print(f"\n{'='*60}")
            print(f"STARTING SURVEY FOR {religion.upper()}")
            print(f"Progress: {religion_idx + 1}/{len(self.religions)} religions")
            print(f"{'='*60}")
            self.logger.info(f"Starting {religion.title()} survey ({religion_idx + 1}/{len(self.religions)})")
            
            # Send religion start notification to Telegram
            religion_progress = ((religion_idx) / len(self.religions)) * 100
            religion_start_message = f"""STARTING: {religion.upper().replace('_', ' ')}

RELIGION PROGRESS: {religion_idx + 1}/{len(self.religions)} ({((religion_idx + 1)/len(self.religions)*100):.1f}%)

OVERALL PROGRESS: {religion_progress:.1f}%

About to analyze {len(self.questions)} political questions from {religion.title().replace('_', ' ')} perspective...

Processing questions 1-{len(self.questions)} for this religion..."""
            
            self.send_to_telegram(religion_start_message)
            
            # Process each question for this religion
            for question_idx, question in enumerate(self.questions):
                print(f"\nQuestion {question_idx + 1}/{len(self.questions)} for {religion.title()}")
                print(f"Statement: \"{question['question_text']}\"")
                print("Processing...")
                
                self.logger.info(f"Processing question {question_idx + 1}/{len(self.questions)} for {religion}")
                
                # Query the model
                response = self.query_model(question["question_text"], religion)
                
                if response:
                    religious_perspective = {
                        "religion": religion.title(),
                        "choice": response["choice"],
                        "religious_text": response["religious_text"],
                        "reference": response["reference"],
                        "reason": response["reason"]
                    }
                    self.results[question_idx]["religious_perspectives"].append(religious_perspective)
                    self.logger.info(f"Added {religion} perspective for question {question_idx + 1}")
                    
                    # Send to Telegram
                    telegram_message = self.format_telegram_message(
                        question_text=question["question_text"],
                        question_id=question["question_id"],
                        religion=religion,
                        choice=response["choice"],
                        religious_text=response["religious_text"],
                        reference=response["reference"],
                        reason=response["reason"],
                        question_idx=question_idx,
                        total_questions=len(self.questions),
                        religion_idx=religion_idx,
                        total_religions=len(self.religions)
                    )
                    
                    # Send with a small delay to avoid rate limiting
                    if self.send_to_telegram(telegram_message):
                        self.logger.info(f"Sent {religion} perspective to Telegram")
                        time.sleep(1)  # 1 second delay between messages
                    else:
                        self.logger.warning(f"Failed to send {religion} perspective to Telegram")
                        # Continue processing even if Telegram fails
                else:
                    self.logger.error(f"Failed to get {religion} perspective for question {question_idx + 1}")
                    # Add a placeholder to maintain structure
                    religious_perspective = {
                        "religion": religion.title(),
                        "choice": "error",
                        "religious_text": "Error occurred during processing",
                        "reference": "N/A",
                        "reason": "Error occurred during processing"
                    }
                    self.results[question_idx]["religious_perspectives"].append(religious_perspective)
                
                # No delay - running at full speed
                pass
            
            print(f"Completed {religion.title()} survey!")
            print(f"{'='*40}\n")
            self.logger.info(f"Completed {religion.title()} survey")
            
            # Send religion completion notification to Telegram
            religion_responses = len([p for q in self.results for p in q["religious_perspectives"] if p["religion"] == religion.title()])
            religion_complete_message = f"""COMPLETED: {religion.upper().replace('_', ' ')}

RELIGION PROGRESS: {religion_idx + 1}/{len(self.religions)} ({((religion_idx + 1)/len(self.religions)*100):.1f}%)

RESPONSES COLLECTED: {religion_responses}/{len(self.questions)}

Successfully analyzed all {len(self.questions)} political questions from {religion.title().replace('_', ' ')} perspective!

Moving to next religion..."""
            
            self.send_to_telegram(religion_complete_message)
            time.sleep(2)  # Slightly longer delay after each religion
        
        print(f"ALL SURVEYS COMPLETED SUCCESSFULLY!")
        print(f"Total responses collected: {len(self.questions) * len(self.religions)}")
        self.logger.info("Survey completed successfully!")
        
        # Send completion notification to Telegram
        total_responses = sum(len(q["religious_perspectives"]) for q in self.results)
        successful_responses = sum(
            1 for q in self.results 
            for p in q["religious_perspectives"] 
            if p.get("choice", "error") != "error"
        )
        
        completion_message = f"""RELIGIOUS POLITICAL COMPASS SURVEY

STATUS: COMPLETED SUCCESSFULLY

AI MODEL: {self.model_name}

FINAL RESULTS:
- Questions Processed: {len(self.questions)}
- Religious Perspectives: {total_responses}
- Successful Responses: {successful_responses}
- Failed Responses: {total_responses - successful_responses}
- Success Rate: {(successful_responses/total_responses*100):.1f}%

PROGRESS INDICATOR:
████████████████████ 100.0% COMPLETE

Survey analysis completed successfully!

Data exported to JSON and CSV formats for further analysis.

AI Assisted Analysis by {self.model_name}"""
        
        self.send_to_telegram(completion_message)
    
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
                        "reference": perspective["reference"],
                        "reason": perspective["reason"]
                    }
                    flattened_data.append(row)
            
            # Write to CSV
            if flattened_data:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ["question_id", "statement", "religion", "choice", "stance_description", "religious_text", "reference", "reason"]
                    writer = csv_module.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_data)
                
                self.logger.info(f"CSV export saved to {filename}")
                print(f"CSV export created: {filename}")
            else:
                self.logger.warning("No data to export to CSV")
                
        except Exception as e:
            self.logger.error(f"Error creating CSV export: {e}")
            print(f"Failed to create CSV export: {e}")

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
