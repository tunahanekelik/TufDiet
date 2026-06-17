import os
import io
import json
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms


class FoodNutritionDatabase:
    def __init__(self):
        self.nutrition_data = self._load_food_nutrition_data()

    def _load_food_nutrition_data(self):
        return {
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
            'cheesecake': {'calories': 321, 'protein': 5.0, 'carbs': 30.0, 'fat': 20.0},
            'chicken_curry': {'calories': 245, 'protein': 22.0, 'carbs': 10.0, 'fat': 13.0},
            'chicken_quesadilla': {'calories': 290, 'protein': 18.0, 'carbs': 22.0, 'fat': 14.0},
            'chicken_wings': {'calories': 290, 'protein': 20.0, 'carbs': 2.0, 'fat': 22.0},
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
            'miso_soup': {'calories': 60, 'protein': 4.0, 'carbs': 8.0, 'fat': 2.0},
            'mussels': {'calories': 120, 'protein': 16.0, 'carbs': 4.0, 'fat': 3.0},
            'nachos': {'calories': 350, 'protein': 9.0, 'carbs': 36.0, 'fat': 19.0},
            'omelette': {'calories': 220, 'protein': 14.0, 'carbs': 2.0, 'fat': 17.0},
            'onion_rings': {'calories': 260, 'protein': 4.0, 'carbs': 30.0, 'fat': 14.0},
            'oysters': {'calories': 80, 'protein': 9.0, 'carbs': 4.0, 'fat': 2.0},
            'pad_thai': {'calories': 380, 'protein': 14.0, 'carbs': 48.0, 'fat': 14.0},
            'paella': {'calories': 320, 'protein': 18.0, 'carbs': 40.0, 'fat': 10.0},
            'pancakes': {'calories': 280, 'protein': 6.0, 'carbs': 38.0, 'fat': 11.0},
            'panna_cotta': {'calories': 220, 'protein': 3.0, 'carbs': 24.0, 'fat': 12.0},
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
            'risotto': {'calories': 300, 'protein': 8.0, 'carbs': 40.0, 'fat': 12.0},
            'samosa': {'calories': 260, 'protein': 6.0, 'carbs': 28.0, 'fat': 14.0},
            'sashimi': {'calories': 140, 'protein': 28.0, 'carbs': 0.0, 'fat': 2.0},
            'scallops': {'calories': 120, 'protein': 22.0, 'carbs': 3.0, 'fat': 2.0},
            'seaweed_salad': {'calories': 80, 'protein': 3.0, 'carbs': 14.0, 'fat': 2.0},
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
        }

    def get_nutrition(self, food_name):
        normalized_name = food_name.lower().replace(' ', '_')
        return self.nutrition_data.get(normalized_name, {
            'calories': 200,
            'protein': 8.0,
            'carbs': 25.0,
            'fat': 9.0,
        })


class FoodClassifier:
    CONFIDENCE_THRESHOLD = 0.5

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        self.config = self._load_config()
        self.model = None
        self.transform = self._create_transform()
        self.nutrition_db = FoodNutritionDatabase()
        self.class_names = self._load_class_names()

    def _load_config(self):
        import os
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_config = {
            'model_path': os.path.join(base_dir, 'ai_model', 'food_classifier.pth'),
            'num_classes': 101,
            'image_size': 224,
            'mean': [0.485, 0.456, 0.406],
            'std': [0.229, 0.224, 0.225],
            'class_names': os.path.join(base_dir, 'ai_model', 'food_classes.txt'),
        }
        
        try:
            from django.conf import settings
            return getattr(settings, 'AI_MODEL_CONFIG', default_config)
        except:
            return default_config

    def _load_class_names(self):
        food_classes_path = self.config.get('class_names')
        if food_classes_path and os.path.exists(food_classes_path):
            with open(food_classes_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
        return list(self.nutrition_db.nutrition_data.keys())[:self.config['num_classes']]

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

        if os.path.exists(model_path):
            try:
                self.model = self._build_model()
                checkpoint = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.model.eval()
                return self.model
            except Exception as e:
                print(f'Failed to load model from {model_path}: {e}')

        self.model = self._build_model()
        self.model.eval()
        return self.model

    def _build_model(self):
        base_model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        num_features = base_model.classifier[1].in_features
        
        base_model.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(num_features, self.config['num_classes']),
            nn.Dropout(p=0.2),
        )
        return base_model.to(self.device)

    def preprocess_image(self, image_file):
        image = Image.open(io.BytesIO(image_file.read()))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return self.transform(image).unsqueeze(0)

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

        if confidence_value < self.CONFIDENCE_THRESHOLD:
            return {
                'food_name': 'Unknown',
                'confidence': round(confidence_value, 4),
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'message': f'Confidence score is too low. Please upload a clearer photo.',
                'top_predictions': self._get_top_predictions(probabilities)
            }

        if predicted_idx.item() < len(self.class_names):
            food_name = self.class_names[predicted_idx.item()]
        else:
            food_name = 'Unknown Food'

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

    def _get_top_predictions(self, probabilities, top_k=5):
        top_probs, top_indices = torch.topk(probabilities, min(top_k, len(probabilities)))

        predictions = []
        for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
            food_name = self.class_names[idx] if idx < len(self.class_names) else 'Unknown'
            food_name_normalized = food_name.replace(' ', '_').lower()
            nutrition = self.nutrition_db.get_nutrition(food_name_normalized)
            predictions.append({
                'food_name': food_name.replace('_', ' ').title(),
                'confidence': round(prob, 4),
                'calories': nutrition['calories'],
                'protein': nutrition['protein'],
                'carbs': nutrition['carbs'],
                'fat': nutrition['fat'],
            })

        return predictions
