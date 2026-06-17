# TufDiet Mobile Port Blueprint & Specification

This blueprint is designed for the Flutter / Mobile Developer Agent to successfully replicate the frontend logic of the TufDiet Django application into a cross-platform mobile client without missing critical backend business logic or AI feedback loops.

---

## 1. ARCHITECTURAL OVERVIEW & LOGIC FLOW

The TufDiet backend utilizes an advanced "Dual-Plan" Active Learning AI Architecture. It is imperative that the mobile client correctly hooks into this workflow to keep the model's feedback loop running smoothly.

### Dual-Plan AI Pipeline
- **Plan A (Local/Edge Prediction):** The backend relies on a custom PyTorch/MobileNetV2 classifier (`CustomFoodClassifier`) that executes fast and cheaply. When a meal image is uploaded, it is evaluated first. If the model's confidence is **$\ge$ 0.75**, the pipeline successfully resolves and immediately returns the result.
- **Plan B (Teacher Model Fallback):** If Plan A yields a confidence of **< 0.75**, the backend automatically routes the image to the **Gemini Vision Multimodal API** (Plan B) to establish an accurate ground truth, tagging the event as `LOW_CONFIDENCE` for future retraining.

### Human-in-the-Loop & Manual Overrides
Users have the ultimate authority to dispute a classification (e.g., via a "Fix with AI" UI button). 
- When the user manually corrects the model, the mobile client must re-submit the image and append the `force_gemini=true` (or `food_name_override` context) parameter. 
- This bypasses Plan A completely and forces Gemini Vision to re-evaluate the meal.
- The system captures this as a `MULTI_OBJECT_MISSED` failure mode, signaling to the data scientists that the local classifier failed to identify the dish correctly.

---

## 2. ACTIVE LEARNING & DATA HARVESTING PIPELINE

Every time Plan B is triggered (either automatically due to low confidence, or manually due to a user override), the data is harvested.

### Data Storage & `metadata.json`
- **Images:** Harvested images are timestamped and isolated into the `media/harvested_dataset/` directory.
- **Metadata Registry:** An atomic `fcntl`-locked JSON file (`metadata.json`) keeps track of all harvested inputs. 
- **Schema Example:**
  ```json
  {
      "harvest_1684365732.jpg": {
          "food_name": "Chicken Salad",
          "calories": 350,
          "protein": 30,
          "carbs": 10,
          "fat": 15,
          "failure_mode": "MULTI_OBJECT_MISSED", // or "LOW_CONFIDENCE"
          "timestamp": "2026-05-18T23:51:12.123456"
      }
  }
  ```

### Automated Fine-Tuning Boundary Loop
- The backend tracks the length of `metadata.json`. 
- Every multiple of **100 entries**, an asynchronous subprocess triggers the training routine (`ai_bot/legacy_train.py`).
- **Lockout Mechanism:** The backend strictly checks for the existence of `media/harvested_dataset/training.lock` before spawning the process to prevent hardware crashing. The mobile client does not need to manage this, but should anticipate potential minor backend latency if hitting the API exactly on a boundary trigger.

---

## 3. REST API CONTRACTS & PAYLOAD SCHEMAS

The Flutter application must communicate with the backend using the following REST APIs.

### A. Authentication & Session Management
The backend utilizes `knox` Token Authentication for API endpoints, while some legacy web-views might expect standard Django Session Cookies.
- **Endpoint:** `POST /api/auth/login/`
- **Headers:** `Content-Type: application/json`
- **Payload:** `{"username": "...", "password": "..."}`
- **Response:** Returns a token (e.g., `{"token": "abcd123...", "user": {...}}`). 
- **Mobile Action:** For subsequent requests, include the Header: `Authorization: Token abcd123...`

### B. AI Meal Analysis Pipeline
- **Endpoint:** `POST /api/ai-analyze/`
- **Headers:** `Authorization: Token <token>`
- **Content-Type:** `multipart/form-data`
- **Payload Details:**
  - `image` (File): The binary image file.
  - `force_gemini` (Boolean String): Send `"true"` if this is a manual user correction (Human-in-the-Loop). Send `"false"` or omit for standard evaluation.
  - `food_name_override` (String): (Optional) Provide explicit context if the user manually types the food name.
- **Expected Success Response:**
  ```json
  {
      "success": true,
      "food_name": "Grilled Salmon",
      "calories": 450,
      "protein": 45,
      "carbs": 0,
      "fat": 20,
      "confidence": 0.88,
      "components": [
          {"name": "Salmon", "amount": "1 filet", "calories": 450, "protein": 45, "carbs": 0, "fat": 20}
      ]
  }
  ```

### C. Chatbot Audit Endpoint
- **Endpoint:** `POST /ai/chat-response/`
- **Headers:** `Authorization: Token <token>`, `Content-Type: application/json`
- **Payload:** `{"message": "How much protein did I eat today?"}`
- **Expected Success Response:**
  ```json
  {
      "status": "success",
      "response": "You have consumed 85g of protein today based on your meal logs."
  }
  ```

### D. Developer Dashboard
- **Endpoint:** `GET /dev-panel/`
- **Note:** This is a server-side rendered Django HTML view secured by `@staff_member_required`. If the mobile app wishes to load this, it must either open a WebView passing the Django session cookie, or a new distinct JSON API wrapper will need to be developed for the `/dev-panel/` metrics.

---

## 4. BUSINESS RULES & CONSTRAINTS

When building the mobile UI and offline caching, adhere to the following logic boundaries:

1. **Default Nutrition Profiles:** If a user does not have a fully populated `TufProfile` in the database, the backend defaults to:
   - Weight: `70 kg`
   - Goal: `MAINTAIN_FAT_LOSS`
   - Target Calories: `2000`
2. **Staff Privileges:** UI elements related to the "Developer Dashboard", "Rapid Dataset Seeding", or raw JSON logs should be hidden in the mobile UI unless the user object returns `is_staff = true`.
3. **Graceful Degradation:** If the `/api/ai-analyze/` endpoint returns a 500 error or `success: false` (e.g., if the Gemini API quota is hit or the image is unreadable), the mobile client MUST gracefully degrade and offer the user a standard manual input form for Calories, Macros, and Name.
