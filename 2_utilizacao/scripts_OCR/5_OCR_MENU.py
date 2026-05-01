from pathlib import Path
import subprocess
import sys
import shutil

APP_NOME = "VPG_OCR"
PASTA_ENTRADA = "ENTRADA_coloque_aqui_seus_pdfs"
PASTA_SAIDA = "SAIDA_pdfs_processados"
ARQ_USER_WORDS = "user-words.txt"
ARQ_USER_PATTERNS = "user-patterns.txt"
SUFIXOS_PROCESSADOS = ("_OCR", "_OCR_OTIM", "_OCR_REDO", "_OCR_FORCE", "_OCR_HIST")


def verificar_ocrmypdf():
    try:
        subprocess.run([sys.executable, "-m", "ocrmypdf", "--version"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def verificar_tesseract():
    return shutil.which("tesseract") is not None


def verificar_pngquant():
    return shutil.which("pngquant") is not None


def verificar_idioma_portugues():
    try:
        resultado = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, check=True)
        saida = (resultado.stdout + "\n" + resultado.stderr).lower()
        return "por" in saida
    except Exception:
        return False


def obter_pastas(base: Path):
    pasta_entrada = base / PASTA_ENTRADA
    pasta_saida = base / PASTA_SAIDA
    pasta_entrada.mkdir(parents=True, exist_ok=True)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    return pasta_entrada, pasta_saida


def arquivo_aux_valido(path: Path):
    return path.exists() and path.is_file() and path.read_text(encoding='utf-8', errors='ignore').strip() != ""


def obter_arquivos_auxiliares(pasta_scripts: Path):
    user_words = pasta_scripts / ARQ_USER_WORDS
    user_patterns = pasta_scripts / ARQ_USER_PATTERNS
    return (
        user_words if arquivo_aux_valido(user_words) else None,
        user_patterns if arquivo_aux_valido(user_patterns) else None,
    )


def pdf_ja_processado(pdf: Path):
    return pdf.stem.endswith(SUFIXOS_PROCESSADOS)


def listar_pdfs_originais(pasta_entrada: Path):
    return sorted([p for p in pasta_entrada.glob("*.pdf") if not pdf_ja_processado(p)])


def montar_comando(entrada: Path, saida: Path, pasta_scripts: Path, *, modo: str = "skip", otimizar: bool = False,
                   usar_patterns: bool = True, jobs: int | None = None, historico: bool = False):
    comando = [sys.executable, "-m", "ocrmypdf", "-l", "por", "--mode", modo]

    if modo != "redo":
        comando.append("--deskew")

    if historico:
        comando.append("--rotate-pages")

    if otimizar:
        comando.extend(["--optimize", "3"])

    if jobs:
        comando.extend(["--jobs", str(jobs)])

    user_words, user_patterns = obter_arquivos_auxiliares(pasta_scripts)
    if user_words:
        comando.extend(["--user-words", str(user_words)])
    if usar_patterns and user_patterns:
        comando.extend(["--user-patterns", str(user_patterns)])

    comando.extend([str(entrada), str(saida)])
    return comando, user_words, (user_patterns if usar_patterns else None)


def _sufixo_saida(modo: str, otimizar: bool = False, historico: bool = False):
    if historico:
        return "_OCR_HIST.pdf"
    if modo == "skip" and otimizar:
        return "_OCR_OTIM.pdf"
    if modo == "skip":
        return "_OCR.pdf"
    if modo == "redo":
        return "_OCR_REDO.pdf"
    if modo == "force":
        return "_OCR_FORCE.pdf"
    raise ValueError("Modo inválido")


def executar_comando(comando, arquivo_saida: Path, desc_tentativa: str):
    print(f"[TENTATIVA]  {desc_tentativa}")
    print(f"[COMANDO]    {' '.join(str(c) for c in comando)}")
    try:
        subprocess.run(comando, check=True)
        print(f"[OK] Arquivo gerado: {arquivo_saida.name}")
        return "ok"
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha (código {e.returncode})")
        return f"erro:{e.returncode}"
    except Exception as e:
        print(f"[ERRO] Falha inesperada: {e}")
        return "erro:unexpected"


def processar_arquivo(arquivo_entrada: Path, pasta_saida: Path, pasta_scripts: Path, *, modo: str = "skip",
                      otimizar: bool = False, historico: bool = False):
    sufixo_saida = _sufixo_saida(modo, otimizar=otimizar, historico=historico)
    arquivo_saida = pasta_saida / f"{arquivo_entrada.stem}{sufixo_saida}"
    if arquivo_saida.exists():
        print(f"[PULADO] Saída já existe: {arquivo_saida.name}")
        return "pulado"

    print(f"\n[PROCESSANDO] {arquivo_entrada.name}")
    print(f"[ENTRADA]     {arquivo_entrada}")
    print(f"[SAÍDA]       {arquivo_saida}")
    print(f"[MODO]        {modo}")
    print(f"[OTIMIZAÇÃO]  {'Sim' if otimizar else 'Não'}")
    print(f"[HISTÓRICO]   {'Sim' if historico else 'Não'}")

    tentativas = []
    usar_patterns_inicial = not historico
    jobs_inicial = 1 if historico else None

    comando, user_words, user_patterns = montar_comando(
        arquivo_entrada, arquivo_saida, pasta_scripts,
        modo=modo, otimizar=otimizar, usar_patterns=usar_patterns_inicial,
        jobs=jobs_inicial, historico=historico
    )
    print(f"[USER-WORDS]  {user_words.name if user_words else 'não utilizado'}")
    print(f"[PATTERNS]    {user_patterns.name if user_patterns else 'não utilizado'}")
    tentativas.append((comando, f"normal{' histórico' if historico else ''}"))

    if user_patterns is not None and usar_patterns_inicial:
        comando2, _, _ = montar_comando(
            arquivo_entrada, arquivo_saida, pasta_scripts,
            modo=modo, otimizar=otimizar, usar_patterns=False,
            jobs=jobs_inicial, historico=historico
        )
        tentativas.append((comando2, "fallback sem user-patterns"))

    if modo == "force" or historico:
        comando3, _, _ = montar_comando(
            arquivo_entrada, arquivo_saida, pasta_scripts,
            modo=modo, otimizar=otimizar, usar_patterns=False,
            jobs=1, historico=historico
        )
        if all(tuple(cmd) != tuple(comando3) for cmd, _ in tentativas):
            tentativas.append((comando3, "fallback sem user-patterns e com --jobs 1"))

    ultimo = None
    for comando, desc in tentativas:
        ultimo = executar_comando(comando, arquivo_saida, desc)
        if ultimo == "ok":
            return "ok"

    print(f"[ERRO FINAL] Não foi possível processar {arquivo_entrada.name} após as tentativas automáticas.")
    return ultimo if ultimo else "erro"


def validar_dependencias(precisa_pngquant=False):
    if not verificar_ocrmypdf():
        print("ERRO: OCRmyPDF não está disponível neste Python.")
        print("Teste com: py -m ocrmypdf --version")
        return False
    if not verificar_tesseract():
        print("ERRO: Tesseract não foi encontrado no PATH.")
        print("Teste com: tesseract --version")
        return False
    if not verificar_idioma_portugues():
        print("ERRO: o idioma 'por' não está instalado no Tesseract.")
        print("Teste com: tesseract --list-langs")
        return False
    if precisa_pngquant and not verificar_pngquant():
        print("ATENÇÃO: pngquant não foi encontrado no PATH.")
        print("O OCR otimizado pode falhar ou perder eficiência sem ele.")
        print("Teste com: pngquant --version")
        return False
    return True


def modo_um_pdf(pasta_entrada: Path, pasta_saida: Path, pasta_scripts: Path, *, modo: str = "skip",
                otimizar: bool = False, historico: bool = False):
    pdfs = listar_pdfs_originais(pasta_entrada)
    if not pdfs:
        print("ERRO: nenhum PDF original encontrado na pasta de entrada.")
        print(f"Coloque 1 PDF em: {pasta_entrada}")
        return
    if len(pdfs) > 1:
        print("ERRO: há mais de um PDF original na pasta de entrada.")
        print("Para o modo de 1 PDF por vez, deixe apenas 1 PDF na pasta de entrada.")
        print("\nPDFs encontrados:")
        for pdf in pdfs:
            print(f" - {pdf.name}")
        return
    processar_arquivo(pdfs[0], pasta_saida, pasta_scripts, modo=modo, otimizar=otimizar, historico=historico)


def modo_lote(pasta_entrada: Path, pasta_saida: Path, pasta_scripts: Path, *, modo: str = "skip",
              otimizar: bool = False, historico: bool = False):
    pdfs = listar_pdfs_originais(pasta_entrada)
    if not pdfs:
        print("Nenhum PDF original encontrado para processar na pasta de entrada.")
        print(f"Pasta de entrada: {pasta_entrada}")
        return
    print("\nArquivos encontrados para processamento:")
    for pdf in pdfs:
        print(f" - {pdf.name}")
    total_ok = total_pulados = total_erros = 0
    for pdf in pdfs:
        resultado = processar_arquivo(pdf, pasta_saida, pasta_scripts, modo=modo, otimizar=otimizar, historico=historico)
        if resultado == "ok":
            total_ok += 1
        elif resultado == "pulado":
            total_pulados += 1
        else:
            total_erros += 1
    print("\n=== RESUMO ===")
    print(f"Processados com sucesso: {total_ok}")
    print(f"Pulados: {total_pulados}")
    print(f"Erros: {total_erros}")
    print(f"Pasta de saída: {pasta_saida}")


def mostrar_menu():
    print("\n" + "=" * 68)
    print(f"                     {APP_NOME} - MENU OCR")
    print("=" * 68)
    print("1 = OCR simples (1 PDF por vez) [usa --mode skip]")
    print("2 = OCR otimizado (1 PDF por vez) [usa --mode skip + --optimize 3]")
    print("3 = OCR em lote (vários PDFs) [usa --mode skip]")
    print("4 = OCR em lote otimizado (vários PDFs) [usa --mode skip + --optimize 3]")
    print("5 = Re-OCR (1 PDF por vez) [usa --mode redo]")
    print("6 = Forçar OCR em tudo (1 PDF por vez) [usa --mode force]")
    print("7 = Forçar OCR em tudo (lote) [usa --mode force]")
    print("8 = OCR histórico (1 PDF por vez) [force + rotate-pages + jobs 1 + sem patterns]")
    print("9 = OCR histórico em lote [force + rotate-pages + jobs 1 + sem patterns]")
    print("0 = Sair")
    print("=" * 68)
    print("Dica: user-words.txt é recomendado para nomes próprios e termos recorrentes.")
    print("Dica: user-patterns.txt é EXPERIMENTAL e pode ser ignorado automaticamente se atrapalhar.")
    print("=" * 68)


def main():
    pasta_scripts = Path(__file__).resolve().parent
    pasta_base = pasta_scripts.parent
    pasta_entrada, pasta_saida = obter_pastas(pasta_base)

    print(f"Programa: {APP_NOME}")
    print(f"Pasta do script: {pasta_scripts}")
    print(f"Pasta de entrada: {pasta_entrada}")
    print(f"Pasta de saída:   {pasta_saida}")

    while True:
        mostrar_menu()
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "0":
            print("Encerrando.")
            break
        elif opcao == "1" and validar_dependencias(False):
            modo_um_pdf(pasta_entrada, pasta_saida, pasta_scripts, modo="skip", otimizar=False)
        elif opcao == "2" and validar_dependencias(True):
            modo_um_pdf(pasta_entrada, pasta_saida, pasta_scripts, modo="skip", otimizar=True)
        elif opcao == "3" and validar_dependencias(False):
            modo_lote(pasta_entrada, pasta_saida, pasta_scripts, modo="skip", otimizar=False)
        elif opcao == "4" and validar_dependencias(True):
            modo_lote(pasta_entrada, pasta_saida, pasta_scripts, modo="skip", otimizar=True)
        elif opcao == "5" and validar_dependencias(False):
            print("Use esta opção quando o PDF já possui uma camada OCR antiga ou ruim.")
            modo_um_pdf(pasta_entrada, pasta_saida, pasta_scripts, modo="redo", otimizar=False)
        elif opcao == "6" and validar_dependencias(False):
            print("Use esta opção apenas quando quiser rasterizar todo o PDF e aplicar OCR em tudo.")
            modo_um_pdf(pasta_entrada, pasta_saida, pasta_scripts, modo="force", otimizar=False)
        elif opcao == "7" and validar_dependencias(False):
            print("Use esta opção apenas quando quiser rasterizar todo o PDF e aplicar OCR em tudo, em lote.")
            modo_lote(pasta_entrada, pasta_saida, pasta_scripts, modo="force", otimizar=False)
        elif opcao == "8" and validar_dependencias(False):
            print("Use esta opção para documentos históricos impressos/datilografados e casos mais difíceis.")
            print("O script usará force, rotate-pages, jobs 1 e user-patterns desativado por padrão.")
            modo_um_pdf(pasta_entrada, pasta_saida, pasta_scripts, modo="force", otimizar=False, historico=True)
        elif opcao == "9" and validar_dependencias(False):
            print("Use esta opção para documentos históricos impressos/datilografados e casos mais difíceis, em lote.")
            print("O script usará force, rotate-pages, jobs 1 e user-patterns desativado por padrão.")
            modo_lote(pasta_entrada, pasta_saida, pasta_scripts, modo="force", otimizar=False, historico=True)
        elif opcao not in {"1","2","3","4","5","6","7","8","9","0"}:
            print("Opção inválida. Tente novamente.")

if __name__ == '__main__':
    main()
