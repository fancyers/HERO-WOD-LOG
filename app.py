import json
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from bson.json_util import dumps
from bson.objectid import ObjectId


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
#token 생성시 필요한 SECRET_KEY
SECRET_KEY = 'eiLTXlzJHV'

client = MongoClient('mongodb://15.165.203.11', 27017, username="test", password="test")
db = client.namedwods

# 운동기록 : 저장
@app.route('/log', methods=['POST'])
def save_log():
    wod_receive= request.form['wod_give']
    id_receive = request.form['id_give']
    # year_receive = request.form['year_give']
    # month_receive = request.form['month_give']
    date_receive = request.form['date_give']
    weight_receive = request.form['weight_give']
    round_receive = request.form['round_give']
    time_receive = request.form['time_give']
    doc = {
        'wod': wod_receive,
        'id' : id_receive,
        # 'year': year_receive,
        # 'month': month_receive,
        'date': date_receive,
        'weight': weight_receive,
        'round': round_receive,
        'time': time_receive
    }
    db.userlog.insert_one(doc)
    return jsonify({'msg': 'LOG SAVE!'})

# 운동기록 : 보여주기
@app.route('/log/<keyword>', methods=['GET'])
def read_log(keyword):
    # logData = db.userlog.find({'id':keyword})
    logData = db.userlog.find({'id':keyword}).sort('_id',-1)
    return jsonify({'all_logData': dumps(logData)})

@app.route('/logdelete', methods=['POST'])
def delete_log():

    _id_receive = request.form['_id']
    doc = {
        '_id':_id_receive
    }
    _id_receive = json.loads(_id_receive);
    db.userlog.delete_one({'_id': ObjectId(_id_receive['$oid'])})
    return jsonify({'msg': 'LOG DELETE!'})

#main page
@app.route('/')
def home():
    #운동 목록 가져오기
    wod_info = list(db.wod_info.find({}, {'_id': False}))

    #쿠키로부터 토큰을 받아옴
    token_receive = request.cookies.get('mytoken')

    try:
        #SECRET_KEY를 사용해서 토큰 복호화
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload['id']})

        return render_template('login_user.html', user_id=user_info['username'], wod_info = wod_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))


@app.route('/login')
def login():
    # 로그인 페이지로 이동
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    # id,pw값 넘겨받음
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    # pw 해시 암호화
    # pw는 보안상의 문제로 해쉬를통해 암호화 후 비교해주어야 함
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    #db에서 id, 암호화된 pw 와 일치하는 user존재하는지 검색
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    #일치 유저가 존재하는 경우
    #유저의 id와 토큰 유효시간 정보(payload)를 담아서 SECRET_KEY를 사용해 토큰을 만들고 브라우저에 해당 토큰을 넘겨줌
    if result is not None:

        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 일치하는 유저 찾지 못하면 (result is None)
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


#회원가입
#브라우저에서 모든 조건에 맞는 입력 후 넘어온 상태
@app.route('/sign_up/save', methods=['POST'])
def sign_up():

    #회원가입 폼에서 id,pw를 받아옴
    #pw는 그대로 사용하지 않고 해시를 통해 암호화 해준 후 사용
    #db에 저장 될 때도 해시암호화된 pw가 저장됨
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    #db에 입력 받은 회원 정보 저장
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

#중복확인
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    #회원가입 input-box ID 입력 값 받아옴
    username_receive = request.form['username_give']

    #db에 이미 존재하는 ID인지 check
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)