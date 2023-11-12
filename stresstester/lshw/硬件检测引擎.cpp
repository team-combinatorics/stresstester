#include <stdio.h>
#include <windows.h>

typedef char* (*Hwinfo_C)();

int main() {
    // Check if the DLL file exists in the current folder
    const char* dllPath = "Ӳ���������.dll";
    if (GetFileAttributesA(dllPath) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxA(NULL, "DLL�����ڣ�Ӳ���������.dll", "����", MB_OK | MB_ICONERROR);
        return 1;
    }

    // Find the files matching the pattern "data\*.edb"
    WIN32_FIND_DATAA findData;
    HANDLE hFind = FindFirstFileA("data\\*.edb", &findData);
    if (hFind == INVALID_HANDLE_VALUE) {
        MessageBoxA(NULL, "��Դ�ļ������ڣ�data\\*.edb", "����", MB_OK | MB_ICONINFORMATION);
        fprintf(stderr, "��Դ�ļ������ڣ�data\\*.edb");
        return 2;
    }

    // Load the DLL
    HMODULE hModule = LoadLibraryA(dllPath);
    if (hModule == NULL) {
        MessageBoxA(NULL, "����DLLʧ��", "����", MB_OK | MB_ICONERROR);
        fprintf(stderr, "����DLLʧ��");
        return 3;
    }

    // Get the function address from the DLL
    Hwinfo_C hwinfoFunc = (Hwinfo_C)GetProcAddress(hModule, "Hwinfo_C");
    if (hwinfoFunc == NULL) {
        MessageBoxA(NULL, "��ȡDLL�������ʧ��", "����", MB_OK | MB_ICONERROR);
        fprintf(stderr, "��ȡDLL�������ʧ��");
        return 4;
    }

    // Call the function from the DLL
    char* result = hwinfoFunc();
    if (result != NULL) {
        printf("%s", result);
    }
    else {
        MessageBoxA(NULL, "��ȡ���ý��ʧ��", "����", MB_OK | MB_ICONERROR);
        fprintf(stderr, "��ȡ���ý��ʧ��");
        return 5;
    }

    // Free the DLL
    FreeLibrary(hModule);

    return 0;
}