import socket
import threading
import re
import pickle
import time

HOST = '127.0.0.1'
PORT = 9090

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()

clients = []
nicknames = []
passwords = {}


def load_data():
    try:
        return pickle.load(open('users.dat', 'rb'))
    except:
        return {}


def save_data():
    pickle.dump(passwords, open('users.dat', 'wb'))


def auth(name, password) -> int:
    if name in passwords:
        return 100 if password == passwords.get(name, '') else 101
    else:
        passwords[name] = password
        return 102


def close(client):
    index = clients.index(client)
    clients.remove(client)
    client.close()
    nickname = nicknames[index]
    nicknames.remove(nickname)


def broadcast(message):
    for client in clients:
        client.send(message)


def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            msg = f"{nicknames[clients.index(client)]}:{message}"
            print(msg)
            if message[0] == '@':
                pattern = re.compile(r'@.*@')
                find = pattern.search(message).group(0)
                if find:
                    id = find[1:-1]
                    message = message[len(find):]
                    try:
                        msg = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+" 【私聊】" + \
                            nicknames[clients.index(client)]+":"+message
                        clients[nicknames.index(id)].send(msg.encode('utf-8'))
                    except Exception as e:
                        client.send(f"错误:{e}\n".encode('utf-8'))
                else:
                    client.send(f"错误:该用户不存在！\n".encode('utf-8'))
            elif message == '.userlist':
                msg = f"server:当前在线用户有{len(nicknames)}人:\n"
                msg += '\n'.join(nicknames)
                msg += '\n'
                client.send(msg.encode('utf-8'))

            else:
                broadcast((time.strftime("%Y-%m-%d %H:%M:%S",
                          time.localtime())+" "+msg).encode('utf-8'))
        except:
            close(client)
            break


def register(client, name, address):
    print(f"创建新用户:{name}")
    client.send("创建了新用户，欢迎加入服务器\n".encode('utf-8'))


def authsuccess(client, name, address):
    print(f"用户{name}连接至服务器")
    client.send("已连接至服务器\n".encode('utf-8'))


def authfail(client, name, address):
    print(f"用户{name}验证失败，请求来自{address}！")
    client.send("验证失败！请重新登陆！\n".encode('utf-8'))


def receive():
    while True:
        client, address = server.accept()
        authfunc = {100: authsuccess, 101: authfail, 102: register}
        print(f"connect to {str(address)}!")

        client.send("NIKE".encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        client.send("PWD".encode('utf-8'))
        password = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)
        authcode = auth(nickname, password)
        authfunc[authcode](client, nickname, address)
        if authcode == 101:
            close(client)
            print(f"已断开与{address}的连接")
            continue
        save_data()
        broadcast(f"{nickname}==桑加入了服务器!\n".encode('utf-8'))
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


if __name__ == '__main__':
    print("正在加载用户数据……")
    passwords = load_data()
    print("服务器运行中……")
    receive()
