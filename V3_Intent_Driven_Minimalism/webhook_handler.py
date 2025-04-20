from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    return jsonify({'status': 'received', 'data': data})

if __name__ == '__main__':
    app.run(port=5000)