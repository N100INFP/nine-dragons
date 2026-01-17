import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 게임 데이터 저장
players = {} 

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    # 플레이어 초기화: 1~9 타일 제공, 점수 0점
    players[request.sid] = {
        'name': data['name'],
        'tiles': list(range(1, 10)),
        'score': 0,
        'current_pick': None
    }
    print(f"{data['name']} 입장 (ID: {request.sid})")

@socketio.on('choice')
def handle_choice(data):
    sid = request.sid
    pick = int(data['pick'])
    
    if sid in players and pick in players[sid]['tiles']:
        players[sid]['current_pick'] = pick
        players[sid]['tiles'].remove(pick)
        
        # 상대방에게는 "제출함" 상태만 알림
        emit('opponent_ready', broadcast=True, include_self=False)
        
        # 두 명 다 선택했는지 확인
        ready_pids = [p for p in players if players[p]['current_pick'] is not None]
        if len(ready_pids) == 2:
            p1_sid, p2_sid = ready_pids
            val1 = players[p1_sid]['current_pick']
            val2 = players[p2_sid]['current_pick']
            
            # 결과 판정
            winner_sid = None
            if val1 > val2: winner_sid = p1_sid
            elif val2 > val1: winner_sid = p2_sid
            
            if winner_sid:
                players[winner_sid]['score'] += 1

            # 양측에 결과 전송
            result = {
                'p1_name': players[p1_sid]['name'], 'p1_pick': val1,
                'p2_name': players[p2_sid]['name'], 'p2_pick': val2,
                'winner': players[winner_sid]['name'] if winner_sid else "무승부",
                'scores': {players[p1_sid]['name']: players[p1_sid]['score'], 
                           players[p2_sid]['name']: players[p2_sid]['score']}
            }
            emit('round_result', result, broadcast=True)
            
            # 라운드 초기화
            players[p1_sid]['current_pick'] = None
            players[p2_sid]['current_pick'] = None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
