# VPG_OCR

**VPG_OCR é um kit organizado para aplicação de OCR em PDFs no Windows, com foco em simplicidade de instalação e uso. O projeto inclui instalação por 1 clique, execução por 1 clique, OCR simples, otimizado e em lote, além de suporte a arquivos auxiliares para melhorar o reconhecimento de termos recorrentes e gerar PDFs pesquisáveis.

## Estrutura

```text
VPG_OCR/
├── 0_LEIA-ME.txt
├── README.md
├── LICENSE
├── THIRD_PARTY_NOTICES.txt
├── .gitignore
├── 1_instalacao/
│   ├── 🛠️_CLIQUE_AQUI_PARA_INSTALAR.bat
│   ├── arquivos/
│   └── script_instalacao/
│       └── instalacao_OCR.py
├── 2_utilizacao/
│   ├── 🚀_CLIQUE_AQUI_PARA_USAR_OCR.bat
│   ├── ENTRADA_coloque_aqui_seus_pdfs/
│   ├── SAIDA_pdfs_processados/
│   └── scripts_OCR/
│       ├── 5_OCR_MENU.py
│       ├── user-words.txt
│       └── user-patterns.txt
└── 3_obsoleto_bkp/
```

## Instalação
1. Abra `1_instalacao`.
2. Clique em `🛠️_CLIQUE_AQUI_PARA_INSTALAR.bat`.
3. Coloque em `1_instalacao/arquivos` os arquivos locais necessários:
   - `tesseract-ocr-w64-setup-5.5.0.20241111.exe`
   - `tesseract-ocr-w64-setup-5.4.0.20240606.exe`
   - `por.traineddata`

## Utilização
1. Abra `2_utilizacao`.
2. Coloque os PDFs em `ENTRADA_coloque_aqui_seus_pdfs`.
3. Clique em `🚀_CLIQUE_AQUI_PARA_USAR_OCR.bat`.
4. Os resultados aparecerão em `SAIDA_pdfs_processados`.

## Personalização do OCR
O script usa automaticamente, se existirem e tiverem conteúdo:
- `user-words.txt`
- `user-patterns.txt`

Use `user-words.txt` para nomes próprios, siglas, numerais romanos e termos recorrentes.
Use `user-patterns.txt` para padrões conservadores.

## Licença do seu wrapper
Este repositório inclui uma licença MIT para os arquivos próprios do VPG_OCR.
Veja também `THIRD_PARTY_NOTICES.txt` para componentes de terceiros.
