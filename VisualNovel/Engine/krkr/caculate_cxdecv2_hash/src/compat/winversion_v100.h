/**
 *  windows version dll proxy, together with winversion.def
 *    v0.1, developed by devseed
 * 
*/

#ifndef _WINVERSION_H
#define _WINVERSION_H
#include <windows.h>
#ifdef __cplusplus
extern "C" {
#endif
#define WIVERSION_VERSION 100
#include "commdef_v110.h"

// macro and global declear
static HMODULE s_winversion = NULL;
#define WINVERSION_WRAP_FUNC(name) \
	static FARPROC s_##name; \
	__declspec(naked) void __wrap_##name() \
	{ \
		__asm jmp[s_##name] \
	}
#define WINVERSION_BIND_FUNC(name) s_##name = GetProcAddress(s_winversion, #name);

// export function define
WINVERSION_WRAP_FUNC(GetFileVersionInfoA)
WINVERSION_WRAP_FUNC(GetFileVersionInfoByHandle)
WINVERSION_WRAP_FUNC(GetFileVersionInfoExW)
WINVERSION_WRAP_FUNC(GetFileVersionInfoExA)
WINVERSION_WRAP_FUNC(GetFileVersionInfoSizeA)
WINVERSION_WRAP_FUNC(GetFileVersionInfoSizeExW)
WINVERSION_WRAP_FUNC(GetFileVersionInfoSizeExA)
WINVERSION_WRAP_FUNC(GetFileVersionInfoSizeW)
WINVERSION_WRAP_FUNC(GetFileVersionInfoW)
WINVERSION_WRAP_FUNC(VerFindFileA)
WINVERSION_WRAP_FUNC(VerFindFileW)
WINVERSION_WRAP_FUNC(VerInstallFileA)
WINVERSION_WRAP_FUNC(VerInstallFileW)
WINVERSION_WRAP_FUNC(VerLanguageNameA)
WINVERSION_WRAP_FUNC(VerLanguageNameW)
WINVERSION_WRAP_FUNC(VerQueryValueA)
WINVERSION_WRAP_FUNC(VerQueryValueW)

static void winversion_init()
{
	// origin version path
	char versionpath[MAX_PATH];
	GetSystemDirectoryA(versionpath, MAX_PATH);
	strcat(versionpath, "\\version.dll");
	s_winversion = LoadLibraryA(versionpath);

	// bind version apis
	WINVERSION_BIND_FUNC(GetFileVersionInfoA);
	WINVERSION_BIND_FUNC(GetFileVersionInfoByHandle);
	WINVERSION_BIND_FUNC(GetFileVersionInfoExW);
	WINVERSION_BIND_FUNC(GetFileVersionInfoExA);
	WINVERSION_BIND_FUNC(GetFileVersionInfoSizeA);
	WINVERSION_BIND_FUNC(GetFileVersionInfoSizeExW);
	WINVERSION_BIND_FUNC(GetFileVersionInfoSizeExA);
	WINVERSION_BIND_FUNC(GetFileVersionInfoSizeW);
	WINVERSION_BIND_FUNC(GetFileVersionInfoW);
	WINVERSION_BIND_FUNC(VerFindFileA);
	WINVERSION_BIND_FUNC(VerFindFileW);
	WINVERSION_BIND_FUNC(VerInstallFileA);
	WINVERSION_BIND_FUNC(VerInstallFileW);
	WINVERSION_BIND_FUNC(VerLanguageNameA);
	WINVERSION_BIND_FUNC(VerLanguageNameW);
	WINVERSION_BIND_FUNC(VerQueryValueA);
	WINVERSION_BIND_FUNC(VerQueryValueW);
}
#ifdef __cplusplus
}
#endif
#endif