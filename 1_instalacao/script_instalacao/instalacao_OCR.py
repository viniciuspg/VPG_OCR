from pathlib import Path
import subprocess
import sys
import shutil
import ctypes
import time
import os
import winreg

APP_NOME = "VPG_OCR"


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    params = ' '.join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, None, 1)


def print_header(titulo):
    print('\n' + '=' * 68)
    print(titulo)
    print('=' * 68)


def run_command(cmd, check=True, capture=False):
    print('>> ' + ' '.join(str(c) for c in cmd))
    if capture:
        return subprocess.run(cmd, check=check, capture_output=True, text=True)
    return subprocess.run(cmd, check=check)


def get_install_root(script_folder: Path):
    return script_folder.parent


def get_install_files_folder(script_folder: Path):
    return get_install_root(script_folder) / 'arquivos'


def find_tesseract_installers(files_folder: Path):
    return sorted(files_folder.glob('tesseract-ocr-w64-setup-*.exe'))


def choose_installer(files_folder: Path):
    installers = find_tesseract_installers(files_folder)
    if not installers:
        return None, []
    return installers[-1], installers[:-1]


def install_ocrmypdf():
    print_header('1) Instalando/atualizando OCRmyPDF')
    run_command([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    run_command([sys.executable, '-m', 'pip', 'install', '--upgrade', 'ocrmypdf'])
    run_command([sys.executable, '-m', 'ocrmypdf', '--version'])


def install_tesseract(installer: Path, backups):
    print_header('2) Instalando Tesseract a partir do instalador local')
    print(f'Instalador principal escolhido automaticamente: {installer.name}')
    if backups:
        print('Instalador(es) de backup encontrado(s):')
        for b in backups:
            print(f' - {b.name}')
    print('\nATENCAO IMPORTANTE:')
    print('- Quando a janela do instalador do Tesseract abrir,')
    print('  selecione o idioma do instalador como: English')
    print('- Depois siga normalmente os passos ate concluir.')
    print('- Se o Windows pedir permissao, confirme a execucao.')
    subprocess.run([str(installer)], check=True)


def detect_tesseract_dir():
    candidatos = [
        Path(r'C:\Program Files\Tesseract-OCR'),
        Path(r'C:\Program Files (x86)\Tesseract-OCR'),
    ]
    for c in candidatos:
        if (c / 'tesseract.exe').exists():
            return c
    caminho = shutil.which('tesseract')
    if caminho:
        return Path(caminho).resolve().parent
    return None


def add_directory_to_system_path(directory: Path):
    path_str = str(directory)
    reg_path = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        current_path, reg_type = winreg.QueryValueEx(key, 'Path')
        parts = [p.strip() for p in current_path.split(';') if p.strip()]
        lower_parts = {p.lower() for p in parts}
        if path_str.lower() not in lower_parts:
            new_path = current_path.rstrip(';') + ';' + path_str if current_path else path_str
            winreg.SetValueEx(key, 'Path', 0, reg_type, new_path)
            # atualiza sessao atual do processo
            os.environ['PATH'] = path_str + ';' + os.environ.get('PATH', '')
            # avisa o Windows que o ambiente mudou
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                'Environment',
                SMTO_ABORTIFHUNG,
                5000,
                None,
            )
            return True
    # mesmo se ja existia, garante sessao atual
    os.environ['PATH'] = path_str + ';' + os.environ.get('PATH', '')
    return False


def copy_portuguese_language(src_por: Path, tesseract_dir: Path):
    print_header('3) Copiando o idioma português (por.traineddata)')
    tessdata = tesseract_dir / 'tessdata'
    tessdata.mkdir(parents=True, exist_ok=True)
    destino = tessdata / 'por.traineddata'
    shutil.copy2(src_por, destino)
    print(f'Arquivo copiado para: {destino}')


def verify_command_available(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def validate_installation():
    print_header('4) Validando instalação')
    try:
        run_command(['tesseract', '--version'])
    except Exception:
        print('ATENÇÃO: o comando tesseract ainda não foi reconhecido no PATH.')
    try:
        resultado = subprocess.run(['tesseract', '--list-langs'], capture_output=True, text=True, check=True)
        print(resultado.stdout)
        if 'por' not in (resultado.stdout + '\n' + resultado.stderr).lower():
            print('ATENÇÃO: o idioma português ainda não apareceu na lista.')
    except Exception:
        print('ATENÇÃO: não foi possível listar os idiomas do Tesseract neste momento.')
    try:
        run_command([sys.executable, '-m', 'ocrmypdf', '--version'])
    except Exception:
        print('ATENÇÃO: o OCRmyPDF não pôde ser validado agora.')


def main():
    pasta_script = Path(__file__).resolve().parent
    pasta_instalacao = get_install_root(pasta_script)
    pasta_arquivos = get_install_files_folder(pasta_script)

    print_header(f'{APP_NOME} - INSTALAÇÃO AUTOMATIZADA')
    print(f'Pasta da instalação: {pasta_instalacao}')
    print(f'Pasta do script de instalação: {pasta_script}')
    print(f'Pasta dos arquivos de instalação: {pasta_arquivos}')

    if not is_admin():
        print('Será solicitado o UAC do Windows para continuar.')
        relaunch_as_admin()
        sys.exit(0)

    if not pasta_arquivos.exists():
        print('ERRO: não encontrei a subpasta arquivos dentro de 1_instalacao.')
        sys.exit(1)

    installer, backups = choose_installer(pasta_arquivos)
    if not installer:
        print('ERRO: não encontrei o instalador local do Tesseract na subpasta arquivos.')
        sys.exit(1)

    por_file = pasta_arquivos / 'por.traineddata'
    if not por_file.exists():
        print('ERRO: não encontrei o arquivo por.traineddata na subpasta arquivos.')
        sys.exit(1)

    try:
        install_ocrmypdf()
        install_tesseract(installer, backups)
        time.sleep(2)

        tesseract_dir = detect_tesseract_dir()
        if not tesseract_dir:
            print('ERRO: não foi possível localizar a pasta do Tesseract após a instalação.')
            print('Verifique se a instalação do Tesseract foi concluída corretamente.')
            sys.exit(1)

        print_header('2.1) Ajustando PATH do Windows para o Tesseract')
        mudou = add_directory_to_system_path(tesseract_dir)
        if mudou:
            print(f'Pasta adicionada ao PATH do sistema: {tesseract_dir}')
        else:
            print(f'Pasta já estava no PATH do sistema: {tesseract_dir}')

        copy_portuguese_language(por_file, tesseract_dir)
        validate_installation()

        print_header('INSTALAÇÃO CONCLUÍDA')
        print('Próximo passo: abra a pasta 2_utilizacao e clique em 🚀_CLIQUE_AQUI_PARA_USAR_OCR.bat.')
    except Exception as e:
        print(f'ERRO durante a instalação: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
