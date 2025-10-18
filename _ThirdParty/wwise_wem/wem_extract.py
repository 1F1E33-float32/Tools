import argparse
import glob
import os
from multiprocessing import Process, cpu_count, Queue
from queue import Empty
from time import sleep

from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn

from wem_tools.converter_opus_wem import rewrap_opus_wwise_to_ogg
from wem_tools.extractor import extract_info, guess_extension


def args_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=r"D:\Reverse\_Unreal Engine\FModel\Output\Exports\Client\Content\Aki\WwiseAudio_Generated")
    ap.add_argument("--output", default=r"D:\Reverse\_Unreal Engine\FModel\Output\Exports\Client\Content\Aki\WwiseAudio_Generated")
    ap.add_argument("--workers", type=int, default=cpu_count(), help="进程数，默认=CPU核心数")
    return ap


def _process_one_file(in_path, out_spec):
    with open(in_path, "rb") as f:
        buf = f.read()

    info = extract_info(buf)

    be = bool(info["be"])
    chunks = info["chunks"]
    fmt_code = int(info["fmt_code"])
    payload_off = int(info["payload_off"])
    payload_sz = int(info["payload_sz"])

    base_name = os.path.splitext(os.path.basename(in_path))[0]
    ext = guess_extension(fmt_code, buf, payload_off)

    if out_spec:
        if os.path.isdir(out_spec):
            out_path = os.path.join(out_spec, base_name + ext)
        else:
            out_dir = os.path.dirname(out_spec)
            if out_dir and not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
            out_path = out_spec
    else:
        out_path = base_name + ext

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    if fmt_code == 0x3041:
        fmt_off, _ = chunks[b"fmt "]
        ogg_bytes = rewrap_opus_wwise_to_ogg(buf, be, chunks, fmt_off)
        with open(out_path, "wb") as out:
            out.write(ogg_bytes)
    else:
        with open(out_path, "wb") as out:
            out.write(buf[payload_off: payload_off + payload_sz])


def _worker(rank, files, input_root, output_root, q: Queue):
    ok = 0
    err = 0
    for src in files:
        try:
            rel = os.path.relpath(src, input_root)
            rel_dir = os.path.dirname(rel)
            out_dir = os.path.join(output_root, rel_dir)
            _process_one_file(src, out_dir)
            ok += 1
            q.put(("progress", rank, 1))  # 单个文件完成
        except Exception as e:
            err += 1
            q.put(("error", rank, str(e)))
    q.put(("done", rank, {"ok": ok, "err": err}))


def _split_even(lst, n):
    n = max(1, int(n))
    size = (len(lst) + n - 1) // n  # ceil
    return [lst[i*size:(i+1)*size] for i in range(n) if lst[i*size:(i+1)*size]]


if __name__ == "__main__":
    args = args_parser().parse_args()

    input_root = os.path.abspath(args.input)
    output_root = os.path.abspath(args.output)
    workers = max(1, int(args.workers or 1))

    files = glob.glob(os.path.join(input_root, "**", "*.wem"), recursive=True)
    files += glob.glob(os.path.join(input_root, "**", "*.WEM"), recursive=True)

    if not files:
        print("未发现 .wem/.WEM 文件。")
        raise SystemExit(0)

    chunks = _split_even(files, workers)
    workers = len(chunks)

    q: Queue = Queue()
    procs = []
    for rank, chunk in enumerate(chunks):
        p = Process(target=_worker, args=(rank, chunk, input_root, output_root, q))
        p.start()
        procs.append(p)

    progress = Progress(
        TextColumn("[bold blue]{task.fields[title]}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("ETA"),
        TimeRemainingColumn(),
        transient=False,
    )

    with progress:
        total_task = progress.add_task("total", total=len(files), title="Total")
        worker_tasks = {}
        for rank, chunk in enumerate(chunks):
            worker_tasks[rank] = progress.add_task(
                f"worker-{rank+1}", total=len(chunk),
                title=f"Worker {rank+1}"
            )

        done_workers = 0
        total_ok = 0
        total_err = 0

        while done_workers < workers:
            try:
                msg_type, rank, payload = q.get(timeout=0.1)
            except Empty:
                sleep(0.05)
                continue

            if msg_type == "progress":
                progress.update(worker_tasks[rank], advance=payload)
                progress.update(total_task, advance=payload)
                total_ok += 1
            elif msg_type == "error":
                total_err += 1
                progress.update(worker_tasks[rank], description=f"worker-{rank+1} (ERR)")
            elif msg_type == "done":
                done_workers += 1
                ok = payload.get("ok", 0)
                err = payload.get("err", 0)
                progress.update(worker_tasks[rank], description=f"worker-{rank+1} done (ok={ok}, err={err})")

    for p in procs:
        p.join()

    print(f"\n完成：总计 {len(files)}，成功 {total_ok}，失败 {total_err}。")