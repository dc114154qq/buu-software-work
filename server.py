import http.server
import socketserver
import json
import os
import time
import datetime

PORT = 8000
BOOKING_FILE = 'bookings.json'          # 停车场数据
RESERVATION_FILE = 'reservations.json'  # 景点/美食预约数据

class BookingHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/book':
            try:
                # 1. 读取前端数据
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                new_order = json.loads(post_data.decode('utf-8'))
                
                print(f"👀 收到前端数据: {new_order}") # 【调试】打印收到的数据

                response = {"success": False, "message": "未知请求"}

                # --- 分支 A：停车场预约 ---
                if 'parkId' in new_order and 'plate' in new_order:
                    new_order['timestamp'] = int(time.time() * 1000)
                    self.save_to_file(BOOKING_FILE, new_order)
                    print("✅ 识别为：停车场预约 -> 成功")
                    response = {"success": True, "message": "车位预约成功！"}

                # --- 分支 B：景点/美食预约 ---
                # 只要有 poiId 就认为是景点预约
                elif 'poiId' in new_order:
                    new_order['reservationId'] = f"res-{int(time.time() * 1000)}"
                    new_order['status'] = 'confirmed'
                    new_order['createTime'] = datetime.datetime.now().isoformat()
                    self.save_to_file(RESERVATION_FILE, new_order)
                    print("✅ 识别为：景点/美食预约 -> 成功")
                    response = {"success": True, "message": "预约成功！已发送至后台"}
                
                else:
                    print("❌ 识别失败：缺少关键字段")
                    # 注意：如果看到这个提示，说明服务器代码已更新，但数据不对
                    response = {"success": False, "message": "服务器已更新，但未识别到 parkId 或 poiId"}

                # 发送响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ 服务器内部错误: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            super().do_POST()

    def save_to_file(self, filename, new_item):
        existing_data = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content: existing_data = json.loads(content)
            except:
                existing_data = []
        
        existing_data.append(new_item)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

print(f"🚀 服务器启动成功！端口: {PORT}")
print(f"📂 数据将写入: {BOOKING_FILE} 和 {RESERVATION_FILE}")
print("--------------------------------------------------")
print("⚠️ 请确保您已关闭之前的黑色窗口，这是新的服务器进程")
print("--------------------------------------------------")

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), BookingHandler) as httpd:
    httpd.serve_forever()