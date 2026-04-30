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
        "Hello! Welcome to our Amazon-style Q&A bot.",
        "Hi there! Ask me anything about products.",
        "Hey! Looking for product details or reviews?"
    ]],

    [r"(?i).*(price|cost).*iphone.*", [
        "The price of iPhone depends on the model. For example, iPhone 14 starts around $799.",
        "iPhone prices vary, but generally range between $700 and $1200.",
    ]],

    [r"(?i).*(battery|backup).*iphone.*", [
        "iPhones usually offer all-day battery life depending on usage.",
        "Battery backup is strong, especially in newer iPhone models.",
    ]],

    [r"(?i).*(gaming|performance).*phone.*", [
        "High-end phones like iPhone and Samsung Galaxy are great for gaming.",
        "For gaming, look for phones with strong processors and good RAM.",
    ]],

    [r"(?i).*(laptop|best laptop).*", [
        "Popular laptops include Dell XPS, MacBook, and HP Pavilion.",
        "For students, mid-range laptops with SSD and 8GB RAM are recommended.",
    ]],

    [r"(?i).*(delivery|shipping).*", [
        "Standard delivery takes 3-5 business days.",
        "Shipping time depends on your location and product availability.",
    ]],

    [r"(?i).*(return|refund).*", [
        "You can return most products within 7-30 days.",
        "Refunds are processed after the product is received and inspected.",
    ]],

    [r"(?i).*(review|rating).*", [
        "This product has generally positive reviews.",
        "Customers rate this product around 4 out of 5 stars.",
    ]],

    [r"(?i)bye|goodbye", [
        "Goodbye! Happy shopping!",
        "Bye! Come back for more product queries.",
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