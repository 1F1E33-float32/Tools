import argparse
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import FreeMote.Consts as Consts
from FreeMote.Logger import Logger
from FreeMote.Psb.IResourceMetadata import PsbLinkOrderBy
from FreeMote.Psb.Plugins.freemount import FreeMount
from FreeMote.PsbEnums import PsbExtractOption, PsbImageFormat, PsbType
from FreeMote.PsBuild.PsbDecompiler import PsbDecompiler


def print_help_plugins() -> str:
    s = []
    s.append("")
    s.append("Plugins:")
    s.append(FreeMount.PrintPluginInfos(2))
    s.append("Examples: \n  PsbDecompile -k 123456789 sample.psb")
    return "\n".join(s)


def decompile(path: str, keepRaw: bool, format: PsbImageFormat, key: int | None, type_value: PsbType, context: dict | None) -> None:
    if path.lower().endswith("_body.bin"):
        pass
    name = os.path.splitext(os.path.basename(path))[0]
    print(f"Decompiling: {name}")
    try:
        if keepRaw:
            PsbDecompiler.DecompileToFile(path, key=key, type=type_value)
        else:
            PsbDecompiler.DecompileToFile(path, PsbExtractOption.Extract, format, key=key, type=type_value, contextDic=context)
    except Exception as e:
        print(e)


def main(argv: list[str]) -> None:
    Logger.InitConsole()
    if len(argv) > 0 and argv[0] == FreeMount.ARG_DISABLE_PLUGINS:
        print("Plugins disabled.")
    else:
        FreeMount.Init()
        print(f"{FreeMount.PluginsCount} Plugins Loaded.")
    Consts.InMemoryLoading = True
    print("")
    commands = {"image", "unlink", "info-psb"}
    if len(argv) == 0:
        base = argparse.ArgumentParser(add_help=True)
        base.print_help()
        return
    if argv[0] in commands:
        if argv[0] == "image":
            image_parser = argparse.ArgumentParser(add_help=True)
            image_parser.add_argument("Path", nargs="+")
            image_parser.add_argument("-1by1", "--enumerate", dest="no_parallel", action="store_true")
            args = image_parser.parse_args(argv[1:])
            enableParallel = not args.no_parallel
            for psbPath in args.Path:
                if os.path.isfile(psbPath):
                    try:
                        PsbDecompiler.ExtractImageFiles(psbPath)
                    except Exception as e:
                        print(e)
                elif os.path.isdir(psbPath):
                    for root, _, files in os.walk(psbPath):
                        for fn in files:
                            if any(fn.endswith(ext) for ext in [".psb", ".pimg", ".m", ".bytes"]):
                                s = os.path.join(root, fn)
                                try:
                                    PsbDecompiler.ExtractImageFiles(s)
                                except Exception as e:
                                    print(e)
            print("Done.")
            return
        if argv[0] == "unlink":
            unlink_parser = argparse.ArgumentParser(add_help=True)
            unlink_parser.add_argument("-o", "--order", dest="order", type=str)
            unlink_parser.add_argument("PSB", nargs="+")
            unlink_parser.add_argument("-e", "--encoding", dest="encoding", type=str)
            args = unlink_parser.parse_args(argv[1:])
            if args.encoding:
                try:
                    PsbDecompiler.Encoding = args.encoding
                except Exception:
                    print(f"[WARN] Encoding {args.encoding} is not valid.")
            order = PsbLinkOrderBy.Name
            psbPaths = args.PSB
            for psbPath in psbPaths:
                if os.path.isfile(psbPath):
                    try:
                        PsbDecompiler.UnlinkToFile(psbPath, order=order)
                    except Exception as e:
                        print(e)
                else:
                    print(f"Input path not found: {psbPath}")
            print("Done.")
            return
        if argv[0] == "info-psb":
            info_parser = argparse.ArgumentParser(add_help=True)
            info_parser.add_argument("-a", "--all", dest="all", action="store_true")
            info_parser.add_argument("-k", "--key", dest="mdf_key", type=str)
            info_parser.add_argument("-l", "--length", dest="mdf_key_len", type=int)
            info_parser.add_argument("-b", "--body", dest="body", type=str)
            info_parser.add_argument("-raw", "--raw", dest="raw", action="store_true")
            info_parser.add_argument("-1by1", "--enumerate", dest="no_parallel", action="store_true")
            info_parser.add_argument("-hex", "--json-hex", dest="json_hex", action="store_true")
            info_parser.add_argument("-indent", "--json-array-indent", dest="json_array_indent", action="store_true")
            info_parser.add_argument("-dfa", "--disable-flatten-array", dest="disable_flatten_array", action="store_true")
            info_parser.add_argument("-e", "--encoding", dest="encoding", type=str)
            info_parser.add_argument("PSB", nargs="+")
            args = info_parser.parse_args(argv[1:])
            if args.encoding:
                try:
                    PsbDecompiler.Encoding = args.encoding
                except Exception:
                    print(f"[WARN] Encoding {args.encoding} is not valid.")
            if args.json_array_indent:
                Consts.JsonArrayCollapse = False
            if args.json_hex:
                Consts.JsonUseHexNumber = True
            if args.disable_flatten_array:
                Consts.FlattenArrayByDefault = False
            bodyPath = args.body if args.body else None
            extractAll = args.all
            outputRaw = args.raw
            enableParallel = True
            if args.no_parallel:
                enableParallel = False
            key = args.mdf_key if args.mdf_key else None
            if not key:
                raise ValueError("No key or seed specified.")
            keyLen = args.mdf_key_len if args.mdf_key_len is not None else 0x83
            context = {}
            if keyLen >= 0:
                context[Consts.Context_MdfKeyLength] = int(keyLen)
            for s in args.PSB:
                PsbDecompiler.ExtractArchive(s, key, context, bodyPath, outputRaw, extractAll, enableParallel)
            print("Done.")
            return
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("Files", nargs="*")
    parser.add_argument("-s", "--seed", dest="seed", type=str)
    parser.add_argument("-l", "--length", dest="length", type=int)
    parser.add_argument("-k", "--key", dest="key", type=int)
    parser.add_argument("-raw", "--raw", dest="raw", action="store_true")
    parser.add_argument("-oom", "--memory-limit", dest="oom", action="store_true")
    parser.add_argument("-hex", "--json-hex", dest="json_hex", action="store_true")
    parser.add_argument("-indent", "--json-array-indent", dest="json_array_indent", action="store_true")
    parser.add_argument("-dfa", "--disable-flatten-array", dest="disable_flatten_array", action="store_true")
    parser.add_argument("-e", "--encoding", dest="encoding", type=str)
    parser.add_argument("-t", "--type", dest="type_value", type=str)
    parser.add_argument("-dci", "--disable-combined-image", dest="disable_combined_image", action="store_true")
    args = parser.parse_args(argv)

    if args.encoding:
        try:
            PsbDecompiler.Encoding = args.encoding
        except Exception:
            print(f"[WARN] Encoding {args.encoding} is not valid.")
    if args.oom:
        pass
    if args.json_array_indent:
        Consts.JsonArrayCollapse = False
    if args.json_hex:
        Consts.JsonUseHexNumber = True
    if args.disable_flatten_array:
        Consts.FlattenArrayByDefault = False
    context = {}
    if args.seed:
        context[Consts.Context_MdfKey] = args.seed
    if args.length is not None:
        context[Consts.Context_MdfKeyLength] = args.length
    if args.disable_combined_image:
        context[Consts.Context_DisableCombinedImage] = True
    useRaw = args.raw
    key = args.key if args.key is not None else None
    t = PsbType.PSB
    if args.type_value:
        try:
            t = PsbType[args.type_value]
        except Exception:
            t = PsbType.PSB
    for s in args.Files:
        if os.path.isfile(s):
            decompile(s, useRaw, PsbImageFormat.png, key, t, context)
        elif os.path.isdir(s):
            for root, _, files in os.walk(s):
                for fn in files:
                    if any(fn.endswith(ext) for ext in [".psb", ".mmo", ".pimg", ".scn", ".dpak", ".psz", ".psp", ".bytes", ".m"]):
                        decompile(os.path.join(root, fn), useRaw, PsbImageFormat.png, key, t, context)
    print("Done.")


if __name__ == "__main__":
    main(sys.argv[1:])
