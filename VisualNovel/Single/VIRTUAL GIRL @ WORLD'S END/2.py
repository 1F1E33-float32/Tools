import frida, sys, os, threading

# 用于跨线程通知“完成”
done_event = threading.Event()

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        if payload == 'done':
            print("[*] 收到 done 信号，准备退出")
            done_event.set()          # 通知主线程可以结束了
        else:
            # 写入 “原字符串,哈希值”
            with open(output_path, 'a', encoding='utf8') as f:
                f.write(payload + '\n')
    elif message['type'] == 'error':
        print("[ERROR]", message['description'], file=sys.stderr)

if __name__ == '__main__':
    here        = os.path.dirname(__file__)
    input_path  = os.path.join(here, 'assetbundles_list.txt')
    output_path = os.path.join(here, 'assetbundles_hashed.txt')

    # 1) 准备样本列表
    with open(input_path, 'r', encoding='utf8') as f:
        samples = [l.strip() for l in f if l.strip()]
    open(output_path, 'w', encoding='utf8').close()  # 清空输出

    # 2) 附加进程、加载脚本
    pid     = int(sys.argv[1])
    session = frida.attach(pid)
    agent   = open(os.path.join(here, 'hook.bundle.js'), 'r', encoding='utf8').read()
    script  = session.create_script(agent)
    script.on('message', on_message)
    script.load()

    # 3) 调用 RPC 开始计算
    script.exports.hash(samples)
    print(f"[*] 已发送 {len(samples)} 个样本，等待完成信号...")

    # 4) 主线程在此阻塞，直到 done_event.set() 被触发
    done_event.wait()

    # 5) 清理并退出
    session.detach()
    print("[*] 已退出")
    sys.exit(0)