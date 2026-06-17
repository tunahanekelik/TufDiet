"""
TufDiet RAG & LLM Service Layer
Production-Ready Hybrid AI Integration (Gemini Vision + Groq RAG)
"""

import os
import json
import base64
import re
import io
import requests
from pathlib import Path
from typing import List, Dict, Optional
from django.conf import settings
from PIL import Image
import pillow_avif  # AVIF image support injection

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document as LCDocument
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / 'knowledge_base' / 'docs'
CHROMA_DIR = PROJECT_ROOT / 'knowledge_base' / 'chroma_db'

def encode_image_to_base64(image_path):
    """Normalizes any incoming image format (including AVIF) to a secure base64 JPEG stream"""
    try:
        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"[Image Processor] Normalization failed, falling back to raw bytes: {str(e)}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


class TufDietAIClient:
    """Gemini Flash Vision model for robust open-world food image analysis"""

    def __init__(self):
        gemini_api_key = getattr(settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
        if gemini_api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",  # Emekliye ayrılan 1.5 sürümü yerine güncel 2.5 sürümünü bağladık!
                google_api_key=gemini_api_key,
                temperature=0.1,
            )
        else:
            self.llm = None
            print("[TufDietAIClient] CRITICAL: GEMINI_API_KEY not found in settings.")

    def analyze_food_image(self, user_data: Dict, image_path: str) -> Dict:
        if not self.llm:
            return {
                'food_name': 'Unknown',
                'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0,
                'confidence': 0.0, 'components': [], 'error': 'GEMINI_API_KEY missing'
            }

        base64_image = encode_image_to_base64(image_path)

        
        system_prompt = SystemMessage(
            content="You are a certified AI Dietitian specializing in visual food analysis. "
                    "Analyze the food image by breaking it down into its separate dietary components. "
                    "CRITICAL CALIBRATION FOR REAL-WORLD ACCURACY (FatSecret & USDA Baseline Alignment):\n"
                    "1. INEDIBLE PORTIONS & REFUSE FACTOR (Bones, Shells, Peels, Rinds, Cores, Seeds): You must critically evaluate if any food component contains visually present parts that are not actually consumed. ALWAYS calculate the final calories and macros based strictly on the EDIBLE NET WEIGHT. Visually estimate the gross weight, but subtract the appropriate refuse percentage BEFORE doing the nutritional math. Examples:\n"
                    "   - Bone-in Meats/Poultry (e.g., chicken drumsticks, wings, T-bone, ribs): Subtract 35% to 40% as bone weight.\n"
                    "   - Fruits/Vegetables with rinds, peels, or cores (e.g., lemon/orange slices, avocado skins, apple cores, melon rinds): Subtract 10% to 35% as inedible waste.\n"
                    "   - Seafood with shells or tails (e.g., unshelled shrimp, mussels, crabs): Subtract 40% to 50% as shell weight.\n"
                    "   Main calorie and macro fields must reflect ONLY the combined sum of these EDIBLE net weights.\n"
                    "2. PREPARATION METHOD: Strictly distinguish between roasted/baked (moderate fat) and deep-fried/breaded (very high fat) foods. Do not overestimate fat content unless heavy oil or breading is explicitly visible.\n"
                    "3. PORTION SCALE: Cross-reference your volumetric estimation with standard nutritional databases. Avoid inflating grams based on 2D perspective close-ups.\n\n"
                    "Respond ONLY with a valid JSON block having exactly these keys:\n"
                    "- food_name: Clean overall name of the dish (string)\n"
                    "- calories: Total combined calories (float)\n"
                    "- protein_g: Total combined protein (float)\n"
                    "- carbs_g: Total combined carbohydrates (float)\n"
                    "- fat_g: Total combined fat (float)\n"
                    "- confidence: Analysis confidence 0-1 (float)\n"
                    "- components: A list of objects, where each object represents a single food item from the plate and contains:\n"
                    "  {'name': string, 'amount': string (e.g. '6 pcs, ~320g net et' or '50g, peel removed'), 'calories': float, 'protein': float, 'carbs': float, 'fat': float}\n"
                    "Do not include markdown wrappers like ```json or any extra text outside the raw JSON."
        )
        
        user_message = HumanMessage(content=[
            {
                "type": "text",
                "text": f"User weight={user_data.get('weight',70)}kg, goal={user_data.get('goal','MAINTAIN_FAT_LOSS')}. Identify and itemize each food component."
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
        ])
        try:
            response = self.llm.invoke([system_prompt, user_message])
            raw = response.content.strip()
            
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                result = json.loads(match.group(0))
            else:
                raise ValueError("No valid JSON found")

            # views.py'a hem toplamları hem de frontend'in parçalayacağı listeyi fırlatıyoruz
            return {
                'food_name': result.get('food_name', 'Unknown'),
                'calories': float(result.get('calories', 0)),
                'protein': float(result.get('protein_g', 0)),
                'carbs': float(result.get('carbs_g', 0)),
                'fat': float(result.get('fat_g', 0)),
                'confidence': float(result.get('confidence', 0)),
                'components': result.get('components', []) # Alt alta bölünecek liste burası!
            }
        except Exception as e:
            return {
                'food_name': 'Unknown',
                'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0,
                'confidence': 0.0, 'components': [], 'error': str(e)
            }


class KnowledgeBase:
    """Ingests dietary documents into Chroma vector store"""

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name='sentence-transformers/all-MiniLM-L6-v2'
        )
        self.vector_store = None

    def _load_text_files(self) -> List:
        docs = []
        if not KNOWLEDGE_DIR.exists():
            os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
            return docs
            
        for fpath in KNOWLEDGE_DIR.glob('*.txt'):
            with open(fpath, 'r', encoding='utf-8') as f:
                text = f.read()
            docs.append(LCDocument(
                page_content=text,
                metadata={'source': str(fpath.name)}
            ))
        for fpath in KNOWLEDGE_DIR.glob('*.json'):
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    docs.append(LCDocument(
                        page_content=json.dumps(item),
                        metadata={'source': str(fpath.name)}
                    ))
            else:
                docs.append(LCDocument(
                    page_content=json.dumps(data),
                    metadata={'source': str(fpath.name)}
                ))
        return docs

    def index_documents(self, force_reindex: bool = False):
        if CHROMA_DIR.exists() and not force_reindex:
            self.vector_store = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=self.embeddings
            )
            return

        raw_docs = self._load_text_files()
        if not raw_docs:
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
        chunks = splitter.split_documents(raw_docs)

        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(CHROMA_DIR)
        )

    def retrieve(self, query: str, k: int = 3) -> List[str]:
        if not self.vector_store:
            self.index_documents()
        if not self.vector_store:
            return []
        results = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]


class TufDietAI:
    """Llama 3 powered AI assistant with real RAG augmentation via Groq"""

    SYSTEM_TEMPLATE = """You are TufDiet AI, a certified AI Dietitian expert specializing in personalized nutrition planning.
Current logged-in user profile metrics:
- Weight: {weight}kg
- Height: {height}cm
- Daily Target Calories: {target_calories}kcal
- Active Fitness Goal: {goal}

You must personalize your response using the user's profile and the retrieved context from our knowledge base below.
If the user's goal is weight loss (LOSE_WEIGHT), strictly prioritize high-protein and low-fat (<15%) recommendations.

CRITICAL INSTRUCTION: You are chatting with a user on a mobile app. Your responses MUST be extremely concise, brief, and easy to read. Do NOT output long paragraphs or walls of text. Use bullet points and keep answers under 3-4 sentences unless specifically asked for a detailed list. Format your response cleanly using basic markdown.

Retrieved Knowledge Base Context:
{context}

User Question: {question}
Compatible Response:
"""

    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        groq_api_key = getattr(settings, "GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
        
        if groq_api_key:
           self.llm = ChatGroq(
              temperature=0.2,
              model_name="llama-3.1-8b-instant",  # Jet hızında çalışan kararlı Groq metin motoru
              groq_api_key=groq_api_key,
              max_tokens=1000,
              timeout=10,
            )
        else:
            self.llm = None
            print("[TufDietAI] CRITICAL: GROQ_API_KEY not found. Please check your settings.")

    def search_usda_fdc(self, query: str) -> str:
        """Searches USDA FoodData Central for the exact nutritional value of a food."""
        api_key = getattr(settings, "USDA_API_KEY", "DEMO_KEY")
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key}&query={query}&pageSize=1"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('foods'):
                    food = data['foods'][0]
                    desc = food.get('description', '')
                    nutrients = food.get('foodNutrients', [])
                    
                    # Extract macros (Nutrient IDs: 1008=Energy, 1003=Protein, 1004=Fat, 1005=Carbs)
                    kcal = next((n['value'] for n in nutrients if n['nutrientId'] == 1008), 'N/A')
                    protein = next((n['value'] for n in nutrients if n['nutrientId'] == 1003), 'N/A')
                    fat = next((n['value'] for n in nutrients if n['nutrientId'] == 1004), 'N/A')
                    carbs = next((n['value'] for n in nutrients if n['nutrientId'] == 1005), 'N/A')
                    
                    return f"Verified USDA Data for '{desc}' (approx. per 100g or serving): {kcal} kcal, Protein: {protein}g, Carbs: {carbs}g, Fat: {fat}g."
        except Exception as e:
            print(f"USDA search failed: {e}")
        return ""

    def search_usda_fdc_raw(self, query: str) -> dict:
        # --- fetching the real numbers rn ---
        # grabbing the exact macros per 100g from usda so our math adds up perfectly
        api_key = getattr(settings, "USDA_API_KEY", "DEMO_KEY")
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key}&query={query}&pageSize=1"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('foods'):
                    food = data['foods'][0]
                    nutrients = food.get('foodNutrients', [])
                    
                    kcal = next((n['value'] for n in nutrients if n['nutrientId'] == 1008), 0.0)
                    protein = next((n['value'] for n in nutrients if n['nutrientId'] == 1003), 0.0)
                    fat = next((n['value'] for n in nutrients if n['nutrientId'] == 1004), 0.0)
                    carbs = next((n['value'] for n in nutrients if n['nutrientId'] == 1005), 0.0)
                    
                    if kcal > 0:
                        return {'kcal': kcal, 'protein': protein, 'carbs': carbs, 'fat': fat}
        except Exception as e:
            print(f"USDA raw search failed: {e}")
        return {}
    def get_advice(self, user_data: Dict) -> str:
        """Generate deterministic advice based on user profile"""
        goal = user_data.get('goal', 'MAINTAIN_FAT_LOSS')
        weight = user_data.get('weight', 70)
        target_cal = user_data.get('target_calories', 2000)

        tips = []
        tips.append(f'Based on your profile, your daily target is {target_cal} kcal.')

        if goal == 'LOSE_WEIGHT':
            tips.append('Prioritize lean proteins and fiber-rich vegetables. Keep fat moderate.')
            tips.append('Aim for at least 30g of fiber daily for satiety and digestion.')
        elif goal == 'GAIN_WEIGHT':
            tips.append('Include calorie-dense foods like nuts, avocados, and whole grains.')
            tips.append('Spread 5-6 smaller meals throughout the day for steady surplus.')
        elif goal == 'MAINTAIN_FAT_LOSS':
            tips.append('High protein (40%) preserves muscle during fat loss.')
            tips.append('Keep fat below 15% of total calories. Focus on unsaturated sources.')

        tips.append(f'At {weight}kg, aim for {round(weight * 1.8)}g of protein daily.')
        tips.append('Consuming most carbohydrates earlier in the day optimizes metabolic health.')
        tips.append('Stay hydrated: at least 2.5L (8 glasses) of water daily.')

        return '\n'.join(tips)

    def analyze_daily_meals(self, user_data: Dict, meals_today: List[Dict]) -> str:
        """Critique today's logged meals against the user's macro budget"""
        if not meals_today:
            return "No food logged today. Snap or add a meal to receive your custom AI macro evaluation!"

        meal_lines = '\n'.join(
            f"- {m.get('food_name', 'Unknown')}: {m.get('calories', 0)}kcal, "
            f"Protein {m.get('protein', 0)}g, Carbs {m.get('carbs', 0)}g, Fat {m.get('fat', 0)}g"
            for m in meals_today
        )

        targets = (f"- Target Calories: {user_data.get('target_calories', 2000)}kcal\n"
                   f"- Target Protein: {user_data.get('target_protein', 0)}g\n"
                   f"- Target Carbs: {user_data.get('target_carbs', 0)}g\n"
                   f"- Target Fat: {user_data.get('target_fat', 0)}g")

        prompt = f"""You are TufDiet AI, an expert diet analyst. Review the user's logged meals today against their macro budget.

User Profile:
- Weight: {user_data.get('weight', 70)}kg
- Goal: {user_data.get('goal', 'MAINTAIN_FAT_LOSS')}

Daily Macro Targets:
{targets}

Today's Logged Meals:
{meal_lines}

Provide a brief 3-4 sentence critique:
1. Are they on track with calories?
2. Are macros balanced for their goal?
3. One actionable tip to improve.

Compatible Response:"""

        if not self.llm:
            total_cal = sum(m.get('calories', 0) for m in meals_today)
            target_cal = user_data.get('target_calories', 2000)
            diff = target_cal - total_cal

            lines = [f"📊 Daily Meal Analysis"]
            if diff > 200:
                lines.append(f"You have {diff:.0f} kcal remaining today. Consider a balanced snack with protein and fiber.")
            elif diff < -200:
                lines.append(f"You are {abs(diff):.0f} kcal over your target. Try a lighter evening meal.")
            else:
                lines.append(f"You are on track! {abs(diff):.0f} kcal from your target.")

            total_protein = sum(m.get('protein', 0) for m in meals_today)
            target_protein = user_data.get('target_protein', 0)
            if total_protein < target_protein * 0.7:
                lines.append(f"Protein intake is low ({total_protein:.0f}g of {target_protein:.0f}g). Add a protein source to your next meal.")

            lines.append("💡 Distribute meals evenly throughout the day for stable energy levels.")
            return '\n'.join(lines)

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error analyzing meals: {str(e)}"

    def chat(self, user_data: Dict, question: str) -> str:
        """Process user query with real RAG integration and USDA search"""
        context_docs = self.knowledge_base.retrieve(question, k=3)
        context = '\n\n'.join(context_docs) if context_docs else 'No specific data found in knowledge base.'
        
        # intercepting calorie queries to fetch usda data
        usda_info = ""
        keywords = ["kalori", "kalori", "kcal", "protein", "besin", "calorie", "makro"]
        if any(kw in question.lower() for kw in keywords):
            usda_info = self.search_usda_fdc(question)
            if usda_info:
                context += f"\n\n[USDA DATABASE EXACT MATCH]: {usda_info}\nUse this exact USDA data instead of guessing if it answers the user's question."

        if not self.llm:
            return "AI Config Error: Groq API key is missing. Please add GROQ_API_KEY to your settings.py"

        prompt = self.SYSTEM_TEMPLATE.format(
            weight=user_data.get('weight', '70'),
            height=user_data.get('height', '170'),
            target_calories=user_data.get('target_calories', '2000'),
            goal=user_data.get('goal', 'MAINTAIN_FAT_LOSS'),
            context=context,
            question=question
        )

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error communicating with Llama 3 Engine: {str(e)}"

    # --- FIXING DIET PLAN GENERATOR ---
    # added this specific method to bypass the chat system prompt
    # we need pure json rn, no conversational text allowed
    def generate_json(self, prompt: str) -> str:
        """Process requests requiring strict JSON output without the chat persona."""
        if not self.llm:
            return "{\"error\": \"Groq API key is missing\"}"
            
        # forcing the model to only output raw JSON
        system_prompt = SystemMessage(
            content="You are a data generator. You MUST return ONLY valid raw JSON and absolutely no other text, markdown blocks, or conversational language."
        )
        user_message = HumanMessage(content=prompt)
        
        try:
            response = self.llm.invoke([system_prompt, user_message])
            return response.content
        except Exception as e:
            return f"{{\"error\": \"LLM JSON gen failed: {str(e)}\"}}"