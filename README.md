# TufDiet: AI-Powered Nutrition and Meal Tracking Application

TufDiet is a full-stack, AI-powered health and nutrition platform. It simplifies dietary tracking by allowing users to instantly analyze the macronutrients of their meals using Generative AI. The project is split into two robust layers: a custom Python/Django REST backend and a cross-platform Flutter mobile application.

## 🚀 Features
- **AI Meal Scanner:** Snap a photo of your food, and the app uses the Gemini Vision model to instantly extract its nutritional value.
- **USDA Mathematical Scaling:** AI guesses are securely scaled against the actual USDA FoodData Central database for 100% scientific accuracy.
- **AI Dietitian Chatbot:** A real-time, context-aware chatbot for nutritional advice.
- **Offline Persistence:** A local SQLite cache allows users to view their dashboard and meal history entirely offline.
- **Dynamic Diet Plans:** Personalized, full-day menus automatically generated based on the user's Total Daily Energy Expenditure (TDEE).

---

## 🏗️ Project Architecture

This repository contains two main directories:
1. `TufDiet-main/` (Backend - Python/Django)
2. `TufDietMobileApp/` (Frontend - Flutter/Dart)

### 1. Backend (Django REST Framework)
The backend serves as the bridge between the mobile app, the Gemini AI Model, and the USDA Database.

**Tech Stack:** Python, Django, Django REST Framework, SQLite3 (Cloud).

**How it works:**
- It securely stores user credentials and API tokens.
- When an image is received from the mobile app, it is sent to the Gemini API to identify the food.
- The identified food name is passed to the USDA API to retrieve raw baseline macronutrients.
- The backend runs a custom "Math Magic" algorithm to scale the AI's portion estimates perfectly against the USDA baseline, returning an exact JSON response to the mobile app.

### 2. Frontend (Flutter Mobile App)
The mobile application is designed with a strict Layered Architecture (Presentation -> Provider/Business Logic -> Repository -> DAO/SQLite).

**Tech Stack:** Flutter, Dart, Provider (State Management), sqflite, http.

**How it works:**
- **Presentation Layer:** Flutter widgets render a responsive, dark-themed UI.
- **Provider Layer:** Reactive state management orchestrates API requests and UI rebuilds.
- **Repository Layer:** Acts as a single source of truth, smartly caching data locally while syncing with the Django backend.
- **Data/SQLite Layer:** Stores user profiles and meal logs offline for immediate access (`meals` and `profile_cache` tables).

---

## 🛠️ How to Run Locally

### Running the Django Backend
1. Navigate to the backend directory: `cd TufDiet-main`
2. Create and activate a virtual environment: `python -m venv venv` and `.\venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt` (if available, otherwise install django, djangorestframework, google-generativeai, requests)
4. Create a `.env` file in the root of the backend folder and add your API Keys:
   ```env
   GROQ_API_KEY=your_groq_key
   GEMINI_API_KEY=your_gemini_key
   USDA_API_KEY=your_usda_key
   ```
5. Apply migrations: `python manage.py migrate`
6. Run the server: `python manage.py runserver` (Runs on `localhost:8000`)

### Running the Flutter Mobile App
1. Ensure the Django backend is running locally.
2. Navigate to the mobile app directory: `cd TufDietMobileApp`
3. Get Flutter dependencies: `flutter pub get`
4. Connect an Android/iOS emulator or a physical device.
5. Run the app: `flutter run`

*(Note: The app is configured to connect to the backend via local IP mappings. If testing on a physical device, ensure your device and PC are on the same Wi-Fi network and update the base API URL in `api_constants.dart` if necessary).*

---

## 📚 Academic Integrity
Prepared by Tunahan Ekelik. All external resources, APIs (USDA, Gemini), and open-source libraries are properly acknowledged.
