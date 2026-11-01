// Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <wchar.h>
#include <stdio.h>

static int launch(const wchar_t *args, int cli) {
    wchar_t folder[32768], program[32768], script[32768], command[65536];
    DWORD length = GetModuleFileNameW(NULL, folder, 32768);
    if (!length || length >= 32768) return 2;
    wchar_t *slash = wcsrchr(folder, L'\\');
    if (!slash) return 2;
    *slash = L'\0';
    swprintf(program, 32768, L"%ls\\runtime\\%ls", folder, cli ? L"python.exe" : L"pythonw.exe");
    swprintf(script, 32768, L"%ls\\app\\boot.py", folder);
    swprintf(command, 65536, L"\"%ls\" -I -S -B \"%ls\" %ls", program, script, args);
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    startup.cb = sizeof(startup);
    if (cli) {
        startup.dwFlags = STARTF_USESTDHANDLES;
        startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
        startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
        startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    }
    if (!CreateProcessW(program, command, NULL, NULL, cli, cli ? 0 : CREATE_NO_WINDOW, NULL, NULL, &startup, &process)) {
        if (!cli) MessageBoxW(NULL, L"Não foi possível iniciar o Amplia. Mantenha Amplia.exe junto das pastas app e runtime.", L"Amplia", MB_OK | MB_ICONERROR);
        else fwprintf(stderr, L"Falha ao iniciar Amplia: %lu\n", GetLastError());
        return 2;
    }
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD result = 2;
    GetExitCodeProcess(process.hProcess, &result);
    CloseHandle(process.hThread); CloseHandle(process.hProcess);
    return (int)result;
}

#ifdef CLI
int wmain(int argc, wchar_t **argv) {
    (void)argc; (void)argv;
    wchar_t *raw = GetCommandLineW();
    if (*raw == L'"') { raw++; while (*raw && *raw != L'"') raw++; if (*raw) raw++; }
    else { while (*raw && *raw != L' ') raw++; }
    while (*raw == L' ') raw++;
    return launch(*raw ? raw : L"--stdio", 1);
}
#else
int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR arguments, int show) {
    (void)instance; (void)previous; (void)show;
    return launch(arguments, 0);
}
#endif
