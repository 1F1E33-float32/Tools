📦
137240 /hook.js
70458 /hook.js.map
✄
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// frida-builtins:/node-globals.js
var init_node_globals = __esm({
  "frida-builtins:/node-globals.js"() {
  }
});

// node_modules/frida-il2cpp-bridge/dist/index.js
var dist_exports = {};
function raise(message) {
  const error = new Error(message);
  error.name = "Il2CppError";
  error.stack = error.stack?.replace(/^(Il2Cpp)?Error/, "\x1B[0m\x1B[38;5;9mil2cpp\x1B[0m")?.replace(/\n    at (.+) \((.+):(.+)\)/, "\x1B[3m\x1B[2m")?.concat("\x1B[0m");
  throw error;
}
function warn(message) {
  globalThis.console.log(`\x1B[38;5;11mil2cpp\x1B[0m: ${message}`);
}
function ok(message) {
  globalThis.console.log(`\x1B[38;5;10mil2cpp\x1B[0m: ${message}`);
}
function inform(message) {
  globalThis.console.log(`\x1B[38;5;12mil2cpp\x1B[0m: ${message}`);
}
function decorate(target, decorator, descriptors = Object.getOwnPropertyDescriptors(target)) {
  for (const key in descriptors) {
    descriptors[key] = decorator(target, key, descriptors[key]);
  }
  Object.defineProperties(target, descriptors);
  return target;
}
function getter(target, key, get, decorator) {
  globalThis.Object.defineProperty(target, key, decorator?.(target, key, { get, configurable: true }) ?? { get, configurable: true });
}
function cyrb53(str) {
  let h1 = 3735928559;
  let h2 = 1103547991;
  for (let i = 0, ch; i < str.length; i++) {
    ch = str.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ h1 >>> 16, 2246822507);
  h1 ^= Math.imul(h2 ^ h2 >>> 13, 3266489909);
  h2 = Math.imul(h2 ^ h2 >>> 16, 2246822507);
  h2 ^= Math.imul(h1 ^ h1 >>> 13, 3266489909);
  return 4294967296 * (2097151 & h2) + (h1 >>> 0);
}
function exportsHash(module) {
  return cyrb53(module.enumerateExports().sort((a, b) => a.name.localeCompare(b.name)).map((_) => _.name + _.address.sub(module.base)).join(""));
}
function lazy(_, propertyKey, descriptor) {
  const getter2 = descriptor.get;
  if (!getter2) {
    throw new Error("@lazy can only be applied to getter accessors");
  }
  descriptor.get = function() {
    const value = getter2.call(this);
    Object.defineProperty(this, propertyKey, {
      value,
      configurable: descriptor.configurable,
      enumerable: descriptor.enumerable,
      writable: false
    });
    return value;
  };
  return descriptor;
}
function addFlippedEntries(obj) {
  return Object.keys(obj).reduce((obj2, key) => (obj2[obj2[key]] = key, obj2), obj);
}
function readNativeIterator(block) {
  const array = [];
  const iterator = Memory.alloc(Process.pointerSize);
  let handle = block(iterator);
  while (!handle.isNull()) {
    array.push(handle);
    handle = block(iterator);
  }
  return array;
}
function readNativeList(block) {
  const lengthPointer = Memory.alloc(Process.pointerSize);
  const startPointer = block(lengthPointer);
  if (startPointer.isNull()) {
    return [];
  }
  const array = new Array(lengthPointer.readInt());
  for (let i = 0; i < array.length; i++) {
    array[i] = startPointer.add(i * Process.pointerSize).readPointer();
  }
  return array;
}
function recycle(Class) {
  return new Proxy(Class, {
    cache: /* @__PURE__ */ new Map(),
    construct(Target, argArray) {
      const handle = argArray[0].toUInt32();
      if (!this.cache.has(handle)) {
        this.cache.set(handle, new Target(argArray[0]));
      }
      return this.cache.get(handle);
    }
  });
}
var __decorate, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Android, NativeStruct, UnityVersion, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2, Il2Cpp2;
var init_dist = __esm({
  "node_modules/frida-il2cpp-bridge/dist/index.js"() {
    "use strict";
    init_node_globals();
    __decorate = function(decorators, target, key, desc) {
      var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
      if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
      else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
      return c > 3 && r && Object.defineProperty(target, key, r), r;
    };
    (function(Il2Cpp3) {
      Il2Cpp3.application = {
        /**
         * Gets the data path name of the current application, e.g.
         * `/data/emulated/0/Android/data/com.example.application/files`
         * on Android.
         *
         * **This information is not guaranteed to exist.**
         *
         * ```ts
         * Il2Cpp.perform(() => {
         *     // prints /data/emulated/0/Android/data/com.example.application/files
         *     console.log(Il2Cpp.application.dataPath);
         * });
         * ```
         */
        get dataPath() {
          return unityEngineCall("get_persistentDataPath");
        },
        /**
         * Gets the identifier name of the current application, e.g.
         * `com.example.application` on Android.
         *
         * In case the identifier cannot be retrieved, the main module name is
         * returned instead, which typically is the process name.
         *
         * ```ts
         * Il2Cpp.perform(() => {
         *     // prints com.example.application
         *     console.log(Il2Cpp.application.identifier);
         * });
         * ```
         */
        get identifier() {
          return unityEngineCall("get_identifier") ?? unityEngineCall("get_bundleIdentifier") ?? Process.mainModule.name;
        },
        /**
         * Gets the version name of the current application, e.g. `4.12.8`.
         *
         * In case the version cannot be retrieved, an hash of the IL2CPP
         * module is returned instead.
         *
         * ```ts
         * Il2Cpp.perform(() => {
         *     // prints 4.12.8
         *     console.log(Il2Cpp.application.version);
         * });
         * ```
         */
        get version() {
          return unityEngineCall("get_version") ?? exportsHash(Il2Cpp3.module).toString(16);
        }
      };
      getter(Il2Cpp3, "unityVersion", () => {
        try {
          const unityVersion = Il2Cpp3.$config.unityVersion ?? unityEngineCall("get_unityVersion");
          if (unityVersion != null) {
            return unityVersion;
          }
        } catch (_) {
        }
        const searchPattern = "69 6c 32 63 70 70";
        for (const range of Il2Cpp3.module.enumerateRanges("r--").concat(Process.getRangeByAddress(Il2Cpp3.module.base))) {
          for (let { address } of Memory.scanSync(range.base, range.size, searchPattern)) {
            while (address.readU8() != 0) {
              address = address.sub(1);
            }
            const match = UnityVersion.find(address.add(1).readCString());
            if (match != void 0) {
              return match;
            }
          }
        }
        raise("couldn't determine the Unity version, please specify it manually");
      }, lazy);
      getter(Il2Cpp3, "unityVersionIsBelow201830", () => {
        return UnityVersion.lt(Il2Cpp3.unityVersion, "2018.3.0");
      }, lazy);
      getter(Il2Cpp3, "unityVersionIsBelow202120", () => {
        return UnityVersion.lt(Il2Cpp3.unityVersion, "2021.2.0");
      }, lazy);
      function unityEngineCall(method) {
        const handle = Il2Cpp3.exports.resolveInternalCall(Memory.allocUtf8String("UnityEngine.Application::" + method));
        const nativeFunction = new NativeFunction(handle, "pointer", []);
        return nativeFunction.isNull() ? null : new Il2Cpp3.String(nativeFunction()).asNullable()?.content ?? null;
      }
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      function boxed(value, type) {
        const mapping = {
          int8: "System.SByte",
          uint8: "System.Byte",
          int16: "System.Int16",
          uint16: "System.UInt16",
          int32: "System.Int32",
          uint32: "System.UInt32",
          int64: "System.Int64",
          uint64: "System.UInt64",
          char: "System.Char",
          intptr: "System.IntPtr",
          uintptr: "System.UIntPtr"
        };
        const className = typeof value == "boolean" ? "System.Boolean" : typeof value == "number" ? mapping[type ?? "int32"] : value instanceof Int64 ? "System.Int64" : value instanceof UInt64 ? "System.UInt64" : value instanceof NativePointer ? mapping[type ?? "intptr"] : raise(`Cannot create boxed primitive using value of type '${typeof value}'`);
        const object = Il2Cpp3.corlib.class(className ?? raise(`Unknown primitive type name '${type}'`)).alloc();
        (object.tryField("m_value") ?? object.tryField("_pointer") ?? raise(`Could not find primitive field in class '${className}'`)).value = value;
        return object;
      }
      Il2Cpp3.boxed = boxed;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      Il2Cpp3.$config = {
        moduleName: void 0,
        unityVersion: void 0,
        exports: void 0
      };
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      function dump(fileName, path) {
        fileName = fileName ?? `${Il2Cpp3.application.identifier}_${Il2Cpp3.application.version}.cs`;
        path = path ?? Il2Cpp3.application.dataPath ?? Process.getCurrentDir();
        createDirectoryRecursively(path);
        const destination = `${path}/${fileName}`;
        const file = new File(destination, "w");
        for (const assembly of Il2Cpp3.domain.assemblies) {
          inform(`dumping ${assembly.name}...`);
          for (const klass of assembly.image.classes) {
            file.write(`${klass}

`);
          }
        }
        file.flush();
        file.close();
        ok(`dump saved to ${destination}`);
        showDeprecationNotice();
      }
      Il2Cpp3.dump = dump;
      function dumpTree(path, ignoreAlreadyExistingDirectory = false) {
        path = path ?? `${Il2Cpp3.application.dataPath ?? Process.getCurrentDir()}/${Il2Cpp3.application.identifier}_${Il2Cpp3.application.version}`;
        if (!ignoreAlreadyExistingDirectory && directoryExists(path)) {
          raise(`directory ${path} already exists - pass ignoreAlreadyExistingDirectory = true to skip this check`);
        }
        for (const assembly of Il2Cpp3.domain.assemblies) {
          inform(`dumping ${assembly.name}...`);
          const destination = `${path}/${assembly.name.replaceAll(".", "/")}.cs`;
          createDirectoryRecursively(destination.substring(0, destination.lastIndexOf("/")));
          const file = new File(destination, "w");
          for (const klass of assembly.image.classes) {
            file.write(`${klass}

`);
          }
          file.flush();
          file.close();
        }
        ok(`dump saved to ${path}`);
        showDeprecationNotice();
      }
      Il2Cpp3.dumpTree = dumpTree;
      function directoryExists(path) {
        return Il2Cpp3.corlib.class("System.IO.Directory").method("Exists").invoke(Il2Cpp3.string(path));
      }
      function createDirectoryRecursively(path) {
        Il2Cpp3.corlib.class("System.IO.Directory").method("CreateDirectory").invoke(Il2Cpp3.string(path));
      }
      function showDeprecationNotice() {
        warn("this api will be removed in a future release, please use `npx frida-il2cpp-bridge dump` instead");
      }
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      function installExceptionListener(targetThread = "current") {
        const currentThread = Il2Cpp3.exports.threadGetCurrent();
        return Interceptor.attach(Il2Cpp3.module.getExportByName("__cxa_throw"), function(args) {
          if (targetThread == "current" && !Il2Cpp3.exports.threadGetCurrent().equals(currentThread)) {
            return;
          }
          inform(new Il2Cpp3.Object(args[0].readPointer()));
        });
      }
      Il2Cpp3.installExceptionListener = installExceptionListener;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      Il2Cpp3.exports = {
        get alloc() {
          return r("il2cpp_alloc", "pointer", ["size_t"]);
        },
        get arrayGetLength() {
          return r("il2cpp_array_length", "uint32", ["pointer"]);
        },
        get arrayNew() {
          return r("il2cpp_array_new", "pointer", ["pointer", "uint32"]);
        },
        get assemblyGetImage() {
          return r("il2cpp_assembly_get_image", "pointer", ["pointer"]);
        },
        get classForEach() {
          return r("il2cpp_class_for_each", "void", ["pointer", "pointer"]);
        },
        get classFromName() {
          return r("il2cpp_class_from_name", "pointer", ["pointer", "pointer", "pointer"]);
        },
        get classFromObject() {
          return r("il2cpp_class_from_system_type", "pointer", ["pointer"]);
        },
        get classGetArrayClass() {
          return r("il2cpp_array_class_get", "pointer", ["pointer", "uint32"]);
        },
        get classGetArrayElementSize() {
          return r("il2cpp_class_array_element_size", "int", ["pointer"]);
        },
        get classGetAssemblyName() {
          return r("il2cpp_class_get_assemblyname", "pointer", ["pointer"]);
        },
        get classGetBaseType() {
          return r("il2cpp_class_enum_basetype", "pointer", ["pointer"]);
        },
        get classGetDeclaringType() {
          return r("il2cpp_class_get_declaring_type", "pointer", ["pointer"]);
        },
        get classGetElementClass() {
          return r("il2cpp_class_get_element_class", "pointer", ["pointer"]);
        },
        get classGetFieldFromName() {
          return r("il2cpp_class_get_field_from_name", "pointer", ["pointer", "pointer"]);
        },
        get classGetFields() {
          return r("il2cpp_class_get_fields", "pointer", ["pointer", "pointer"]);
        },
        get classGetFlags() {
          return r("il2cpp_class_get_flags", "int", ["pointer"]);
        },
        get classGetImage() {
          return r("il2cpp_class_get_image", "pointer", ["pointer"]);
        },
        get classGetInstanceSize() {
          return r("il2cpp_class_instance_size", "int32", ["pointer"]);
        },
        get classGetInterfaces() {
          return r("il2cpp_class_get_interfaces", "pointer", ["pointer", "pointer"]);
        },
        get classGetMethodFromName() {
          return r("il2cpp_class_get_method_from_name", "pointer", ["pointer", "pointer", "int"]);
        },
        get classGetMethods() {
          return r("il2cpp_class_get_methods", "pointer", ["pointer", "pointer"]);
        },
        get classGetName() {
          return r("il2cpp_class_get_name", "pointer", ["pointer"]);
        },
        get classGetNamespace() {
          return r("il2cpp_class_get_namespace", "pointer", ["pointer"]);
        },
        get classGetNestedClasses() {
          return r("il2cpp_class_get_nested_types", "pointer", ["pointer", "pointer"]);
        },
        get classGetParent() {
          return r("il2cpp_class_get_parent", "pointer", ["pointer"]);
        },
        get classGetStaticFieldData() {
          return r("il2cpp_class_get_static_field_data", "pointer", ["pointer"]);
        },
        get classGetValueTypeSize() {
          return r("il2cpp_class_value_size", "int32", ["pointer", "pointer"]);
        },
        get classGetType() {
          return r("il2cpp_class_get_type", "pointer", ["pointer"]);
        },
        get classHasReferences() {
          return r("il2cpp_class_has_references", "bool", ["pointer"]);
        },
        get classInitialize() {
          return r("il2cpp_runtime_class_init", "void", ["pointer"]);
        },
        get classIsAbstract() {
          return r("il2cpp_class_is_abstract", "bool", ["pointer"]);
        },
        get classIsAssignableFrom() {
          return r("il2cpp_class_is_assignable_from", "bool", ["pointer", "pointer"]);
        },
        get classIsBlittable() {
          return r("il2cpp_class_is_blittable", "bool", ["pointer"]);
        },
        get classIsEnum() {
          return r("il2cpp_class_is_enum", "bool", ["pointer"]);
        },
        get classIsGeneric() {
          return r("il2cpp_class_is_generic", "bool", ["pointer"]);
        },
        get classIsInflated() {
          return r("il2cpp_class_is_inflated", "bool", ["pointer"]);
        },
        get classIsInterface() {
          return r("il2cpp_class_is_interface", "bool", ["pointer"]);
        },
        get classIsSubclassOf() {
          return r("il2cpp_class_is_subclass_of", "bool", ["pointer", "pointer", "bool"]);
        },
        get classIsValueType() {
          return r("il2cpp_class_is_valuetype", "bool", ["pointer"]);
        },
        get domainGetAssemblyFromName() {
          return r("il2cpp_domain_assembly_open", "pointer", ["pointer", "pointer"]);
        },
        get domainGet() {
          return r("il2cpp_domain_get", "pointer", []);
        },
        get domainGetAssemblies() {
          return r("il2cpp_domain_get_assemblies", "pointer", ["pointer", "pointer"]);
        },
        get fieldGetClass() {
          return r("il2cpp_field_get_parent", "pointer", ["pointer"]);
        },
        get fieldGetFlags() {
          return r("il2cpp_field_get_flags", "int", ["pointer"]);
        },
        get fieldGetName() {
          return r("il2cpp_field_get_name", "pointer", ["pointer"]);
        },
        get fieldGetOffset() {
          return r("il2cpp_field_get_offset", "int32", ["pointer"]);
        },
        get fieldGetStaticValue() {
          return r("il2cpp_field_static_get_value", "void", ["pointer", "pointer"]);
        },
        get fieldGetType() {
          return r("il2cpp_field_get_type", "pointer", ["pointer"]);
        },
        get fieldSetStaticValue() {
          return r("il2cpp_field_static_set_value", "void", ["pointer", "pointer"]);
        },
        get free() {
          return r("il2cpp_free", "void", ["pointer"]);
        },
        get gcCollect() {
          return r("il2cpp_gc_collect", "void", ["int"]);
        },
        get gcCollectALittle() {
          return r("il2cpp_gc_collect_a_little", "void", []);
        },
        get gcDisable() {
          return r("il2cpp_gc_disable", "void", []);
        },
        get gcEnable() {
          return r("il2cpp_gc_enable", "void", []);
        },
        get gcGetHeapSize() {
          return r("il2cpp_gc_get_heap_size", "int64", []);
        },
        get gcGetMaxTimeSlice() {
          return r("il2cpp_gc_get_max_time_slice_ns", "int64", []);
        },
        get gcGetUsedSize() {
          return r("il2cpp_gc_get_used_size", "int64", []);
        },
        get gcHandleGetTarget() {
          return r("il2cpp_gchandle_get_target", "pointer", ["uint32"]);
        },
        get gcHandleFree() {
          return r("il2cpp_gchandle_free", "void", ["uint32"]);
        },
        get gcHandleNew() {
          return r("il2cpp_gchandle_new", "uint32", ["pointer", "bool"]);
        },
        get gcHandleNewWeakRef() {
          return r("il2cpp_gchandle_new_weakref", "uint32", ["pointer", "bool"]);
        },
        get gcIsDisabled() {
          return r("il2cpp_gc_is_disabled", "bool", []);
        },
        get gcIsIncremental() {
          return r("il2cpp_gc_is_incremental", "bool", []);
        },
        get gcSetMaxTimeSlice() {
          return r("il2cpp_gc_set_max_time_slice_ns", "void", ["int64"]);
        },
        get gcStartIncrementalCollection() {
          return r("il2cpp_gc_start_incremental_collection", "void", []);
        },
        get gcStartWorld() {
          return r("il2cpp_start_gc_world", "void", []);
        },
        get gcStopWorld() {
          return r("il2cpp_stop_gc_world", "void", []);
        },
        get getCorlib() {
          return r("il2cpp_get_corlib", "pointer", []);
        },
        get imageGetAssembly() {
          return r("il2cpp_image_get_assembly", "pointer", ["pointer"]);
        },
        get imageGetClass() {
          return r("il2cpp_image_get_class", "pointer", ["pointer", "uint"]);
        },
        get imageGetClassCount() {
          return r("il2cpp_image_get_class_count", "uint32", ["pointer"]);
        },
        get imageGetName() {
          return r("il2cpp_image_get_name", "pointer", ["pointer"]);
        },
        get initialize() {
          return r("il2cpp_init", "void", ["pointer"]);
        },
        get livenessAllocateStruct() {
          return r("il2cpp_unity_liveness_allocate_struct", "pointer", ["pointer", "int", "pointer", "pointer", "pointer"]);
        },
        get livenessCalculationBegin() {
          return r("il2cpp_unity_liveness_calculation_begin", "pointer", ["pointer", "int", "pointer", "pointer", "pointer", "pointer"]);
        },
        get livenessCalculationEnd() {
          return r("il2cpp_unity_liveness_calculation_end", "void", ["pointer"]);
        },
        get livenessCalculationFromStatics() {
          return r("il2cpp_unity_liveness_calculation_from_statics", "void", ["pointer"]);
        },
        get livenessFinalize() {
          return r("il2cpp_unity_liveness_finalize", "void", ["pointer"]);
        },
        get livenessFreeStruct() {
          return r("il2cpp_unity_liveness_free_struct", "void", ["pointer"]);
        },
        get memorySnapshotCapture() {
          return r("il2cpp_capture_memory_snapshot", "pointer", []);
        },
        get memorySnapshotFree() {
          return r("il2cpp_free_captured_memory_snapshot", "void", ["pointer"]);
        },
        get memorySnapshotGetClasses() {
          return r("il2cpp_memory_snapshot_get_classes", "pointer", ["pointer", "pointer"]);
        },
        get memorySnapshotGetObjects() {
          return r("il2cpp_memory_snapshot_get_objects", "pointer", ["pointer", "pointer"]);
        },
        get methodGetClass() {
          return r("il2cpp_method_get_class", "pointer", ["pointer"]);
        },
        get methodGetFlags() {
          return r("il2cpp_method_get_flags", "uint32", ["pointer", "pointer"]);
        },
        get methodGetName() {
          return r("il2cpp_method_get_name", "pointer", ["pointer"]);
        },
        get methodGetObject() {
          return r("il2cpp_method_get_object", "pointer", ["pointer", "pointer"]);
        },
        get methodGetParameterCount() {
          return r("il2cpp_method_get_param_count", "uint8", ["pointer"]);
        },
        get methodGetParameterName() {
          return r("il2cpp_method_get_param_name", "pointer", ["pointer", "uint32"]);
        },
        get methodGetParameters() {
          return r("il2cpp_method_get_parameters", "pointer", ["pointer", "pointer"]);
        },
        get methodGetParameterType() {
          return r("il2cpp_method_get_param", "pointer", ["pointer", "uint32"]);
        },
        get methodGetReturnType() {
          return r("il2cpp_method_get_return_type", "pointer", ["pointer"]);
        },
        get methodIsGeneric() {
          return r("il2cpp_method_is_generic", "bool", ["pointer"]);
        },
        get methodIsInflated() {
          return r("il2cpp_method_is_inflated", "bool", ["pointer"]);
        },
        get methodIsInstance() {
          return r("il2cpp_method_is_instance", "bool", ["pointer"]);
        },
        get monitorEnter() {
          return r("il2cpp_monitor_enter", "void", ["pointer"]);
        },
        get monitorExit() {
          return r("il2cpp_monitor_exit", "void", ["pointer"]);
        },
        get monitorPulse() {
          return r("il2cpp_monitor_pulse", "void", ["pointer"]);
        },
        get monitorPulseAll() {
          return r("il2cpp_monitor_pulse_all", "void", ["pointer"]);
        },
        get monitorTryEnter() {
          return r("il2cpp_monitor_try_enter", "bool", ["pointer", "uint32"]);
        },
        get monitorTryWait() {
          return r("il2cpp_monitor_try_wait", "bool", ["pointer", "uint32"]);
        },
        get monitorWait() {
          return r("il2cpp_monitor_wait", "void", ["pointer"]);
        },
        get objectGetClass() {
          return r("il2cpp_object_get_class", "pointer", ["pointer"]);
        },
        get objectGetVirtualMethod() {
          return r("il2cpp_object_get_virtual_method", "pointer", ["pointer", "pointer"]);
        },
        get objectInitialize() {
          return r("il2cpp_runtime_object_init_exception", "void", ["pointer", "pointer"]);
        },
        get objectNew() {
          return r("il2cpp_object_new", "pointer", ["pointer"]);
        },
        get objectGetSize() {
          return r("il2cpp_object_get_size", "uint32", ["pointer"]);
        },
        get objectUnbox() {
          return r("il2cpp_object_unbox", "pointer", ["pointer"]);
        },
        get resolveInternalCall() {
          return r("il2cpp_resolve_icall", "pointer", ["pointer"]);
        },
        get stringGetChars() {
          return r("il2cpp_string_chars", "pointer", ["pointer"]);
        },
        get stringGetLength() {
          return r("il2cpp_string_length", "int32", ["pointer"]);
        },
        get stringNew() {
          return r("il2cpp_string_new", "pointer", ["pointer"]);
        },
        get valueTypeBox() {
          return r("il2cpp_value_box", "pointer", ["pointer", "pointer"]);
        },
        get threadAttach() {
          return r("il2cpp_thread_attach", "pointer", ["pointer"]);
        },
        get threadDetach() {
          return r("il2cpp_thread_detach", "void", ["pointer"]);
        },
        get threadGetAttachedThreads() {
          return r("il2cpp_thread_get_all_attached_threads", "pointer", ["pointer"]);
        },
        get threadGetCurrent() {
          return r("il2cpp_thread_current", "pointer", []);
        },
        get threadIsVm() {
          return r("il2cpp_is_vm_thread", "bool", ["pointer"]);
        },
        get typeEquals() {
          return r("il2cpp_type_equals", "bool", ["pointer", "pointer"]);
        },
        get typeGetClass() {
          return r("il2cpp_class_from_type", "pointer", ["pointer"]);
        },
        get typeGetName() {
          return r("il2cpp_type_get_name", "pointer", ["pointer"]);
        },
        get typeGetObject() {
          return r("il2cpp_type_get_object", "pointer", ["pointer"]);
        },
        get typeGetTypeEnum() {
          return r("il2cpp_type_get_type", "int", ["pointer"]);
        }
      };
      decorate(Il2Cpp3.exports, lazy);
      getter(Il2Cpp3, "memorySnapshotExports", () => new CModule("#include <stdint.h>\n#include <string.h>\n\ntypedef struct Il2CppManagedMemorySnapshot Il2CppManagedMemorySnapshot;\ntypedef struct Il2CppMetadataType Il2CppMetadataType;\n\nstruct Il2CppManagedMemorySnapshot\n{\n  struct Il2CppManagedHeap\n  {\n    uint32_t section_count;\n    void * sections;\n  } heap;\n  struct Il2CppStacks\n  {\n    uint32_t stack_count;\n    void * stacks;\n  } stacks;\n  struct Il2CppMetadataSnapshot\n  {\n    uint32_t type_count;\n    Il2CppMetadataType * types;\n  } metadata_snapshot;\n  struct Il2CppGCHandles\n  {\n    uint32_t tracked_object_count;\n    void ** pointers_to_objects;\n  } gc_handles;\n  struct Il2CppRuntimeInformation\n  {\n    uint32_t pointer_size;\n    uint32_t object_header_size;\n    uint32_t array_header_size;\n    uint32_t array_bounds_offset_in_header;\n    uint32_t array_size_offset_in_header;\n    uint32_t allocation_granularity;\n  } runtime_information;\n  void * additional_user_information;\n};\n\nstruct Il2CppMetadataType\n{\n  uint32_t flags;\n  void * fields;\n  uint32_t field_count;\n  uint32_t statics_size;\n  uint8_t * statics;\n  uint32_t base_or_element_type_index;\n  char * name;\n  const char * assembly_name;\n  uint64_t type_info_address;\n  uint32_t size;\n};\n\nuintptr_t\nil2cpp_memory_snapshot_get_classes (\n    const Il2CppManagedMemorySnapshot * snapshot, Il2CppMetadataType ** iter)\n{\n  const int zero = 0;\n  const void * null = 0;\n\n  if (iter != NULL && snapshot->metadata_snapshot.type_count > zero)\n  {\n    if (*iter == null)\n    {\n      *iter = snapshot->metadata_snapshot.types;\n      return (uintptr_t) (*iter)->type_info_address;\n    }\n    else\n    {\n      Il2CppMetadataType * metadata_type = *iter + 1;\n\n      if (metadata_type < snapshot->metadata_snapshot.types +\n                              snapshot->metadata_snapshot.type_count)\n      {\n        *iter = metadata_type;\n        return (uintptr_t) (*iter)->type_info_address;\n      }\n    }\n  }\n  return 0;\n}\n\nvoid **\nil2cpp_memory_snapshot_get_objects (\n    const Il2CppManagedMemorySnapshot * snapshot, uint32_t * size)\n{\n  *size = snapshot->gc_handles.tracked_object_count;\n  return snapshot->gc_handles.pointers_to_objects;\n}\n"), lazy);
      function r(exportName, retType, argTypes) {
        const handle = Il2Cpp3.$config.exports?.[exportName]?.() ?? Il2Cpp3.module.findExportByName(exportName) ?? Il2Cpp3.memorySnapshotExports[exportName];
        const target = new NativeFunction(handle ?? NULL, retType, argTypes);
        return target.isNull() ? new Proxy(target, {
          get(value, name) {
            const property = value[name];
            return typeof property === "function" ? property.bind(value) : property;
          },
          apply() {
            if (handle == null) {
              raise(`couldn't resolve export ${exportName}`);
            } else if (handle.isNull()) {
              raise(`export ${exportName} points to NULL IL2CPP library has likely been stripped, obfuscated, or customized`);
            }
          }
        }) : target;
      }
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      function is(klass) {
        return (element) => {
          if (element instanceof Il2Cpp3.Class) {
            return klass.isAssignableFrom(element);
          } else {
            return klass.isAssignableFrom(element.class);
          }
        };
      }
      Il2Cpp3.is = is;
      function isExactly(klass) {
        return (element) => {
          if (element instanceof Il2Cpp3.Class) {
            return element.equals(klass);
          } else {
            return element.class.equals(klass);
          }
        };
      }
      Il2Cpp3.isExactly = isExactly;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      Il2Cpp3.gc = {
        /**
         * Gets the heap size in bytes.
         */
        get heapSize() {
          return Il2Cpp3.exports.gcGetHeapSize();
        },
        /**
         * Determines whether the garbage collector is enabled.
         */
        get isEnabled() {
          return !Il2Cpp3.exports.gcIsDisabled();
        },
        /**
         * Determines whether the garbage collector is incremental
         * ([source](https://docs.unity3d.com/Manual/performance-incremental-garbage-collection.html)).
         */
        get isIncremental() {
          return !!Il2Cpp3.exports.gcIsIncremental();
        },
        /**
         * Gets the number of nanoseconds the garbage collector can spend in a
         * collection step.
         */
        get maxTimeSlice() {
          return Il2Cpp3.exports.gcGetMaxTimeSlice();
        },
        /**
         * Gets the used heap size in bytes.
         */
        get usedHeapSize() {
          return Il2Cpp3.exports.gcGetUsedSize();
        },
        /**
         * Enables or disables the garbage collector.
         */
        set isEnabled(value) {
          value ? Il2Cpp3.exports.gcEnable() : Il2Cpp3.exports.gcDisable();
        },
        /**
         *  Sets the number of nanoseconds the garbage collector can spend in
         * a collection step.
         */
        set maxTimeSlice(nanoseconds) {
          Il2Cpp3.exports.gcSetMaxTimeSlice(nanoseconds);
        },
        /**
         * Returns the heap allocated objects of the specified class. \
         * This variant reads GC descriptors.
         */
        choose(klass) {
          const matches = [];
          const callback = (objects, size) => {
            for (let i = 0; i < size; i++) {
              matches.push(new Il2Cpp3.Object(objects.add(i * Process.pointerSize).readPointer()));
            }
          };
          const chooseCallback = new NativeCallback(callback, "void", ["pointer", "int", "pointer"]);
          if (Il2Cpp3.unityVersionIsBelow202120) {
            const onWorld = new NativeCallback(() => {
            }, "void", []);
            const state = Il2Cpp3.exports.livenessCalculationBegin(klass, 0, chooseCallback, NULL, onWorld, onWorld);
            Il2Cpp3.exports.livenessCalculationFromStatics(state);
            Il2Cpp3.exports.livenessCalculationEnd(state);
          } else {
            const realloc = (handle, size) => {
              if (!handle.isNull() && size.compare(0) == 0) {
                Il2Cpp3.free(handle);
                return NULL;
              } else {
                return Il2Cpp3.alloc(size);
              }
            };
            const reallocCallback = new NativeCallback(realloc, "pointer", ["pointer", "size_t", "pointer"]);
            this.stopWorld();
            const state = Il2Cpp3.exports.livenessAllocateStruct(klass, 0, chooseCallback, NULL, reallocCallback);
            Il2Cpp3.exports.livenessCalculationFromStatics(state);
            Il2Cpp3.exports.livenessFinalize(state);
            this.startWorld();
            Il2Cpp3.exports.livenessFreeStruct(state);
          }
          return matches;
        },
        /**
         * Forces a garbage collection of the specified generation.
         */
        collect(generation) {
          Il2Cpp3.exports.gcCollect(generation < 0 ? 0 : generation > 2 ? 2 : generation);
        },
        /**
         * Forces a garbage collection.
         */
        collectALittle() {
          Il2Cpp3.exports.gcCollectALittle();
        },
        /**
         *  Resumes all the previously stopped threads.
         */
        startWorld() {
          return Il2Cpp3.exports.gcStartWorld();
        },
        /**
         * Performs an incremental garbage collection.
         */
        startIncrementalCollection() {
          return Il2Cpp3.exports.gcStartIncrementalCollection();
        },
        /**
         * Stops all threads which may access the garbage collected heap, other
         * than the caller.
         */
        stopWorld() {
          return Il2Cpp3.exports.gcStopWorld();
        }
      };
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Android2) {
      getter(Android2, "apiLevel", () => {
        const value = getProperty("ro.build.version.sdk");
        return value ? parseInt(value) : null;
      }, lazy);
      function getProperty(name) {
        const handle = Process.findModuleByName("libc.so")?.findExportByName("__system_property_get");
        if (handle) {
          const __system_property_get = new NativeFunction(handle, "void", ["pointer", "pointer"]);
          const value = Memory.alloc(92).writePointer(NULL);
          __system_property_get(Memory.allocUtf8String(name), value);
          return value.readCString() ?? void 0;
        }
      }
    })(Android || (Android = {}));
    NativeStruct = class {
      handle;
      constructor(handleOrWrapper) {
        if (handleOrWrapper instanceof NativePointer) {
          this.handle = handleOrWrapper;
        } else {
          this.handle = handleOrWrapper.handle;
        }
      }
      equals(other) {
        return this.handle.equals(other.handle);
      }
      isNull() {
        return this.handle.isNull();
      }
      asNullable() {
        return this.isNull() ? null : this;
      }
    };
    NativePointer.prototype.offsetOf = function(condition, depth) {
      depth ??= 512;
      for (let i = 0; depth > 0 ? i < depth : i < -depth; i++) {
        if (condition(depth > 0 ? this.add(i) : this.sub(i))) {
          return i;
        }
      }
      return null;
    };
    (function(UnityVersion2) {
      const pattern = /(6\d{3}|20\d{2}|\d)\.(\d)\.(\d{1,2})(?:[abcfp]|rc){0,2}\d?/;
      function find(string) {
        return string?.match(pattern)?.[0];
      }
      UnityVersion2.find = find;
      function gte(a, b) {
        return compare(a, b) >= 0;
      }
      UnityVersion2.gte = gte;
      function lt(a, b) {
        return compare(a, b) < 0;
      }
      UnityVersion2.lt = lt;
      function compare(a, b) {
        const aMatches = a.match(pattern);
        const bMatches = b.match(pattern);
        for (let i = 1; i <= 3; i++) {
          const a2 = Number(aMatches?.[i] ?? -1);
          const b2 = Number(bMatches?.[i] ?? -1);
          if (a2 > b2)
            return 1;
          else if (a2 < b2)
            return -1;
        }
        return 0;
      }
    })(UnityVersion || (UnityVersion = {}));
    (function(Il2Cpp3) {
      function alloc(size = Process.pointerSize) {
        return Il2Cpp3.exports.alloc(size);
      }
      Il2Cpp3.alloc = alloc;
      function free(pointer) {
        return Il2Cpp3.exports.free(pointer);
      }
      Il2Cpp3.free = free;
      function read(pointer, type) {
        switch (type.enumValue) {
          case Il2Cpp3.Type.Enum.BOOLEAN:
            return !!pointer.readS8();
          case Il2Cpp3.Type.Enum.BYTE:
            return pointer.readS8();
          case Il2Cpp3.Type.Enum.UBYTE:
            return pointer.readU8();
          case Il2Cpp3.Type.Enum.SHORT:
            return pointer.readS16();
          case Il2Cpp3.Type.Enum.USHORT:
            return pointer.readU16();
          case Il2Cpp3.Type.Enum.INT:
            return pointer.readS32();
          case Il2Cpp3.Type.Enum.UINT:
            return pointer.readU32();
          case Il2Cpp3.Type.Enum.CHAR:
            return pointer.readU16();
          case Il2Cpp3.Type.Enum.LONG:
            return pointer.readS64();
          case Il2Cpp3.Type.Enum.ULONG:
            return pointer.readU64();
          case Il2Cpp3.Type.Enum.FLOAT:
            return pointer.readFloat();
          case Il2Cpp3.Type.Enum.DOUBLE:
            return pointer.readDouble();
          case Il2Cpp3.Type.Enum.NINT:
          case Il2Cpp3.Type.Enum.NUINT:
            return pointer.readPointer();
          case Il2Cpp3.Type.Enum.POINTER:
            return new Il2Cpp3.Pointer(pointer.readPointer(), type.class.baseType);
          case Il2Cpp3.Type.Enum.VALUE_TYPE:
            return new Il2Cpp3.ValueType(pointer, type);
          case Il2Cpp3.Type.Enum.OBJECT:
          case Il2Cpp3.Type.Enum.CLASS:
            return new Il2Cpp3.Object(pointer.readPointer());
          case Il2Cpp3.Type.Enum.GENERIC_INSTANCE:
            return type.class.isValueType ? new Il2Cpp3.ValueType(pointer, type) : new Il2Cpp3.Object(pointer.readPointer());
          case Il2Cpp3.Type.Enum.STRING:
            return new Il2Cpp3.String(pointer.readPointer());
          case Il2Cpp3.Type.Enum.ARRAY:
          case Il2Cpp3.Type.Enum.NARRAY:
            return new Il2Cpp3.Array(pointer.readPointer());
        }
        raise(`couldn't read the value from ${pointer} using an unhandled or unknown type ${type.name} (${type.enumValue}), please file an issue`);
      }
      Il2Cpp3.read = read;
      function write(pointer, value, type) {
        switch (type.enumValue) {
          case Il2Cpp3.Type.Enum.BOOLEAN:
            return pointer.writeS8(+value);
          case Il2Cpp3.Type.Enum.BYTE:
            return pointer.writeS8(value);
          case Il2Cpp3.Type.Enum.UBYTE:
            return pointer.writeU8(value);
          case Il2Cpp3.Type.Enum.SHORT:
            return pointer.writeS16(value);
          case Il2Cpp3.Type.Enum.USHORT:
            return pointer.writeU16(value);
          case Il2Cpp3.Type.Enum.INT:
            return pointer.writeS32(value);
          case Il2Cpp3.Type.Enum.UINT:
            return pointer.writeU32(value);
          case Il2Cpp3.Type.Enum.CHAR:
            return pointer.writeU16(value);
          case Il2Cpp3.Type.Enum.LONG:
            return pointer.writeS64(value);
          case Il2Cpp3.Type.Enum.ULONG:
            return pointer.writeU64(value);
          case Il2Cpp3.Type.Enum.FLOAT:
            return pointer.writeFloat(value);
          case Il2Cpp3.Type.Enum.DOUBLE:
            return pointer.writeDouble(value);
          case Il2Cpp3.Type.Enum.NINT:
          case Il2Cpp3.Type.Enum.NUINT:
          case Il2Cpp3.Type.Enum.POINTER:
          case Il2Cpp3.Type.Enum.STRING:
          case Il2Cpp3.Type.Enum.ARRAY:
          case Il2Cpp3.Type.Enum.NARRAY:
            return pointer.writePointer(value);
          case Il2Cpp3.Type.Enum.VALUE_TYPE:
            return Memory.copy(pointer, value, type.class.valueTypeSize), pointer;
          case Il2Cpp3.Type.Enum.OBJECT:
          case Il2Cpp3.Type.Enum.CLASS:
          case Il2Cpp3.Type.Enum.GENERIC_INSTANCE:
            return value instanceof Il2Cpp3.ValueType ? (Memory.copy(pointer, value, type.class.valueTypeSize), pointer) : pointer.writePointer(value);
        }
        raise(`couldn't write value ${value} to ${pointer} using an unhandled or unknown type ${type.name} (${type.enumValue}), please file an issue`);
      }
      Il2Cpp3.write = write;
      function fromFridaValue(value, type) {
        if (globalThis.Array.isArray(value)) {
          const handle = Memory.alloc(type.class.valueTypeSize);
          const fields = type.class.fields.filter((_) => !_.isStatic);
          for (let i = 0; i < fields.length; i++) {
            const convertedValue = fromFridaValue(value[i], fields[i].type);
            write(handle.add(fields[i].offset).sub(Il2Cpp3.Object.headerSize), convertedValue, fields[i].type);
          }
          return new Il2Cpp3.ValueType(handle, type);
        } else if (value instanceof NativePointer) {
          if (type.isByReference) {
            return new Il2Cpp3.Reference(value, type);
          }
          switch (type.enumValue) {
            case Il2Cpp3.Type.Enum.POINTER:
              return new Il2Cpp3.Pointer(value, type.class.baseType);
            case Il2Cpp3.Type.Enum.STRING:
              return new Il2Cpp3.String(value);
            case Il2Cpp3.Type.Enum.CLASS:
            case Il2Cpp3.Type.Enum.GENERIC_INSTANCE:
            case Il2Cpp3.Type.Enum.OBJECT:
              return new Il2Cpp3.Object(value);
            case Il2Cpp3.Type.Enum.ARRAY:
            case Il2Cpp3.Type.Enum.NARRAY:
              return new Il2Cpp3.Array(value);
            default:
              return value;
          }
        } else if (type.enumValue == Il2Cpp3.Type.Enum.BOOLEAN) {
          return !!value;
        } else if (type.enumValue == Il2Cpp3.Type.Enum.VALUE_TYPE && type.class.isEnum) {
          return fromFridaValue([value], type);
        } else {
          return value;
        }
      }
      Il2Cpp3.fromFridaValue = fromFridaValue;
      function toFridaValue(value) {
        if (typeof value == "boolean") {
          return +value;
        } else if (value instanceof Il2Cpp3.ValueType) {
          if (value.type.class.isEnum) {
            return value.field("value__").value;
          } else {
            const _ = value.type.class.fields.filter((_2) => !_2.isStatic).map((_2) => toFridaValue(_2.bind(value).value));
            return _.length == 0 ? [0] : _;
          }
        } else {
          return value;
        }
      }
      Il2Cpp3.toFridaValue = toFridaValue;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      getter(Il2Cpp3, "module", () => {
        return tryModule() ?? raise("Could not find IL2CPP module");
      });
      async function initialize(blocking = false) {
        const module = tryModule() ?? await new Promise((resolve) => {
          const [moduleName, fallbackModuleName] = getExpectedModuleNames();
          const timeout = setTimeout(() => {
            warn(`after 10 seconds, IL2CPP module '${moduleName}' has not been loaded yet, is the app running?`);
          }, 1e4);
          const moduleObserver = Process.attachModuleObserver({
            onAdded(module2) {
              if (module2.name == moduleName || fallbackModuleName && module2.name == fallbackModuleName) {
                clearTimeout(timeout);
                setImmediate(() => {
                  resolve(module2);
                  moduleObserver.detach();
                });
              }
            }
          });
        });
        Reflect.defineProperty(Il2Cpp3, "module", { value: module });
        if (Il2Cpp3.exports.getCorlib().isNull()) {
          return await new Promise((resolve) => {
            const interceptor = Interceptor.attach(Il2Cpp3.exports.initialize, {
              onLeave() {
                interceptor.detach();
                blocking ? resolve(true) : setImmediate(() => resolve(false));
              }
            });
          });
        }
        return false;
      }
      Il2Cpp3.initialize = initialize;
      function tryModule() {
        const [moduleName, fallback] = getExpectedModuleNames();
        return Process.findModuleByName(moduleName) ?? Process.findModuleByName(fallback ?? moduleName) ?? (Process.platform == "darwin" ? Process.findModuleByAddress(DebugSymbol.fromName("il2cpp_init").address) : void 0) ?? void 0;
      }
      function getExpectedModuleNames() {
        if (Il2Cpp3.$config.moduleName) {
          return [Il2Cpp3.$config.moduleName];
        }
        switch (Process.platform) {
          case "linux":
            return [Android.apiLevel ? "libil2cpp.so" : "GameAssembly.so"];
          case "windows":
            return ["GameAssembly.dll"];
          case "darwin":
            return ["UnityFramework", "GameAssembly.dylib"];
        }
        raise(`${Process.platform} is not supported yet`);
      }
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      async function perform(block, flag = "bind") {
        let attachedThread = null;
        try {
          const isInMainThread = await Il2Cpp3.initialize(flag == "main");
          if (flag == "main" && !isInMainThread) {
            return perform(() => Il2Cpp3.mainThread.schedule(block), "free");
          }
          if (Il2Cpp3.currentThread == null) {
            attachedThread = Il2Cpp3.domain.attach();
          }
          if (flag == "bind" && attachedThread != null) {
            Script.bindWeak(globalThis, () => attachedThread?.detach());
          }
          const result = block();
          return result instanceof Promise ? await result : result;
        } catch (error) {
          Script.nextTick((_) => {
            throw _;
          }, error);
          return Promise.reject(error);
        } finally {
          if (flag == "free" && attachedThread != null) {
            attachedThread.detach();
          }
        }
      }
      Il2Cpp3.perform = perform;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Tracer {
        /** @internal */
        #state = {
          depth: 0,
          buffer: [],
          history: /* @__PURE__ */ new Set(),
          flush: () => {
            if (this.#state.depth == 0) {
              const message = `
${this.#state.buffer.join("\n")}
`;
              if (this.#verbose) {
                inform(message);
              } else {
                const hash = cyrb53(message);
                if (!this.#state.history.has(hash)) {
                  this.#state.history.add(hash);
                  inform(message);
                }
              }
              this.#state.buffer.length = 0;
            }
          }
        };
        /** @internal */
        #threadId = Il2Cpp3.mainThread.id;
        /** @internal */
        #verbose = false;
        /** @internal */
        #applier;
        /** @internal */
        #targets = [];
        /** @internal */
        #domain;
        /** @internal */
        #assemblies;
        /** @internal */
        #classes;
        /** @internal */
        #methods;
        /** @internal */
        #assemblyFilter;
        /** @internal */
        #classFilter;
        /** @internal */
        #methodFilter;
        /** @internal */
        #parameterFilter;
        constructor(applier) {
          this.#applier = applier;
        }
        /** */
        thread(thread) {
          this.#threadId = thread.id;
          return this;
        }
        /** Determines whether print duplicate logs. */
        verbose(value) {
          this.#verbose = value;
          return this;
        }
        /** Sets the application domain as the place where to find the target methods. */
        domain() {
          this.#domain = Il2Cpp3.domain;
          return this;
        }
        /** Sets the passed `assemblies` as the place where to find the target methods. */
        assemblies(...assemblies) {
          this.#assemblies = assemblies;
          return this;
        }
        /** Sets the passed `classes` as the place where to find the target methods. */
        classes(...classes) {
          this.#classes = classes;
          return this;
        }
        /** Sets the passed `methods` as the target methods. */
        methods(...methods) {
          this.#methods = methods;
          return this;
        }
        /** Filters the assemblies where to find the target methods. */
        filterAssemblies(filter) {
          this.#assemblyFilter = filter;
          return this;
        }
        /** Filters the classes where to find the target methods. */
        filterClasses(filter) {
          this.#classFilter = filter;
          return this;
        }
        /** Filters the target methods. */
        filterMethods(filter) {
          this.#methodFilter = filter;
          return this;
        }
        /** Filters the target methods. */
        filterParameters(filter) {
          this.#parameterFilter = filter;
          return this;
        }
        /** Commits the current changes by finding the target methods. */
        and() {
          const filterMethod = (method) => {
            if (this.#parameterFilter == void 0) {
              this.#targets.push(method);
              return;
            }
            for (const parameter of method.parameters) {
              if (this.#parameterFilter(parameter)) {
                this.#targets.push(method);
                break;
              }
            }
          };
          const filterMethods = (values) => {
            for (const method of values) {
              filterMethod(method);
            }
          };
          const filterClass = (klass) => {
            if (this.#methodFilter == void 0) {
              filterMethods(klass.methods);
              return;
            }
            for (const method of klass.methods) {
              if (this.#methodFilter(method)) {
                filterMethod(method);
              }
            }
          };
          const filterClasses = (values) => {
            for (const klass of values) {
              filterClass(klass);
            }
          };
          const filterAssembly = (assembly) => {
            if (this.#classFilter == void 0) {
              filterClasses(assembly.image.classes);
              return;
            }
            for (const klass of assembly.image.classes) {
              if (this.#classFilter(klass)) {
                filterClass(klass);
              }
            }
          };
          const filterAssemblies = (assemblies) => {
            for (const assembly of assemblies) {
              filterAssembly(assembly);
            }
          };
          const filterDomain = (domain) => {
            if (this.#assemblyFilter == void 0) {
              filterAssemblies(domain.assemblies);
              return;
            }
            for (const assembly of domain.assemblies) {
              if (this.#assemblyFilter(assembly)) {
                filterAssembly(assembly);
              }
            }
          };
          this.#methods ? filterMethods(this.#methods) : this.#classes ? filterClasses(this.#classes) : this.#assemblies ? filterAssemblies(this.#assemblies) : this.#domain ? filterDomain(this.#domain) : void 0;
          this.#assemblies = void 0;
          this.#classes = void 0;
          this.#methods = void 0;
          this.#assemblyFilter = void 0;
          this.#classFilter = void 0;
          this.#methodFilter = void 0;
          this.#parameterFilter = void 0;
          return this;
        }
        /** Starts tracing. */
        attach() {
          for (const target of this.#targets) {
            if (!target.virtualAddress.isNull()) {
              try {
                this.#applier(target, this.#state, this.#threadId);
              } catch (e) {
                switch (e.message) {
                  case /unable to intercept function at \w+; please file a bug/.exec(e.message)?.input:
                  case "already replaced this function":
                    break;
                  default:
                    throw e;
                }
              }
            }
          }
        }
      }
      Il2Cpp3.Tracer = Tracer;
      function trace(parameters = false) {
        const applier = () => (method, state, threadId) => {
          const paddedVirtualAddress = method.relativeVirtualAddress.toString(16).padStart(8, "0");
          Interceptor.attach(method.virtualAddress, {
            onEnter() {
              if (this.threadId == threadId) {
                state.buffer.push(`\x1B[2m0x${paddedVirtualAddress}\x1B[0m ${`\u2502 `.repeat(state.depth++)}\u250C\u2500\x1B[35m${method.class.type.name}::\x1B[1m${method.name}\x1B[0m\x1B[0m`);
              }
            },
            onLeave() {
              if (this.threadId == threadId) {
                state.buffer.push(`\x1B[2m0x${paddedVirtualAddress}\x1B[0m ${`\u2502 `.repeat(--state.depth)}\u2514\u2500\x1B[33m${method.class.type.name}::\x1B[1m${method.name}\x1B[0m\x1B[0m`);
                state.flush();
              }
            }
          });
        };
        const applierWithParameters = () => (method, state, threadId) => {
          const paddedVirtualAddress = method.relativeVirtualAddress.toString(16).padStart(8, "0");
          const startIndex = +!method.isStatic | +Il2Cpp3.unityVersionIsBelow201830;
          const callback = function(...args) {
            if (this.threadId == threadId) {
              const thisParameter = method.isStatic ? void 0 : new Il2Cpp3.Parameter("this", -1, method.class.type);
              const parameters2 = thisParameter ? [thisParameter].concat(method.parameters) : method.parameters;
              state.buffer.push(`\x1B[2m0x${paddedVirtualAddress}\x1B[0m ${`\u2502 `.repeat(state.depth++)}\u250C\u2500\x1B[35m${method.class.type.name}::\x1B[1m${method.name}\x1B[0m\x1B[0m(${parameters2.map((e) => `\x1B[32m${e.name}\x1B[0m = \x1B[31m${Il2Cpp3.fromFridaValue(args[e.position + startIndex], e.type)}\x1B[0m`).join(", ")})`);
            }
            const returnValue = method.nativeFunction(...args);
            if (this.threadId == threadId) {
              state.buffer.push(`\x1B[2m0x${paddedVirtualAddress}\x1B[0m ${`\u2502 `.repeat(--state.depth)}\u2514\u2500\x1B[33m${method.class.type.name}::\x1B[1m${method.name}\x1B[0m\x1B[0m${returnValue == void 0 ? "" : ` = \x1B[36m${Il2Cpp3.fromFridaValue(returnValue, method.returnType)}`}\x1B[0m`);
              state.flush();
            }
            return returnValue;
          };
          method.revert();
          const nativeCallback = new NativeCallback(callback, method.returnType.fridaAlias, method.fridaSignature);
          Interceptor.replace(method.virtualAddress, nativeCallback);
        };
        return new Il2Cpp3.Tracer(parameters ? applierWithParameters() : applier());
      }
      Il2Cpp3.trace = trace;
      function backtrace(mode) {
        const methods = Il2Cpp3.domain.assemblies.flatMap((_) => _.image.classes.flatMap((_2) => _2.methods.filter((_3) => !_3.virtualAddress.isNull()))).sort((_, __) => _.virtualAddress.compare(__.virtualAddress));
        const searchInsert = (target) => {
          let left = 0;
          let right = methods.length - 1;
          while (left <= right) {
            const pivot = Math.floor((left + right) / 2);
            const comparison = methods[pivot].virtualAddress.compare(target);
            if (comparison == 0) {
              return methods[pivot];
            } else if (comparison > 0) {
              right = pivot - 1;
            } else {
              left = pivot + 1;
            }
          }
          return methods[right];
        };
        const applier = () => (method, state, threadId) => {
          Interceptor.attach(method.virtualAddress, function() {
            if (this.threadId == threadId) {
              const handles = globalThis.Thread.backtrace(this.context, mode);
              handles.unshift(method.virtualAddress);
              for (const handle of handles) {
                if (handle.compare(Il2Cpp3.module.base) > 0 && handle.compare(Il2Cpp3.module.base.add(Il2Cpp3.module.size)) < 0) {
                  const method2 = searchInsert(handle);
                  if (method2) {
                    const offset = handle.sub(method2.virtualAddress);
                    if (offset.compare(4095) < 0) {
                      state.buffer.push(`\x1B[2m0x${method2.relativeVirtualAddress.toString(16).padStart(8, "0")}\x1B[0m\x1B[2m+0x${offset.toString(16).padStart(3, `0`)}\x1B[0m ${method2.class.type.name}::\x1B[1m${method2.name}\x1B[0m`);
                    }
                  }
                }
              }
              state.flush();
            }
          });
        };
        return new Il2Cpp3.Tracer(applier());
      }
      Il2Cpp3.backtrace = backtrace;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Array2 extends NativeStruct {
        /** Gets the Il2CppArray struct size, possibly equal to `Process.pointerSize * 4`. */
        static get headerSize() {
          return Il2Cpp3.corlib.class("System.Array").instanceSize;
        }
        /** @internal Gets a pointer to the first element of the current array. */
        get elements() {
          const array2 = Il2Cpp3.string("v").object.method("ToCharArray", 0).invoke();
          const offset = array2.handle.offsetOf((_) => _.readS16() == 118) ?? raise("couldn't find the elements offset in the native array struct");
          getter(Il2Cpp3.Array.prototype, "elements", function() {
            return new Il2Cpp3.Pointer(this.handle.add(offset), this.elementType);
          }, lazy);
          return this.elements;
        }
        /** Gets the size of the object encompassed by the current array. */
        get elementSize() {
          return this.elementType.class.arrayElementSize;
        }
        /** Gets the type of the object encompassed by the current array. */
        get elementType() {
          return this.object.class.type.class.baseType;
        }
        /** Gets the total number of elements in all the dimensions of the current array. */
        get length() {
          return Il2Cpp3.exports.arrayGetLength(this);
        }
        /** Gets the encompassing object of the current array. */
        get object() {
          return new Il2Cpp3.Object(this);
        }
        /** Gets the element at the specified index of the current array. */
        get(index) {
          if (index < 0 || index >= this.length) {
            raise(`cannot get element at index ${index} as the array length is ${this.length}`);
          }
          return this.elements.get(index);
        }
        /** Sets the element at the specified index of the current array. */
        set(index, value) {
          if (index < 0 || index >= this.length) {
            raise(`cannot set element at index ${index} as the array length is ${this.length}`);
          }
          this.elements.set(index, value);
        }
        /** */
        toString() {
          return this.isNull() ? "null" : `[${this.elements.read(this.length, 0)}]`;
        }
        /** Iterable. */
        *[Symbol.iterator]() {
          for (let i = 0; i < this.length; i++) {
            yield this.elements.get(i);
          }
        }
      }
      __decorate([
        lazy
      ], Array2.prototype, "elementSize", null);
      __decorate([
        lazy
      ], Array2.prototype, "elementType", null);
      __decorate([
        lazy
      ], Array2.prototype, "length", null);
      __decorate([
        lazy
      ], Array2.prototype, "object", null);
      __decorate([
        lazy
      ], Array2, "headerSize", null);
      Il2Cpp3.Array = Array2;
      function array(klass, lengthOrElements) {
        const length = typeof lengthOrElements == "number" ? lengthOrElements : lengthOrElements.length;
        const array2 = new Il2Cpp3.Array(Il2Cpp3.exports.arrayNew(klass, length));
        if (globalThis.Array.isArray(lengthOrElements)) {
          array2.elements.write(lengthOrElements);
        }
        return array2;
      }
      Il2Cpp3.array = array;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      let Assembly = class Assembly extends NativeStruct {
        /** Gets the image of this assembly. */
        get image() {
          if (Il2Cpp3.exports.assemblyGetImage.isNull()) {
            const runtimeModule = this.object.tryMethod("GetType", 1)?.invoke(Il2Cpp3.string("<Module>"))?.asNullable()?.tryMethod("get_Module")?.invoke() ?? this.object.tryMethod("GetModules", 1)?.invoke(false)?.get(0) ?? raise(`couldn't find the runtime module object of assembly ${this.name}`);
            return new Il2Cpp3.Image(runtimeModule.field("_impl").value);
          }
          return new Il2Cpp3.Image(Il2Cpp3.exports.assemblyGetImage(this));
        }
        /** Gets the name of this assembly. */
        get name() {
          return this.image.name.replace(".dll", "");
        }
        /** Gets the encompassing object of the current assembly. */
        get object() {
          for (const _ of Il2Cpp3.domain.object.method("GetAssemblies", 1).invoke(false)) {
            if (_.field("_mono_assembly").value.equals(this)) {
              return _;
            }
          }
          raise("couldn't find the object of the native assembly struct");
        }
      };
      __decorate([
        lazy
      ], Assembly.prototype, "name", null);
      __decorate([
        lazy
      ], Assembly.prototype, "object", null);
      Assembly = __decorate([
        recycle
      ], Assembly);
      Il2Cpp3.Assembly = Assembly;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      let Class = class Class extends NativeStruct {
        /** Gets the actual size of the instance of the current class. */
        get actualInstanceSize() {
          const SystemString = Il2Cpp3.corlib.class("System.String");
          const offset = SystemString.handle.offsetOf((_) => _.readInt() == SystemString.instanceSize - 2) ?? raise("couldn't find the actual instance size offset in the native class struct");
          getter(Il2Cpp3.Class.prototype, "actualInstanceSize", function() {
            return this.handle.add(offset).readS32();
          }, lazy);
          return this.actualInstanceSize;
        }
        /** Gets the array class which encompass the current class. */
        get arrayClass() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.classGetArrayClass(this, 1));
        }
        /** Gets the size of the object encompassed by the current array class. */
        get arrayElementSize() {
          return Il2Cpp3.exports.classGetArrayElementSize(this);
        }
        /** Gets the name of the assembly in which the current class is defined. */
        get assemblyName() {
          return Il2Cpp3.exports.classGetAssemblyName(this).readUtf8String().replace(".dll", "");
        }
        /** Gets the class that declares the current nested class. */
        get declaringClass() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.classGetDeclaringType(this)).asNullable();
        }
        /** Gets the encompassed type of this array, reference, pointer or enum type. */
        get baseType() {
          return new Il2Cpp3.Type(Il2Cpp3.exports.classGetBaseType(this)).asNullable();
        }
        /** Gets the class of the object encompassed or referred to by the current array, pointer or reference class. */
        get elementClass() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.classGetElementClass(this)).asNullable();
        }
        /** Gets the fields of the current class. */
        get fields() {
          return readNativeIterator((_) => Il2Cpp3.exports.classGetFields(this, _)).map((_) => new Il2Cpp3.Field(_));
        }
        /** Gets the flags of the current class. */
        get flags() {
          return Il2Cpp3.exports.classGetFlags(this);
        }
        /** Gets the full name (namespace + name) of the current class. */
        get fullName() {
          return this.namespace ? `${this.namespace}.${this.name}` : this.name;
        }
        /** Gets the generic class of the current class if the current class is inflated. */
        get genericClass() {
          const klass = this.image.tryClass(this.fullName)?.asNullable();
          return klass?.equals(this) ? null : klass ?? null;
        }
        /** Gets the generics parameters of this generic class. */
        get generics() {
          if (!this.isGeneric && !this.isInflated) {
            return [];
          }
          const types = this.type.object.method("GetGenericArguments").invoke();
          return globalThis.Array.from(types).map((_) => new Il2Cpp3.Class(Il2Cpp3.exports.classFromObject(_)));
        }
        /** Determines whether the GC has tracking references to the current class instances. */
        get hasReferences() {
          return !!Il2Cpp3.exports.classHasReferences(this);
        }
        /** Determines whether ther current class has a valid static constructor. */
        get hasStaticConstructor() {
          const staticConstructor = this.tryMethod(".cctor");
          return staticConstructor != null && !staticConstructor.virtualAddress.isNull();
        }
        /** Gets the image in which the current class is defined. */
        get image() {
          return new Il2Cpp3.Image(Il2Cpp3.exports.classGetImage(this));
        }
        /** Gets the size of the instance of the current class. */
        get instanceSize() {
          return Il2Cpp3.exports.classGetInstanceSize(this);
        }
        /** Determines whether the current class is abstract. */
        get isAbstract() {
          return !!Il2Cpp3.exports.classIsAbstract(this);
        }
        /** Determines whether the current class is blittable. */
        get isBlittable() {
          return !!Il2Cpp3.exports.classIsBlittable(this);
        }
        /** Determines whether the current class is an enumeration. */
        get isEnum() {
          return !!Il2Cpp3.exports.classIsEnum(this);
        }
        /** Determines whether the current class is a generic one. */
        get isGeneric() {
          return !!Il2Cpp3.exports.classIsGeneric(this);
        }
        /** Determines whether the current class is inflated. */
        get isInflated() {
          return !!Il2Cpp3.exports.classIsInflated(this);
        }
        /** Determines whether the current class is an interface. */
        get isInterface() {
          return !!Il2Cpp3.exports.classIsInterface(this);
        }
        /** Determines whether the current class is a struct. */
        get isStruct() {
          return this.isValueType && !this.isEnum;
        }
        /** Determines whether the current class is a value type. */
        get isValueType() {
          return !!Il2Cpp3.exports.classIsValueType(this);
        }
        /** Gets the interfaces implemented or inherited by the current class. */
        get interfaces() {
          return readNativeIterator((_) => Il2Cpp3.exports.classGetInterfaces(this, _)).map((_) => new Il2Cpp3.Class(_));
        }
        /** Gets the methods implemented by the current class. */
        get methods() {
          return readNativeIterator((_) => Il2Cpp3.exports.classGetMethods(this, _)).map((_) => new Il2Cpp3.Method(_));
        }
        /** Gets the name of the current class. */
        get name() {
          return Il2Cpp3.exports.classGetName(this).readUtf8String();
        }
        /** Gets the namespace of the current class. */
        get namespace() {
          return Il2Cpp3.exports.classGetNamespace(this).readUtf8String() || void 0;
        }
        /** Gets the classes nested inside the current class. */
        get nestedClasses() {
          return readNativeIterator((_) => Il2Cpp3.exports.classGetNestedClasses(this, _)).map((_) => new Il2Cpp3.Class(_));
        }
        /** Gets the class from which the current class directly inherits. */
        get parent() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.classGetParent(this)).asNullable();
        }
        /** Gets the pointer class of the current class. */
        get pointerClass() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.classFromObject(this.type.object.method("MakePointerType").invoke()));
        }
        /** Gets the rank (number of dimensions) of the current array class. */
        get rank() {
          let rank = 0;
          const name = this.name;
          for (let i = this.name.length - 1; i > 0; i--) {
            const c = name[i];
            if (c == "]")
              rank++;
            else if (c == "[" || rank == 0)
              break;
            else if (c == ",")
              rank++;
            else
              break;
          }
          return rank;
        }
        /** Gets a pointer to the static fields of the current class. */
        get staticFieldsData() {
          return Il2Cpp3.exports.classGetStaticFieldData(this);
        }
        /** Gets the size of the instance - as a value type - of the current class. */
        get valueTypeSize() {
          return Il2Cpp3.exports.classGetValueTypeSize(this, NULL);
        }
        /** Gets the type of the current class. */
        get type() {
          return new Il2Cpp3.Type(Il2Cpp3.exports.classGetType(this));
        }
        /** Allocates a new object of the current class. */
        alloc() {
          return new Il2Cpp3.Object(Il2Cpp3.exports.objectNew(this));
        }
        /** Gets the field identified by the given name. */
        field(name) {
          return this.tryField(name) ?? raise(`couldn't find field ${name} in class ${this.type.name}`);
        }
        /** Gets the hierarchy of the current class. */
        *hierarchy(options) {
          let klass = options?.includeCurrent ?? true ? this : this.parent;
          while (klass) {
            yield klass;
            klass = klass.parent;
          }
        }
        /** Builds a generic instance of the current generic class. */
        inflate(...classes) {
          if (!this.isGeneric) {
            raise(`cannot inflate class ${this.type.name} as it has no generic parameters`);
          }
          if (this.generics.length != classes.length) {
            raise(`cannot inflate class ${this.type.name} as it needs ${this.generics.length} generic parameter(s), not ${classes.length}`);
          }
          const types = classes.map((_) => _.type.object);
          const typeArray = Il2Cpp3.array(Il2Cpp3.corlib.class("System.Type"), types);
          const inflatedType = this.type.object.method("MakeGenericType", 1).invoke(typeArray);
          return new Il2Cpp3.Class(Il2Cpp3.exports.classFromObject(inflatedType));
        }
        /** Calls the static constructor of the current class. */
        initialize() {
          Il2Cpp3.exports.classInitialize(this);
          return this;
        }
        /** Determines whether an instance of `other` class can be assigned to a variable of the current type. */
        isAssignableFrom(other) {
          return !!Il2Cpp3.exports.classIsAssignableFrom(this, other);
        }
        /** Determines whether the current class derives from `other` class. */
        isSubclassOf(other, checkInterfaces) {
          return !!Il2Cpp3.exports.classIsSubclassOf(this, other, +checkInterfaces);
        }
        /** Gets the method identified by the given name and parameter count. */
        method(name, parameterCount = -1) {
          return this.tryMethod(name, parameterCount) ?? raise(`couldn't find method ${name} in class ${this.type.name}`);
        }
        /** Gets the nested class with the given name. */
        nested(name) {
          return this.tryNested(name) ?? raise(`couldn't find nested class ${name} in class ${this.type.name}`);
        }
        /** Allocates a new object of the current class and calls its default constructor. */
        new() {
          const object = this.alloc();
          const exceptionArray = Memory.alloc(Process.pointerSize);
          Il2Cpp3.exports.objectInitialize(object, exceptionArray);
          const exception = exceptionArray.readPointer();
          if (!exception.isNull()) {
            raise(new Il2Cpp3.Object(exception).toString());
          }
          return object;
        }
        /** Gets the field with the given name. */
        tryField(name) {
          return new Il2Cpp3.Field(Il2Cpp3.exports.classGetFieldFromName(this, Memory.allocUtf8String(name))).asNullable();
        }
        /** Gets the method with the given name and parameter count. */
        tryMethod(name, parameterCount = -1) {
          return new Il2Cpp3.Method(Il2Cpp3.exports.classGetMethodFromName(this, Memory.allocUtf8String(name), parameterCount)).asNullable();
        }
        /** Gets the nested class with the given name. */
        tryNested(name) {
          return this.nestedClasses.find((_) => _.name == name);
        }
        /** */
        toString() {
          const inherited = [this.parent].concat(this.interfaces);
          return `// ${this.assemblyName}
${this.isEnum ? `enum` : this.isStruct ? `struct` : this.isInterface ? `interface` : `class`} ${this.type.name}${inherited ? ` : ${inherited.map((_) => _?.type.name).join(`, `)}` : ``}
{
    ${this.fields.join(`
    `)}
    ${this.methods.join(`
    `)}
}`;
        }
        /** Executes a callback for every defined class. */
        static enumerate(block) {
          const callback = new NativeCallback((_) => block(new Il2Cpp3.Class(_)), "void", ["pointer", "pointer"]);
          return Il2Cpp3.exports.classForEach(callback, NULL);
        }
      };
      __decorate([
        lazy
      ], Class.prototype, "arrayClass", null);
      __decorate([
        lazy
      ], Class.prototype, "arrayElementSize", null);
      __decorate([
        lazy
      ], Class.prototype, "assemblyName", null);
      __decorate([
        lazy
      ], Class.prototype, "declaringClass", null);
      __decorate([
        lazy
      ], Class.prototype, "baseType", null);
      __decorate([
        lazy
      ], Class.prototype, "elementClass", null);
      __decorate([
        lazy
      ], Class.prototype, "fields", null);
      __decorate([
        lazy
      ], Class.prototype, "flags", null);
      __decorate([
        lazy
      ], Class.prototype, "fullName", null);
      __decorate([
        lazy
      ], Class.prototype, "generics", null);
      __decorate([
        lazy
      ], Class.prototype, "hasReferences", null);
      __decorate([
        lazy
      ], Class.prototype, "hasStaticConstructor", null);
      __decorate([
        lazy
      ], Class.prototype, "image", null);
      __decorate([
        lazy
      ], Class.prototype, "instanceSize", null);
      __decorate([
        lazy
      ], Class.prototype, "isAbstract", null);
      __decorate([
        lazy
      ], Class.prototype, "isBlittable", null);
      __decorate([
        lazy
      ], Class.prototype, "isEnum", null);
      __decorate([
        lazy
      ], Class.prototype, "isGeneric", null);
      __decorate([
        lazy
      ], Class.prototype, "isInflated", null);
      __decorate([
        lazy
      ], Class.prototype, "isInterface", null);
      __decorate([
        lazy
      ], Class.prototype, "isValueType", null);
      __decorate([
        lazy
      ], Class.prototype, "interfaces", null);
      __decorate([
        lazy
      ], Class.prototype, "methods", null);
      __decorate([
        lazy
      ], Class.prototype, "name", null);
      __decorate([
        lazy
      ], Class.prototype, "namespace", null);
      __decorate([
        lazy
      ], Class.prototype, "nestedClasses", null);
      __decorate([
        lazy
      ], Class.prototype, "parent", null);
      __decorate([
        lazy
      ], Class.prototype, "pointerClass", null);
      __decorate([
        lazy
      ], Class.prototype, "rank", null);
      __decorate([
        lazy
      ], Class.prototype, "staticFieldsData", null);
      __decorate([
        lazy
      ], Class.prototype, "valueTypeSize", null);
      __decorate([
        lazy
      ], Class.prototype, "type", null);
      Class = __decorate([
        recycle
      ], Class);
      Il2Cpp3.Class = Class;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      function delegate(klass, block) {
        const SystemDelegate = Il2Cpp3.corlib.class("System.Delegate");
        const SystemMulticastDelegate = Il2Cpp3.corlib.class("System.MulticastDelegate");
        if (!SystemDelegate.isAssignableFrom(klass)) {
          raise(`cannot create a delegate for ${klass.type.name} as it's a non-delegate class`);
        }
        if (klass.equals(SystemDelegate) || klass.equals(SystemMulticastDelegate)) {
          raise(`cannot create a delegate for neither ${SystemDelegate.type.name} nor ${SystemMulticastDelegate.type.name}, use a subclass instead`);
        }
        const delegate2 = klass.alloc();
        const key = delegate2.handle.toString();
        const Invoke = delegate2.tryMethod("Invoke") ?? raise(`cannot create a delegate for ${klass.type.name}, there is no Invoke method`);
        delegate2.method(".ctor").invoke(delegate2, Invoke.handle);
        const callback = Invoke.wrap(block);
        delegate2.field("method_ptr").value = callback;
        delegate2.field("invoke_impl").value = callback;
        Il2Cpp3._callbacksToKeepAlive[key] = callback;
        return delegate2;
      }
      Il2Cpp3.delegate = delegate;
      Il2Cpp3._callbacksToKeepAlive = {};
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      let Domain = class Domain extends NativeStruct {
        /** Gets the assemblies that have been loaded into the execution context of the application domain. */
        get assemblies() {
          let handles = readNativeList((_) => Il2Cpp3.exports.domainGetAssemblies(this, _));
          if (handles.length == 0) {
            const assemblyObjects = this.object.method("GetAssemblies").overload().invoke();
            handles = globalThis.Array.from(assemblyObjects).map((_) => _.field("_mono_assembly").value);
          }
          return handles.map((_) => new Il2Cpp3.Assembly(_));
        }
        /** Gets the encompassing object of the application domain. */
        get object() {
          return Il2Cpp3.corlib.class("System.AppDomain").method("get_CurrentDomain").invoke();
        }
        /** Opens and loads the assembly with the given name. */
        assembly(name) {
          return this.tryAssembly(name) ?? raise(`couldn't find assembly ${name}`);
        }
        /** Attached a new thread to the application domain. */
        attach() {
          return new Il2Cpp3.Thread(Il2Cpp3.exports.threadAttach(this));
        }
        /** Opens and loads the assembly with the given name. */
        tryAssembly(name) {
          return new Il2Cpp3.Assembly(Il2Cpp3.exports.domainGetAssemblyFromName(this, Memory.allocUtf8String(name))).asNullable();
        }
      };
      __decorate([
        lazy
      ], Domain.prototype, "assemblies", null);
      __decorate([
        lazy
      ], Domain.prototype, "object", null);
      Domain = __decorate([
        recycle
      ], Domain);
      Il2Cpp3.Domain = Domain;
      getter(Il2Cpp3, "domain", () => {
        return new Il2Cpp3.Domain(Il2Cpp3.exports.domainGet());
      }, lazy);
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Field extends NativeStruct {
        /** Gets the class in which this field is defined. */
        get class() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.fieldGetClass(this));
        }
        /** Gets the flags of the current field. */
        get flags() {
          return Il2Cpp3.exports.fieldGetFlags(this);
        }
        /** Determines whether this field value is known at compile time. */
        get isLiteral() {
          return (this.flags & 64) != 0;
        }
        /** Determines whether this field is static. */
        get isStatic() {
          return (this.flags & 16) != 0;
        }
        /** Determines whether this field is thread static. */
        get isThreadStatic() {
          const offset = Il2Cpp3.corlib.class("System.AppDomain").field("type_resolve_in_progress").offset;
          getter(Il2Cpp3.Field.prototype, "isThreadStatic", function() {
            return this.offset == offset;
          }, lazy);
          return this.isThreadStatic;
        }
        /** Gets the access modifier of this field. */
        get modifier() {
          switch (this.flags & 7) {
            case 1:
              return "private";
            case 2:
              return "private protected";
            case 3:
              return "internal";
            case 4:
              return "protected";
            case 5:
              return "protected internal";
            case 6:
              return "public";
          }
        }
        /** Gets the name of this field. */
        get name() {
          return Il2Cpp3.exports.fieldGetName(this).readUtf8String();
        }
        /** Gets the offset of this field, calculated as the difference with its owner virtual address. */
        get offset() {
          return Il2Cpp3.exports.fieldGetOffset(this);
        }
        /** Gets the type of this field. */
        get type() {
          return new Il2Cpp3.Type(Il2Cpp3.exports.fieldGetType(this));
        }
        /** Gets the value of this field. */
        get value() {
          if (!this.isStatic) {
            raise(`cannot access instance field ${this.class.type.name}::${this.name} from a class, use an object instead`);
          }
          const handle = Memory.alloc(Process.pointerSize);
          Il2Cpp3.exports.fieldGetStaticValue(this.handle, handle);
          return Il2Cpp3.read(handle, this.type);
        }
        /** Sets the value of this field. Thread static or literal values cannot be altered yet. */
        set value(value) {
          if (!this.isStatic) {
            raise(`cannot access instance field ${this.class.type.name}::${this.name} from a class, use an object instead`);
          }
          if (this.isThreadStatic || this.isLiteral) {
            raise(`cannot write the value of field ${this.name} as it's thread static or literal`);
          }
          const handle = (
            // pointer-like values should be passed as-is, but boxed
            // value types (primitives included) must be unboxed first
            value instanceof Il2Cpp3.Object && this.type.class.isValueType ? value.unbox() : value instanceof NativeStruct ? value.handle : value instanceof NativePointer ? value : Il2Cpp3.write(Memory.alloc(this.type.class.valueTypeSize), value, this.type)
          );
          Il2Cpp3.exports.fieldSetStaticValue(this.handle, handle);
        }
        /** */
        toString() {
          return `${this.isThreadStatic ? `[ThreadStatic] ` : ``}${this.isStatic ? `static ` : ``}${this.type.name} ${this.name}${this.isLiteral ? ` = ${this.type.class.isEnum ? Il2Cpp3.read(this.value.handle, this.type.class.baseType) : this.value}` : ``};${this.isThreadStatic || this.isLiteral ? `` : ` // 0x${this.offset.toString(16)}`}`;
        }
        /**
         * @internal
         * Binds the current field to a {@link Il2Cpp.Object} or a
         * {@link Il2Cpp.ValueType} (also known as *instances*), so that it is
         * possible to retrieve its value - see {@link Il2Cpp.Field.value} for
         * details. \
         * Binding a static field is forbidden.
         */
        bind(instance) {
          if (this.isStatic) {
            raise(`cannot bind static field ${this.class.type.name}::${this.name} to an instance`);
          }
          const offset = this.offset - (instance instanceof Il2Cpp3.ValueType ? Il2Cpp3.Object.headerSize : 0);
          return new Proxy(this, {
            get(target, property) {
              if (property == "value") {
                return Il2Cpp3.read(instance.handle.add(offset), target.type);
              }
              return Reflect.get(target, property);
            },
            set(target, property, value) {
              if (property == "value") {
                Il2Cpp3.write(instance.handle.add(offset), value, target.type);
                return true;
              }
              return Reflect.set(target, property, value);
            }
          });
        }
      }
      __decorate([
        lazy
      ], Field.prototype, "class", null);
      __decorate([
        lazy
      ], Field.prototype, "flags", null);
      __decorate([
        lazy
      ], Field.prototype, "isLiteral", null);
      __decorate([
        lazy
      ], Field.prototype, "isStatic", null);
      __decorate([
        lazy
      ], Field.prototype, "isThreadStatic", null);
      __decorate([
        lazy
      ], Field.prototype, "modifier", null);
      __decorate([
        lazy
      ], Field.prototype, "name", null);
      __decorate([
        lazy
      ], Field.prototype, "offset", null);
      __decorate([
        lazy
      ], Field.prototype, "type", null);
      Il2Cpp3.Field = Field;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class GCHandle {
        handle;
        /** @internal */
        constructor(handle) {
          this.handle = handle;
        }
        /** Gets the object associated to this handle. */
        get target() {
          return new Il2Cpp3.Object(Il2Cpp3.exports.gcHandleGetTarget(this.handle)).asNullable();
        }
        /** Frees this handle. */
        free() {
          return Il2Cpp3.exports.gcHandleFree(this.handle);
        }
      }
      Il2Cpp3.GCHandle = GCHandle;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      let Image = class Image extends NativeStruct {
        /** Gets the assembly in which the current image is defined. */
        get assembly() {
          return new Il2Cpp3.Assembly(Il2Cpp3.exports.imageGetAssembly(this));
        }
        /** Gets the amount of classes defined in this image. */
        get classCount() {
          if (Il2Cpp3.unityVersionIsBelow201830) {
            return this.classes.length;
          } else {
            return Il2Cpp3.exports.imageGetClassCount(this);
          }
        }
        /** Gets the classes defined in this image. */
        get classes() {
          if (Il2Cpp3.unityVersionIsBelow201830) {
            const types = this.assembly.object.method("GetTypes").invoke(false);
            const classes = globalThis.Array.from(types, (_) => new Il2Cpp3.Class(Il2Cpp3.exports.classFromObject(_)));
            const Module = this.tryClass("<Module>");
            if (Module) {
              classes.unshift(Module);
            }
            return classes;
          } else {
            return globalThis.Array.from(globalThis.Array(this.classCount), (_, i) => new Il2Cpp3.Class(Il2Cpp3.exports.imageGetClass(this, i)));
          }
        }
        /** Gets the name of this image. */
        get name() {
          return Il2Cpp3.exports.imageGetName(this).readUtf8String();
        }
        /** Gets the class with the specified name defined in this image. */
        class(name) {
          return this.tryClass(name) ?? raise(`couldn't find class ${name} in assembly ${this.name}`);
        }
        /** Gets the class with the specified name defined in this image. */
        tryClass(name) {
          const dotIndex = name.lastIndexOf(".");
          const classNamespace = Memory.allocUtf8String(dotIndex == -1 ? "" : name.slice(0, dotIndex));
          const className = Memory.allocUtf8String(name.slice(dotIndex + 1));
          return new Il2Cpp3.Class(Il2Cpp3.exports.classFromName(this, classNamespace, className)).asNullable();
        }
      };
      __decorate([
        lazy
      ], Image.prototype, "assembly", null);
      __decorate([
        lazy
      ], Image.prototype, "classCount", null);
      __decorate([
        lazy
      ], Image.prototype, "classes", null);
      __decorate([
        lazy
      ], Image.prototype, "name", null);
      Image = __decorate([
        recycle
      ], Image);
      Il2Cpp3.Image = Image;
      getter(Il2Cpp3, "corlib", () => {
        return new Il2Cpp3.Image(Il2Cpp3.exports.getCorlib());
      }, lazy);
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class MemorySnapshot extends NativeStruct {
        /** Captures a memory snapshot. */
        static capture() {
          return new Il2Cpp3.MemorySnapshot();
        }
        /** Creates a memory snapshot with the given handle. */
        constructor(handle = Il2Cpp3.exports.memorySnapshotCapture()) {
          super(handle);
        }
        /** Gets any initialized class. */
        get classes() {
          return readNativeIterator((_) => Il2Cpp3.exports.memorySnapshotGetClasses(this, _)).map((_) => new Il2Cpp3.Class(_));
        }
        /** Gets the objects tracked by this memory snapshot. */
        get objects() {
          return readNativeList((_) => Il2Cpp3.exports.memorySnapshotGetObjects(this, _)).filter((_) => !_.isNull()).map((_) => new Il2Cpp3.Object(_));
        }
        /** Frees this memory snapshot. */
        free() {
          Il2Cpp3.exports.memorySnapshotFree(this);
        }
      }
      __decorate([
        lazy
      ], MemorySnapshot.prototype, "classes", null);
      __decorate([
        lazy
      ], MemorySnapshot.prototype, "objects", null);
      Il2Cpp3.MemorySnapshot = MemorySnapshot;
      function memorySnapshot(block) {
        const memorySnapshot2 = Il2Cpp3.MemorySnapshot.capture();
        const result = block(memorySnapshot2);
        memorySnapshot2.free();
        return result;
      }
      Il2Cpp3.memorySnapshot = memorySnapshot;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Method extends NativeStruct {
        /** Gets the class in which this method is defined. */
        get class() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.methodGetClass(this));
        }
        /** Gets the flags of the current method. */
        get flags() {
          return Il2Cpp3.exports.methodGetFlags(this, NULL);
        }
        /** Gets the implementation flags of the current method. */
        get implementationFlags() {
          const implementationFlagsPointer = Memory.alloc(Process.pointerSize);
          Il2Cpp3.exports.methodGetFlags(this, implementationFlagsPointer);
          return implementationFlagsPointer.readU32();
        }
        /** */
        get fridaSignature() {
          const types = [];
          for (const parameter of this.parameters) {
            types.push(parameter.type.fridaAlias);
          }
          if (!this.isStatic || Il2Cpp3.unityVersionIsBelow201830) {
            types.unshift("pointer");
          }
          if (this.isInflated) {
            types.push("pointer");
          }
          return types;
        }
        /** Gets the generic parameters of this generic method. */
        get generics() {
          if (!this.isGeneric && !this.isInflated) {
            return [];
          }
          const types = this.object.method("GetGenericArguments").invoke();
          return globalThis.Array.from(types).map((_) => new Il2Cpp3.Class(Il2Cpp3.exports.classFromObject(_)));
        }
        /** Determines whether this method is external. */
        get isExternal() {
          return (this.implementationFlags & 4096) != 0;
        }
        /** Determines whether this method is generic. */
        get isGeneric() {
          return !!Il2Cpp3.exports.methodIsGeneric(this);
        }
        /** Determines whether this method is inflated (generic with a concrete type parameter). */
        get isInflated() {
          return !!Il2Cpp3.exports.methodIsInflated(this);
        }
        /** Determines whether this method is static. */
        get isStatic() {
          return !Il2Cpp3.exports.methodIsInstance(this);
        }
        /** Determines whether this method is synchronized. */
        get isSynchronized() {
          return (this.implementationFlags & 32) != 0;
        }
        /** Gets the access modifier of this method. */
        get modifier() {
          switch (this.flags & 7) {
            case 1:
              return "private";
            case 2:
              return "private protected";
            case 3:
              return "internal";
            case 4:
              return "protected";
            case 5:
              return "protected internal";
            case 6:
              return "public";
          }
        }
        /** Gets the name of this method. */
        get name() {
          return Il2Cpp3.exports.methodGetName(this).readUtf8String();
        }
        /** @internal */
        get nativeFunction() {
          return new NativeFunction(this.virtualAddress, this.returnType.fridaAlias, this.fridaSignature);
        }
        /** Gets the encompassing object of the current method. */
        get object() {
          return new Il2Cpp3.Object(Il2Cpp3.exports.methodGetObject(this, NULL));
        }
        /** Gets the amount of parameters of this method. */
        get parameterCount() {
          return Il2Cpp3.exports.methodGetParameterCount(this);
        }
        /** Gets the parameters of this method. */
        get parameters() {
          return globalThis.Array.from(globalThis.Array(this.parameterCount), (_, i) => {
            const parameterName = Il2Cpp3.exports.methodGetParameterName(this, i).readUtf8String();
            const parameterType = Il2Cpp3.exports.methodGetParameterType(this, i);
            return new Il2Cpp3.Parameter(parameterName, i, new Il2Cpp3.Type(parameterType));
          });
        }
        /** Gets the relative virtual address (RVA) of this method. */
        get relativeVirtualAddress() {
          return this.virtualAddress.sub(Il2Cpp3.module.base);
        }
        /** Gets the return type of this method. */
        get returnType() {
          return new Il2Cpp3.Type(Il2Cpp3.exports.methodGetReturnType(this));
        }
        /** Gets the virtual address (VA) of this method. */
        get virtualAddress() {
          const FilterTypeName = Il2Cpp3.corlib.class("System.Reflection.Module").initialize().field("FilterTypeName").value;
          const FilterTypeNameMethodPointer = FilterTypeName.field("method_ptr").value;
          const FilterTypeNameMethod = FilterTypeName.field("method").value;
          const offset = FilterTypeNameMethod.offsetOf((_) => _.readPointer().equals(FilterTypeNameMethodPointer)) ?? raise("couldn't find the virtual address offset in the native method struct");
          getter(Il2Cpp3.Method.prototype, "virtualAddress", function() {
            return this.handle.add(offset).readPointer();
          }, lazy);
          Il2Cpp3.corlib.class("System.Reflection.Module").method(".cctor").invoke();
          return this.virtualAddress;
        }
        /** Replaces the body of this method. */
        set implementation(block) {
          try {
            Interceptor.replace(this.virtualAddress, this.wrap(block));
          } catch (e) {
            switch (e.message) {
              case "access violation accessing 0x0":
                raise(`couldn't set implementation for method ${this.name} as it has a NULL virtual address`);
              case /unable to intercept function at \w+; please file a bug/.exec(e.message)?.input:
                warn(`couldn't set implementation for method ${this.name} as it may be a thunk`);
                break;
              case "already replaced this function":
                warn(`couldn't set implementation for method ${this.name} as it has already been replaced by a thunk`);
                break;
              default:
                throw e;
            }
          }
        }
        /** Creates a generic instance of the current generic method. */
        inflate(...classes) {
          if (!this.isGeneric || this.generics.length != classes.length) {
            for (const method of this.overloads()) {
              if (method.isGeneric && method.generics.length == classes.length) {
                return method.inflate(...classes);
              }
            }
            raise(`could not find inflatable signature of method ${this.name} with ${classes.length} generic parameter(s)`);
          }
          const types = classes.map((_) => _.type.object);
          const typeArray = Il2Cpp3.array(Il2Cpp3.corlib.class("System.Type"), types);
          const inflatedMethodObject = this.object.method("MakeGenericMethod", 1).invoke(typeArray);
          return new Il2Cpp3.Method(inflatedMethodObject.field("mhandle").value);
        }
        /** Invokes this method. */
        invoke(...parameters) {
          if (!this.isStatic) {
            raise(`cannot invoke non-static method ${this.name} as it must be invoked throught a Il2Cpp.Object, not a Il2Cpp.Class`);
          }
          return this.invokeRaw(NULL, ...parameters);
        }
        /** @internal */
        invokeRaw(instance, ...parameters) {
          const allocatedParameters = parameters.map(Il2Cpp3.toFridaValue);
          if (!this.isStatic || Il2Cpp3.unityVersionIsBelow201830) {
            allocatedParameters.unshift(instance);
          }
          if (this.isInflated) {
            allocatedParameters.push(this.handle);
          }
          try {
            const returnValue = this.nativeFunction(...allocatedParameters);
            return Il2Cpp3.fromFridaValue(returnValue, this.returnType);
          } catch (e) {
            if (e == null) {
              raise("an unexpected native invocation exception occurred, this is due to parameter types mismatch");
            }
            switch (e.message) {
              case "bad argument count":
                raise(`couldn't invoke method ${this.name} as it needs ${this.parameterCount} parameter(s), not ${parameters.length}`);
              case "expected a pointer":
              case "expected number":
              case "expected array with fields":
                raise(`couldn't invoke method ${this.name} using incorrect parameter types`);
            }
            throw e;
          }
        }
        /** Gets the overloaded method with the given parameter types. */
        overload(...typeNamesOrClasses) {
          const method = this.tryOverload(...typeNamesOrClasses);
          return method ?? raise(`couldn't find overloaded method ${this.name}(${typeNamesOrClasses.map((_) => _ instanceof Il2Cpp3.Class ? _.type.name : _)})`);
        }
        /** @internal */
        *overloads() {
          for (const klass of this.class.hierarchy()) {
            for (const method of klass.methods) {
              if (this.name == method.name) {
                yield method;
              }
            }
          }
        }
        /** Gets the parameter with the given name. */
        parameter(name) {
          return this.tryParameter(name) ?? raise(`couldn't find parameter ${name} in method ${this.name}`);
        }
        /** Restore the original method implementation. */
        revert() {
          Interceptor.revert(this.virtualAddress);
          Interceptor.flush();
        }
        /** Gets the overloaded method with the given parameter types. */
        tryOverload(...typeNamesOrClasses) {
          const minScore = typeNamesOrClasses.length * 1;
          const maxScore = typeNamesOrClasses.length * 2;
          let candidate = void 0;
          loop: for (const method of this.overloads()) {
            if (method.parameterCount != typeNamesOrClasses.length)
              continue;
            let score = 0;
            let i = 0;
            for (const parameter of method.parameters) {
              const desiredTypeNameOrClass = typeNamesOrClasses[i];
              if (desiredTypeNameOrClass instanceof Il2Cpp3.Class) {
                if (parameter.type.is(desiredTypeNameOrClass.type)) {
                  score += 2;
                } else if (parameter.type.class.isAssignableFrom(desiredTypeNameOrClass)) {
                  score += 1;
                } else {
                  continue loop;
                }
              } else if (parameter.type.name == desiredTypeNameOrClass) {
                score += 2;
              } else {
                continue loop;
              }
              i++;
            }
            if (score < minScore) {
              continue;
            } else if (score == maxScore) {
              return method;
            } else if (candidate == void 0 || score > candidate[0]) {
              candidate = [score, method];
            } else if (score == candidate[0]) {
              let i2 = 0;
              for (const parameter of candidate[1].parameters) {
                if (parameter.type.class.isAssignableFrom(method.parameters[i2].type.class)) {
                  candidate = [score, method];
                  continue loop;
                }
                i2++;
              }
            }
          }
          return candidate?.[1];
        }
        /** Gets the parameter with the given name. */
        tryParameter(name) {
          return this.parameters.find((_) => _.name == name);
        }
        /** */
        toString() {
          return `${this.isStatic ? `static ` : ``}${this.returnType.name} ${this.name}${this.generics.length > 0 ? `<${this.generics.map((_) => _.type.name).join(",")}>` : ""}(${this.parameters.join(`, `)});${this.virtualAddress.isNull() ? `` : ` // 0x${this.relativeVirtualAddress.toString(16).padStart(8, `0`)}`}`;
        }
        /**
         * @internal
         * Binds the current method to a {@link Il2Cpp.Object} or a
         * {@link Il2Cpp.ValueType} (also known as *instances*), so that it is
         * possible to invoke it - see {@link Il2Cpp.Method.invoke} for
         * details. \
         * Binding a static method is forbidden.
         */
        bind(instance) {
          if (this.isStatic) {
            raise(`cannot bind static method ${this.class.type.name}::${this.name} to an instance`);
          }
          return new Proxy(this, {
            get(target, property, receiver) {
              switch (property) {
                case "invoke":
                  const handle = instance instanceof Il2Cpp3.ValueType ? target.class.isValueType ? instance.handle.sub(structMethodsRequireObjectInstances() ? Il2Cpp3.Object.headerSize : 0) : raise(`cannot invoke method ${target.class.type.name}::${target.name} against a value type, you must box it first`) : target.class.isValueType ? instance.handle.add(structMethodsRequireObjectInstances() ? 0 : Il2Cpp3.Object.headerSize) : instance.handle;
                  return target.invokeRaw.bind(target, handle);
                case "overloads":
                  return function* () {
                    for (const method of target[property]()) {
                      if (!method.isStatic) {
                        yield method;
                      }
                    }
                  };
                case "inflate":
                case "overload":
                case "tryOverload":
                  const member = Reflect.get(target, property).bind(receiver);
                  return function(...args) {
                    return member(...args)?.bind(instance);
                  };
              }
              return Reflect.get(target, property);
            }
          });
        }
        /** @internal */
        wrap(block) {
          const startIndex = +!this.isStatic | +Il2Cpp3.unityVersionIsBelow201830;
          return new NativeCallback((...args) => {
            const thisObject = this.isStatic ? this.class : this.class.isValueType ? new Il2Cpp3.ValueType(args[0].add(structMethodsRequireObjectInstances() ? Il2Cpp3.Object.headerSize : 0), this.class.type) : new Il2Cpp3.Object(args[0]);
            const parameters = this.parameters.map((_, i) => Il2Cpp3.fromFridaValue(args[i + startIndex], _.type));
            const result = block.call(thisObject, ...parameters);
            return Il2Cpp3.toFridaValue(result);
          }, this.returnType.fridaAlias, this.fridaSignature);
        }
      }
      __decorate([
        lazy
      ], Method.prototype, "class", null);
      __decorate([
        lazy
      ], Method.prototype, "flags", null);
      __decorate([
        lazy
      ], Method.prototype, "implementationFlags", null);
      __decorate([
        lazy
      ], Method.prototype, "fridaSignature", null);
      __decorate([
        lazy
      ], Method.prototype, "generics", null);
      __decorate([
        lazy
      ], Method.prototype, "isExternal", null);
      __decorate([
        lazy
      ], Method.prototype, "isGeneric", null);
      __decorate([
        lazy
      ], Method.prototype, "isInflated", null);
      __decorate([
        lazy
      ], Method.prototype, "isStatic", null);
      __decorate([
        lazy
      ], Method.prototype, "isSynchronized", null);
      __decorate([
        lazy
      ], Method.prototype, "modifier", null);
      __decorate([
        lazy
      ], Method.prototype, "name", null);
      __decorate([
        lazy
      ], Method.prototype, "nativeFunction", null);
      __decorate([
        lazy
      ], Method.prototype, "object", null);
      __decorate([
        lazy
      ], Method.prototype, "parameterCount", null);
      __decorate([
        lazy
      ], Method.prototype, "parameters", null);
      __decorate([
        lazy
      ], Method.prototype, "relativeVirtualAddress", null);
      __decorate([
        lazy
      ], Method.prototype, "returnType", null);
      Il2Cpp3.Method = Method;
      let structMethodsRequireObjectInstances = () => {
        const object = Il2Cpp3.corlib.class("System.Int64").alloc();
        object.field("m_value").value = 3735928559;
        const result = object.method("Equals", 1).overload(object.class).invokeRaw(object, 3735928559);
        return (structMethodsRequireObjectInstances = () => result)();
      };
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Object2 extends NativeStruct {
        /** Gets the Il2CppObject struct size, possibly equal to `Process.pointerSize * 2`. */
        static get headerSize() {
          return Il2Cpp3.corlib.class("System.Object").instanceSize;
        }
        /**
         * Returns the same object, but having its parent class as class.
         * It basically is the C# `base` keyword, so that parent members can be
         * accessed.
         *
         * **Example** \
         * Consider the following classes:
         * ```csharp
         * class Foo
         * {
         *     int foo()
         *     {
         *          return 1;
         *     }
         * }
         * class Bar : Foo
         * {
         *     new int foo()
         *     {
         *          return 2;
         *     }
         * }
         * ```
         * then:
         * ```ts
         * const Bar: Il2Cpp.Class = ...;
         * const bar = Bar.new();
         *
         * console.log(bar.foo()); // 2
         * console.log(bar.base.foo()); // 1
         * ```
         */
        get base() {
          if (this.class.parent == null) {
            raise(`class ${this.class.type.name} has no parent`);
          }
          return new Proxy(this, {
            get(target, property, receiver) {
              if (property == "class") {
                return Reflect.get(target, property).parent;
              } else if (property == "base") {
                return Reflect.getOwnPropertyDescriptor(Il2Cpp3.Object.prototype, property).get.bind(receiver)();
              }
              return Reflect.get(target, property);
            }
          });
        }
        /** Gets the class of this object. */
        get class() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.objectGetClass(this));
        }
        /** Returns a monitor for this object. */
        get monitor() {
          return new Il2Cpp3.Object.Monitor(this);
        }
        /** Gets the size of the current object. */
        get size() {
          return Il2Cpp3.exports.objectGetSize(this);
        }
        /** Gets the non-static field with the given name of the current class hierarchy. */
        field(name) {
          return this.tryField(name) ?? raise(`couldn't find non-static field ${name} in hierarchy of class ${this.class.type.name}`);
        }
        /** Gets the non-static method with the given name (and optionally parameter count) of the current class hierarchy. */
        method(name, parameterCount = -1) {
          return this.tryMethod(name, parameterCount) ?? raise(`couldn't find non-static method ${name} in hierarchy of class ${this.class.type.name}`);
        }
        /** Creates a reference to this object. */
        ref(pin) {
          return new Il2Cpp3.GCHandle(Il2Cpp3.exports.gcHandleNew(this, +pin));
        }
        /** Gets the correct virtual method from the given virtual method. */
        virtualMethod(method) {
          return new Il2Cpp3.Method(Il2Cpp3.exports.objectGetVirtualMethod(this, method)).bind(this);
        }
        /** Gets the non-static field with the given name of the current class hierarchy, if it exists. */
        tryField(name) {
          const field = this.class.tryField(name);
          if (field?.isStatic) {
            for (const klass of this.class.hierarchy({ includeCurrent: false })) {
              for (const field2 of klass.fields) {
                if (field2.name == name && !field2.isStatic) {
                  return field2.bind(this);
                }
              }
            }
            return void 0;
          }
          return field?.bind(this);
        }
        /** Gets the non-static method with the given name (and optionally parameter count) of the current class hierarchy, if it exists. */
        tryMethod(name, parameterCount = -1) {
          const method = this.class.tryMethod(name, parameterCount);
          if (method?.isStatic) {
            for (const klass of this.class.hierarchy()) {
              for (const method2 of klass.methods) {
                if (method2.name == name && !method2.isStatic && (parameterCount < 0 || method2.parameterCount == parameterCount)) {
                  return method2.bind(this);
                }
              }
            }
            return void 0;
          }
          return method?.bind(this);
        }
        /** */
        toString() {
          return this.isNull() ? "null" : this.method("ToString", 0).invoke().content ?? "null";
        }
        /** Unboxes the value type (either a primitive, a struct or an enum) out of this object. */
        unbox() {
          return this.class.isValueType ? new Il2Cpp3.ValueType(Il2Cpp3.exports.objectUnbox(this), this.class.type) : raise(`couldn't unbox instances of ${this.class.type.name} as they are not value types`);
        }
        /** Creates a weak reference to this object. */
        weakRef(trackResurrection) {
          return new Il2Cpp3.GCHandle(Il2Cpp3.exports.gcHandleNewWeakRef(this, +trackResurrection));
        }
      }
      __decorate([
        lazy
      ], Object2.prototype, "class", null);
      __decorate([
        lazy
      ], Object2.prototype, "size", null);
      __decorate([
        lazy
      ], Object2, "headerSize", null);
      Il2Cpp3.Object = Object2;
      (function(Object3) {
        class Monitor {
          handle;
          /** @internal */
          constructor(handle) {
            this.handle = handle;
          }
          /** Acquires an exclusive lock on the current object. */
          enter() {
            return Il2Cpp3.exports.monitorEnter(this.handle);
          }
          /** Release an exclusive lock on the current object. */
          exit() {
            return Il2Cpp3.exports.monitorExit(this.handle);
          }
          /** Notifies a thread in the waiting queue of a change in the locked object's state. */
          pulse() {
            return Il2Cpp3.exports.monitorPulse(this.handle);
          }
          /** Notifies all waiting threads of a change in the object's state. */
          pulseAll() {
            return Il2Cpp3.exports.monitorPulseAll(this.handle);
          }
          /** Attempts to acquire an exclusive lock on the current object. */
          tryEnter(timeout) {
            return !!Il2Cpp3.exports.monitorTryEnter(this.handle, timeout);
          }
          /** Releases the lock on an object and attempts to block the current thread until it reacquires the lock. */
          tryWait(timeout) {
            return !!Il2Cpp3.exports.monitorTryWait(this.handle, timeout);
          }
          /** Releases the lock on an object and blocks the current thread until it reacquires the lock. */
          wait() {
            return Il2Cpp3.exports.monitorWait(this.handle);
          }
        }
        Object3.Monitor = Monitor;
      })(Object2 = Il2Cpp3.Object || (Il2Cpp3.Object = {}));
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Parameter {
        /** Name of this parameter. */
        name;
        /** Position of this parameter. */
        position;
        /** Type of this parameter. */
        type;
        constructor(name, position, type) {
          this.name = name;
          this.position = position;
          this.type = type;
        }
        /** */
        toString() {
          return `${this.type.name} ${this.name}`;
        }
      }
      Il2Cpp3.Parameter = Parameter;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Pointer extends NativeStruct {
        type;
        constructor(handle, type) {
          super(handle);
          this.type = type;
        }
        /** Gets the element at the given index. */
        get(index) {
          return Il2Cpp3.read(this.handle.add(index * this.type.class.arrayElementSize), this.type);
        }
        /** Reads the given amount of elements starting at the given offset. */
        read(length, offset = 0) {
          const values = new globalThis.Array(length);
          for (let i = 0; i < length; i++) {
            values[i] = this.get(i + offset);
          }
          return values;
        }
        /** Sets the given element at the given index */
        set(index, value) {
          Il2Cpp3.write(this.handle.add(index * this.type.class.arrayElementSize), value, this.type);
        }
        /** */
        toString() {
          return this.handle.toString();
        }
        /** Writes the given elements starting at the given index. */
        write(values, offset = 0) {
          for (let i = 0; i < values.length; i++) {
            this.set(i + offset, values[i]);
          }
        }
      }
      Il2Cpp3.Pointer = Pointer;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Reference extends NativeStruct {
        type;
        constructor(handle, type) {
          super(handle);
          this.type = type;
        }
        /** Gets the element referenced by the current reference. */
        get value() {
          return Il2Cpp3.read(this.handle, this.type);
        }
        /** Sets the element referenced by the current reference. */
        set value(value) {
          Il2Cpp3.write(this.handle, value, this.type);
        }
        /** */
        toString() {
          return this.isNull() ? "null" : `->${this.value}`;
        }
      }
      Il2Cpp3.Reference = Reference;
      function reference(value, type) {
        const handle = Memory.alloc(Process.pointerSize);
        switch (typeof value) {
          case "boolean":
            return new Il2Cpp3.Reference(handle.writeS8(+value), Il2Cpp3.corlib.class("System.Boolean").type);
          case "number":
            switch (type?.enumValue) {
              case Il2Cpp3.Type.Enum.UBYTE:
                return new Il2Cpp3.Reference(handle.writeU8(value), type);
              case Il2Cpp3.Type.Enum.BYTE:
                return new Il2Cpp3.Reference(handle.writeS8(value), type);
              case Il2Cpp3.Type.Enum.CHAR:
              case Il2Cpp3.Type.Enum.USHORT:
                return new Il2Cpp3.Reference(handle.writeU16(value), type);
              case Il2Cpp3.Type.Enum.SHORT:
                return new Il2Cpp3.Reference(handle.writeS16(value), type);
              case Il2Cpp3.Type.Enum.UINT:
                return new Il2Cpp3.Reference(handle.writeU32(value), type);
              case Il2Cpp3.Type.Enum.INT:
                return new Il2Cpp3.Reference(handle.writeS32(value), type);
              case Il2Cpp3.Type.Enum.ULONG:
                return new Il2Cpp3.Reference(handle.writeU64(value), type);
              case Il2Cpp3.Type.Enum.LONG:
                return new Il2Cpp3.Reference(handle.writeS64(value), type);
              case Il2Cpp3.Type.Enum.FLOAT:
                return new Il2Cpp3.Reference(handle.writeFloat(value), type);
              case Il2Cpp3.Type.Enum.DOUBLE:
                return new Il2Cpp3.Reference(handle.writeDouble(value), type);
            }
          case "object":
            if (value instanceof Il2Cpp3.ValueType || value instanceof Il2Cpp3.Pointer) {
              return new Il2Cpp3.Reference(value.handle, value.type);
            } else if (value instanceof Il2Cpp3.Object) {
              return new Il2Cpp3.Reference(handle.writePointer(value), value.class.type);
            } else if (value instanceof Il2Cpp3.String || value instanceof Il2Cpp3.Array) {
              return new Il2Cpp3.Reference(handle.writePointer(value), value.object.class.type);
            } else if (value instanceof NativePointer) {
              switch (type?.enumValue) {
                case Il2Cpp3.Type.Enum.NUINT:
                case Il2Cpp3.Type.Enum.NINT:
                  return new Il2Cpp3.Reference(handle.writePointer(value), type);
              }
            } else if (value instanceof Int64) {
              return new Il2Cpp3.Reference(handle.writeS64(value), Il2Cpp3.corlib.class("System.Int64").type);
            } else if (value instanceof UInt64) {
              return new Il2Cpp3.Reference(handle.writeU64(value), Il2Cpp3.corlib.class("System.UInt64").type);
            }
          default:
            raise(`couldn't create a reference to ${value} using an unhandled type ${type?.name}`);
        }
      }
      Il2Cpp3.reference = reference;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class String extends NativeStruct {
        /** Gets the content of this string. */
        get content() {
          return Il2Cpp3.exports.stringGetChars(this).readUtf16String(this.length);
        }
        /** @unsafe Sets the content of this string - it may write out of bounds! */
        set content(value) {
          const offset = Il2Cpp3.string("vfsfitvnm").handle.offsetOf((_) => _.readInt() == 9) ?? raise("couldn't find the length offset in the native string struct");
          globalThis.Object.defineProperty(Il2Cpp3.String.prototype, "content", {
            set(value2) {
              Il2Cpp3.exports.stringGetChars(this).writeUtf16String(value2 ?? "");
              this.handle.add(offset).writeS32(value2?.length ?? 0);
            }
          });
          this.content = value;
        }
        /** Gets the length of this string. */
        get length() {
          return Il2Cpp3.exports.stringGetLength(this);
        }
        /** Gets the encompassing object of the current string. */
        get object() {
          return new Il2Cpp3.Object(this);
        }
        /** */
        toString() {
          return this.isNull() ? "null" : `"${this.content}"`;
        }
      }
      Il2Cpp3.String = String;
      function string(content) {
        return new Il2Cpp3.String(Il2Cpp3.exports.stringNew(Memory.allocUtf8String(content ?? "")));
      }
      Il2Cpp3.string = string;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class Thread extends NativeStruct {
        /** Gets the native id of the current thread. */
        get id() {
          let get = function() {
            return this.internal.field("thread_id").value.toNumber();
          };
          if (Process.platform != "windows") {
            const currentThreadId = Process.getCurrentThreadId();
            const currentPosixThread = ptr(get.apply(Il2Cpp3.currentThread));
            const offset = currentPosixThread.offsetOf((_) => _.readS32() == currentThreadId, 1024) ?? raise(`couldn't find the offset for determining the kernel id of a posix thread`);
            const _get = get;
            get = function() {
              return ptr(_get.apply(this)).add(offset).readS32();
            };
          }
          getter(Il2Cpp3.Thread.prototype, "id", get, lazy);
          return this.id;
        }
        /** Gets the encompassing internal object (System.Threding.InternalThreead) of the current thread. */
        get internal() {
          return this.object.tryField("internal_thread")?.value ?? this.object;
        }
        /** Determines whether the current thread is the garbage collector finalizer one. */
        get isFinalizer() {
          return !Il2Cpp3.exports.threadIsVm(this);
        }
        /** Gets the managed id of the current thread. */
        get managedId() {
          return this.object.method("get_ManagedThreadId").invoke();
        }
        /** Gets the encompassing object of the current thread. */
        get object() {
          return new Il2Cpp3.Object(this);
        }
        /** @internal */
        get staticData() {
          return this.internal.field("static_data").value;
        }
        /** @internal */
        get synchronizationContext() {
          const get_ExecutionContext = this.object.tryMethod("GetMutableExecutionContext") ?? this.object.method("get_ExecutionContext");
          const executionContext = get_ExecutionContext.invoke();
          const synchronizationContext = executionContext.tryField("_syncContext")?.value ?? executionContext.tryMethod("get_SynchronizationContext")?.invoke() ?? this.tryLocalValue(Il2Cpp3.corlib.class("System.Threading.SynchronizationContext"));
          return synchronizationContext?.asNullable() ?? null;
        }
        /** Detaches the thread from the application domain. */
        detach() {
          return Il2Cpp3.exports.threadDetach(this);
        }
        /** Schedules a callback on the current thread. */
        schedule(block) {
          const Post = this.synchronizationContext?.tryMethod("Post");
          if (Post == null) {
            return Process.runOnThread(this.id, block);
          }
          return new Promise((resolve) => {
            const delegate = Il2Cpp3.delegate(Il2Cpp3.corlib.class("System.Threading.SendOrPostCallback"), () => {
              const result = block();
              setImmediate(() => resolve(result));
            });
            Script.bindWeak(globalThis, () => {
              delegate.field("method_ptr").value = delegate.field("invoke_impl").value = Il2Cpp3.exports.domainGet;
            });
            Post.invoke(delegate, NULL);
          });
        }
        /** @internal */
        tryLocalValue(klass) {
          for (let i = 0; i < 16; i++) {
            const base = this.staticData.add(i * Process.pointerSize).readPointer();
            if (!base.isNull()) {
              const object = new Il2Cpp3.Object(base.readPointer()).asNullable();
              if (object?.class?.isSubclassOf(klass, false)) {
                return object;
              }
            }
          }
        }
      }
      __decorate([
        lazy
      ], Thread.prototype, "internal", null);
      __decorate([
        lazy
      ], Thread.prototype, "isFinalizer", null);
      __decorate([
        lazy
      ], Thread.prototype, "managedId", null);
      __decorate([
        lazy
      ], Thread.prototype, "object", null);
      __decorate([
        lazy
      ], Thread.prototype, "staticData", null);
      __decorate([
        lazy
      ], Thread.prototype, "synchronizationContext", null);
      Il2Cpp3.Thread = Thread;
      getter(Il2Cpp3, "attachedThreads", () => {
        if (Il2Cpp3.exports.threadGetAttachedThreads.isNull()) {
          const currentThreadHandle = Il2Cpp3.currentThread?.handle ?? raise("Current thread is not attached to IL2CPP");
          const pattern = currentThreadHandle.toMatchPattern();
          const threads = [];
          for (const range of Process.enumerateRanges("rw-")) {
            if (range.file == void 0) {
              const matches = Memory.scanSync(range.base, range.size, pattern);
              if (matches.length == 1) {
                while (true) {
                  const handle = matches[0].address.sub(matches[0].size * threads.length).readPointer();
                  if (handle.isNull() || !handle.readPointer().equals(currentThreadHandle.readPointer())) {
                    break;
                  }
                  threads.unshift(new Il2Cpp3.Thread(handle));
                }
                break;
              }
            }
          }
          return threads;
        }
        return readNativeList(Il2Cpp3.exports.threadGetAttachedThreads).map((_) => new Il2Cpp3.Thread(_));
      });
      getter(Il2Cpp3, "currentThread", () => {
        return new Il2Cpp3.Thread(Il2Cpp3.exports.threadGetCurrent()).asNullable();
      });
      getter(Il2Cpp3, "mainThread", () => {
        return Il2Cpp3.attachedThreads[0];
      });
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      let Type = class Type extends NativeStruct {
        /** */
        static get Enum() {
          const _ = (_2, block = (_3) => _3) => block(Il2Cpp3.corlib.class(_2)).type.enumValue;
          const initial = {
            VOID: _("System.Void"),
            BOOLEAN: _("System.Boolean"),
            CHAR: _("System.Char"),
            BYTE: _("System.SByte"),
            UBYTE: _("System.Byte"),
            SHORT: _("System.Int16"),
            USHORT: _("System.UInt16"),
            INT: _("System.Int32"),
            UINT: _("System.UInt32"),
            LONG: _("System.Int64"),
            ULONG: _("System.UInt64"),
            NINT: _("System.IntPtr"),
            NUINT: _("System.UIntPtr"),
            FLOAT: _("System.Single"),
            DOUBLE: _("System.Double"),
            POINTER: _("System.IntPtr", (_2) => _2.field("m_value")),
            VALUE_TYPE: _("System.Decimal"),
            OBJECT: _("System.Object"),
            STRING: _("System.String"),
            CLASS: _("System.Array"),
            ARRAY: _("System.Void", (_2) => _2.arrayClass),
            NARRAY: _("System.Void", (_2) => new Il2Cpp3.Class(Il2Cpp3.exports.classGetArrayClass(_2, 2))),
            GENERIC_INSTANCE: _("System.Int32", (_2) => _2.interfaces.find((_3) => _3.name.endsWith("`1")))
          };
          Reflect.defineProperty(this, "Enum", { value: initial });
          return addFlippedEntries({
            ...initial,
            VAR: _("System.Action`1", (_2) => _2.generics[0]),
            MVAR: _("System.Array", (_2) => _2.method("AsReadOnly", 1).generics[0])
          });
        }
        /** Gets the class of this type. */
        get class() {
          return new Il2Cpp3.Class(Il2Cpp3.exports.typeGetClass(this));
        }
        /** */
        get fridaAlias() {
          function getValueTypeFields(type) {
            const instanceFields = type.class.fields.filter((_) => !_.isStatic);
            return instanceFields.length == 0 ? ["char"] : instanceFields.map((_) => _.type.fridaAlias);
          }
          if (this.isByReference) {
            return "pointer";
          }
          switch (this.enumValue) {
            case Il2Cpp3.Type.Enum.VOID:
              return "void";
            case Il2Cpp3.Type.Enum.BOOLEAN:
              return "bool";
            case Il2Cpp3.Type.Enum.CHAR:
              return "uchar";
            case Il2Cpp3.Type.Enum.BYTE:
              return "int8";
            case Il2Cpp3.Type.Enum.UBYTE:
              return "uint8";
            case Il2Cpp3.Type.Enum.SHORT:
              return "int16";
            case Il2Cpp3.Type.Enum.USHORT:
              return "uint16";
            case Il2Cpp3.Type.Enum.INT:
              return "int32";
            case Il2Cpp3.Type.Enum.UINT:
              return "uint32";
            case Il2Cpp3.Type.Enum.LONG:
              return "int64";
            case Il2Cpp3.Type.Enum.ULONG:
              return "uint64";
            case Il2Cpp3.Type.Enum.FLOAT:
              return "float";
            case Il2Cpp3.Type.Enum.DOUBLE:
              return "double";
            case Il2Cpp3.Type.Enum.NINT:
            case Il2Cpp3.Type.Enum.NUINT:
            case Il2Cpp3.Type.Enum.POINTER:
            case Il2Cpp3.Type.Enum.STRING:
            case Il2Cpp3.Type.Enum.ARRAY:
            case Il2Cpp3.Type.Enum.NARRAY:
              return "pointer";
            case Il2Cpp3.Type.Enum.VALUE_TYPE:
              return this.class.isEnum ? this.class.baseType.fridaAlias : getValueTypeFields(this);
            case Il2Cpp3.Type.Enum.CLASS:
            case Il2Cpp3.Type.Enum.OBJECT:
            case Il2Cpp3.Type.Enum.GENERIC_INSTANCE:
              return this.class.isStruct ? getValueTypeFields(this) : this.class.isEnum ? this.class.baseType.fridaAlias : "pointer";
            default:
              return "pointer";
          }
        }
        /** Determines whether this type is passed by reference. */
        get isByReference() {
          return this.name.endsWith("&");
        }
        /** Determines whether this type is primitive. */
        get isPrimitive() {
          switch (this.enumValue) {
            case Il2Cpp3.Type.Enum.BOOLEAN:
            case Il2Cpp3.Type.Enum.CHAR:
            case Il2Cpp3.Type.Enum.BYTE:
            case Il2Cpp3.Type.Enum.UBYTE:
            case Il2Cpp3.Type.Enum.SHORT:
            case Il2Cpp3.Type.Enum.USHORT:
            case Il2Cpp3.Type.Enum.INT:
            case Il2Cpp3.Type.Enum.UINT:
            case Il2Cpp3.Type.Enum.LONG:
            case Il2Cpp3.Type.Enum.ULONG:
            case Il2Cpp3.Type.Enum.FLOAT:
            case Il2Cpp3.Type.Enum.DOUBLE:
            case Il2Cpp3.Type.Enum.NINT:
            case Il2Cpp3.Type.Enum.NUINT:
              return true;
            default:
              return false;
          }
        }
        /** Gets the name of this type. */
        get name() {
          const handle = Il2Cpp3.exports.typeGetName(this);
          try {
            return handle.readUtf8String();
          } finally {
            Il2Cpp3.free(handle);
          }
        }
        /** Gets the encompassing object of the current type. */
        get object() {
          return new Il2Cpp3.Object(Il2Cpp3.exports.typeGetObject(this));
        }
        /** Gets the {@link Il2Cpp.Type.Enum} value of the current type. */
        get enumValue() {
          return Il2Cpp3.exports.typeGetTypeEnum(this);
        }
        is(other) {
          if (Il2Cpp3.exports.typeEquals.isNull()) {
            return this.object.method("Equals").invoke(other.object);
          }
          return !!Il2Cpp3.exports.typeEquals(this, other);
        }
        /** */
        toString() {
          return this.name;
        }
      };
      __decorate([
        lazy
      ], Type.prototype, "class", null);
      __decorate([
        lazy
      ], Type.prototype, "fridaAlias", null);
      __decorate([
        lazy
      ], Type.prototype, "isByReference", null);
      __decorate([
        lazy
      ], Type.prototype, "isPrimitive", null);
      __decorate([
        lazy
      ], Type.prototype, "name", null);
      __decorate([
        lazy
      ], Type.prototype, "object", null);
      __decorate([
        lazy
      ], Type.prototype, "enumValue", null);
      __decorate([
        lazy
      ], Type, "Enum", null);
      Type = __decorate([
        recycle
      ], Type);
      Il2Cpp3.Type = Type;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    (function(Il2Cpp3) {
      class ValueType extends NativeStruct {
        type;
        constructor(handle, type) {
          super(handle);
          this.type = type;
        }
        /** Boxes the current value type in a object. */
        box() {
          return new Il2Cpp3.Object(Il2Cpp3.exports.valueTypeBox(this.type.class, this));
        }
        /** Gets the non-static field with the given name of the current class hierarchy. */
        field(name) {
          return this.tryField(name) ?? raise(`couldn't find non-static field ${name} in hierarchy of class ${this.type.name}`);
        }
        /** Gets the non-static method with the given name (and optionally parameter count) of the current class hierarchy. */
        method(name, parameterCount = -1) {
          return this.tryMethod(name, parameterCount) ?? raise(`couldn't find non-static method ${name} in hierarchy of class ${this.type.name}`);
        }
        /** Gets the non-static field with the given name of the current class hierarchy, if it exists. */
        tryField(name) {
          const field = this.type.class.tryField(name);
          if (field?.isStatic) {
            for (const klass of this.type.class.hierarchy()) {
              for (const field2 of klass.fields) {
                if (field2.name == name && !field2.isStatic) {
                  return field2.bind(this);
                }
              }
            }
            return void 0;
          }
          return field?.bind(this);
        }
        /** Gets the non-static method with the given name (and optionally parameter count) of the current class hierarchy, if it exists. */
        tryMethod(name, parameterCount = -1) {
          const method = this.type.class.tryMethod(name, parameterCount);
          if (method?.isStatic) {
            for (const klass of this.type.class.hierarchy()) {
              for (const method2 of klass.methods) {
                if (method2.name == name && !method2.isStatic && (parameterCount < 0 || method2.parameterCount == parameterCount)) {
                  return method2.bind(this);
                }
              }
            }
            return void 0;
          }
          return method?.bind(this);
        }
        /** */
        toString() {
          const ToString = this.method("ToString", 0);
          return this.isNull() ? "null" : (
            // If ToString is defined within a value type class, we can
            // avoid a boxing operation.
            ToString.class.isValueType ? ToString.invoke().content ?? "null" : this.box().toString() ?? "null"
          );
        }
      }
      Il2Cpp3.ValueType = ValueType;
    })(Il2Cpp2 || (Il2Cpp2 = {}));
    globalThis.Il2Cpp = Il2Cpp2;
  }
});

// hook.cjs
var require_hook = __commonJS({
  "hook.cjs"() {
    init_node_globals();
    init_dist();
    rpc.exports = {
      hash(samples) {
        Il2Cpp.perform(() => {
          const asm = Il2Cpp.domain.assembly("Assembly-CSharp");
          const image = asm.image;
          const AmberHash = image.class("Amber.Hash");
          const getHash = AmberHash.method("GetHashCode");
          for (const s of samples) {
            const h = getHash.invoke(Il2Cpp.string(s), 0);
            send(`${s},${h}`);
          }
          send("done");
        });
      }
    };
  }
});
export default require_hook();

✄
{
  "version": 3,
  "sources": ["frida-builtins:/node-globals.js", "node_modules/frida-il2cpp-bridge/dist/application.ts", "node_modules/frida-il2cpp-bridge/dist/boxed.ts", "node_modules/frida-il2cpp-bridge/dist/config.ts", "node_modules/frida-il2cpp-bridge/dist/dump.ts", "node_modules/frida-il2cpp-bridge/dist/exception-listener.ts", "node_modules/frida-il2cpp-bridge/dist/exports.ts", "node_modules/frida-il2cpp-bridge/dist/filters.ts", "node_modules/frida-il2cpp-bridge/dist/gc.ts", "node_modules/frida-il2cpp-bridge/dist/utils/android.ts", "node_modules/frida-il2cpp-bridge/dist/utils/console.ts", "node_modules/frida-il2cpp-bridge/dist/utils/decorate.ts", "node_modules/frida-il2cpp-bridge/dist/utils/getter.ts", "node_modules/frida-il2cpp-bridge/dist/utils/hash.ts", "node_modules/frida-il2cpp-bridge/dist/utils/lazy.ts", "node_modules/frida-il2cpp-bridge/dist/utils/native-struct.ts", "node_modules/frida-il2cpp-bridge/dist/utils/object.ts", "node_modules/frida-il2cpp-bridge/dist/utils/offset-of.ts", "node_modules/frida-il2cpp-bridge/dist/utils/read-native-iterator.ts", "node_modules/frida-il2cpp-bridge/dist/utils/read-native-list.ts", "node_modules/frida-il2cpp-bridge/dist/utils/recycle.ts", "node_modules/frida-il2cpp-bridge/dist/utils/unity-version.ts", "node_modules/frida-il2cpp-bridge/dist/memory.ts", "node_modules/frida-il2cpp-bridge/dist/module.ts", "node_modules/frida-il2cpp-bridge/dist/perform.ts", "node_modules/frida-il2cpp-bridge/dist/tracer.ts", "node_modules/frida-il2cpp-bridge/dist/structs/array.ts", "node_modules/frida-il2cpp-bridge/dist/structs/assembly.ts", "node_modules/frida-il2cpp-bridge/dist/structs/class.ts", "node_modules/frida-il2cpp-bridge/dist/structs/delegate.ts", "node_modules/frida-il2cpp-bridge/dist/structs/domain.ts", "node_modules/frida-il2cpp-bridge/dist/structs/field.ts", "node_modules/frida-il2cpp-bridge/dist/structs/gc-handle.ts", "node_modules/frida-il2cpp-bridge/dist/structs/image.ts", "node_modules/frida-il2cpp-bridge/dist/structs/memory-snapshot.ts", "node_modules/frida-il2cpp-bridge/dist/structs/method.ts", "node_modules/frida-il2cpp-bridge/dist/structs/object.ts", "node_modules/frida-il2cpp-bridge/dist/structs/parameter.ts", "node_modules/frida-il2cpp-bridge/dist/structs/pointer.ts", "node_modules/frida-il2cpp-bridge/dist/structs/reference.ts", "node_modules/frida-il2cpp-bridge/dist/structs/string.ts", "node_modules/frida-il2cpp-bridge/dist/structs/thread.ts", "node_modules/frida-il2cpp-bridge/dist/structs/type.ts", "node_modules/frida-il2cpp-bridge/dist/structs/value-type.ts", "node_modules/frida-il2cpp-bridge/dist/index.ts", "hook.cjs"],
  "mappings": "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",
  "names": ["getter", "obj", "Il2Cpp", "Android", "UnityVersion", "a", "b", "_", "module", "parameters", "method", "Array", "array", "delegate", "memorySnapshot", "i", "Object", "field", "value"]
}
