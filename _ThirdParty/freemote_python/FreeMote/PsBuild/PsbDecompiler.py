import json
import os
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from ..Consts import Context_ArchiveItemFileNames, Context_ArchiveSource, Context_BodyBinName, Context_CryptKey, Context_FileName, Context_MdfKey, Context_MdfKeyLength, Context_MdfMtKey, Context_PsbShellType, JsonArrayCollapse
from ..Logger import Logger
from ..MPack import IsSignatureMPack as MPack_IsSig
from ..Psb.Plugins.freemount import FreeMount
from ..Psb.Psb import PSB
from ..Psb.PsbExtension import PsbExtension
from ..PsbEnums import PsbExtractOption, PsbImageFormat, PsbType
from ..PsbFile import PsbFile
from .PsbResourceJson import PsbResourceJson


class PsbDecompiler:
    Encoding = "utf-8"

    @staticmethod
    def Decompile(path: str) -> str:
        psb = PSB(path, PsbDecompiler.Encoding)
        return PsbDecompiler.DecompilePsb(psb)

    @staticmethod
    def DecompileWithContext(path: str, context: Dict[str, object] | None = None, psbType: PsbType = PsbType.PSB) -> Tuple[str, PSB]:
        with open(path, "rb") as fs:
            ctx = FreeMount.CreateContext(context)
            t = None
            stream = fs
            ms = ctx.OpenFromShell(fs, t)
            if ms is not None:
                ctx.Context[Context_PsbShellType] = t
                stream = ms
            try:
                psb = PSB(stream, False, PsbDecompiler.Encoding)
            except Exception:
                stream.seek(0)
                key = None
                if ctx.Context.get(Context_CryptKey) is not None:
                    key = ctx.Context.get(Context_CryptKey)
                stream.seek(0)
                if key is not None:
                    try:
                        mms = BytesIO()
                        PsbFile.Encode(int(key), None, None, stream, mms)
                        psb = PSB(mms, True, PsbDecompiler.Encoding)
                        ctx.Context[Context_CryptKey] = key
                    except Exception as e:
                        raise e
                else:
                    psb = PSB.DullahanLoad(stream)
        if psbType != PsbType.PSB:
            psb.Type = psbType
        return PsbDecompiler.DecompilePsb(psb), psb

    @staticmethod
    def DecompilePsb(psb: PSB) -> str:
        if JsonArrayCollapse:
            return json.dumps(psb.Root, ensure_ascii=False)
        return json.dumps(psb.Root, indent=2, ensure_ascii=False)

    @staticmethod
    def OutputResources(psb: PSB, context, filePath: str, extractOption: PsbExtractOption = PsbExtractOption.Original, extractFormat: PsbImageFormat = PsbImageFormat.png, useResx: bool = True) -> None:
        name = os.path.splitext(os.path.basename(filePath))[0]
        dirPath = os.path.join(os.path.dirname(filePath), name)
        resx = PsbResourceJson(psb, context.Context)
        if PsbDecompiler.Encoding and PsbDecompiler.Encoding.lower() != "utf-8":
            resx.Encoding = 65001
        if os.path.exists(dirPath):
            name += "-resources"
            dirPath += "-resources"
        if not os.path.exists(dirPath):
            if len(getattr(psb, "Resources", [])) != 0:
                os.makedirs(dirPath, exist_ok=True)
        resDictionary = psb.TypeHandler.OutputResources(psb, context, name, dirPath, extractOption)
        if useResx:
            resx.Resources = resDictionary
            resx.Context = context.Context
            if JsonArrayCollapse:
                json_text = json.dumps(resx.__dict__, ensure_ascii=False)
            else:
                json_text = json.dumps(resx.__dict__, indent=2, ensure_ascii=False)
            out_json = PsbDecompiler._change_extension_for_output_json(filePath, ".resx.json")
            with open(out_json, "w", encoding="utf-8") as f:
                f.write(json_text)
        else:
            if len(getattr(psb, "ExtraResources", [])) > 0:
                raise Exception("PSBv4 cannot use legacy res.json format.")
            out_json = PsbDecompiler._change_extension_for_output_json(filePath, ".res.json")
            with open(out_json, "w", encoding="utf-8") as f:
                f.write(json.dumps(list(resDictionary.values()), indent=2, ensure_ascii=False))

    @staticmethod
    def _change_extension_for_output_json(inputPath: str, extension: str = ".json") -> str:
        if not extension.startswith("."):
            extension = "." + extension
        if inputPath.endswith(".m"):
            return inputPath + extension
        base, _ = os.path.splitext(inputPath)
        return base + extension

    @staticmethod
    def DecompileToFilePsb(psb: PSB, outputPath: str, additionalContext: Dict[str, object] | None = None, extractOption: PsbExtractOption = PsbExtractOption.Original, extractFormat: PsbImageFormat = PsbImageFormat.png, useResx: bool = True, key: Optional[int] = None) -> None:
        context = FreeMount.CreateContext(additionalContext)
        if key is not None:
            context.Context[Context_CryptKey] = key
        with open(outputPath, "w", encoding="utf-8") as f:
            f.write(PsbDecompiler.DecompilePsb(psb))
        PsbDecompiler.OutputResources(psb, context, outputPath, extractOption, extractFormat, useResx)

    @staticmethod
    def DecompileToFile(inputPath: str, extractOption: PsbExtractOption = PsbExtractOption.Original, extractFormat: PsbImageFormat = PsbImageFormat.png, useResx: bool = True, key: Optional[int] = None, type: PsbType = PsbType.PSB, contextDic: Dict[str, object] | None = None) -> Tuple[str, PSB]:
        context = FreeMount.CreateContext(contextDic)
        if key is not None:
            context.Context[Context_CryptKey] = key
        outputPath = PsbDecompiler._change_extension_for_output_json(inputPath, ".json")
        json_text, psb = PsbDecompiler.DecompileWithContext(inputPath, context.Context)
        if type != PsbType.PSB:
            psb.Type = type
        with open(outputPath, "w", encoding="utf-8") as f:
            f.write(json_text)
        PsbDecompiler.OutputResources(psb, context, inputPath, extractOption, extractFormat, useResx)
        return outputPath, psb

    @staticmethod
    def UnlinkToFile(inputPath: str, outputUnlinkedPsb: bool = True, order: Any = None, format: PsbImageFormat = PsbImageFormat.png) -> Optional[str]:
        if not os.path.exists(inputPath):
            return None
        name = os.path.splitext(os.path.basename(inputPath))[0]
        dirPath = os.path.join(os.path.dirname(inputPath), name)
        psbSavePath = inputPath
        if os.path.exists(dirPath):
            name += "-resources"
            dirPath += "-resources"
        if not os.path.exists(dirPath):
            os.makedirs(dirPath, exist_ok=True)
        context = FreeMount.CreateContext()
        context.ImageFormat = format
        psb = PSB(inputPath, PsbDecompiler.Encoding)
        psb.TypeHandler.UnlinkToFile(psb, context, name, dirPath, outputUnlinkedPsb, order)
        if outputUnlinkedPsb:
            psbSavePath = os.path.splitext(inputPath)[0] + ".unlinked.psb"
            with open(psbSavePath, "wb") as f:
                f.write(b"")
        return psbSavePath

    @staticmethod
    def ExtractImageFiles(inputPath: str, format: PsbImageFormat = PsbImageFormat.png) -> None:
        psb = PSB(inputPath, PsbDecompiler.Encoding)
        path = os.path.splitext(os.path.abspath(inputPath))[0]
        PsbDecompiler.OutputResources(psb, FreeMount.CreateContext(), path, PsbExtractOption.Extract, format)

    @staticmethod
    def ExtractArchive(filePath: str, key: str, context: Dict[str, object], bodyPath: Optional[str], outputRaw: bool, extractAll: bool, enableParallel: bool) -> None:
        if not os.path.exists(filePath):
            Logger.LogError(f"Cannot find input file: {filePath}")
            return
        fileName = os.path.basename(filePath)
        dir = os.path.dirname(filePath)
        archiveMdfKey = key + fileName
        name = fileName
        if not name:
            Logger.LogWarn(f"File name incorrect: {fileName}")
            name = fileName
        hasBody = False
        body = None
        bodyBinName = None
        if bodyPath:
            if not os.path.exists(bodyPath):
                if not os.path.isabs(bodyPath) and os.path.isabs(filePath):
                    bodyFullPath = os.path.join(os.path.dirname(filePath), bodyPath)
                    if os.path.exists(bodyFullPath):
                        body = bodyFullPath
                        hasBody = True
                        bodyBinName = os.path.basename(bodyPath)
                        Logger.Log(f"Body FilePath: {bodyFullPath}")
            else:
                body = bodyPath
                hasBody = True
                bodyBinName = os.path.basename(bodyPath)
                Logger.Log(f"Body FilePath: {bodyPath}")
            if not hasBody:
                Logger.LogWarn(f"Can not find body from specified path: {bodyPath}")
        else:
            possible = [f"{name}_body.bin", f"{name}body.bin", f"{name}.bin"]
            for possibleBodyName in possible:
                body_candidate = os.path.join(dir or "", possibleBodyName)
                if os.path.exists(body_candidate):
                    hasBody = True
                    body = body_candidate
                    bodyBinName = possibleBodyName
                    break
            if hasBody:
                Logger.Log(f"Assume Body FilePath: {body}")
            else:
                Logger.LogWarn(f"Can not find body (use `-b` to set body.bin path manually): {body} ")
        try:
            psb = None
            with open(filePath, "rb") as fs:
                shellType = PsbFile.GetSignatureShellType(fs)
                if shellType != "PSB":
                    try:
                        unpacked = PsbExtension.MdfConvert(fs, shellType, context)
                        psb = PSB(unpacked)
                    except Exception:
                        realName = fileName
                        if realName != fileName:
                            Logger.Log(f"Trying file name: {realName}")
                            archiveMdfKey = key + realName
                            context[Context_FileName] = realName
                            context[Context_MdfKey] = archiveMdfKey
                            fs.seek(0)
                            unpacked = PsbExtension.MdfConvert(fs, shellType, context)
                            psb = PSB(unpacked)
                        else:
                            raise
                else:
                    psb = PSB(fs)
            out_json = os.path.abspath(filePath) + ".json"
            with open(out_json, "w", encoding="utf-8") as f:
                f.write(PsbDecompiler.DecompilePsb(psb))
            resx = PsbResourceJson(psb, context)
            if not hasBody:
                context[Context_ArchiveSource] = [name]
                PsbDecompiler.OutputResources(psb, FreeMount.CreateContext(context), os.path.abspath(filePath), PsbExtractOption.Extract)
                return
            resx.PsbType = PsbType.ArchiveInfo
            extractDir = os.path.join(dir, name)
            if os.path.isfile(extractDir):
                name += "-resources"
                extractDir += "-resources"
            if not os.path.exists(extractDir):
                os.makedirs(extractDir, exist_ok=True)
            specialItemFileNames: List[str] = []
            resx.Context[Context_ArchiveSource] = [name]
            resx.Context[Context_MdfMtKey] = key
            resx.Context[Context_MdfKey] = archiveMdfKey
            resx.Context[Context_ArchiveItemFileNames] = specialItemFileNames
            resx.Context[Context_FileName] = fileName
            if bodyBinName:
                resx.Context[Context_BodyBinName] = bodyBinName
            with open(os.path.abspath(filePath) + ".resx.json", "w", encoding="utf-8") as f:
                f.write(resx.SerializeToJson())
        except Exception as e:
            Logger.LogError(e)

    @staticmethod
    def MtUnpack(filePath: str, outputPath: str, key: str, keyLength: int, fileKey: str = "", suffix: str = "") -> None:
        if not os.path.exists(filePath):
            Logger.LogError(f"Cannot find input file: {filePath}")
            return
        with open(filePath, "rb") as f:
            bodyBytes = f.read()
        _, shellType = MPack_IsSig(bodyBytes)
        fileName = os.path.basename(filePath)
        fileKey = fileKey or ""
        name = fileName if not fileKey else fileKey
        possibleFileNames = PsbExtension.ArchiveInfo_GetAllPossibleFileNames(name, suffix)
        finalContext: Dict[str, object] = {Context_MdfKeyLength: keyLength}
        ms = BytesIO(bodyBytes)
        mms = None
        if shellType and possibleFileNames:
            for possibleFileName in possibleFileNames:
                bodyContext = dict(finalContext)
                bodyContext[Context_MdfKey] = key + possibleFileName
                bodyContext[Context_FileName] = possibleFileName
                try:
                    mms = PsbExtension.MdfConvert(ms, shellType, bodyContext)
                except Exception:
                    ms.close()
                    mms = BytesIO(bodyBytes)
                if mms is not None:
                    out_path = outputPath if outputPath else os.path.splitext(filePath)[0] + ".unpack.psb"
                    with open(out_path, "wb") as outFs:
                        outFs.write(mms.getvalue())
                    mms.close()
                    break
        else:
            raise Exception("File is not a shell PSB.")
