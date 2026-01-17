# 🏀 Shot Selection Advisory System for Developing Point Guards

A complete end-to-end data-driven system that trains ML models on NBA shot data and provides real-time shot selection advice ("TAKE SHOT" or "PASS") for developing point guards.

## 📋 Overview

This system helps point guards learn:
- **When a shot is efficient** - Based on historical NBA data
- **When to move the ball** - When passing is the better option
- **Why a decision is recommended** - Interpretable explanations

## 🏗️ System Architecture

```
Shot Selection Advisory System/
├── ml/                    # Machine Learning components
│   ├── data_loader.py     # Memory-efficient data loading
│   ├── feature_engineering.py  # Feature engineering
│   ├── train_model.py     # Model training script
│   ├── shot_advisory.py   # Advisory logic
│   └── requirements.txt   # Python dependencies
├── backend/               # FastAPI backend
│   ├── main.py           # API server
│   └── requirements.txt  # Backend dependencies
└── frontend/             # React frontend
    ├── src/
    │   ├── App.js        # Main React component
    │   └── App.css       # Styling
    └── package.json      # Frontend dependencies
```

## 📊 Dataset

The system uses NBA shot-level data from CSV files located in:
```
C:\Users\Aayash\Downloads\archive
```

**Data Structure:**
- ~190k rows per season (2004-2024)
- Columns include: `SHOT_MADE`, `SHOT_DISTANCE`, `LOC_X`, `LOC_Y`, `BASIC_ZONE`, `ZONE_NAME`, `SHOT_TYPE`, `QUARTER`, `MINS_LEFT`, `SECS_LEFT`, `POSITION`, etc.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+ and npm
- CSV files in `C:\Users\Aayash\Downloads\archive`

### Step 1: Install Dependencies

**ML Components:**
```bash
cd ml
pip install -r requirements.txt
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### Step 2: Train ML Models

Train the models on NBA shot data:

```bash
cd ml
python train_model.py
```

This will:
- Load all CSV files from the archive directory
- Preprocess and engineer features
- Train a baseline Logistic Regression model
- Train a main Gradient Boosting model
- Save models to `ml/models/`
- Generate feature importance report

**Options:**
- For faster testing, modify `train_model.py` to use `sample_frac=0.1` (10% of data)
- To filter for point guards only, use `filter_position='PG'`

**Expected Output:**
```
Models saved to: ml/models/
- feature_engineer.pkl
- logistic_regression.pkl
- gradient_boosting.pkl
- feature_importance.csv
```

### Step 3: Start Backend API

```bash
cd backend
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

**Endpoints:**
- `GET /` - API information
- `GET /health` - Health check
- `POST /predict-shot` - Shot prediction endpoint

### Step 4: Start Frontend

```bash
cd frontend
npm start
```

The frontend will open at `http://localhost:3000`

## 📖 Usage

### Using the Frontend

1. **Adjust Shot Parameters:**
   - Shot Distance (0-30 ft)
   - Location X/Y (court coordinates)
   - Shot Type (2PT or 3PT)
   - Zone (Restricted Area, Mid-Range, 3PT zones, etc.)
   - Quarter (1-5)
   - Time Remaining (minutes and seconds)
   - Position (PG, SG, SF, PF, C)

2. **Click "Predict Shot"** to get advice

3. **View Results:**
   - **Green = TAKE SHOT** - Shot is recommended
   - **Red = PASS** - Passing is recommended
   - See make probability, threshold, and explanations

### Using the API Directly

**Request:**
```bash
curl -X POST "http://localhost:8000/predict-shot" \
  -H "Content-Type: application/json" \
  -d '{
    "shot_distance": 24,
    "loc_x": -5.2,
    "loc_y": 7.1,
    "shot_type": "3PT Field Goal",
    "zone": "Above the Break 3",
    "quarter": 4,
    "mins_left": 0,
    "secs_left": 18,
    "position": "PG"
  }'
```

**Response:**
```json
{
  "decision": "TAKE SHOT",
  "make_probability": 0.4234,
  "threshold": 0.3500,
  "confidence": 0.0734,
  "explanation": [
    "Shot make probability (42.3%) exceeds threshold (35.0%)",
    "3-point shots are valuable - lower threshold applied",
    "3-point zone - efficient shot if open",
    "Late clock situation - take available shots",
    "Late game - shot selection becomes critical"
  ]
}
```

## 🧠 Model Details

### Baseline Model: Logistic Regression
- Fast and interpretable
- Good baseline for comparison
- Provides probability estimates

### Main Model: Gradient Boosting
- Higher accuracy and ROC-AUC
- Captures non-linear relationships
- Feature importance analysis

### Features Engineered

**Numerical Features:**
- Shot distance
- Court location (LOC_X, LOC_Y)
- Shot angle (from basket)
- Distance from center
- Time remaining (total seconds)
- Quarter, minutes, seconds

**Categorical Features (One-Hot Encoded):**
- Shot type (2PT/3PT)
- Basic zone
- Zone name
- Position
- Position group

## 🎯 Shot Advisory Logic

The advisory system uses **dynamic thresholds** based on:

1. **Shot Type:**
   - 3PT shots: Lower threshold (35%) - more valuable
   - 2PT shots: Higher threshold (50%) - need higher efficiency

2. **Zone:**
   - Restricted Area: 40% threshold
   - Mid-Range: 55% threshold (less efficient)
   - 3PT zones: 35% threshold

3. **Time Context:**
   - Late clock (≤5 seconds): 30% threshold
   - Normal time: Standard thresholds

4. **Game Context:**
   - Overtime: Slightly lower thresholds

## 📈 Model Performance

After training, you'll see:
- **Accuracy**: Percentage of correct predictions
- **ROC-AUC**: Area under ROC curve (higher is better)
- **Feature Importance**: Top features influencing predictions

Example output:
```
Gradient Boosting Results:
  Accuracy: 0.6234
  ROC-AUC: 0.6789
```

## 🔧 Configuration

### Memory Optimization

The system is designed for laptop-level hardware:
- **Column selection**: Only loads needed columns
- **Efficient dtypes**: Uses int16, float32, category types
- **Optional sampling**: Can use `sample_frac` for faster testing

### Customization

**Adjust Thresholds:**
Edit `ml/shot_advisory.py` to modify:
- Base thresholds
- Shot type adjustments
- Zone-specific thresholds
- Time-based adjustments

**Filter Data:**
In `ml/train_model.py`, set:
- `filter_position='PG'` - Train only on point guard data
- `sample_frac=0.1` - Use 10% of data for faster training

## 🐛 Troubleshooting

**Models not loading:**
- Make sure you've run `python ml/train_model.py` first
- Check that `ml/models/` directory exists with model files

**API connection error:**
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`

**Frontend not starting:**
- Run `npm install` in the frontend directory
- Check Node.js version (14+ required)

**Memory issues:**
- Use `sample_frac=0.1` in training for faster/less memory usage
- Process files in batches if needed

## 📝 Code Quality

- **Clean folder structure**: Separated ML, backend, frontend
- **Clear docstrings**: All functions documented
- **Modular design**: Easy to extend and modify
- **Production-ready**: Error handling, validation, logging

## 🎓 How This Helps Developing Point Guards

1. **Data-Driven Learning**: Uses real NBA shot data, not opinions
2. **Context-Aware**: Considers game situation (time, quarter, zone)
3. **Interpretable**: Explains WHY a decision is recommended
4. **Real-Time**: Instant feedback during practice or review
5. **Efficiency Focus**: Teaches shot selection based on expected value

## 📄 License

This project is for educational purposes.

## 🤝 Contributing

Feel free to extend the system:
- Add more features (defender distance, shot clock, etc.)
- Improve model architecture
- Enhance frontend UI
- Add visualization of shot zones

---

**Built with:** Python, scikit-learn, FastAPI, React


