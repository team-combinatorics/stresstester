#include <stdio.h>
#include <windows.h>

typedef char* (*Hwinfo_C)();

int main() {
    // Check if the DLL file exists in the current folder
    const char* dllPath = "硬件检测引擎.dll";
    if (GetFileAttributesA(dllPath) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxA(NULL, "DLL不存在：硬件检测引擎.dll", "错误", MB_OK | MB_ICONERROR);
        return 1;
    }

    // Find the files matching the pattern "data\*.edb"
    WIN32_FIND_DATAA findData;
    HANDLE hFind = FindFirstFileA("data\\*.edb", &findData);
    if (hFind == INVALID_HANDLE_VALUE) {
        MessageBoxA(NULL, "资源文件不存在：data\\*.edb", "错误", MB_OK | MB_ICONINFORMATION);
        fprintf(stderr, "资源文件不存在：data\\*.edb");
        return 2;
    }

    // Load the DLL
    HMODULE hModule = LoadLibraryA(dllPath);
    if (hModule == NULL) {
        MessageBoxA(NULL, "加载DLL失败", "错误", MB_OK | MB_ICONERROR);
        fprintf(stderr, "加载DLL失败");
        return 3;
    }

    // Get the function address from the DLL
    Hwinfo_C hwinfoFunc = (Hwinfo_C)GetProcAddress(hModule, "Hwinfo_C");
    if (hwinfoFunc == NULL) {
        MessageBoxA(NULL, "获取DLL函数入口失败", "错误", MB_OK | MB_ICONERROR);
        fprintf(stderr, "获取DLL函数入口失败");
        return 4;
    }

    // Call the function from the DLL
    char* result = hwinfoFunc();
    if (result != NULL) {
        printf("%s", result);
    }
    else {
        MessageBoxA(NULL, "获取调用结果失败", "错误", MB_OK | MB_ICONERROR);
        fprintf(stderr, "获取调用结果失败");
        return 5;
    }

    // Free the DLL
    FreeLibrary(hModule);

    return 0;
}