from flask import Blueprint, Flask, request, jsonify
from . import create_app
from .yolo import yolo_dbr
from .yolo import dbr_only
from .models import *
from sqlalchemy.ext.declarative import DeclarativeMeta
from flask_mail import Mail, Message
import json

bp = Blueprint('routes', __name__, url_prefix='/')
app = create_app()
mail = Mail(app)

@bp.route('/')
def test():
    return 'test'

@bp.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        print(request.files)
        img_file = request.files['file']
        codes = dbr_only.main(img_file)
        # YOLO 테스트 시
        #codes = yolo_dbr.main(img_file)

        data = []

        for code in codes:
            print(code + " code ")
            code_info = Barcode.query.filter(Barcode.cnum == code).first()
            print(code_info)
            if code_info is not None:
                pro_info = Product.query.filter(Product.id == code_info.product_id).first()
                
                if pro_info is not None:
                    data.append(pro_info.toDict())
    
    return jsonify(data)

@bp.route('/send-mail', methods=['POST'])
def send_mail():
    msg = Message('Hello', sender= 'code110100@gmail.com', recipients=['ghk784@naver.com'])
    msg.body = '결제가 완료되었습니다'
    mail.send(msg)
    return 'Sent'
