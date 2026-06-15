import os
import redis
from flask import Flask, jsonify, request

app = Flask(__name__)

# 从环境变量读取 Redis 配置（由 K8s ConfigMap + Secret 注入）
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
redis_password = os.environ.get("REDIS_PASSWORD", None)

# 连接 Redis（本地无密码时可不传 password）
try:
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password if redis_password else None,
        decode_responses=True,
    )
    r.ping()
    redis_connected = True
except Exception:
    redis_connected = False


@app.route("/api/ping")
def ping():
    """健康检查端点，用于 ELB 探测和 HPA 压测"""
    return jsonify({"status": "ok"})


@app.route("/api/hello")
def hello():
    """返回欢迎信息"""
    return jsonify({
        "message": "Hello from Cloud Computing Course Project!",
        "student_id": "2023112462",
        "name": "亚兴龙"
    })


@app.route("/api/redis-set")
def redis_set():
    """向 Redis 写入测试数据（验证持久化用）"""
    key = request.args.get("key", "testkey")
    value = request.args.get("value", "hello")
    if redis_connected:
        r.set(key, value)
        return jsonify({"status": "ok", "key": key, "value": value})
    return jsonify({"status": "error", "message": "Redis not connected"}), 500


@app.route("/api/redis-get")
def redis_get():
    """从 Redis 读取测试数据"""
    key = request.args.get("key", "testkey")
    if redis_connected:
        value = r.get(key)
        return jsonify({"status": "ok", "key": key, "value": value})
    return jsonify({"status": "error", "message": "Redis not connected"}), 500


@app.route("/api/info")
def info():
    """返回环境信息"""
    return jsonify({
        "REDIS_HOST": redis_host,
        "REDIS_PORT": redis_port,
        "redis_connected": redis_connected,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
