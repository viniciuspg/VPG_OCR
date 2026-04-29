from pathlib import Path
import subprocess
import sys
import shutil
import ctypes
import time

APP_NOME = "VPG_OCR"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    params = ' '.join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, None, 1)


def print_header(titulo):
    print('\n' + '=' * 68)
    print(titulo)
    print('=' * 68)


def run_command(cmd, check=True):
    print('>> ' + ' '.join(str(c) for c in cmd))
    return subprocess.run(cmd, check=check)


def get_install_root(script_folder: Path):
    return script_folder.parent


def get_install_files_folder(script_folder: Path):
    return get_install_root(script_folder) / 'arquivos'


def find_tesseract_installers(files_folder: Path):
    return sorted(files_folder.glob('tesseract-ocr-w64-setup-*.exe'))


def choose_installer(files_folder: Path):
    installers = find_tesseract_installers(files_folder)
    return (installers[-1], installers[:-1]) if installers else (None, [])


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
    print('O instalador do Tesseract será aberto agora.')
    subprocess.run([str(installer)], check=True)


def detect_tesseract_dir():
    for c in [Path(r'C:\Program Files\Tesseract-OCR'), Path(r'C:\Program Files (x86)\Tesseract-OCR')]:
        if c.exists(): return c
    caminho = shutil.which('tesseract')
    return Path(caminho).resolve().parent if caminho else None


def copy_portuguese_language(src_por: Path, tesseract_dir: Path):
    print_header('3) Copiando o idioma português (por.traineddata)')
    tessdata = tesseract_dir / 'tessdata'
    tessdata.mkdir(parents=True, exist_ok=True)
    destino = tessdata / 'por.traineddata'
    shutil.copy2(src_por, destino)
    print(f'Arquivo copiado para: {destino}')


def validate_installation():
    print_header('4) Validando instalação')
    try: run_command(['tesseract', '--version'])
    except Exception: print('ATENÇÃO: o comando tesseract ainda não foi reconhecido no PATH.')
    try: print(subprocess.run(['tesseract', '--list-langs'], capture_output=True, text=True, check=True).stdout)
    except Exception: print('ATENÇÃO: não foi possível listar os idiomas do Tesseract neste momento.')
    try: run_command([sys.executable, '-m', 'ocrmypdf', '--version'])
    except Exception: print('ATENÇÃO: o OCRmyPDF não pôde ser validado agora.')


def main():
    pasta_script = Path(__file__).resolve().parent
    pasta_instalacao = get_install_root(pasta_script)
    pasta_arquivos = get_install_files_folder(pasta_script)
    print_header(f'{APP_NOME} - INSTALAÇÃO AUTOMATIZADA')
    print(f'Pasta da instalação: {pasta_instalacao}')
    print(f'Pasta do script de instalação: {pasta_script}')
    print(f'Pasta dos arquivos de instalação: {pasta_arquivos}')

    if not is_admin():
        relaunch_as_admin(); sys.exit(0)
    if not pasta_arquivos.exists():
        print('ERRO: não encontrei a subpasta arquivos dentro de 1_instalacao.'); sys.exit(1)
    installer, backups = choose_installer(pasta_arquivos)
    if not installer:
        print('ERRO: não encontrei o instalador local do Tesseract na subpasta arquivos.'); sys.exit(1)
    por_file = pasta_arquivos / 'por.traineddata'
    if not por_file.exists():
        print('ERRO: não encontrei o arquivo por.traineddata na subpasta arquivos.'); sys.exit(1)
    install_ocrmypdf(); install_tesseract(installer, backups); time.sleep(2)
    tesseract_dir = detect_tesseract_dir()
    if not tesseract_dir:
        print('ERRO: não foi possível localizar a pasta do Tesseract após a instalação.'); sys.exit(1)
    copy_portuguese_language(por_file, tesseract_dir); validate_installation()
    print_header('INSTALAÇÃO CONCLUÍDA')
    print('Próximo passo: abra a pasta 2_utilizacao e clique em 🚀_CLIQUE_AQUI_PARA_USAR_OCR.bat.')

if __name__ == '__main__':
    main()
