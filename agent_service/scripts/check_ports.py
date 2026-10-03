import socket

def test_ports():
    hosts = ["192.168.1.184", "127.0.0.1", "localhost"]
    ports = [8090, 8091, 5432, 5433, 6379]
    for h in hosts:
        for p in ports:
            s = socket.socket()
            s.settimeout(1.0)
            res = s.connect_ex((h, p))
            s.close()
            status = "OPEN" if res == 0 else f"CLOSED/TIMEOUT ({res})"
            print(f"Host {h}:{p} -> {status}")

if __name__ == "__main__":
    test_ports()
