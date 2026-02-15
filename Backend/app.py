from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
import joblib
import numpy as np
import pytesseract
import os
from PIL import Image
import easyocr
from pdf2image import convert_from_path
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
app.secret_key = "mediscan_ai_secret_key"
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=False
)
CORS(app, supports_credentials=True,origins=["http://127.0.0.1:5500"])

from auth import auth_blueprint
app.register_blueprint(auth_blueprint)

reader = easyocr.Reader(['en'])

# Load Diabetes ML model
diabetes_model = joblib.load("diabetes_model.pkl")

@app.route("/")
def home():
    return "MediScan AI Multi-Disease Clinical System Running"



# =========================
# MAIN ROUTER
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    disease = data.get("disease")
    features = data.get("features")

    if disease == "diabetes":
        return predict_diabetes(features)
    elif disease == "thyroid":
        return predict_thyroid(features)
    elif disease == "kft":
        return predict_kft(features)
    elif disease == "lft":
        return predict_lft(features)
    elif disease == "cbc":
        return predict_cbc(features)
    else:
        return jsonify({"error": "Disease module not implemented yet"})

# =========================
# DIABETES (ML)
# =========================
def predict_diabetes(features):
    X = np.array(features).reshape(1, -1)
    prob = diabetes_model.predict_proba(X)[0][1]
    prediction = int(prob >= 0.5)

    if prob < 0.3:
        severity = "Low Risk"
        advice = [
            "💚 Your sugar levels look well controlled. Keep up the good habits, stay active, drink enough water, and enjoy a balanced diet.",
            "🌱 A little daily walk and home-cooked food will help you stay healthy for years to come."
        ]
    elif prob < 0.6:
        severity = "Pre-Diabetic"
        advice = [
            "⚠️ Your body is giving an early warning. Don’t worry, this stage is reversible with care.",
            "🥗 Reduce sugary foods, exercise regularly, and get your sugar checked again in a few months."
        ]
    elif prob < 0.8:
        severity = "High Risk"
        advice = [
            "🚨 Your sugar control needs attention. You may feel tired or thirsty often.",
            "👨‍⚕️ Please consult a doctor soon and follow a strict diet and activity plan."
        ]
    else:
        severity = "Critical Risk"
        advice = [
            "🆘 Your report shows very high risk of diabetes complications.",
            "🏥 Immediate medical consultation is important. With proper care, your health can still improve."
        ]

    return jsonify({
        "disease": "Diabetes",
        "prediction": prediction,
        "probability": round(prob * 100, 2),
        "severity": severity,
        "advice": advice
    })

# =========================
# THYROID (CLINICAL AI)
# =========================
def predict_thyroid(features):
    TSH, T3, T4, age = features

    if TSH is None:
        return jsonify({"error": "TSH value required for thyroid analysis"})

    if 0.5 <= TSH <= 4.5:
        severity = "Normal Thyroid"
        probability = 3
        advice = [
            "💚 Your thyroid levels are in a healthy range. Keep taking care of yourself and go for yearly checkups.",
            "🌞 A balanced diet and stress-free lifestyle will help maintain this stability."
        ]
    elif 0.1 <= TSH < 0.5:
        severity = "Subclinical Hyperthyroidism"
        probability = 30
        advice = [
            "⚠️ Your thyroid seems slightly overactive. You might feel anxious or have palpitations.",
            "👩‍⚕️ A doctor visit and repeat test will help prevent future problems."
        ]
    elif TSH < 0.1:
        severity = "Hyperthyroidism"
        probability = 85
        advice = [
            "🚨 Your thyroid is clearly overactive. This can affect your heart and weight.",
            "🏥 Please consult an endocrinologist and start treatment as advised."
        ]
    elif 4.5 < TSH <= 10:
        severity = "Subclinical Hypothyroidism"
        probability = 40
        advice = [
            "⚠️ Your thyroid is a little slow. You may feel tired or gain weight easily.",
            "🥗 Proper nutrition and follow-up tests will help manage this early stage."
        ]
    else:
        severity = "Hypothyroidism"
        probability = 85
        advice = [
            "🚨 Your thyroid is underactive and needs medical support.",
            "💊 With proper medication and care, you can feel energetic again."
        ]

    return jsonify({
        "disease": "Thyroid",
        "prediction": 1 if probability > 50 else 0,
        "probability": probability,
        "severity": severity,
        "advice": advice
    })

# =========================
# KFT (KIDNEY AI)
# =========================
def predict_kft(features):
    creatinine, urea, egfr, age = features

    if egfr is None:
        return jsonify({"error": "eGFR value required for kidney analysis"})

    if egfr >= 90:
        stage = "Normal"
        prob = 5
        sev = "Low Risk"
        advice = [
            "💚 Your kidneys are working well. Keep drinking enough water and maintain a healthy lifestyle.",
            "🌱 Regular checkups will help keep them strong for life."
        ]
    elif 60 <= egfr < 90:
        stage = "CKD Stage 2"
        prob = 30
        sev = "Mild Risk"
        advice = [
            "⚠️ Your kidney function is slightly reduced. This is an early warning stage.",
            "💧 Stay hydrated and consult a doctor for preventive care."
        ]
    elif 30 <= egfr < 60:
        stage = "CKD Stage 3"
        prob = 60
        sev = "Moderate Risk"
        advice = [
            "🚨 Your kidneys need close attention now.",
            "👨‍⚕️ A nephrologist consultation and diet control can slow further damage."
        ]
    elif 15 <= egfr < 30:
        stage = "CKD Stage 4"
        prob = 85
        sev = "High Risk"
        advice = [
            "🆘 Your kidney function is severely reduced.",
            "🏥 Please seek specialist care immediately to protect your health."
        ]
    else:
        stage = "CKD Stage 5"
        prob = 95
        sev = "Critical Risk"
        advice = [
            "🆘 Your kidneys are in critical condition and need urgent medical support.",
            "❤️ With proper treatment, you can still improve your quality of life."
        ]

    return jsonify({
        "disease": "Kidney Function (KFT)",
        "prediction": 1 if prob > 50 else 0,
        "probability": prob,
        "severity": f"{sev} – {stage}",
        "advice": advice
    })

# =========================
# LFT (LIVER AI)
# =========================
def predict_lft(features):
    alt, ast, bilirubin, albumin = features

    if alt is None and ast is None and bilirubin is None and albumin is None:
        return jsonify({"error": "At least one LFT parameter required"})

    if (alt is not None and alt > 80) or (ast is not None and ast > 80):
        severity = "Liver Injury"
        probability = 85
        advice = [
            "🚨 Your liver enzymes are high, which may mean liver stress or infection.",
            "🍎 Avoid alcohol completely and consult a doctor for proper care."
        ]
    elif bilirubin is not None and bilirubin > 2:
        severity = "Jaundice Risk"
        probability = 75
        advice = [
            "⚠️ Your bilirubin is high, which can cause yellowing of eyes and skin.",
            "💧 Rest well, drink fluids, and seek medical advice."
        ]
    elif albumin is not None and albumin < 3.5:
        severity = "Chronic Liver Risk"
        probability = 70
        advice = [
            "⚠️ Your body protein level is low, suggesting possible long-term liver issues.",
            "🥗 Improve nutrition and consult a specialist."
        ]
    else:
        severity = "Normal Liver Function"
        probability = 5
        advice = [
            "💚 Your liver is healthy. Keep eating balanced food and avoid excess alcohol.",
            "🌿 A healthy lifestyle will keep your liver strong."
        ]

    return jsonify({
        "disease": "Liver Function (LFT)",
        "prediction": 1 if probability > 50 else 0,
        "probability": probability,
        "severity": severity,
        "advice": advice
    })

# =========================
# CBC (BLOOD AI)
# =========================
def predict_cbc(features):
    hb, wbc, platelets = features

    if hb is None and wbc is None and platelets is None:
        return jsonify({"error": "At least one CBC parameter required"})

    probability = 5
    severity = "Normal Blood Profile"
    advice = [
        "💚 Your blood report looks healthy. Keep eating well and stay active.",
        "🌞 A yearly CBC check is enough to stay on track."
    ]

    if hb is not None and hb < 10:
        severity = "Anemia"
        probability = 80
        advice = [
            "🚨 Your hemoglobin is low, which may cause weakness and dizziness.",
            "🥗 Add iron-rich foods like spinach, dates, pomegranate, and consult a doctor."
        ]

    if wbc is not None and wbc > 11000:
        severity = "Infection / Inflammation"
        probability = max(probability, 75)
        advice = [
            "⚠️ Your body may be fighting an infection.",
            "💊 Rest well, drink fluids, and seek medical advice if fever persists."
        ]

    if platelets is not None and platelets < 100000:
        severity = "Bleeding Risk"
        probability = max(probability, 85)
        advice = [
            "🆘 Your platelet count is low, which may increase bleeding risk.",
            "🏥 Avoid injuries and consult a doctor immediately for proper care."
        ]

    return jsonify({
        "disease": "Complete Blood Count (CBC)",
        "prediction": 1 if probability > 50 else 0,
        "probability": probability,
        "severity": severity,
        "advice": advice
    })

@app.route("/upload_report", methods=["POST"])
def upload_report():
    

    file = request.files['file']
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)

    text = ""

    if file.filename.lower().endswith(".pdf"):
        images = convert_from_path(file_path, dpi=300)
        for img in images:
            text += pytesseract.image_to_string(img)
    else:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)

    # fallback with EasyOCR if Tesseract gives very low text
    if len(text.strip()) < 20:
        result = reader.readtext(file_path, detail=0)
        text = " ".join(result)

    text_lower = text.lower()

    patterns = {
        "hb": r"(haemoglobin|hemoglobin|hb)[^\d]*([\d]+\.?[\d]*)",
        "wbc": r"(total\s*leukocyte\s*count|tlc|wbc)[^\d]*([\d]+\.?[\d]*)",
        "platelets": r"(platelet|plt)[^\d]*([\d]+\.?[\d]*)",
        "creatinine": r"(creatinine)[^\d]*([\d]+\.?[\d]*)",
        "urea": r"(urea)[^\d]*([\d]+\.?[\d]*)",
        "egfr": r"(egfr)[^\d]*([\d]+\.?[\d]*)",
        "alt": r"(alt|sgpt)[^\d]*([\d]+\.?[\d]*)",
        "ast": r"(ast|sgot)[^\d]*([\d]+\.?[\d]*)",
        "bilirubin": r"(bilirubin)[^\d]*([\d]+\.?[\d]*)",
        "albumin": r"(albumin)[^\d]*([\d]+\.?[\d]*)",
        "glucose": r"(glucose)[^\d]*([\d]+\.?[\d]*)",
        "tsh": r"(tsh)[^\d]*([\d]+\.?[\d]*)",
        "t3": r"(t3)[^\d]*([\d]+\.?[\d]*)",
        "t4": r"(t4)[^\d]*([\d]+\.?[\d]*)"
    }

    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            extracted[key] = float(match.group(2))

    detected_tests = []
    if "creatinine" in extracted or "egfr" in extracted:
        detected_tests.append("kft")
    if "alt" in extracted or "ast" in extracted or "bilirubin" in extracted:
        detected_tests.append("lft")
    if "hb" in extracted or "wbc" in extracted or "platelets" in extracted:
        detected_tests.append("cbc")
    if "tsh" in extracted:
        detected_tests.append("thyroid")
    if "glucose" in extracted:
        detected_tests.append("diabetes")

    return jsonify({
        "raw_text": text,
        "extracted_values": extracted,
        "detected_modules": detected_tests
    })

if __name__ == "__main__":
    app.run(debug=True)
