import "frida-il2cpp-bridge";

Il2Cpp.perform(() => {
    const asmGame = Il2Cpp.domain.assembly("Assembly-CSharp");

    Il2Cpp.trace(true)
        .assemblies(asmGame)
        .filterClasses(klass => klass.namespace === "Amber" && klass.name === "AssetLoadManager")
        .filterMethods(method => method.name === "LoadBundle")
        .and()
        .attach();

    Il2Cpp.trace(true)
        .assemblies(asmGame)
        .filterClasses(klass => klass.namespace === "Amber" && klass.name === "Hash")
        .filterMethods(method => method.name === "GetHashCode")
        .and()
        .attach();

    Il2Cpp.trace(true)
        .assemblies(asmGame)
        .filterClasses(klass => klass.namespace === "Amber" && klass.name === "Jamming")
        .filterMethods(method => ["GetJammingInt", ".cctor", ".cctor()"].includes(method.name))
        .and()
        .attach();

    let dumpedOnce = false;
    let jamClass: Il2Cpp.Class | null = null;
    let bytesField: Il2Cpp.Field | null = null;

    function findJamming() {
        if (!jamClass) {
            jamClass = asmGame.image.classes.find(k => k.namespace === "Amber" && k.name === "Jamming")!;
            jamClass?.initialize(); // 确保静态字段已可读
        }
        if (!bytesField) {
            bytesField = jamClass.fields.find(f => f.isStatic && f.name === "bytes256")!;
        }
    }

    function hex2(n: number) { return "0x" + n.toString(16).padStart(2, "0"); }
    function hex8(n: number) { return "0x" + (n >>> 0).toString(16).padStart(8, "0"); }

    function dumpBytes256(tag: string) {
        try {
            findJamming();
            const arr: any = (bytesField as any).value;           // System.Byte[]
            const len: number = Number(arr.length);               // 256
            const bytes: number[] = [];
            for (let i = 0; i < len; i++) bytes.push(Number(arr.get(i)));
            console.log(`[Amber.Jamming.bytes256] (${tag}) len=${len}\n` +
                bytes.map((b, i) => (i % 16 === 0 ? "\n" : "") + hex2(b)).join(" "));
            dumpedOnce = true;
        } catch (e) {
            console.log("[bytes256 dump error]", e);
        }
    }

    // 1) 在 .cctor 完成后 dump 一次
    try {
        const jam = asmGame.image.classes.find(k => k.namespace === "Amber" && k.name === "Jamming");
        jam?.initialize();
        const cctor = jam?.methods.find(m => m.name === ".cctor" || m.name === ".cctor()");
        if (cctor) {
            Interceptor.attach(cctor.virtualAddress, {
                onLeave() {
                    if (!dumpedOnce) dumpBytes256(".cctor");
                }
            });
        } else {
            // 如果进程启动时已初始化，直接尝试 dump 一次
            dumpBytes256("eager");
        }
    } catch (e) {
        console.log("[hook .cctor error]", e);
    }

    // 2) hook GetJammingInt，打印 top_index 以及取到的四个字节与拼接值
    try {
        findJamming();
        const getJam = jamClass!.methods.find(m => m.name === "GetJammingInt" && m.parameterCount === 1);
        if (getJam) {
            Interceptor.attach(getJam.virtualAddress, {
                onEnter(args) {
                    // Windows x64 调用约定：第一个整型参数在 RCX
                    this.top = args[0].toInt32();
                },
                onLeave(retval) {
                    try {
                        if (!dumpedOnce) dumpBytes256("lazy"); // 万一之前没 dump 到，这里兜底
                        findJamming();
                        const arr: any = (bytesField as any).value;
                        const idx = this.top & 0xFF;
                        const b0 = Number(arr.get(idx));
                        const b1 = Number(arr.get((idx + 1) & 0xFF));
                        const b2 = Number(arr.get((idx + 2) & 0xFF));
                        const b3 = Number(arr.get((idx + 3) & 0xFF));
                        const val = (b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)) >>> 0;

                        console.log(`[GetJammingInt] top=${this.top} (idx=${idx}) -> retval=${retval.toInt32()} ${hex8(val)} | bytes=` +
                            `${hex2(b0)},${hex2(b1)},${hex2(b2)},${hex2(b3)}`);
                    } catch (e) {
                        console.log("[GetJammingInt post error]", e);
                    }
                }
            });
        }
    } catch (e) {
        console.log("[hook GetJammingInt error]", e);
    }

    // 3) 作为保险：第一次进入 Hash.GetHashCode 时也尝试 dump（防止 .cctor 没抓到）
    try {
        const hashClass = asmGame.image.classes.find(k => k.namespace === "Amber" && k.name === "Hash");
        hashClass?.initialize();
        const getHash = hashClass?.methods.find(m => m.name === "GetHashCode");
        if (getHash) {
            Interceptor.attach(getHash.virtualAddress, {
                onEnter() {
                    if (!dumpedOnce) dumpBytes256("from Hash.GetHashCode");
                }
            });
        }
    } catch (e) {
        console.log("[hook Hash.GetHashCode error]", e);
    }
});
