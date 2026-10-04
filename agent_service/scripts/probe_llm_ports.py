import socket

for i in range(1, 255):
    ip = f"192.168.1.{i}"
    for p in [8080, 11434, 8000]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.02)
        if s.connect_ex((ip, p)) == 0:
            print(f"OPEN: {ip}:{p}")
        s.close()
