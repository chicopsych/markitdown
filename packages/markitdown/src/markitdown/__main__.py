# SPDX-FileCopyrightText: 2024-present Adam Fourney <adamfo@microsoft.com>
#
# SPDX-License-Identifier: MIT
import argparse
import sys
import codecs
from textwrap import dedent
from importlib.metadata import entry_points
from .__about__ import __version__
from ._markitdown import MarkItDown, StreamInfo, DocumentConverterResult


def main():
    parser = argparse.ArgumentParser(
        description="Converte vários formatos de arquivo para markdown.",
        prog="markitdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage=dedent(
            """
            SINTAXE:

                markitdown <OPCIONAL: NOME_DO_ARQUIVO>
                Se NOME_DO_ARQUIVO estiver vazio, markitdown lê da entrada padrão (stdin).

            EXEMPLO:

                markitdown exemplo.pdf

                OU

                cat exemplo.pdf | markitdown

                OU

                markitdown < exemplo.pdf

                OU para salvar em um arquivo use

                markitdown exemplo.pdf -o exemplo.md

                OU

                markitdown exemplo.pdf > exemplo.md
            """
        ).strip(),
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="mostra o número da versão e sai",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Nome do arquivo de saída. Se não fornecido, a saída é escrita no stdout.",
    )

    parser.add_argument(
        "-x",
        "--extension",
        help="Fornece uma dica sobre a extensão do arquivo (ex: ao ler de stdin).",
    )

    parser.add_argument(
        "-m",
        "--mime-type",
        help="Fornece uma dica sobre o tipo MIME do arquivo.",
    )

    parser.add_argument(
        "-c",
        "--charset",
        help="Fornece uma dica sobre o conjunto de caracteres do arquivo (ex: UTF-8).",
    )

    parser.add_argument(
        "-d",
        "--use-docintel",
        action="store_true",
        help="Usa Document Intelligence para extrair texto em vez de conversão offline. Requer um Endpoint de Document Intelligence válido.",
    )

    parser.add_argument(
        "-e",
        "--endpoint",
        type=str,
        help="Endpoint do Document Intelligence. Obrigatório se estiver usando Document Intelligence.",
    )

    parser.add_argument(
        "-p",
        "--use-plugins",
        action="store_true",
        help="Usa plugins de terceiros para converter arquivos. Use --list-plugins para ver plugins instalados.",
    )

    parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="Lista plugins de terceiros instalados. Plugins são carregados ao usar a opção -p ou --use-plugin.",
    )

    parser.add_argument(
        "--keep-data-uris",
        action="store_true",
        help="Mantém URIs de dados (como imagens codificadas em base64) na saída. Por padrão, URIs de dados são truncadas.",
    )

    parser.add_argument("filename", nargs="?")
    args = parser.parse_args()

    # Analisa a dica de extensão
    extension_hint = args.extension
    if extension_hint is not None:
        extension_hint = extension_hint.strip().lower()
        if len(extension_hint) > 0:
            if not extension_hint.startswith("."):
                extension_hint = "." + extension_hint
        else:
            extension_hint = None

    # Analisa o tipo mime
    mime_type_hint = args.mime_type
    if mime_type_hint is not None:
        mime_type_hint = mime_type_hint.strip()
        if len(mime_type_hint) > 0:
            if mime_type_hint.count("/") != 1:
                _exit_with_error(f"Invalid MIME type: {mime_type_hint}")
        else:
            mime_type_hint = None

    # Analisa o conjunto de caracteres (charset)
    charset_hint = args.charset
    if charset_hint is not None:
        charset_hint = charset_hint.strip()
        if len(charset_hint) > 0:
            try:
                charset_hint = codecs.lookup(charset_hint).name
            except LookupError:
                _exit_with_error(f"Invalid charset: {charset_hint}")
        else:
            charset_hint = None

    stream_info = None
    if (
        extension_hint is not None
        or mime_type_hint is not None
        or charset_hint is not None
    ):
        stream_info = StreamInfo(
            extension=extension_hint, mimetype=mime_type_hint, charset=charset_hint
        )

    if args.list_plugins:
        # Lista plugins instalados, então sai
        print("Plugins de terceiros do MarkItDown Instalados:\n")
        plugin_entry_points = list(entry_points(group="markitdown.plugin"))
        if len(plugin_entry_points) == 0:
            print("  * Nenhum plugin de terceiros instalado.")
            print(
                "\nEncontre plugins pesquisando pela hashtag #markitdown-plugin no GitHub.\n"
            )
        else:
            for entry_point in plugin_entry_points:
                print(f"  * {entry_point.name:<16}\t(package: {entry_point.value})")
            print(
                "\nUse a opção -p (ou --use-plugins) para habilitar plugins de terceiros.\n"
            )
        sys.exit(0)

    if args.use_docintel:
        if args.endpoint is None:
            _exit_with_error(
                "Document Intelligence Endpoint is required when using Document Intelligence."
            )
        elif args.filename is None:
            _exit_with_error("Filename is required when using Document Intelligence.")

        markitdown = MarkItDown(
            enable_plugins=args.use_plugins, docintel_endpoint=args.endpoint
        )
    else:
        markitdown = MarkItDown(enable_plugins=args.use_plugins)

    if args.filename is None:
        result = markitdown.convert_stream(
            sys.stdin.buffer,
            stream_info=stream_info,
            keep_data_uris=args.keep_data_uris,
        )
    else:
        result = markitdown.convert(
            args.filename, stream_info=stream_info, keep_data_uris=args.keep_data_uris
        )

    _handle_output(args, result)


def _handle_output(args, result: DocumentConverterResult):
    """Lida com a saída para stdout ou arquivo"""
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.markdown)
    else:
        # Lida com erros de codificação stdout com mais elegância
        print(
            result.markdown.encode(sys.stdout.encoding, errors="replace").decode(
                sys.stdout.encoding
            )
        )


def _exit_with_error(message: str):
    print(message)
    sys.exit(1)


if __name__ == "__main__":
    main()
