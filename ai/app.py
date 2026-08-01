from flask import Flask, request, jsonify
from predictor import predict_accident

app = Flask(__name__)
@app.route("/")
def home():
    return "RoadShield AI Backend is Running!"
@app.route("/predict", methods=["POST"])
def predict():

    data = request.json

    weather = data["weather"]
    traffic = data["traffic"]
    road = data["road"]
    speed = data["speed"]
    time = data["time"]

    result = predict_accident(
        weather,
        traffic,
        road,
        speed,
        time
    )

    return jsonify({
        "prediction": result
    })
    
if __name__ == "__main__":
    app.run(debug=True)
