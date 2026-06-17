import os
import json
import argparse
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms


class CustomFoodDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.classes = self._load_classes()
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.images = self._load_image_paths()

    def _load_classes(self):
        classes = []
        for item in self.data_dir.iterdir():
            if item.is_dir():
                classes.append(item.name)
        return sorted(classes)

    def _load_image_paths(self):
        images = []
        for class_dir in self.data_dir.iterdir():
            if class_dir.is_dir():
                class_name = class_dir.name
                class_idx = self.class_to_idx[class_name]
                for img_file in class_dir.iterdir():
                    if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                        images.append((str(img_file), class_idx))
        print(f"Loaded {len(images)} images for {len(self.classes)} classes: {self.classes}")
        return images

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path, label = self.images[idx]
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label


class Food101Dataset(Dataset):
    def __init__(self, data_dir, split='train', transform=None):
        self.data_dir = data_dir
        self.split = split
        self.transform = transform
        self.classes = self._load_classes()
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.images = self._load_image_paths()

    def _load_classes(self):
        return [
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

    def _load_image_paths(self):
        images = []
        split_file = os.path.join(self.data_dir, 'meta', f'{self.split}.txt')
        if os.path.exists(split_file):
            with open(split_file, 'r') as f:
                for line in f:
                    parts = line.strip().split('/')
                    if len(parts) < 2:
                        continue
                    class_name = parts[0]
                    img_name = parts[1]
                    img_path = os.path.join(self.data_dir, 'images', class_name, f'{img_name}.jpg')
                    if os.path.exists(img_path) and class_name in self.class_to_idx:
                        images.append((img_path, self.class_to_idx[class_name]))
        print(f"Loaded {len(images)} images for {self.split} split")
        return images

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path, label = self.images[idx]
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label


class CombinedDataset(Dataset):
    def __init__(self, food101_dataset, custom_dataset):
        self.food101_dataset = food101_dataset
        self.custom_dataset = custom_dataset
        self.food101_len = len(food101_dataset)
        self.custom_len = len(custom_dataset)

    def __len__(self):
        return self.food101_len + self.custom_len

    def __getitem__(self, idx):
        if idx < self.food101_len:
            return self.food101_dataset[idx]
        else:
            return self.custom_dataset[idx - self.food101_len]


class TransferLearningTrainer:
    def __init__(self, pretrained_model_path, custom_data_dir, output_dir, batch_size=16, num_epochs=10, learning_rate=0.0005, freeze_backbone=True, dropout_rate=0.3):
        self.pretrained_model_path = pretrained_model_path
        self.custom_data_dir = custom_data_dir
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate
        self.freeze_backbone = freeze_backbone
        self.dropout_rate = dropout_rate
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.train_loader = None
        self.val_loader = None
        self.optimizer = None
        self.criterion = None
        self.scheduler = None
        self.classes = None
        self.train_transform = self._get_train_transform()
        self.val_transform = self._get_val_transform()

    def _load_original_classes(self):
        return [
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

    def _get_train_transform(self):
        return transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.RandomRotation(degrees=15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def _get_val_transform(self):
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def prepare_data(self):
        food101_dir = './data/food-101'
        custom_dir = self.custom_data_dir

        food101_train = Food101Dataset(food101_dir, split='train', transform=self.train_transform)
        food101_test = Food101Dataset(food101_dir, split='test', transform=self.val_transform)

        custom_dataset = CustomFoodDataset(custom_dir, transform=self.train_transform)
        custom_val = CustomFoodDataset(custom_dir, transform=self.val_transform)

        self.classes = self._load_original_classes()

        if len(custom_dataset.classes) > 0:
            for cls in custom_dataset.classes:
                if cls not in self.classes:
                    self.classes.append(cls)

        combined_train = self._combine_datasets(food101_train, custom_dataset)
        combined_val = self._combine_datasets(food101_test, custom_val)

        self.train_loader = DataLoader(combined_train, batch_size=self.batch_size, shuffle=True, num_workers=4, pin_memory=True)
        self.val_loader = DataLoader(combined_val, batch_size=self.batch_size, shuffle=False, num_workers=4, pin_memory=True)

        print(f'Training samples: {len(combined_train)}, Validation samples: {len(combined_val)}')
        print(f'Total classes: {len(self.classes)}')

    def _combine_datasets(self, food101_dataset, custom_dataset):
        combined_images = []
        
        for img_path, label in food101_dataset.images:
            combined_images.append((img_path, label, 'food101'))
        
        custom_class_offset = len(self._load_original_classes())
        for img_path, label in custom_dataset.images:
            combined_images.append((img_path, label + custom_class_offset, 'custom'))
        
        class CombinedSubset(Dataset):
            def __init__(self, images, transform, classes):
                self.images = images
                self.transform = transform
                self.classes = classes
            
            def __len__(self):
                return len(self.images)
            
            def __getitem__(self, idx):
                img_path, label, _ = self.images[idx]
                image = Image.open(img_path).convert('RGB')
                if self.transform:
                    image = self.transform(image)
                return image, label
        
        return CombinedSubset(combined_images, food101_dataset.transform if hasattr(food101_dataset, 'transform') else self.val_transform, self.classes)

    def build_model(self):
        base_model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        num_features = base_model.classifier[1].in_features
        
        base_model.classifier = nn.Sequential(
            nn.Dropout(p=self.dropout_rate, inplace=True),
            nn.Linear(num_features, len(self.classes)),
            nn.Dropout(p=0.2),
        )

        if os.path.exists(self.pretrained_model_path):
            print(f'Loading pretrained model from {self.pretrained_model_path}')
            checkpoint = torch.load(self.pretrained_model_path, map_location=self.device)
            
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            else:
                state_dict = checkpoint
            
            new_state_dict = {}
            for key, value in state_dict.items():
                if 'classifier' in key:
                    continue
                new_state_dict[key] = value
            
            base_model.load_state_dict(new_state_dict, strict=False)
            print('Pretrained weights loaded (except classifier layer)')

        if self.freeze_backbone:
            for param in base_model.features.parameters():
                param.requires_grad = False
            print('Backbone frozen - only classifier will be trained')
        else:
            for param in base_model.parameters():
                param.requires_grad = True
            print('Full model will be fine-tuned')

        self.model = base_model.to(self.device)

    def setup_training(self):
        self.criterion = nn.CrossEntropyLoss()
        
        if self.freeze_backbone:
            self.optimizer = optim.AdamW(self.model.classifier.parameters(), lr=self.learning_rate, weight_decay=0.01)
        else:
            self.optimizer = optim.AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=0.01)
        
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=self.num_epochs, eta_min=1e-6)

    def train_epoch(self):
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        progress_bar = tqdm(self.train_loader, desc='Training')

        for images, labels in progress_bar:
            images = images.to(self.device)
            labels = labels.to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{100 * correct / total:.2f}%'
            })

        return running_loss / len(self.train_loader), 100 * correct / total

    def validate(self):
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for images, labels in tqdm(self.val_loader, desc='Validating'):
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, labels)

                running_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        return running_loss / len(self.val_loader), 100 * correct / total

    def save_model(self, epoch, train_loss, train_acc, val_loss, val_acc):
        os.makedirs(self.output_dir, exist_ok=True)
        model_path = os.path.join(self.output_dir, 'food_classifier.pth')
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'train_loss': train_loss,
            'train_acc': train_acc,
            'val_loss': val_loss,
            'val_acc': val_acc,
            'classes': self.classes,
            'dropout_rate': self.dropout_rate,
        }, model_path)

        classes_path = os.path.join(self.output_dir, 'food_classes.txt')
        with open(classes_path, 'w') as f:
            f.write('\n'.join(self.classes))

        print(f'Model saved to {model_path}')

    def train(self):
        print(f'Using device: {self.device}')
        print(f'Training for {self.num_epochs} epochs')
        
        best_val_acc = 0.0

        for epoch in range(1, self.num_epochs + 1):
            print(f'\nEpoch {epoch}/{self.num_epochs}')
            print('-' * 50)

            train_loss, train_acc = self.train_epoch()
            val_loss, val_acc = self.validate()

            self.scheduler.step()

            print(f'Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%')
            print(f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%')
            print(f'Learning Rate: {self.scheduler.get_last_lr()[0]:.6f}')

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                self.save_model(epoch, train_loss, train_acc, val_loss, val_acc)

        print(f'\nTraining completed. Best validation accuracy: {best_val_acc:.2f}%')
        return best_val_acc


def prepare_custom_data(custom_dir, class_name, image_paths):
    class_dir = Path(custom_dir) / class_name
    class_dir.mkdir(parents=True, exist_ok=True)
    
    for i, img_path in enumerate(image_paths):
        dst = class_dir / f'{class_name}_{i:04d}{Path(img_path).suffix}'
        shutil.copy(img_path, dst)
    
    print(f'Added {len(image_paths)} images to {class_dir}')


def main():
    parser = argparse.ArgumentParser(description='Transfer Learning for Custom Food Images')
    parser.add_argument('--pretrained_model', type=str, default='./tufdiet/ai_model/food_classifier.pth', help='Path to pretrained model')
    parser.add_argument('--custom_data_dir', type=str, required=True, help='Directory containing custom food images')
    parser.add_argument('--output_dir', type=str, default='./output', help='Path to save fine-tuned model')
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size for training')
    parser.add_argument('--num_epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--learning_rate', type=float, default=0.0005, help='Learning rate')
    parser.add_argument('--freeze_backbone', type=bool, default=True, help='Freeze backbone during training')
    parser.add_argument('--dropout_rate', type=float, default=0.3, help='Dropout rate')

    args = parser.parse_args()

    trainer = TransferLearningTrainer(
        pretrained_model_path=args.pretrained_model,
        custom_data_dir=args.custom_data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        num_epochs=args.num_epochs,
        learning_rate=args.learning_rate,
        freeze_backbone=args.freeze_backbone,
        dropout_rate=args.dropout_rate
    )

    trainer.prepare_data()
    trainer.build_model()
    trainer.setup_training()
    trainer.train()


if __name__ == '__main__':
    main()
