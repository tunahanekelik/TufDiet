import os
import io
import json
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms


class CombinedFoodNutritionDatabase:
    def __init__(self):
        self.nutrition_data = self._load_combined_nutrition()

    def _load_combined_nutrition(self):
        # First our custom classes (5 classes)
        custom_data = {
            'baklava': {'calories': 335, 'protein': 5.0, 'carbs': 38.0, 'fat': 19.0},
            'corba': {'calories': 150, 'protein': 8.0, 'carbs': 20.0, 'fat': 5.0},
            'elma': {'calories': 52, 'protein': 0.3, 'carbs': 14.0, 'fat': 0.2},
            'salata': {'calories': 35, 'protein': 1.5, 'carbs': 7.0, 'fat': 0.3},
            'tavuk': {'calories': 165, 'protein': 31.0, 'carbs': 0.0, 'fat': 3.6},
        }

        # Kaggle Food Nutrition Dataset (2395 yemek)
        kaggle_data = {
            'apple': {'calories': 52, 'protein': 0.3, 'carbs': 14.0, 'fat': 0.2},
            'apple_pie': {'calories': 237, 'protein': 2.0, 'carbs': 27.0, 'fat': 13.0},
            'baby_back_ribs': {'calories': 277, 'protein': 20.0, 'carbs': 8.0, 'fat': 19.0},
            'baklava': {'calories': 335, 'protein': 5.0, 'carbs': 38.0, 'fat': 19.0},
            'beef_carpaccio': {'calories': 145, 'protein': 18.0, 'carbs': 1.0, 'fat': 8.0},
            'beef_tartare': {'calories': 180, 'protein': 22.0, 'carbs': 2.0, 'fat': 9.0},
            'beet_salad': {'calories': 89, 'protein': 3.0, 'carbs': 15.0, 'fat': 2.0},
            'beignets': {'calories': 262, 'protein': 5.0, 'carbs': 32.0, 'fat': 12.0},
            'bibimbap': {'calories': 410, 'protein': 18.0, 'carbs': 55.0, 'fat': 14.0},
            'bread_pudding': {'calories': 232, 'protein': 6.0, 'carbs': 33.0, 'fat': 8.0},
            'breakfast_burrito': {'calories': 390, 'protein': 16.0, 'carbs': 30.0, 'fat': 22.0},
            'bruschetta': {'calories': 135, 'protein': 4.0, 'carbs': 18.0, 'fat': 5.0},
            'caesar_salad': {'calories': 190, 'protein': 6.0, 'carbs': 10.0, 'fat': 14.0},
            'cannoli': {'calories': 250, 'protein': 5.0, 'carbs': 26.0, 'fat': 14.0},
            'caprese_salad': {'calories': 180, 'protein': 10.0, 'carbs': 6.0, 'fat': 14.0},
            'carrot_cake': {'calories': 320, 'protein': 4.0, 'carbs': 42.0, 'fat': 16.0},
            'ceviche': {'calories': 120, 'protein': 18.0, 'carbs': 5.0, 'fat': 3.0},
            'cheese': {'calories': 113, 'protein': 6.4, 'carbs': 0.9, 'fat': 9.3},
            'cheesecake': {'calories': 321, 'protein': 5.0, 'carbs': 30.0, 'fat': 20.0},
            'chicken_curry': {'calories': 245, 'protein': 22.0, 'carbs': 10.0, 'fat': 13.0},
            'chicken_quesadilla': {'calories': 290, 'protein': 18.0, 'carbs': 22.0, 'fat': 14.0},
            'chicken_wings': {'calories': 290, 'protein': 20.0, 'carbs': 2.0, 'fat': 22.0},
            'chocolate': {'calories': 546, 'protein': 4.9, 'carbs': 60.0, 'fat': 31.0},
            'chocolate_cake': {'calories': 352, 'protein': 4.0, 'carbs': 45.0, 'fat': 18.0},
            'chocolate_mousse': {'calories': 220, 'protein': 4.0, 'carbs': 24.0, 'fat': 12.0},
            'churros': {'calories': 280, 'protein': 4.0, 'carbs': 35.0, 'fat': 14.0},
            'clam_chowder': {'calories': 200, 'protein': 8.0, 'carbs': 20.0, 'fat': 10.0},
            'club_sandwich': {'calories': 350, 'protein': 18.0, 'carbs': 30.0, 'fat': 18.0},
            'crab_cakes': {'calories': 190, 'protein': 16.0, 'carbs': 10.0, 'fat': 10.0},
            'creme_brulee': {'calories': 280, 'protein': 4.0, 'carbs': 28.0, 'fat': 16.0},
            'croissant': {'calories': 230, 'protein': 5.0, 'carbs': 26.0, 'fat': 12.0},
            'cup_cakes': {'calories': 290, 'protein': 3.0, 'carbs': 40.0, 'fat': 14.0},
            'deviled_eggs': {'calories': 140, 'protein': 8.0, 'carbs': 2.0, 'fat': 11.0},
            'donuts': {'calories': 289, 'protein': 4.0, 'carbs': 36.0, 'fat': 14.0},
            'dumplings': {'calories': 180, 'protein': 6.0, 'carbs': 24.0, 'fat': 6.0},
            'edamame': {'calories': 120, 'protein': 11.0, 'carbs': 14.0, 'fat': 5.0},
            'eggs_benedict': {'calories': 360, 'protein': 15.0, 'carbs': 20.0, 'fat': 26.0},
            'escargots': {'calories': 120, 'protein': 14.0, 'carbs': 3.0, 'fat': 6.0},
            'falafel': {'calories': 220, 'protein': 8.0, 'carbs': 25.0, 'fat': 11.0},
            'filet_mignon': {'calories': 270, 'protein': 28.0, 'carbs': 0.0, 'fat': 17.0},
            'fish_and_chips': {'calories': 380, 'protein': 18.0, 'carbs': 35.0, 'fat': 18.0},
            'foie_gras': {'calories': 320, 'protein': 10.0, 'carbs': 4.0, 'fat': 28.0},
            'french_fries': {'calories': 365, 'protein': 4.0, 'carbs': 48.0, 'fat': 17.0},
            'french_onion_soup': {'calories': 150, 'protein': 4.0, 'carbs': 15.0, 'fat': 8.0},
            'french_toast': {'calories': 290, 'protein': 8.0, 'carbs': 36.0, 'fat': 12.0},
            'fried_calamari': {'calories': 220, 'protein': 14.0, 'carbs': 16.0, 'fat': 12.0},
            'fried_rice': {'calories': 320, 'protein': 8.0, 'carbs': 45.0, 'fat': 12.0},
            'frozen_yogurt': {'calories': 130, 'protein': 3.0, 'carbs': 24.0, 'fat': 3.0},
            'garlic_bread': {'calories': 180, 'protein': 4.0, 'carbs': 22.0, 'fat': 8.0},
            'gnocchi': {'calories': 250, 'protein': 6.0, 'carbs': 40.0, 'fat': 6.0},
            'greek_salad': {'calories': 150, 'protein': 5.0, 'carbs': 10.0, 'fat': 10.0},
            'grilled_cheese_sandwich': {'calories': 290, 'protein': 10.0, 'carbs': 26.0, 'fat': 16.0},
            'grilled_salmon': {'calories': 210, 'protein': 30.0, 'carbs': 0.0, 'fat': 10.0},
            'guacamole': {'calories': 160, 'protein': 2.0, 'carbs': 10.0, 'fat': 14.0},
            'gyoza': {'calories': 200, 'protein': 8.0, 'carbs': 22.0, 'fat': 9.0},
            'hamburger': {'calories': 450, 'protein': 25.0, 'carbs': 30.0, 'fat': 24.0},
            'hot_and_sour_soup': {'calories': 80, 'protein': 5.0, 'carbs': 8.0, 'fat': 3.0},
            'hot_dog': {'calories': 290, 'protein': 10.0, 'carbs': 22.0, 'fat': 18.0},
            'huevos_rancheros': {'calories': 270, 'protein': 12.0, 'carbs': 20.0, 'fat': 16.0},
            'hummus': {'calories': 166, 'protein': 8.0, 'carbs': 14.0, 'fat': 10.0},
            'ice_cream': {'calories': 207, 'protein': 3.5, 'carbs': 24.0, 'fat': 11.0},
            'lasagna': {'calories': 350, 'protein': 18.0, 'carbs': 30.0, 'fat': 16.0},
            'lobster_bisque': {'calories': 180, 'protein': 8.0, 'carbs': 12.0, 'fat': 11.0},
            'lobster_roll_sandwich': {'calories': 320, 'protein': 20.0, 'carbs': 24.0, 'fat': 16.0},
            'macaroni_and_cheese': {'calories': 380, 'protein': 12.0, 'carbs': 40.0, 'fat': 18.0},
            'macarons': {'calories': 180, 'protein': 3.0, 'carbs': 26.0, 'fat': 7.0},
            'meat': {'calories': 250, 'protein': 26.0, 'carbs': 0.0, 'fat': 15.0},
            'miso_soup': {'calories': 60, 'protein': 4.0, 'carbs': 8.0, 'fat': 2.0},
            'mozzarella': {'calories': 90, 'protein': 6.7, 'carbs': 0.7, 'fat': 6.6},
            'mussels': {'calories': 120, 'protein': 16.0, 'carbs': 4.0, 'fat': 3.0},
            'nachos': {'calories': 350, 'protein': 9.0, 'carbs': 36.0, 'fat': 19.0},
            'omelette': {'calories': 220, 'protein': 14.0, 'carbs': 2.0, 'fat': 17.0},
            'onion_rings': {'calories': 260, 'protein': 4.0, 'carbs': 30.0, 'fat': 14.0},
            'oysters': {'calories': 80, 'protein': 9.0, 'carbs': 4.0, 'fat': 2.0},
            'pad_thai': {'calories': 380, 'protein': 14.0, 'carbs': 48.0, 'fat': 14.0},
            'paella': {'calories': 320, 'protein': 18.0, 'carbs': 40.0, 'fat': 10.0},
            'pancakes': {'calories': 280, 'protein': 6.0, 'carbs': 38.0, 'fat': 11.0},
            'panna_cotta': {'calories': 220, 'protein': 3.0, 'carbs': 24.0, 'fat': 12.0},
            'parmesan': {'calories': 71, 'protein': 6.4, 'carbs': 0.6, 'fat': 4.5},
            'peking_duck': {'calories': 340, 'protein': 24.0, 'carbs': 18.0, 'fat': 20.0},
            'pho': {'calories': 350, 'protein': 20.0, 'carbs': 40.0, 'fat': 12.0},
            'pizza': {'calories': 285, 'protein': 12.0, 'carbs': 36.0, 'fat': 10.0},
            'pork_chop': {'calories': 280, 'protein': 26.0, 'carbs': 0.0, 'fat': 18.0},
            'poutine': {'calories': 420, 'protein': 10.0, 'carbs': 45.0, 'fat': 22.0},
            'prime_rib': {'calories': 320, 'protein': 28.0, 'carbs': 0.0, 'fat': 22.0},
            'pulled_pork_sandwich': {'calories': 380, 'protein': 22.0, 'carbs': 30.0, 'fat': 18.0},
            'ramen': {'calories': 380, 'protein': 16.0, 'carbs': 48.0, 'fat': 14.0},
            'ravioli': {'calories': 290, 'protein': 12.0, 'carbs': 36.0, 'fat': 10.0},
            'red_velvet_cake': {'calories': 340, 'protein': 4.0, 'carbs': 44.0, 'fat': 17.0},
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28.0, 'fat': 0.3},
            'risotto': {'calories': 300, 'protein': 8.0, 'carbs': 40.0, 'fat': 12.0},
            'samosa': {'calories': 260, 'protein': 6.0, 'carbs': 28.0, 'fat': 14.0},
            'sashimi': {'calories': 140, 'protein': 28.0, 'carbs': 0.0, 'fat': 2.0},
            'scallops': {'calories': 120, 'protein': 22.0, 'carbs': 3.0, 'fat': 2.0},
            'seaweed_salad': {'calories': 80, 'protein': 3.0, 'carbs': 14.0, 'fat': 2.0},
            'shrimp': {'calories': 99, 'protein': 24.0, 'carbs': 0.2, 'fat': 0.3},
            'spaghetti_bolognese': {'calories': 380, 'protein': 18.0, 'carbs': 48.0, 'fat': 14.0},
            'spaghetti_carbonara': {'calories': 400, 'protein': 14.0, 'carbs': 40.0, 'fat': 20.0},
            'spring_rolls': {'calories': 180, 'protein': 5.0, 'carbs': 22.0, 'fat': 8.0},
            'steak': {'calories': 290, 'protein': 30.0, 'carbs': 0.0, 'fat': 18.0},
            'strawberry_shortcake': {'calories': 280, 'protein': 4.0, 'carbs': 38.0, 'fat': 12.0},
            'sushi': {'calories': 200, 'protein': 12.0, 'carbs': 28.0, 'fat': 4.0},
            'tacos': {'calories': 320, 'protein': 16.0, 'carbs': 24.0, 'fat': 18.0},
            'takoyaki': {'calories': 240, 'protein': 10.0, 'carbs': 28.0, 'fat': 10.0},
            'tiramisu': {'calories': 280, 'protein': 5.0, 'carbs': 30.0, 'fat': 15.0},
            'tuna_tartare': {'calories': 150, 'protein': 20.0, 'carbs': 3.0, 'fat': 7.0},
            'waffles': {'calories': 310, 'protein': 7.0, 'carbs': 38.0, 'fat': 14.0},
            'yogurt': {'calories': 61, 'protein': 3.5, 'carbs': 4.7, 'fat': 3.3},
            'salad': {'calories': 35, 'protein': 1.5, 'carbs': 7.0, 'fat': 0.3},
            'soup': {'calories': 150, 'protein': 8.0, 'carbs': 20.0, 'fat': 5.0},
            'chicken': {'calories': 165, 'protein': 31.0, 'carbs': 0.0, 'fat': 3.6},
            'pasta': {'calories': 131, 'protein': 5.0, 'carbs': 25.0, 'fat': 1.1},
            'bread': {'calories': 265, 'protein': 9.0, 'carbs': 49.0, 'fat': 3.2},
            'egg': {'calories': 155, 'protein': 13.0, 'carbs': 1.1, 'fat': 11.0},
            'fish': {'calories': 136, 'protein': 22.0, 'carbs': 0.0, 'fat': 5.0},
            'beef': {'calories': 250, 'protein': 26.0, 'carbs': 0.0, 'fat': 15.0},
            'pork': {'calories': 242, 'protein': 27.0, 'carbs': 0.0, 'fat': 14.0},
            'lamb': {'calories': 294, 'protein': 25.0, 'carbs': 0.0, 'fat': 21.0},
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28.0, 'fat': 0.3},
            'potato': {'calories': 77, 'protein': 2.0, 'carbs': 17.0, 'fat': 0.1},
            'tomato': {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2},
            'onion': {'calories': 40, 'protein': 1.1, 'carbs': 9.3, 'fat': 0.1},
            'garlic': {'calories': 149, 'protein': 6.4, 'carbs': 33.0, 'fat': 0.5},
            'carrot': {'calories': 41, 'protein': 0.9, 'carbs': 10.0, 'fat': 0.2},
            'broccoli': {'calories': 34, 'protein': 2.8, 'carbs': 7.0, 'fat': 0.4},
            'spinach': {'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4},
            'lettuce': {'calories': 15, 'protein': 1.4, 'carbs': 2.9, 'fat': 0.2},
            'cucumber': {'calories': 16, 'protein': 0.7, 'carbs': 3.6, 'fat': 0.1},
            'pepper': {'calories': 31, 'protein': 1.0, 'carbs': 6.0, 'fat': 0.3},
            'mushroom': {'calories': 22, 'protein': 3.1, 'carbs': 3.3, 'fat': 0.3},
            'corn': {'calories': 86, 'protein': 3.3, 'carbs': 19.0, 'fat': 1.4},
            'pea': {'calories': 81, 'protein': 5.4, 'carbs': 14.5, 'fat': 0.4},
            'bean': {'calories': 127, 'protein': 8.7, 'carbs': 22.8, 'fat': 0.5},
            'lentil': {'calories': 116, 'protein': 9.0, 'carbs': 20.0, 'fat': 0.4},
            'chickpea': {'calories': 164, 'protein': 8.9, 'carbs': 27.0, 'fat': 2.6},
            'tofu': {'calories': 76, 'protein': 8.0, 'carbs': 1.9, 'fat': 4.8},
            'milk': {'calories': 42, 'protein': 3.4, 'carbs': 5.0, 'fat': 1.0},
            'butter': {'calories': 717, 'protein': 0.9, 'carbs': 0.1, 'fat': 81.0},
            'cream': {'calories': 340, 'protein': 2.1, 'carbs': 2.8, 'fat': 36.0},
            'oil': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0},
            'sugar': {'calories': 387, 'protein': 0.0, 'carbs': 100.0, 'fat': 0.0},
            'honey': {'calories': 304, 'protein': 0.3, 'carbs': 82.0, 'fat': 0.0},
            'salt': {'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0},
        }

        # Combine
        combined = {**kaggle_data, **custom_data}
        return combined

    def get_nutrition(self, food_name):
        normalized_name = food_name.lower().replace(' ', '_').replace('-', '_')
        
        # Direct check
        if normalized_name in self.nutrition_data:
            return self.nutrition_data[normalized_name]
        
        # Partial match
        for key in self.nutrition_data:
            if key in normalized_name or normalized_name in key:
                return self.nutrition_data[key]
        
        # Default values
        return {
            'calories': 200,
            'protein': 8.0,
            'carbs': 25.0,
            'fat': 9.0,
        }


class CustomFoodClassifier:
    CONFIDENCE_THRESHOLD = 0.5

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.config = self._load_config()
        self.model = None
        self.transform = self._create_transform()
        self.nutrition_db = CombinedFoodNutritionDatabase()
        self.class_names = self._load_class_names()

    def _load_config(self):
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(base_dir)
        
        # Food-101 model is more comprehensive
        return {
            'model_path': os.path.join(project_root, 'tufdiet', 'ai_model', 'food_classifier.pth'),
            'num_classes': 99,
            'image_size': 224,
            'mean': [0.485, 0.456, 0.406],
            'std': [0.229, 0.224, 0.225],
            'class_names': [
                'apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
                'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito',
                'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
                'ceviche', 'cheesecake', 'chicken_curry', 'chicken_quesadilla', 'chicken_wings',
                'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder', 'club_sandwich',
                'crab_cakes', 'creme_brulee', 'croissant', 'cup_cakes', 'deviled_eggs',
                'donuts', 'dumplings', 'edamame', 'eggs_benedict', 'escargots',
                'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras', 'french_fries',
                'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice', 'frozen_yogurt',
                'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich', 'grilled_salmon',
                'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup', 'hot_dog',
                'huevos_rancheros', 'hummus', 'ice_cream', 'lasagna', 'lobster_bisque',
                'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup', 'mussels',
                'nachos', 'omelette', 'onion_rings', 'oysters', 'pad_thai',
                'paella', 'pancakes', 'panna_cotta', 'peking_duck', 'pho',
                'pizza', 'pork_chop', 'poutine', 'prime_rib', 'pulled_pork_sandwich',
                'ramen', 'ravioli', 'red_velvet_cake', 'risotto', 'samosa',
                'sashimi', 'scallops', 'seaweed_salad', 'spaghetti_bolognese', 'spaghetti_carbonara',
                'spring_rolls', 'steak', 'strawberry_shortcake', 'sushi', 'tacos',
                'takoyaki', 'tiramisu', 'tuna_tartare', 'waffles'
            ]
        }

    def _load_class_names(self):
        return self.config.get('class_names', ['baklava', 'corba', 'elma', 'salata', 'tavuk'])

    def _create_transform(self):
        return transforms.Compose([
            transforms.Resize((self.config['image_size'], self.config['image_size'])),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=self.config['mean'],
                std=self.config['std']
            )
        ])

    def _load_model(self):
        if self.model is not None:
            return self.model

        model_path = self.config.get('model_path')
        
        print(f"[DEBUG] Model path: {model_path}")
        print(f"[DEBUG] Model exists: {os.path.exists(model_path)}")
        
        if not os.path.exists(model_path):
            print(f"[ERROR] Model file not found: {model_path}")
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        try:
            self.model = self._build_model()
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            
            # Check checkpoint contents
            print(f"[DEBUG] Checkpoint keys: {checkpoint.keys()}")
            print(f"[DEBUG] Classes: {checkpoint.get('classes', 'N/A')}")
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            print("[DEBUG] Model loaded successfully!")
            return self.model
        except Exception as e:
            print(f'[ERROR] Failed to load model: {e}')
            import traceback
            traceback.print_exc()
            raise

    def _build_model(self):
        # EfficientNet-B0 - Architecture matching Food-101 model
        base_model = models.efficientnet_b0(weights=None)
        num_features = base_model.classifier[1].in_features
        
        base_model.classifier = nn.Sequential(
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(num_features, self.config['num_classes'])
        )
        return base_model.to(self.device)

    def preprocess_image(self, image_file):
        try:
            # Reset file pointer if already read
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            
            image = Image.open(image_file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return self.transform(image).unsqueeze(0)
        except Exception as e:
            print(f"[ERROR] Image preprocessing failed: {e}")
            raise

    def predict(self, image_file):
        model = self._load_model()

        try:
            image_tensor = self.preprocess_image(image_file)
        except Exception as e:
            return {
                'food_name': 'Unknown',
                'confidence': 0.0,
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'error': str(e)
            }

        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            outputs = model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted_idx = torch.max(probabilities, dim=0)

        confidence_value = confidence.item()
        predicted_class_idx = predicted_idx.item()

        if predicted_class_idx < len(self.class_names):
            food_name = self.class_names[predicted_class_idx]
        else:
            food_name = 'Unknown Food'

        if confidence_value < self.CONFIDENCE_THRESHOLD:
            return {
                'food_name': 'Unknown',
                'confidence': round(confidence_value, 4),
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'message': 'Low confidence! Please upload a clearer photo.',
                'top_predictions': self._get_top_predictions(probabilities)
            }

        nutrition = self.nutrition_db.get_nutrition(food_name)

        return {
            'food_name': food_name.replace('_', ' ').title(),
            'confidence': round(confidence_value, 4),
            'calories': nutrition['calories'],
            'protein': nutrition['protein'],
            'carbs': nutrition['carbs'],
            'fat': nutrition['fat'],
            'top_predictions': self._get_top_predictions(probabilities)
        }

    def _get_top_predictions(self, probabilities, top_k=10):
        top_probs, top_indices = torch.topk(probabilities, min(top_k, len(probabilities)))
        
        predictions = []
        model_classes = self.config.get('class_names', [])
        
        for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
            if idx < len(model_classes):
                food_name = model_classes[idx]
            else:
                food_name = 'Unknown'
            
            nutrition = self.nutrition_db.get_nutrition(food_name)
            predictions.append({
                'food_name': food_name.replace('_', ' ').title(),
                'confidence': round(prob, 4),
                'calories': nutrition['calories'],
                'protein': nutrition['protein'],
                'carbs': nutrition['carbs'],
                'fat': nutrition['fat'],
            })

        return predictions

    def predict(self, image_file):
        model = self._load_model()

        try:
            image_tensor = self.preprocess_image(image_file)
        except Exception as e:
            return {
                'food_name': 'Unknown',
                'confidence': 0.0,
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'error': str(e)
            }

        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            outputs = model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted_idx = torch.max(probabilities, dim=0)

        confidence_value = confidence.item()
        predicted_class_idx = predicted_idx.item()
        
        model_classes = self.config.get('class_names', [])
        
        if predicted_class_idx < len(model_classes):
            food_name = model_classes[predicted_class_idx]
        else:
            food_name = 'Unknown Food'

        top_preds = self._get_top_predictions(probabilities, top_k=10)
        nutrition = self.nutrition_db.get_nutrition(food_name)

        return {
            'food_name': food_name.replace('_', ' ').title(),
            'confidence': round(confidence_value, 4),
            'calories': nutrition['calories'],
            'protein': nutrition['protein'],
            'carbs': nutrition['carbs'],
            'fat': nutrition['fat'],
            'top_predictions': top_preds,
            'is_low_confidence': confidence_value < self.CONFIDENCE_THRESHOLD
        }
