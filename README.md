# VPG_OCR v1.0.2

**VPG_OCR** é um kit organizado para OCR de PDFs no Windows, com instalação e uso simplificados.

## Destaques da versão 1.0.2
- fallback automático quando `user-patterns.txt` atrapalha
- novo **modo 8 = OCR histórico**
- novo **modo 9 = OCR histórico em lote**
- tratamento mais robusto para documentos difíceis
- instalador revisado

## Instalação
1. Abra `1_instalacao`.
2. Clique em `🛠️_CLIQUE_AQUI_PARA_INSTALAR.bat`.
3. Se o Windows mostrar a janela de segurança do `.bat`, clique em **Executar**.
4. Se o Python não estiver instalado, o instalador tentará instalar automaticamente o **Python 3.14** com `winget`.
5. Quando o instalador do Tesseract abrir, escolha o idioma do instalador como **English** e conclua a instalação.
6. O instalador também tentará ajustar automaticamente o `PATH` do Windows para o Tesseract.

## Utilização
1. Abra `2_utilizacao`.
2. Coloque os PDFs em `ENTRADA_coloque_aqui_seus_pdfs`.
3. Clique em `🚀_CLIQUE_AQUI_PARA_USAR_OCR.bat`.
4. Os resultados aparecerão em `SAIDA_pdfs_processados`.

## Observações sobre os arquivos auxiliares
- `user-words.txt`: recomendado para nomes próprios, lugares, siglas e termos recorrentes.
- `user-patterns.txt`: recurso experimental. O script pode ignorá-lo automaticamente se detectar falhas.

## Sobre o modo 8 e o modo 9
Os modos 8 e 9 foram pensados para documentos históricos impressos/datilografados. Eles usam:
- `--mode force`
- `--rotate-pages`
- `--jobs 1`
- `user-patterns` desativado por padrão
