# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Python Dependencies

```bash
# Install ML dependencies
pip install -r ml/requirements.txt

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 2. Train Models (First Time Only)

```bash
cd ml
python train_model.py
```

**Note:** This may take 10-30 minutes depending on your system. For faster testing, edit `train_model.py` and set `sample_frac=0.1` to use 10% of data.

### 3. Start Backend

```bash
cd backend
python main.py
```

Backend runs on `http://localhost:8000`

### 4. Start Frontend (New Terminal)

```bash
cd frontend
npm install  # First time only
npm start
```

Frontend opens at `http://localhost:3000`

### 5. Use the System!

1. Open `http://localhost:3000` in your browser
2. Adjust shot parameters using sliders
3. Click "Predict Shot"
4. See the recommendation (Green = TAKE SHOT, Red = PASS)

## 🧪 Test the API Directly

```bash
curl -X POST "http://localhost:8000/predict-shot" ^
  -H "Content-Type: application/json" ^
  -d "{\"shot_distance\": 24, \"loc_x\": -5.2, \"loc_y\": 7.1, \"shot_type\": \"3PT Field Goal\", \"zone\": \"Above the Break 3\", \"quarter\": 4, \"mins_left\": 0, \"secs_left\": 18, \"position\": \"PG\"}"
```

## ⚠️ Troubleshooting

**"Models not loaded" error:**
- Make sure you ran `python ml/train_model.py` first
- Check that `ml/models/` contains `.pkl` files

**Frontend can't connect to API:**
- Ensure backend is running on port 8000
- Check browser console for CORS errors

**Out of memory during training:**
- Edit `ml/train_model.py` and set `sample_frac=0.1`
- This uses 10% of data for faster training

## 📊 Expected Model Performance

After training, you should see:
- **Logistic Regression**: Accuracy ~60-65%, ROC-AUC ~0.65-0.70
- **Gradient Boosting**: Accuracy ~62-67%, ROC-AUC ~0.67-0.72

These are reasonable for shot prediction (which is inherently difficult).


