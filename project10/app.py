import nltk
nltk.download('vader_lexicon')
nltk.download('punkt')
from flask import Flask, render_template, request, jsonify
from nltk.chat.util import Chat
from nltk.sentiment import SentimentIntensityAnalyzer
import re
app = Flask(__name__)
pair = [
    [r"(?i)hello|hi|hey", [
        "hello! welcome to our hotel chatbot ",
        "hi there! how can i help you with your stay today?",
        "hey! looking for room options or booking info?"
    ]],
    [r"(?i).*(room types|available rooms|rooms).*", [
        "we have three types of rooms: standard, deluxe, and suite.",
        "our rooms include standard and deluxe options, plus suites for a luxurious stay.",
        "you can choose from standard, deluxe, or our suite rooms for extra comfort."
    ]],
    [r"(?i).*(price|cost|rate|tariff).*", [
        "standard room costs $50 per night.",
        "deluxe room is $80 per night, and our suite is $120 per night.",
        "prices can vary depending on the season and room type."
    ]],
    [r"(?i).*(amenities|facilities|services).*", [
        "our hotel offers free wifi, air conditioning, breakfast, a swimming pool, and a gym.",
        "facilities include wifi, gym, swimming pool, and complimentary breakfast every morning.",
        "we provide all modern amenities to make your stay comfortable and enjoyable."
    ]],
    [r"(?i).*(book|reservation|availability).*", [
        "you can book online through our website or call us at +92-xxx-xxxx.",
        "to reserve a room, simply visit our booking page or contact our front desk.",
        "booking is easy! just choose your room type and check availability online."
    ]],
    [r"(?i)bye|goodbye", [
        "goodbye! we hope to see you at our hotel soon.",
        "bye! feel free to reach out for bookings anytime.",
        "take care! looking forward to welcoming you on your next visit."
    ]],
]
chatbot = Chat(pair)
sia = SentimentIntensityAnalyzer()
def analyzesentiment(text):
    sentimentscore = sia.polarity_scores(text)
    if sentimentscore['compound'] >= 0.05:
        return "positive"
    elif sentimentscore['compound'] <= -0.05:
        return "negative"
    else:
        return "neutral"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_response():
    user_input = request.json["msg"]

    if user_input.lower() == "sentiment":
        return jsonify({"reply": "please enter text for sentiment analysis"})

    response = chatbot.respond(user_input)

    if response:
        return jsonify({"reply": response})
    else:
        return jsonify({"reply": "I'm not sure how to respond to that query."})

# Run app
if __name__ == "__main__":
    app.run(debug=True)