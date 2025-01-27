import json
import os
import random
from datetime import datetime

from payos import PayOS, PaymentData, ItemData
from flask import Flask, render_template, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint

# Khởi tạo PayOS với thông tin xác thực
payOS = PayOS(
    client_id="YOUR_CLIENT_ID",
    api_key="YOUR_API_KEY",
    checksum_key="YOUR_CHECK_SUM_KEY"
)

app = Flask(__name__, static_folder='PUBLIC',
           static_url_path='', template_folder='PUBLIC')

# Cấu hình Swagger UI
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
API_URL = '/static/swagger.json'  # Our API url

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "PayOS Payment API"
    }
)

# Register blueprint at URL
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Thêm route để phục vụ file swagger.json
@app.route('/static/swagger.json')
def serve_swagger_spec():
    with open('swagger.json', 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/')
def index():
    return app.send_static_file('checkout.html')

@app.route('/create_payment_link', methods=['POST'])
def create_payment():
    domain = request.host_url.rstrip('/')
    try:
        # Lấy dữ liệu từ request body
        data = request.get_json()
        
        # Validate required fields
        if not data or 'amount' not in data or 'description' not in data:
            return jsonify({
                "error": "Missing required fields",
                "message": "Amount và description là bắt buộc"
            }), 400
            
        # Tạo mã đơn hàng ngắn hơn: YYMMDDHHMMSS + xxx
        order_code = int(datetime.now().strftime('%y%m%d%H%M%S') + str(random.randint(100, 999)))
        
        # Chuyển đổi items thành ItemData objects
        items_data = []
        if 'items' in data:
            for item in data['items']:
                items_data.append(ItemData(
                    name=item['name'],
                    quantity=item['quantity'],
                    price=item['price']
                ))
        
        paymentData = PaymentData(
            orderCode=order_code,
            amount=data['amount'],
            description=data['description'],
            cancelUrl=f"{domain}/cancel.html",
            returnUrl=f"{domain}/success.html",
            signature="",
            items=items_data  # Sử dụng list của ItemData objects
        )
        
        payosCreatePayment = payOS.createPaymentLink(paymentData)
        print("PayOS Response:", payosCreatePayment.to_json())
        return jsonify(payosCreatePayment.to_json())
    except Exception as e:
        print("Error:", str(e))
        return jsonify({
            "error": str(e),
            "message": "Không thể tạo link thanh toán"
        }), 403

if __name__ == '__main__':
    app.run(debug=True, port=5000)
